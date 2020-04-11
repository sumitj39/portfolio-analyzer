import datetime
import os

import pandas

import utils
import ZerodhaConnector as zc


def get_scrip_path(scrip):
    return utils.DATA_DIR + os.sep + scrip + utils.CSV_EXT


def scrip_exists(scrip):
    scrip_path = get_scrip_path(scrip)
    if os.path.exists(scrip_path):
        return True
    else:
        return False


def get_candles(scrips, start_date, end_date):
    # TODO: Check in the data csv file first before fetching data from Zerodha
    candles_dict = {}
    for scrip in scrips:
        download_data = True
        if scrip_exists(scrip):

            '''
            dataframe returned from zc.get_candles will have
            dataType of 'Date' column as datetime64.
            to bring same effect to read_csv dataframe's 'Date' column,
            first we send parameters parse_dates=True, index_col='Date',
            this will set 'Date' column's datatype to datetime64
            then we drop the 'Date' index by doing reset_index.
            '''

            candles = pandas.read_csv(get_scrip_path(
                scrip), parse_dates=True, index_col='Date').reset_index()
            candles.sort_values(by='Date', inplace=True)
            last_date = pandas.Timestamp(pandas.Series(
                candles.tail(1)['Date']).values[0]).date()

            # Check to make sure that data is not too outdated.
            # download data if the last candle in csv is older than 15 days.
            if datetime.datetime.strptime(end_date, '%Y-%m-%d').date() < last_date + datetime.timedelta(15):
                # If end_date is in range of (last_date_in_csv - 15, last_date_in_csv)
                # then don't download.
                download_data = False

        if download_data:
            candles = zc.get_candles(
                scrip, start_date, end_date, duration='week')
            candles.to_csv(
                get_scrip_path(scrip), index=False)
        candles_dict[scrip] = candles
        print(candles.set_index('Date').head())
    return candles_dict
