import requests
from bs4 import BeautifulSoup
import re
from typing import NamedTuple
import smtplib
from email.message import EmailMessage
from pycoingecko import CoinGeckoAPI

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


class Token(NamedTuple):
    name: str
    symbol: str

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

#getNewListingFromGateIo()
registry = Registry("/home/seb/Workspace/ListingWatcher/gateio_annoucement.txt")
newTokens = getNewListingFromGateIo()
for token in newTokens:
    if(registry.append(token.symbol)):
        print(token.symbol + " added in registry")
        newTokens.append(token)

if(newTokens):
    coinGeckoAPI = CoinGeckoAPI()
    print(coinGeckoAPI.get_coin_by_id(newTokens[0].name))
    #notifyByMail("New currency listing announced on Gate.io", '\n'.join(newTokens))


