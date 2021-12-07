import os
import re


path = os.environ['HOME'] + '/prod/logs'

def analyseFile(file):
    firstProfit = 0
    maxprofit = 0
    pnl = 0
    with open(file, 'r') as logFile:
        for line in logFile.readlines():
            result = re.search(' USDT, (.+?)%', line)
            if(result):
                pnl = float(result.group(1))
                #print('pnl=', pnl)
            
            result = re.search('PROFIT\=(.+?)\%', line)
            if(result):
                profit = float(result.group(1))
                #print('profit=', profit)
                if(maxprofit < profit):
                    maxprofit = profit
                    #print('maxprofit=',maxprofit)
                if(profit != 0 and profit != -100):
                    if(firstProfit == 0):
                        firstProfit = profit
                        #print('first =',firstProfit)
        return firstProfit, maxprofit, pnl

search_dir = path
os.chdir(search_dir)
files = filter(os.path.isfile, os.listdir(search_dir))
files = [os.path.join(search_dir, f) for f in files] # add path to each file
files.sort(key=lambda x: os.path.getmtime(x))

for filename in files:
    if filename.endswith(".log"):
        firstProfit, maxprofit, pnl = analyseFile(filename)
        if(firstProfit or maxprofit or pnl):
            print( filename
                + ', firstProfit=' + str(firstProfit)
                + '% ,maxProfit=' + str(maxprofit)
                + '% ,pnl=' + str(pnl)
                + '% ,pnl_théorique=' + str(pnl - firstProfit) +'%')