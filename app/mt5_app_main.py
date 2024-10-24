from flask import Flask, jsonify, request
import MetaTrader5 as mt5
import logging
import json
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, generate_latest
from lib import (
    get_timeframe,
    send_market_order,
    close_position,
    close_all_positions,
    modify_sl_tp,
    get_positions,
    get_deal_from_ticket,
    get_order_from_ticket,
    get_last_error,
    get_last_error_str,
    get_positions_total,
    get_history_deals,
    get_history_orders
)
from datetime import datetime
import pandas as pd
import pytz

app = Flask(__name__)

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(message)s')
logHandler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])

# Request logging middleware
@app.before_request
def log_request_info():
    logger.info('Request', extra={
        'method': request.method,
        'url': request.url,
        'headers': dict(request.headers),
        'body': request.get_data().decode('utf-8')
    })

@app.after_request
def log_response_info(response):
    logger.info('Response', extra={
        'status': response.status,
        'headers': dict(response.headers),
        'body': response.get_data().decode('utf-8')
    })
    return response

@app.route('/health')
def health_check():
    initialized = mt5.initialize() if mt5 is not None else False
    return jsonify({
        "status": "healthy",
        "mt5_connected": mt5 is not None,
        "mt5_initialized": initialized
    }), 200

@app.route('/metrics')
def metrics():
    return generate_latest()

@app.route('/symbol_info/<symbol>', methods=['GET'])
def get_symbol_info(symbol):
    if not mt5.initialize():
        return jsonify({"error": "Failed to initialize MT5."}), 500

    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return jsonify({"error": f"Symbol {symbol} not found."}), 404

    return jsonify({
        "symbol": symbol,
        "bid": symbol_info.bid,
        "ask": symbol_info.ask,
        "spread": symbol_info.spread,
        "volume": symbol_info.volume
    }), 200

@app.route('/symbol_info_tick/<symbol>', methods=['GET'])
def get_symbol_info_tick_endpoint(symbol):
    if not mt5.initialize():
        return jsonify({"error": "Failed to initialize MT5."}), 500

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return jsonify({"error": f"Symbol {symbol} not found."}), 404

    return jsonify({
        "symbol": symbol,
        "bid": tick.bid,
        "ask": tick.ask,
        "time": tick.time
    }), 200

# Existing endpoints...

# New Endpoints Corresponding to business.py

@app.route('/order_send', methods=['POST'])
def order_send_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON data."}), 400

    order_result = send_market_order(**data)
    if order_result is None:
        error_code = get_last_error()
        error_description = get_last_error_str()
        return jsonify({"error": "Failed to send market order", "code": error_code, "description": error_description}), 500
    elif order_result.retcode != 'TRADE_RETCODE_DONE':
        return jsonify({
            "error": "Order not completed",
            "retcode": order_result.retcode,
            "description": mt5.MT5_RETCODE_DESCRIPTION.get(order_result.retcode, 'Unknown')
        }), 500

    return jsonify({"success": True, "order": order_result._asdict()}), 200

@app.route('/last_error', methods=['GET'])
def last_error_endpoint():
    error_code = get_last_error()
    return jsonify({"last_error_code": error_code}), 200

@app.route('/last_error_str', methods=['GET'])
def last_error_str_endpoint():
    error_str = get_last_error_str()
    return jsonify({"last_error_str": error_str}), 200

@app.route('/positions_total', methods=['GET'])
def positions_total_endpoint():
    total = get_positions_total()
    return jsonify({"total_positions": total}), 200

@app.route('/positions_get', methods=['GET'])
def positions_get_endpoint():
    magic = request.args.get('magic', type=int)
    positions = get_positions(magic)
    if positions.empty:
        return jsonify({"positions": []}), 200
    return jsonify(positions.to_dict(orient='records')), 200

@app.route('/history_deals_get', methods=['GET'])
def history_deals_get_endpoint():
    from_timestamp = request.args.get('from_timestamp', type=int)
    to_timestamp = request.args.get('to_timestamp', type=int)
    position = request.args.get('position', type=int)

    if not from_timestamp or not to_timestamp:
        return jsonify({"error": "Missing required parameters: from_timestamp, to_timestamp"}), 400

    deals = get_history_deals(from_timestamp, to_timestamp, position)
    if not deals:
        return jsonify({"error": "No deals found"}), 404

    deals_df = pd.DataFrame([deal._asdict() for deal in deals])
    return jsonify(deals_df.to_dict(orient='records')), 200

@app.route('/history_orders_get', methods=['GET'])
def history_orders_get_endpoint():
    ticket = request.args.get('ticket', type=int)
    if not ticket:
        return jsonify({"error": "Missing required parameter: ticket"}), 400

    orders = get_history_orders(ticket)
    if not orders:
        return jsonify({"error": "No orders found for the given ticket"}), 404

    orders_df = pd.DataFrame([order._asdict() for order in orders])
    return jsonify(orders_df.to_dict(orient='records')), 200

if __name__ == '__main__':
    if not mt5.initialize():
        logger.error("Failed to initialize MT5.")
    app.run(host='0.0.0.0', port=5001)
