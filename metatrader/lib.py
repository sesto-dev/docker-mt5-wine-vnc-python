from mt5linux import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd

def fetch_data_pos(symbol: str, timeframe, bars: int) -> pd.DataFrame:
    try:
        return mt5.copy_rates_from_pos(symbol, timeframe.value, 0, bars)
    except Exception as e:
        print(f"Exception fetching data for {symbol} on {timeframe}: {e}")
        return None
    
def fetch_data_range(symbol: str, timeframe, from_date: datetime, to_date: datetime) -> pd.DataFrame:
    try:
        return mt5.copy_rates_range(symbol, timeframe.value, from_date, to_date)
    except Exception as e:
        print(f"Exception fetching data for {symbol} on {timeframe}: {e}")
        return None

def send_market_order(symbol, volume, order_type, sl=0.0, tp=0.0,
                      deviation=20, comment='', magic=0, type_filling=mt5.ORDER_FILLING_IOC):
    if order_type not in ['buy', 'sell']:
        print(f"Invalid order_type: {order_type}. Must be 'buy' or 'sell'.")
        return None

    if volume <= 0:
        print("Volume must be greater than 0.")
        return None

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"Failed to get tick for symbol: {symbol}")
        return None

    order_type_dict = {'buy': mt5.ORDER_TYPE_BUY, 'sell': mt5.ORDER_TYPE_SELL}
    price_dict = {'buy': tick.ask, 'sell': tick.bid}

    if price_dict[order_type] == 0.0:
        print(f"Invalid price retrieved for symbol: {symbol} and order_type: {order_type}")
        return None

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type_dict[order_type],
        "price": price_dict[order_type],
        "sl": sl,
        "tp": tp,
        "deviation": deviation,
        "magic": magic,
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": type_filling,
    }

    order_result = mt5.order_send(request)

    if order_result is None:
        error_code = mt5.last_error()
        error_description = mt5.last_error_str()
        print(f"Order failed, error code: {error_code}, description: {error_description}")
        return None
    elif order_result.retcode != mt5.TRADE_RETCODE_DONE:
        return None
    
    print(f"Order successfully placed for {symbol}")
    return order_result


def close_position(position, deviation=20, magic=0, comment='', type_filling=mt5.ORDER_FILLING_IOC):
    if 'type' not in position or 'ticket' not in position:
        print("Position dictionary missing 'type' or 'ticket' keys.")
        return None

    order_type_dict = {
        0: mt5.ORDER_TYPE_BUY,   # Corrected
        1: mt5.ORDER_TYPE_SELL   # Corrected
    }

    position_type = position['type']
    if position_type not in order_type_dict:
        print(f"Unknown position type: {position_type}")
        return None

    tick = mt5.symbol_info_tick(position['symbol'])
    if tick is None:
        print(f"Failed to get tick for symbol: {position['symbol']}")
        return None

    price_dict = {
        0: tick.ask,  # Buy order uses Ask price
        1: tick.bid   # Sell order uses Bid price
    }

    price = price_dict[position_type]
    if price == 0.0:
        print(f"Invalid price retrieved for symbol: {position['symbol']}")
        return None

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": position['ticket'],  # select the position you want to close
        "symbol": position['symbol'],
        "volume": position['volume'],  # FLOAT
        "type": order_type_dict[position_type],
        "price": price,
        "deviation": deviation,  # INTEGER
        "magic": magic,          # INTEGER
        "comment": comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": type_filling,
    }

    order_result = mt5.order_send(request)

    if order_result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to close position {position['ticket']}: {order_result.comment}")
        return None

    print(f"Position {position['ticket']} closed successfully.")
    return order_result


def close_all_positions(order_type='all', magic=None, type_filling=mt5.ORDER_FILLING_IOC):
    order_type_dict = {
        'buy': mt5.ORDER_TYPE_BUY,
        'sell': mt5.ORDER_TYPE_SELL
    }

    if mt5.positions_total() > 0:
        positions = mt5.positions_get()
        if positions is None:
            print("Failed to retrieve positions.")
            return []

        positions_data = [pos._asdict() for pos in positions]
        positions_df = pd.DataFrame(positions_data)

        # Filtering by magic if specified
        if magic is not None:
            positions_df = positions_df[positions_df['magic'] == magic]

        # Filtering by order_type if not 'all'
        if order_type != 'all':
            if order_type not in order_type_dict:
                print(f"Invalid order_type: {order_type}. Must be 'buy', 'sell', or 'all'.")
                return []
            positions_df = positions_df[positions_df['type'] == order_type_dict[order_type]]

        if positions_df.empty:
            print('No open positions matching the criteria.')
            return []

        results = []
        for _, position in positions_df.iterrows():
            order_result = close_position(position, type_filling=type_filling)
            if order_result:
                results.append(order_result)
            else:
                print(f"Failed to close position {position['ticket']}.")
        
        return results
    else:
        print("No open positions to close.")
        return []


def modify_sl_tp(ticket, stop_loss, take_profit):
    if not isinstance(ticket, int):
        print("Ticket must be an integer.")
        return None

    try:
        stop_loss = float(stop_loss)
        take_profit = float(take_profit)
    except ValueError:
        print("Stop loss and take profit must be numbers.")
        return None

    request = {
        'action': mt5.TRADE_ACTION_SLTP,
        'position': ticket,
        'sl': stop_loss,
        'tp': take_profit
    }

    res = mt5.order_send(request)

    if res.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to modify SL/TP for ticket {ticket}: {res.comment}")
        return None

    print(f"SL/TP modified for ticket {ticket} successfully.")
    return res


def get_positions(magic=None):
    total_positions = mt5.positions_total()
    if total_positions > 0:
        positions = mt5.positions_get()
        if positions is None:
            print("Failed to retrieve positions.")
            return pd.DataFrame()

        positions_data = [pos._asdict() for pos in positions]
        positions_df = pd.DataFrame(positions_data)

        if magic is not None:
            positions_df = positions_df[positions_df['magic'] == magic]

        return positions_df
    else:
        return pd.DataFrame(columns=['ticket', 'time', 'time_msc', 'time_update', 'time_update_msc', 'type',
                                     'magic', 'identifier', 'reason', 'volume', 'price_open', 'sl', 'tp',
                                     'price_current', 'swap', 'profit', 'symbol', 'comment', 'external_id'])
    

def get_deal_from_ticket(ticket, TIMEZONE, from_date=None, to_date=None):
    if not isinstance(ticket, int):
        print("Ticket must be an integer.")
        return None

    # Define default date range if not provided
    if from_date is None or to_date is None:
        to_date = datetime.now(TIMEZONE)
        from_date = to_date - timedelta(minutes=15)  # Adjust based on polling interval

    # Convert datetime to MT5 time (integer)
    from_timestamp = int(from_date.timestamp())
    to_timestamp = int(to_date.timestamp())

    # Retrieve deals using the specified date range and position
    deals = mt5.history_deals_get(from_timestamp, to_timestamp, position=ticket)
    if not deals:
        print(f"No deal history found for position ticket {ticket} between {from_date} and {to_date}.")
        return None

    # Convert deals to a DataFrame for easier processing
    deals_df = pd.DataFrame([deal._asdict() for deal in deals])

    # Optional: Verify that all deals belong to the same symbol
    if not deals_df.empty and not all(deal == deals_df['symbol'].iloc[0] for deal in deals_df['symbol']):
        print(f"Inconsistent symbols found in deals for position ticket {ticket}.")
        return None

    # Extract relevant information
    if not deals_df.empty:
        deal_details = {
            'ticket': ticket,
            'symbol': deals_df['symbol'].iloc[0],
            'type': 'buy' if deals_df['type'].iloc[0] == mt5.DEAL_TYPE_BUY else 'sell',
            'volume': deals_df['volume'].sum(),
            'open_time': datetime.fromtimestamp(deals_df['time'].min(), tz=TIMEZONE),
            'close_time': datetime.fromtimestamp(deals_df['time'].max(), tz=TIMEZONE),
            'open_price': deals_df['price'].iloc[0],
            'close_price': deals_df['price'].iloc[-1],
            'profit': deals_df['profit'].sum(),
            'commission': deals_df['commission'].sum(),
            'swap': deals_df['swap'].sum(),
            'comment': deals_df['comment'].iloc[-1]  # Use the last comment if multiple
        }
        return deal_details
    else:
        return None


def get_order_from_ticket(ticket):
    if not isinstance(ticket, int):
        print("Ticket must be an integer.")
        return None

    # Get the order history
    order = mt5.history_orders_get(ticket=ticket)
    if order is None or len(order) == 0:
        print(f"No order history found for ticket {ticket}")
        return None

    # Convert order to a dictionary
    order_dict = order[0]._asdict()

    return order_dict