from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json

url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
parameters = {
    # 'start': '1',
    # 'limit': '5000',
    'convert': 'USD',
    'symbol': 'BTC,ETH'
}
headers = {
    'Accepts': 'application/json',
    'Accept-Encoding': 'deflate, gzip',
    'X-CMC_PRO_API_KEY': '99532c69-1561-423e-8bd3-e0d766bac105'
}

session = Session()
session.headers.update(headers)

try:
    response = session.get(url, params=parameters)
    data = json.loads(response.text)
    BTC_price = data['data']['BTC']['quote']['USD']['price']
    ETH_price = data['data']['ETH']['quote']['USD']['price']
    print(f"The current price of Bitcoin (BTC) in USD is: {BTC_price}")
    print(f"The current price of ETH in USD is: {ETH_price}")
except (ConnectionError, Timeout, TooManyRedirects) as e:
    print(e)
