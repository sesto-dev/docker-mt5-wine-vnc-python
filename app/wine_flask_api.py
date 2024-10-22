from flask import Flask, jsonify
import MetaTrader5 as mt5

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)