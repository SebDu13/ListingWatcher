import os
from bs4 import BeautifulSoup
from typing import NamedTuple
import smtplib
from email.message import EmailMessage
from pycoingecko import CoinGeckoAPI
import logging
import logging.config
import ccxt
from ListingTracker import getExchangeTracker
import threading
import time


class ThreadTrackerBot(threading.Thread):
    def __init__(self, exchangeTracker):
        super(ThreadTrackerBot, self).__init__()
        self.exchangeTracker = exchangeTracker
        self.stopFlag = False
        self.name = "Thread-"+ self.exchangeTracker.getExchangeName() # Thread name
    
    def stop(self):
        self.stopFlag = True

    def run(self):
        while not self.stopFlag:
            t = time.time()
            newListingTokens = self.exchangeTracker.getNewListing()
            for newToken in newListingTokens:
                logger.info(f"New listing planned on {self.exchangeTracker.getExchangeName()}: {newToken}")
                #buy("gateio", newToken.symbol + "/USDT")
            elapsed_time = time.time() - t
            #logger.info(f"getNewListing() execution time: {elapsed_time}")

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
    #ccxt.hitbtc({'verbose': True}).create_limit_buy_order
    #exchange = geckoToCcxtExchangeID(exchange)
    logger = logging.getLogger('root')
    apiKey, secret, password = getApiKey(exchange)
    ccxtExchange = getattr(ccxt, exchange)({'apiKey': apiKey, 'secret': secret, 'password': password})
    ticker = ccxtExchange.fetch_ticker(symbol)
    buyOrder = ccxtExchange.create_limit_buy_order(symbol, 10, ticker['last']*1.20)
    log = f"Bought {symbol} for 10 usdt on {exchange}"
    logger.info(log)
    logger.info(buyOrder)
    notifyByMail(log, buyOrder)

    #profit = 10
    #ccxtExchange.create_limit_sell_order(symbol, 10, ticker['last']*(1 + profit/100) )# 100 usdt
    

def run():
    try:
        bots = [ThreadTrackerBot(getExchangeTracker("binance"))
        , ThreadTrackerBot(getExchangeTracker("binancebis"))]
        
        for bot in bots:
            bot.start()

        for bot in bots:
            bot.join()

    except  Exception as e:
        logger.exception(e, exc_info=True)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt")
        for bot in bots:
            bot.stop()
        pass

if __name__ == '__main__':
    logging.config.fileConfig(fname='log.conf')
    logger = logging.getLogger('root')
    run()



