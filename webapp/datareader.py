import ZerodhaConnector as zc

def get_candles(scrips, start_date, end_date):
    # TODO: Check in the data csv file first before fetching data from Zerodha
    candles = {}
    for scrip in scrips:
        candles[scrip] = zc.get_candles(scrip, start_date, end_date, duration='week')
    return candles
