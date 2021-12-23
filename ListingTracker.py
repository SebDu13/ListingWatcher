from hmac import new
import logging
import logging.config
import re
from bs4 import BeautifulSoup
import requests
import os
import random
import string
import time
from datetime import datetime
import ccxt
from abc import ABC, abstractmethod

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

class ExchangeTracker(ABC):
    @abstractmethod
    def getNewListing(self):
        pass

    @abstractmethod
    def getExchangeName(self):
        pass


class GateIoListingTracker(ExchangeTracker):
    def __init__(self):
        self.link = "https://www.gateio.pro/articlelist/ann/0"
        self.registry = Registry(os.path.join(os.getcwd(), 'gateio_annoucement.txt'))
    
    def __findTorken(self, title):
        if(title.find('Listing Vote') != -1):
            #print(title)
            tokenName = re.search(' \- (.+?) \(', title)
            #print(tokenName)
            tokenSymbol = re.search('\((.+?)\)', title)
            #print(tokenSymbol)
            if(tokenName and tokenSymbol):
                return Token(tokenName.group(1), tokenSymbol.group(1))
        return None
    
    def getNewListing(self):
        soup = BeautifulSoup(requests.get(self.link).text, 'html.parser')
        entries = soup.find_all('div', {'class' : 'entry'})
        newListingTokens = []

        for entry in entries:
            title = entry.find('a')["title"]
            token = self.__findTorken(title)
            if(token):
                if(self.registry.append(token.symbol)):
                    newListingTokens.append(token)
        return newListingTokens

    def getExchangeName(self):
        return "gateio"

class GateIoListingTrackerBis(ExchangeTracker):
    def __init__(self):
        self.registry = Registry(os.path.join(os.getcwd(), 'gateio_annoucementBis.txt'))
    
    def getNewListing(self):
        self.gateio = ccxt.gateio()
        markets = self.gateio.load_markets()
        newListingTokens = []
        for key, value in markets.items():
            if(value["info"]["buy_start"] != "0" and "USDT" in key):
                if(self.registry.append(value["base"])):
                    newListingTokens.append(Token("", value["base"]))
        return newListingTokens
    
    def getExchangeName(self):
        return "gateio_(api)"

class BinanceListingTracker(ExchangeTracker):
    def __init__(self):
        self.registry = Registry(os.path.join(os.getcwd(), 'binance_annoucement.txt'))
        self.previous = None

    #Binance Will List Anyswap (ANY)
    #Binance Will List Amp (AMP) and PlayDapp (PLA)
    def getNewListing(self):
        logger = logging.getLogger('root')
        # Generate random query/params to help prevent caching
        rand_page_size = random.randint(1, 200)
        letters = string.ascii_letters
        random_string = ''.join(random.choice(letters) for i in range(random.randint(10, 20)))
        random_number = random.randint(1, 99999999999999999999)
        queries = ["type=1", "catalogId=48", "pageNo=1", f"pageSize={str(rand_page_size)}", f"rnd={str(time.time())}",
                f"{random_string}={str(random_number)}"]
        random.shuffle(queries)
        request_url = f"https://www.binancezh.com/gateway-api/v1/public/cms/article/list/query" \
                    f"?{queries[0]}&{queries[1]}&{queries[2]}&{queries[3]}&{queries[4]}&{queries[5]}"
        
        latest_announcement = requests.get(request_url)

        #latest_json = latest_announcement.json()
        #if(self.previous != latest_json):
        #    self.previous = latest_json
        #    logger.info(latest_json)

            
        try:
            logger.debug(f'X-Cache: {latest_announcement.headers["X-Cache"]}')
        except KeyError:
            logger.debug("No X-Cache header was found - great news, we're hitting the source.")
            pass

        newListingTokens = []
        for article in latest_announcement.json()['data']['catalogs'][0]['articles']:
            releaseDateSecond = article['releaseDate']/1000
            token = self.__findTorken(article['title'])
            if(token):
                if(self.registry.append(token.symbol)):
                    logger.info(f'New token found: {token.symbol}, release date: {releaseDateSecond}, {datetime.utcfromtimestamp(releaseDateSecond)} UTC')
                    if(time.time() - int(releaseDateSecond) < 120): #2min old maximum
                        newListingTokens.append(token)
        return newListingTokens

    def getExchangeName(self):
        return "binance"


    #def getNewListing(self):
    #    request = requests.get(self.link)
    #    soup = BeautifulSoup(request.text, 'html.parser')
    #    entries = soup.find_all(class_ = 'css-1ej4hfo')
    #    newListingTokens = []
    #    for entry in entries:
    #        token = self.__findTorken(entry.text)
    #        if(token):
    #            if(self.registry.append(token.symbol)):
    #                newListingTokens.append(token)
    #    return newListingTokens

    def __findTorken(self, title):
        if(title.find('Binance Will List') != -1):
            tokenSymbol = re.search('\((.+?)\)', title)
            if(tokenSymbol):
                return Token("", tokenSymbol.group(1))
        return None

class BinanceListingTrackerBis(ExchangeTracker):
    def __init__(self):
        self.tickers = {}

    def getNewListing(self):
        logger = logging.getLogger('root')
        self.binance = ccxt.binance()
        newListingTokens = []
        newTickers = self.binance.fetch_tickers()
        if(not self.tickers):
            self.tickers = newTickers
            return newListingTokens
        
        if(len(self.tickers) != len(newTickers)):
            logger.info(f"len(self.tickers) != len(newTickers): {len(self.tickers)} {len(newTickers)}")
            for key, value in newTickers.items():
                if(not self.tickers[key]):
                    logger.info(f"New token found: {key}")
                    logger.info(newTickers[value])
                    newListingTokens.append(Token("",value))
            self.tickers = newTickers
    
        return newListingTokens
    
    def getExchangeName(self):
        return "binance_tickers"


class BinanceListingTrackerBisBis(ExchangeTracker):
    def __init__(self):
        self.tickers = {}

    def getNewListing(self):
        logger = logging.getLogger('root')
        self.binance = ccxt.binance()
        newListingTokens = []
        newTickers = self.binance.publicGetExchangeInfo()
        if(not self.tickers):
            self.tickers = newTickers
            return newListingTokens

        values = { k : self.tickers[k] for k in set(self.tickers) - set(newTickers) }
            
        for value in values:
            logger.info(f"New token found: {value}")
            logger.info(newTickers[value])
            newListingTokens.append(Token("",value))

        return newListingTokens
    
    def getExchangeName(self):
        return "binance_info"


def getExchangeTracker(exchange):
    if exchange.casefold() == "gateio".casefold():
        return GateIoListingTracker()
    if exchange.casefold() == "binance".casefold():
        return BinanceListingTracker()
    if exchange.casefold() == "gateiobis".casefold():
        return GateIoListingTrackerBis()
    if exchange.casefold() == "binancebis".casefold():
        return BinanceListingTrackerBis()
    if exchange.casefold() == "binancebisbis".casefold():
        return BinanceListingTrackerBisBis()
    return None
