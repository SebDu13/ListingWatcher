import requests
import os
from bs4 import BeautifulSoup
import re
from typing import NamedTuple
import smtplib
from email.message import EmailMessage
from pycoingecko import CoinGeckoAPI
import logging
import logging.config
import ccxt
from ListingTracker import getNewListingFrom

class Registry:
    def __init__(self, filePath):
        self.file = open(filePath, 'a+')
    
    def __del__(self):
        self.file.close()

    def isNotListed(lines, entry):
        for line in lines:
            if line == entry:
                return False
        return True

    def append(self, entry):
        self.file.seek(0)
        entry += "\n"
        if(Registry.isNotListed(self.file.readlines(), entry)):
            self.file.writelines(entry)
            return True
        return False

class Token:
    def __init__(self, name, symbol):
        self.name = name
        self.symbol = symbol
        self.marketCap = 0
        self.exchanges= []
        
    def __repr__(self):
        return f"<Token name:{self.name} symbol:{self.symbol} marketCap:{self.marketCap} exchanges:{self.exchanges}>"

def notifyByMail(subject, body):
    msg = EmailMessage()
    #sebcrypto57
    msg['Subject'] = subject
    msg['From'] = "sebcrypto57@gmail.com"
    msg['To'] = "sebastien.suignard@hotmail.fr"
    msg.set_content(body)
    with smtplib.SMTP("smtp.gmail.com",587) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(msg['From'], "crypto123")
        s.send_message(msg)

def findToken(title):
    if(title.find('Listing Vote') != -1):
        #print(title)
        tokenName = re.search(' \- (.+?) \(', title)
        #print(tokenName)
        tokenSymbol = re.search('\((.+?)\)', title)
        #print(tokenSymbol)
        if(tokenName and tokenSymbol):
            return Token(tokenName.group(1), tokenSymbol.group(1))
    return None

# what we are searching:
# </div>, <div class="entry">
# <a href="/article/23970" target="_blank" title="Gate.io Listing Vote #236 - Kadena (KDA), ＄13,000 KDA Giveaway 26381">
# Supposed to return Kadena KDA
def getNewListingFromGateIo():
    link = "https://www.gateio.pro/articlelist/ann/2"
    soup = BeautifulSoup(requests.get(link).text, 'html.parser')
    entries = soup.find_all('div', {'class' : 'entry'})
    newListingTokens = []

    for entry in entries:
        title = entry.find('a')["title"]
        token = findToken(title)
        if(token):
            newListingTokens.append(token)

    return newListingTokens

def getTokenInfo(token):
    logger = logging.getLogger('root', level=logging.INFO)
    coinGeckoAPI = CoinGeckoAPI()
    try:
        coins = coinGeckoAPI.get_coins_list()
        for coin in coins:
            if(coin["symbol"].casefold() == token.symbol.casefold() and coin["name"].casefold() == token.name.casefold()):
                coinData = coinGeckoAPI.get_coin_by_id(coin["id"])
                token.marketCap = coinData["market_data"]["market_cap"]["usd"]
                for ticker in coinData["tickers"]:
                    token.exchanges.append(ticker["market"]["identifier"])
                
    except ValueError as ve:
        logger.info(f'getTokenInfo exception caught: %s', ve)

def getMyExchanges():
    return ['gate']

def getExchangeToBuyOn(token):
    if(token.marketCap > 500000):
        return None
    myExchanges = getMyExchanges()
    for exchange in token.exchanges:
        if exchange.casefold() in map(str.casefold, myExchanges):
            return exchange

def geckoToCcxtExchangeID(exchange):
    return {
        'gate': 'gateio',
        'kucoin': 'kucoin',
    }[exchange]

def getApiKey(exchange):
    return {
        'gateio': (os.getenv('GATEIO_K'), os.getenv('GATEIO_S'), ''),
        'kucoin': (os.getenv('KUCOIN_K'), os.getenv('KUCOIN_S'), os.getenv('KUCOIN_P')),
    }[exchange]

def buy(exchange, symbol):
    exchange = geckoToCcxtExchangeID(exchange)
    logger = logging.getLogger('root')
    apiKey, secret, password = getApiKey(exchange)
    ccxtExchange = getattr(ccxt, exchange)({'apiKey': apiKey, 'secret': secret, 'password': password})
    ticker = ccxtExchange.fetch_ticker(symbol)
    #buyOrder = ccxtExchange.create_limit_buy_order(symbol, 10, ticker['last']*1.03) # 100 usdt
    #logger.info("Bought %s", symbol)
    #logger.info(buyOrder)
    profit = 10
    ccxtExchange.create_limit_sell_order(symbol, 10, ticker['last']*(1 + profit/100) )# 100 usdt
    

def run():
    #registry = Registry(os.path.join(os.getcwd(), 'gateio_annoucement.txt'))
    #newTokens = []
    #for token in getNewListingFromGateIo():
    #    if(registry.append(token.symbol)):
    #        getTokenInfo(token)
    #        newTokens.append(token)
    #        logger.info(f'New listing found on gateio: {token}')
#
    #if(newTokens):
    #    for token in newTokens:
    #        exchange = getExchangeToBuyOn(token)
    #        if exchange:
    #            logger.info(f"I should buy here: {exchange}")

    #buy('kucoin', 'XRP/USDT')
    #if(newTokens):
        #notifyByMail("New currency listing announced on Gate.io", '\n'.join(newTokens))

     for newToken in getNewListingFrom("binance"):
        logger.info(f"New listing planned on Binance: {newToken}")
    
     for newToken in getNewListingFrom("gateio"):
        logger.info(f"New listing planned on Gateio: {newToken}")

if __name__ == '__main__':
    logging.config.fileConfig(fname='log.conf')
    logger = logging.getLogger('root')

    try:
        run()
    except  Exception as e:
        logger.exception(e, exc_info=True)


