import logging
import logging.config
import re
from bs4 import BeautifulSoup
import requests
import os
import pprint

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

class GateIoListingTracker:
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


class BinanceListingTracker:
    def __init__(self):
        self.link = "https://www.binance.com/en/support/announcement/c-48?navId=48"
        self.registry = Registry(os.path.join(os.getcwd(), 'binance_annoucement.txt'))

    #Binance Will List Anyswap (ANY)
    #Binance Will List Amp (AMP) and PlayDapp (PLA)
    def getNewListing(self):
        request = requests.get(self.link)
        soup = BeautifulSoup(request.text, 'html.parser')
        entries = soup.find_all(class_ = 'css-1ej4hfo')
        newListingTokens = []
        for entry in entries:
            token = self.__findTorken(entry.text)
            if(token):
                if(self.registry.append(token.symbol)):
                    newListingTokens.append(token)
        return newListingTokens


    def __findTorken(self, title):
        if(title.find('Binance Will List') != -1):
            tokenSymbol = re.search('\((.+?)\)', title)
            if(tokenSymbol):
                return Token("", tokenSymbol.group(1))
        return None


def getNewListingFrom(exchange):
    if exchange.casefold() == "gateio":
        return GateIoListingTracker().getNewListing()
    if exchange.casefold() == "binance":
        return BinanceListingTracker().getNewListing()
    return None
