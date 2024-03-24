from typing import AsyncGenerator
from pyrogram.types import Message
import logging
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
from dotenv import load_dotenv
from pyrogram import Client as PyrogramClient
from tenacity import retry, wait_random_exponential, stop_after_attempt
from binance.client import Client
import pandas as pd
import datetime, time
import numpy as np


load_dotenv()  # load environment variables from .env file

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')

#  Telegram stuff
GROUP_URL = "@unfolded"  # Telegram group for getting latest news
app = PyrogramClient("my_session", api_id=api_id, api_hash=api_hash)

# Binance API stuff
api_key = os.getenv('API_KEY')
api_secret = os.getenv('API_SECRET')
binance_client = Client(api_key, api_secret)


@retry(wait=wait_random_exponential(multiplier=1, max=40),
       stop=stop_after_attempt(3))
def get_binance_data(symbol="BTCUSDT", how_long=90):
    # Calculate the timestamps for the binance api function
    until_this_date = datetime.datetime.now()
    since_this_date = until_this_date - datetime.timedelta(days=how_long)
    # Execute the query from binance - timestamps must be converted to strings
    # We need daily chart
    try:
        candle = binance_client.get_historical_klines(symbol,
                                              Client.KLINE_INTERVAL_1DAY,
                                              str(since_this_date),
                                              str(until_this_date))
    except Exception as e:
        print(f"Exception: {e}")
        return e


    # Create a dataframe to label all the columns returned by binance, so we
    # work with them later.
    df = pd.DataFrame(candle,
                      columns=['dateTime', 'open', 'high', 'low', 'close',
                               'volume', 'closeTime', 'quoteAssetVolume',
                               'numberOfTrades', 'takerBuyBaseVol',
                               'takerBuyQuoteVol', 'ignore'])
    # as timestamp is returned in ms, let us convert this back to proper
    # timestamps.
    df.dateTime = pd.to_datetime(df.dateTime, unit='ms').dt.strftime(
        '%Y-%m-%d')
    df.set_index('dateTime', inplace=True)

    # Convert columns to the correct datatype
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Get rid of columns we do not need
    df = df.drop(
        ['closeTime', 'quoteAssetVolume', 'numberOfTrades', 'takerBuyBaseVol',
         'takerBuyQuoteVol', 'ignore'], axis=1)

    # Calculate Simple Moving Averages (SMAs)
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['SMA_200'] = df['close'].rolling(window=200).mean()

    # Identify potential support and resistance levels
    # Using rolling max/min for a window to find local peaks and troughs
    window_size = 14  # Define window size for local maxima and minima

    # Calculate local maxima for potential resistance levels
    df['is_local_max'] = df['close'] == df['close'].rolling(window=window_size,
                                                            min_periods=1,
                                                            center=True).max()
    # Calculate local minima for potential support levels
    df['is_local_min'] = df['close'] == df['close'].rolling(window=window_size,
                                                            min_periods=1,
                                                            center=True).min()

    # Potential resistance levels where is_local_max is True
    resistance_levels = df[df['is_local_max']]['close']

    # Potential support levels where is_local_min is True
    support_levels = df[df['is_local_min']]['close']

    # Folder name
    folder_name = "data_files"

    # Get the current script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the folder path
    folder_path = os.path.join(script_dir, folder_name)

    # Create the folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"{symbol}{how_long}d_market_data_{current_date}"
    file_path = os.path.join(folder_path, filename)
    df.to_excel(file_path + '.xlsx', sheet_name='Sheet1', index=True)
    df.to_json(file_path + '.json', orient='records', lines=True)
    # Prepare the data
    output_data = {
        "dataframe": json.loads(df.to_json(orient='records')),
        "support_levels": json.loads(support_levels.to_json()),
        "resistance_levels": json.loads(resistance_levels.to_json())
    }

    # Convert to JSON
    output_json = json.dumps(output_data)

    return output_json


@retry(wait=wait_random_exponential(multiplier=1, max=40),
       stop=stop_after_attempt(3))
def get_historical_data(symbol='BTC', currency_transform='USD',
                        limit='20') -> str | Exception:
    """Return historical data using Cryptocompare API"""
    headers: dict = {
        'Accepts': 'application/json',
        'Accept-Encoding': 'deflate, gzip',
        'authorization': os.getenv('CRYPTO_API_KEY')
        # get API key from environment variable
    }
    parameters: dict = {
        # 'start': '1',
        'limit': limit,
        'tsym': currency_transform,
        'fsym': symbol
    }
    url: str = "https://min-api.cryptocompare.com/data/v2/histoday"
    try:
        historical_data = get_response_object(headers, parameters, url)
        return json.dumps(historical_data['Data']['Data'])
    except Exception as e:
        print("Unable to get price")
        print(f"Exception: {e}")
        return e


def get_response_object(headers: dict, parameters: dict, url: str) -> json:
    session = Session()
    session.headers.update(headers)
    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
    return data


@retry(wait=wait_random_exponential(multiplier=1, max=40),
       stop=stop_after_attempt(3))
def get_crypto_price(ticker) -> str | Exception:
    """Function to get cryptocurrency which is used by Chatgpt during
    function call"""
    # ticker = input("Enter the ticker: ").upper()
    url: str = ('https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes'
                '/latest')  # Coinmarketcap API
    headers: dict = {
        'Accepts': 'application/json',
        'Accept-Encoding': 'deflate, gzip',
        'X-CMC_PRO_API_KEY': os.getenv('X_CMC_PRO_API_KEY')
        # get API key from environment variable
    }
    parameters: dict = {
        # 'start': '1',
        # 'limit': '5000',
        'convert': 'USD',
        'symbol': ticker
    }
    try:
        price_object = get_response_object(headers, parameters, url)
        return f'{round(price_object["data"][ticker]["quote"]["USD"]["price"],
                        2)}'
    except Exception as e:
        print("Unable to get price")
        print(f"Exception: {e}")
        return e


@retry(wait=wait_random_exponential(multiplier=1, max=40),
       stop=stop_after_attempt(3))
def get_crypto_latest() -> str | Exception:
    """Function to get cryptocurrency which is used by Chatgpt during
    function call"""
    # ticker = input("Enter the ticker: ").upper()
    url: str = ('https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings'
                '/latest')  # Coinmarketcap API
    headers: dict = {
        'Accepts': 'application/json',
        'Accept-Encoding': 'deflate, gzip',
        'X-CMC_PRO_API_KEY': os.getenv('X_CMC_PRO_API_KEY')
        # get API key from environment variable
    }
    parameters: dict = {
        # 'start': '1',
        'limit': '20',
        'convert': 'USD',
    }
    try:
        price_object = get_response_object(headers, parameters, url)
        return json.dumps(price_object)
    except Exception as e:
        print("Unable to get price")
        print(f"Exception: {e}")
        return e


group_for_search = "@unfolded"
query = "OKX"
limit = 30


def get_news_from_telegram() -> str:
    with app:
        all_messages = []
        for message in app.get_chat_history(GROUP_URL, limit=60):
            formatted_date = message.date.strftime('%Y-%m-%d %H:%M:%S')
            message_content = message.caption if message.caption else message.text
            if message_content:
                all_messages.append(f"{formatted_date}: {message_content}")

        return '\n'.join(reversed(all_messages))
    # reversed нужно, чтобы в
    # конце вывода были самые недавние сообщения


def search_for_keywords(keyword) -> str:
    """Search for keywords in group with amount of messages limited by
    limit_of_last_msg"""
    if keyword is None:
        return "Keyword cannot be None."
    with app:
        all_messages = []
        messages = app.search_messages(
            chat_id=group_for_search, query=keyword,
            limit=limit)
        for message in messages:
            formatted_date = message.date.strftime('%Y-%m-%d %H:%M:%S')
            message_content = message.caption if message.caption else message.text
            if message_content:
                all_messages.append(f"{formatted_date}: {message_content}")

        return '\n'.join(reversed(all_messages))


if __name__ == '__main__':
    print(get_binance_data("ETHUSDT", how_long=90))
    # print("Support Levels:\n", supports)
    # print("Resistance Levels:\n", resistances)
    # df['close'] = df['close'].astype(
    #     float)  # Ensure 'close' is float for calculations
    # df['SMA_50'] = df['close'].rolling(window=50).mean()
    # df['SMA_200'] = df['close'].rolling(window=200).mean()

    # To print the last 10 rows of the DataFrame including the moving averages
    # print(df[['close', 'SMA_50', 'SMA_200']].tail(10))
    # print(search_for_keywords(query))
    # print(get_crypto_price('BTC'))
    # print(get_news_from_telegram())
    # print(get_historical_data())
    # print(get_crypto_latest())
