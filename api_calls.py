from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
from dotenv import load_dotenv

load_dotenv() # load environment variables from .env file

url: str = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
headers: dict = {
    'Accepts': 'application/json',
    'Accept-Encoding': 'deflate, gzip',
    'X-CMC_PRO_API_KEY': os.getenv('X_CMC_PRO_API_KEY')  # get API key from environment variable
}
# TODO: убрать ключ в исключаемый файл
# TODO: прикрутить telegram api для загрузки новостей с crypto headlines (Саша говорил что это нетрудно)


def get_crypto_price(ticker):
    """Function to get cryptocurrency which is used by Chatgpt during function call"""
    # ticker = input("Enter the ticker: ").upper()
    parameters = {
        # 'start': '1',
        # 'limit': '5000',
        'convert': 'USD',
        'symbol': ticker
    }
    session = Session()
    session.headers.update(headers)

    try:
        response = session.get(url, params=parameters)
        data = json.loads(response.text)
        ticker_price = data['data'][ticker]['quote']['USD']['price']
        # print(f"The current price of {ticker} in USD is: {ticker_price}")
    except (ConnectionError, Timeout, TooManyRedirects) as e:
        print(e)
    return f'{round(ticker_price)}'


# print(get_crypto_price('BTC'))
