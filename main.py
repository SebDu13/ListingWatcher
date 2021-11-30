import ccxt
import datetime

import smtplib
from email.message import EmailMessage

filePath = "/home/seb/Workspace/ListingWatcher/gateio_listing.txt"
gateio = ccxt.gateio()
markets = gateio.load_markets()

def isNotListed(lines, entry):
    for line in lines:
        if line == entry:
            return False
    return True

with open(filePath, 'r') as gateioListing:
    lines = gateioListing.readlines()
    newEntries = []

    for key, value in markets.items():
        if(value["info"]["buy_start"] != "0" and "USDT" in key):
            entry = key + " " + str(datetime.datetime.fromtimestamp(int(value["info"]["buy_start"]))) + "\n"
            if(isNotListed(lines, entry)):
                newEntries.append(entry)

if(newEntries):
    with open(filePath, 'a') as gateioListing:
        gateioListing.writelines(newEntries)
        print("Adding new entries in file")
        print(newEntries)

    sender_email = "seb.crypto@hotmail.com"
    receiver_email = "sebastien.suignard@hotmail.fr"
    subject = "New currency will soon be listed on Gate.io"


    msg = EmailMessage()
    msg['Subject'] = "New currency will soon be listed on Gate.io"
    msg['From'] = "seb.crypto@hotmail.com"
    msg['To'] = "sebastien.suignard@hotmail.fr"
    msg.set_content(''.join(newEntries))

    with smtplib.SMTP("smtp.live.com",587) as s:
        s.ehlo() # Hostname to send for this command defaults to the fully qualified domain name of the local host.
        s.starttls() #Puts connection to SMTP server in TLS mode
        s.ehlo()
        s.login(sender_email, "crypto123")
        s.send_message(msg)



