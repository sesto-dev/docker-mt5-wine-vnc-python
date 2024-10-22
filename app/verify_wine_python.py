from mt5linux import MetaTrader5 as mt5
import sys

def main():
    print("Python Version:", sys.version)
    print("Python Executable:", sys.executable)
    print("Python Path:", sys.path)

    # Initialize MetaTrader5
    if not mt5.initialize(host='localhost', port=18812):
        print("Failed to initialize MT5:", mt5.last_error())
        sys.exit(1)
    print("MT5 initialized successfully.")

    # Get symbol info for EURUSD
    symbol_info = mt5.symbol_info("EURUSD")
    if symbol_info is None:
        print("Failed to get symbol info for EURUSD.")
    else:
        print("Symbol Info for EURUSD:", symbol_info)

    # Shutdown MT5
    mt5.shutdown()

if __name__ == "__main__":
    main()