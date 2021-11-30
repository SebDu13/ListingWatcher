import requests
from bs4 import BeautifulSoup
import re
from typing import NamedTuple
import smtplib
from email.message import EmailMessage
from pycoingecko import CoinGeckoAPI
import json

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

def notifyByMail(subject, body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = "seb.crypto@hotmail.com"
    msg['To'] = "sebastien.suignard@hotmail.fr"
    msg.set_content(body)
    with smtplib.SMTP("smtp.live.com",587) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(msg['From'], "crypto123")
        s.send_message(msg)

def findToken(title):
    if(title.find('Listing Vote') != -1):
        print(title)
        tokenName = re.search(' \- (.+?) \(', title)
        print(tokenName)
        tokenSymbol = re.search('\((.+?)\)', title)
        print(tokenSymbol)
        if(tokenName and tokenSymbol):
            return Token(tokenName.group(1), tokenSymbol.group(1))
    return None

# what we are searching:
# </div>, <div class="entry">
# <a href="/article/23970" target="_blank" title="Gate.io Listing Vote #236 - Kadena (KDA), ＄13,000 KDA Giveaway 26381">
# Supposed to return Kadena KDA
def getNewListingFromGateIo():
    link = "https://www.gateio.pro/articlelist/ann/3"
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
    coinGeckoAPI = CoinGeckoAPI()
    try:
        coins = coinGeckoAPI.get_coins_list()
        for coin in coins:
            if(coin["symbol"].casefold() == token.symbol.casefold() and coin["name"].casefold() == token.name.casefold()):
                coinData = coinGeckoAPI.get_coin_by_id(coin["id"])
                token.marketCap = coinData["market_data"]["market_cap"]["usd"]

    except ValueError as ve:
        print(ve)

#getNewListingFromGateIo()
registry = Registry("/home/seb/Workspace/ListingWatcher/gateio_annoucement.txt")
newTokens = getNewListingFromGateIo()
for token in newTokens:
    if(registry.append(token.symbol)):
        print(token.symbol + " added in registry")
        getTokenInfo(token)
        newTokens.append(token)
        print(token.marketCap)


#if(newTokens):
    #notifyByMail("New currency listing announced on Gate.io", '\n'.join(newTokens))


