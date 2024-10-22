from flask import Flask, jsonify, request
import MetaTrader5 as mt5
import logging
import json
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, generate_latest
from lib import (
    fetch_data_pos,
    fetch_data_range,
    send_market_order,
    close_position,
    close_all_positions,
    modify_sl_tp,
    get_positions,
    get_deal_from_ticket,
    get_order_from_ticket
)
from datetime import datetime
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

# Endpoint for fetch_data_pos
@app.route('/fetch_data_pos', methods=['GET'])
def fetch_data_pos_endpoint():
    symbol = request.args.get('symbol')
    timeframe = request.args.get('timeframe')
    bars = request.args.get('bars', type=int)

    if not symbol or not timeframe or bars is None:
        return jsonify({"error": "Missing required parameters: symbol, timeframe, bars"}), 400

    data = fetch_data_pos(symbol, timeframe, bars)
    if data is not None:
        return jsonify(data.to_dict()), 200
    else:
        return jsonify({"error": "Failed to fetch data"}), 500

# Endpoint for fetch_data_range
@app.route('/fetch_data_range', methods=['GET'])
def fetch_data_range_endpoint():
    symbol = request.args.get('symbol')
    timeframe = request.args.get('timeframe')
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')
    timezone_str = request.args.get('timezone', 'UTC')

    if not symbol or not timeframe or not from_date_str or not to_date_str:
        return jsonify({"error": "Missing required parameters: symbol, timeframe, from_date, to_date"}), 400

    try:
        timezone = pytz.timezone(timezone_str)
        from_date = datetime.fromisoformat(from_date_str).astimezone(timezone)
        to_date = datetime.fromisoformat(to_date_str).astimezone(timezone)
    except Exception as e:
        return jsonify({"error": f"Invalid date format or timezone: {e}"}), 400

    data = fetch_data_range(symbol, timeframe, from_date, to_date)
    if data is not None:
        return jsonify(data.to_dict()), 200
    else:
        return jsonify({"error": "Failed to fetch data"}), 500

# Endpoint for send_market_order
@app.route('/send_market_order', methods=['POST'])
def send_market_order_endpoint():
    data = request.get_json()
    required_fields = ['symbol', 'volume', 'order_type']
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400

    symbol = data['symbol']
    volume = data['volume']
    order_type = data['order_type']
    sl = data.get('sl', 0.0)
    tp = data.get('tp', 0.0)
    deviation = data.get('deviation', 20)
    comment = data.get('comment', '')
    magic = data.get('magic', 0)
    type_filling = data.get('type_filling', mt5.ORDER_FILLING_IOC)

    order_result = send_market_order(symbol, volume, order_type, sl, tp, deviation, comment, magic, type_filling)
    if order_result:
        return jsonify({"success": True, "order": order_result._asdict()}), 200
    else:
        return jsonify({"error": "Failed to send market order"}), 500

# Endpoint for close_position
@app.route('/close_position', methods=['POST'])
def close_position_endpoint():
    data = request.get_json()
    required_fields = ['ticket', 'symbol', 'type', 'volume']
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400

    position = {
        'ticket': data['ticket'],
        'symbol': data['symbol'],
        'type': data['type'],
        'volume': data['volume']
    }
    deviation = data.get('deviation', 20)
    magic = data.get('magic', 0)
    comment = data.get('comment', '')
    type_filling = data.get('type_filling', mt5.ORDER_FILLING_IOC)

    order_result = close_position(position, deviation, magic, comment, type_filling)
    if order_result:
        return jsonify({"success": True, "order": order_result._asdict()}), 200
    else:
        return jsonify({"error": "Failed to close position"}), 500

# Endpoint for close_all_positions
@app.route('/close_all_positions', methods=['POST'])
def close_all_positions_endpoint():
    data = request.get_json()
    order_type = data.get('order_type', 'all')
    magic = data.get('magic', None)
    type_filling = data.get('type_filling', mt5.ORDER_FILLING_IOC)

    order_results = close_all_positions(order_type, magic, type_filling)
    if order_results:
        orders = [result._asdict() for result in order_results]
        return jsonify({"success": True, "closed_orders": orders}), 200
    else:
        return jsonify({"error": "Failed to close some or all positions"}), 500

# Endpoint for modify_sl_tp
@app.route('/modify_sl_tp', methods=['POST'])
def modify_sl_tp_endpoint():
    data = request.get_json()
    required_fields = ['ticket', 'stop_loss', 'take_profit']
    if not all(field in data for field in required_fields):
        return jsonify({"error": f"Missing required fields: {required_fields}"}), 400

    ticket = data['ticket']
    stop_loss = data['stop_loss']
    take_profit = data['take_profit']

    result = modify_sl_tp(ticket, stop_loss, take_profit)
    if result:
        return jsonify({"success": True, "result": result._asdict()}), 200
    else:
        return jsonify({"error": "Failed to modify SL/TP"}), 500

# Endpoint for get_positions
@app.route('/get_positions', methods=['GET'])
def get_positions_endpoint():
    magic = request.args.get('magic', type=int)
    positions_df = get_positions(magic)
    if not positions_df.empty:
        return jsonify(positions_df.to_dict(orient='records')), 200
    else:
        return jsonify({"positions": []}), 200

# Endpoint for get_deal_from_ticket
@app.route('/get_deal_from_ticket', methods=['GET'])
def get_deal_from_ticket_endpoint():
    ticket = request.args.get('ticket', type=int)
    timezone_str = request.args.get('timezone', 'UTC')
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')

    if not ticket:
        return jsonify({"error": "Missing required parameter: ticket"}), 400

    try:
        timezone = pytz.timezone(timezone_str)
    except Exception as e:
        return jsonify({"error": f"Invalid timezone: {e}"}), 400

    from_date = None
    to_date = None
    if from_date_str and to_date_str:
        try:
            from_date = datetime.fromisoformat(from_date_str).astimezone(timezone)
            to_date = datetime.fromisoformat(to_date_str).astimezone(timezone)
        except Exception as e:
            return jsonify({"error": f"Invalid date format: {e}"}), 400

    deal_details = get_deal_from_ticket(ticket, timezone, from_date, to_date)
    if deal_details:
        return jsonify(deal_details), 200
    else:
        return jsonify({"error": "No deal details found"}), 404

# Endpoint for get_order_from_ticket
@app.route('/get_order_from_ticket', methods=['GET'])
def get_order_from_ticket_endpoint():
    ticket = request.args.get('ticket', type=int)
    if not ticket:
        return jsonify({"error": "Missing required parameter: ticket"}), 400

    order = get_order_from_ticket(ticket)
    if order:
        return jsonify(order), 200
    else:
        return jsonify({"error": "Order not found"}), 404

if __name__ == '__main__':
    if not mt5.initialize():
        logger.error("Failed to initialize MT5.")
    app.run(host='0.0.0.0', port=5001)