from flask import Flask, jsonify
from mt5linux import MetaTrader5
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

try:
    mt5 = MetaTrader5(
        host = 'localhost',
        port = 18812
    )
    logging.info("Successfully connected to MT5 server")
except Exception as e:
    logging.error(f"Failed to connect to MT5 server: {str(e)}")
    mt5 = None

@app.route('/')
def get_health_check():
    return jsonify({"status": "ok"}), 200

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
