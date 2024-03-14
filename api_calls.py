from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import os
from dotenv import load_dotenv
from pyrogram import Client

load_dotenv()  # load environment variables from .env file

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
group_url = "@unfolded"  # Telegram group for getting latest news
app = Client("my_session", api_id=api_id, api_hash=api_hash)
url: str = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'  # Coinmarketcap API
headers: dict = {
    'Accepts': 'application/json',
    'Accept-Encoding': 'deflate, gzip',
    'X-CMC_PRO_API_KEY': os.getenv('X_CMC_PRO_API_KEY')  # get API key from environment variable
}


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


def get_news_from_telegram():
    with app:
        all_messages = []
        for message in app.get_chat_history(group_url, limit=10):
            if message.caption:
                all_messages.append(message.caption)
            elif message.text:
                all_messages.append(message.text)
        return '\n'.join(all_messages)


# print(get_crypto_price('BTC'))
# print(get_news_from_telegram())
