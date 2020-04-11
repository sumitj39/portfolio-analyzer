import json
import logging
import os
import sys
import time
from datetime import timedelta

import click
import pandas as pd
import requests

ts = pd.Timestamp

"""
the url https://kitecharts-aws.zerodha.com/api/chart/{instrument_id}/{duration}?&from={start_date}&to={end_date}
returns maximum of 2000 candles, after that it returns an exception for too many candles request error.
So, the below varaible maps duration to candle limit by day
i.e., for minute bar, 6 days of  1 minute candle data makes up ~2000 candles
"""
duration_limits = {
    "minute": 6,
    "3minute": 18,
    "5minute": 30,
    "10minute": 60,
    "15minute": 90,
    "30minute": 180,
    "60minute": 360,
    "day": 2000,
    "week": 2000
}
DEFAULT_EXCHANGE = 'NSE'
cur_path = os.path.dirname(os.path.abspath(__file__))
instruments_file = cur_path + "/" + "instruments.csv"


def verify_date_format(dt):
    try:
        time.strptime(dt, "%Y-%m-%d")
    except:
        logging.error(
            "{0} is not in parsable format: Use YYYY-MM-DD format".format(dt))
        raise


def verify_duration(duration):
    return duration in duration_limits.keys()


def convert_date_in_intervals(fromdate, todate, diff):

    # TODO: If the stock is not present during start date, it will skip 'diff' number of days
    # diff should be an integer
    # date should be in yyyy-mm-dd format. Otherwise it will throw error/ unexpected behavior
    # Converts fromdate-todate in the range of [fromdate+interval, fromdate+2*interval ... to todate]
    # If the last period is less than given interval, we will make it a 90 days interval
    # For eg: start 1st nov, end =10th nov, interval = 3, periods will be [(1-3), (4-6), (7-9), (8-10)]
    fromdate_dt = ts(fromdate).date()
    todate_dt = ts(todate).date()
    diff_dt = timedelta(days=diff - 1)

    if todate_dt - fromdate_dt < diff_dt:
        return [(fromdate_dt, todate_dt)]
    curdate = fromdate_dt
    intervals = []
    while curdate + diff_dt < todate_dt:
        interval = (curdate, curdate + diff_dt)
        intervals.append(interval)
        curdate = curdate + diff_dt
    intervals.append((todate_dt - diff_dt, todate_dt))
    return intervals


def get_instruments(exchange='NSE', instrument_type='EQ'):
    df = pd.read_csv(instruments_file)
    filtered_df = df[(df['instrument_type'] == instrument_type) & (df['exchange'] == exchange)][[
        'exchange', 'instrument_type', 'tradingsymbol', 'instrument_token', 'segment']]
    # print(filtered_df[filtered_df['tradingsymbol']=='KOTAKBANK'])
    return filtered_df


def get_id_for_instrument(stockname, exchange='NSE', instrument_type='EQ'):
    df = get_instruments(exchange, instrument_type)
    row = df[df['tradingsymbol'] == stockname]
    if(row.shape[0] == 0):
        logging.debug(row)
        logging.error(
            "CSV file contains {0} records for instrument_token. expected: 1".format(row.shape[0]))
        raise Exception("Enter valid stockname ({0}), exchangename ({1}), instrument_type ({2})"
                        .format(stockname, exchange, instrument_type))
    return (row['instrument_token'].values[0])


def parse_to_df(json_response):
    json_response = json.loads(json_response)
    # if isinstance(json_response, str):
    #     json_response = json.loads(json_response, encoding='utf-8')
    #     # may throw exception
    # if isinstance(json_response, str):
    #     json_response = json.loads(json_response)
    # may throw exception
    data = json_response.get("data")
    if data is None:
        logging.error(
            "json response does not contain key 'data' or no data present")
        return None
    candles = data.get("candles")
    if candles is None:
        logging.error(
            "json response does not contain key 'candles' or no candles present")
        return None

    # Zerodha may return no values inside candles because
    # 1. company might not have been listed in that time
    # 2. Zerodha doesn't contain historical data for that point
    if isinstance(candles, list) and candles == []:
        logging.warning("No candles found for the given interval")
        # pd.DataFrame(columns=["ts", "open", "high", "low", "close", "volume"])
        return None
    candles = pd.read_json(json.dumps(candles), orient="columns")
    candles.columns = ["ts", "Open", "High", "Low", "Close", "Volume"]
    candles['Adj Close'] = candles['Close']
    candles['Date'] = pd.DatetimeIndex(pd.to_datetime(candles['ts']))
    del candles['ts']

    # print (pd.DatetimeIndex(["2018-01-01T00:00:00+0530"]).strftime("%Y-%m-%d"))
    # candles['ts'] = candles.replace({"ts", r"\+0530"}, {"ts", r""}, regex=True)
    # candles['ts'] = candles.replace({"ts", r"T"}, {"ts", " "}, regex=True)
    # candles['ts'] = pd.to_datetime(candles['ts']).dt.tz_localize('Asia/Calcutta')
    return candles[["Date", "Open", "High", "Low", "Close", "Volume", "Adj Close"]]


def get_candles_from_zerodha(instrument_id, duration, start_date, end_date):
    if (ts(end_date).date() - ts(start_date).date()) > timedelta(duration_limits[duration]):
        raise Exception("date difference cannot be more than {} days for duration of '{}'".format(
            duration_limits[duration], duration))
    candles_url = "https://kitecharts-aws.zerodha.com/api/chart/{instrument_id}/{duration}?&from={start_date}&to={end_date}" \
        .format(instrument_id=instrument_id, duration=duration, start_date=start_date, end_date=end_date)
    logging.debug("request url: {0}".format(candles_url))
    print("request url: " + candles_url)
    resp = requests.get(url=candles_url)
    if not resp.ok:
        logging.error("Error, could not get response from server")
        logging.error(resp.status_code)
        raise Exception("Error, could not get response from server")
    return parse_to_df(resp.text)


def get_candles(scrip, start_date, end_date, duration='day', exchange=DEFAULT_EXCHANGE):
    verify_date_format(start_date)
    verify_date_format(end_date)
    verify_duration(duration)
    chunksize = duration_limits[duration]
    intervals = convert_date_in_intervals(start_date, end_date, chunksize)
    df = None
    instrument_id = get_id_for_instrument(
        scrip.upper(), exchange.upper(), 'EQ')
    for interval in intervals:
        fd, td = interval
        fd, td = fd.strftime("%Y-%m-%d"), td.strftime("%Y-%m-%d")
        batch_df = get_candles_from_zerodha(
            instrument_id, duration, fd, td)
        if batch_df is not None:
            logging.debug(batch_df.head())
            logging.debug("#" * 20)
            if df is None:
                df = batch_df
            else:
                df = df.append(batch_df, ignore_index=True)
    # df.to_csv("~/qstrader/data/INFY.csv", index = False)
    return df.drop_duplicates("Date")


@click.command()
@click.option('--instrument', '-i', required=True, help='instrument name, eg: INFY')
@click.option('--start', '-s', 'start_date', required=True, help='start date in YYYY-mm-dd format, eg: 2010-10-23')
@click.option('--end', '-e', 'end_date', required=True, help='end date in YYYY-mm-dd format, eg: 2019-10-23')
@click.option('--duration', '-d', default='day', help='duration from [minute,3minute,5minute,10minute,15minute,30minute,60minute,day], eg: 3minute')
@click.option('--exchange', '-x', default='NSE', help='exchange name, eg: BSE')
def main(instrument, start_date, end_date, duration, exchange):
    csv_dir = "~/qstrader/data/{}".format(duration)
    stock_csv = "{}/{}.csv".format(csv_dir, instrument)
    print(stock_csv)

    stock = get_candles(instrument, start_date, end_date, duration, exchange)
    print(stock.head())
    stock.to_csv(stock_csv, index=False)


    #start = "2010-01-01"
    #end = "2019-01-01"
    #exchange = "NSE"
    #stockname1 = "HDFCBANK"
    #stockname2 = "HDFC"
    #stock1 = batch_get_day_candles_from_zerodha(stockname1, exchange, start, end)
    #stock1.to_csv("~/qstrader/data/%s.csv"%stockname1, index=False)
    # print("stock2")
    #stock2 = batch_get_day_candles_from_zerodha(stockname2, exchange, start, end)
    #stock2.to_csv("~/qstrader/data/%s.csv"%stockname2, index=False)
    ##print("stock2 end")
if __name__ == '__main__':
    main()

    #end = "2019-01-01"
    #exchange = "NSE"
    #stockname1 = "HDFCBANK"
    #stockname2 = "HDFC"
    #stock1 = batch_get_day_candles_from_zerodha(stockname1, exchange, start, end)
    #stock1.to_csv("~/qstrader/data/%s.csv"%stockname1, index=False)

    # print("stock2")
    #stock2 = batch_get_day_candles_from_zerodha(stockname2, exchange, start, end)
    #stock2.to_csv("~/qstrader/data/%s.csv"%stockname2, index=False)
    ##print("stock2 end")
