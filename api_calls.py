from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
from dotenv import load_dotenv
from pyrogram import Client
from tenacity import retry, wait_random_exponential, stop_after_attempt

load_dotenv()  # load environment variables from .env file

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')

#  Telegram stuff
GROUP_URL = "@unfolded"  # Telegram group for getting latest news
app = Client("my_session", api_id=api_id, api_hash=api_hash)

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


def get_news_from_telegram():
    with app:
        all_messages = []
        for message in app.get_chat_history(GROUP_URL, limit=60):
            if message.caption:
                all_messages.append(message.caption)
            elif message.text:
                all_messages.append(message.text)
        return '\n'.join(all_messages)


if __name__ == '__main__':
    print(get_crypto_price('BTC'))
    # print(get_news_from_telegram())
    # print(get_historical_data())
    # print(get_crypto_latest())
