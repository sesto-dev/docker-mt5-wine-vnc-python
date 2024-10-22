from flask import Flask, jsonify, request
from mt5linux import MetaTrader5
import logging
import json
from pythonjsonlogger import jsonlogger
from prometheus_client import Counter, Histogram, generate_latest

mt5server_port = 18812

app = Flask(__name__)

# Configure JSON logging
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

try:
    logger.info(f"Attempting to connect to MT5 server at localhost:{mt5server_port}")
    mt5 = MetaTrader5(
        host='localhost',
        port=mt5server_port
    )
    if not mt5.initialize():
        logger.error(f"Failed to initialize MT5: {mt5.last_error()}")
        mt5 = None
    else:
        logger.info("Successfully connected to MT5 server")
except Exception as e:
    logger.error(f"Failed to connect to MT5 server: {str(e)}")
    logger.error(f"Exception type: {type(e).__name__}")
    logger.error(f"Exception args: {e.args}")
    mt5 = None

# Add a health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "mt5_connected": mt5 is not None,
        "mt5_initialized": mt5.initialize() if mt5 is not None else False
    }), 200

@app.route('/metrics')
def metrics():
    return generate_latest()

@app.route('/symbol_info/<symbol>')
def get_symbol_info(symbol):
    if not mt5.initialize():
        return jsonify({"error": "Failed to initialize MT5"}), 500
    
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        return jsonify({"error": f"Failed to get info for {symbol}"}), 404
    
    return jsonify({
        "bid": symbol_info.bid,
        "ask": symbol_info.ask,
        "spread": symbol_info.spread,
        "volume": symbol_info.volume,
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
