import os
import json
import numpy as np
import time
import datetime
import re

aa = dict()
aa[1] = 2
if not aa:
    print("dd")


"""
dataset1 = np.load('dataset_short_mini.npy', allow_pickle=True)[0]
dataset2 = np.load('dataset_short_test.npy', allow_pickle=True)[0]
dataset1['testdata'] = dataset2.get('testdata')
np.save('dataset_short_mini.npy', np.array([dataset1]))

dataset1 = np.load('dataset_long_mini.npy', allow_pickle=True)[0]
dataset2 = np.load('dataset_long_test.npy', allow_pickle=True)[0]
dataset1['testdata'] = dataset2.get('testdata')
np.save('dataset_long_mini.npy', np.array([dataset1]))
"""

def checkTextValid(text):
    dic = dict()
    try:
        dic = json.loads(text)
    except ValueError:
        return False

    dic = json.loads(text)
    if 'history' not in dic.keys():
        return False
        
    dic = dic.get('history')
    if len(dic.keys()) < 365:
        return False


def getStockdata( ticker):
    if os.path.exists('stocks/'+ticker+'.txt'):
        f = open('stocks/'+ticker+'.txt',"r")
        text = f.read()
        f.close()
        return text

    return ""


def parseStockData(text, finaltime = None, begintime = None):

    data = json.loads(text)
    data = data.get('history')

    if finaltime != None:
        # 如果指定的日期不存在数据，则返回None
        if data.get(finaltime) == None:
            return [],[],[],[],[]
    else:
        finaltime = datetime.datetime.now().strftime('%F')

    if begintime == None:
        begintime = '1995-1-1'

    # convey the finaltime (string) to a comparable numerical variable
    finaltime_num = 0
    lst = finaltime.split('-')
    for i in lst:
        finaltime_num = finaltime_num * 1000 + int(i)

    begintime_num = 0
    lst = begintime.split('-')
    for i in lst:
        begintime_num = begintime_num * 1000 + int(i)

    data_in_order = dict()
    
    for key in data.keys():
        lst = key.split('-')
        order = 0
        for i in lst:
            order = order * 1000 + int(i)
        if order >= begintime_num and order <= finaltime_num: # 只分析近30年的
            value = data.get(key)
            value['date'] = key
            data_in_order[order] = value

    keys = sorted(data_in_order.keys())
    
    low = np.zeros((len(keys)), dtype=np.float64)
    high = np.zeros((len(keys)), dtype=np.float64)
    openprice = np.zeros((len(keys)), dtype=np.float64)
    closeprice = np.zeros((len(keys)), dtype=np.float64)
    volume = np.zeros((len(keys)), dtype=np.float64)
    date = []

    for id in range(len(keys)):
        value = data_in_order.get(keys[id])
        
        low[id] = value.get('low')
        high[id] = value.get('high')
        openprice[id] = value.get('open')
        closeprice[id] = value.get('close')
        volume[id] = value.get('volume')
        date.append(value.get('date'))
    
    return openprice, closeprice, low, high, volume, date


def convertStocksData():
    stock_used = np.load('longstock_used.1.npy',allow_pickle=True)

    metadataPath = "stocksdata/meta.npy"
    metadata = dict()
    if os.path.exists(metadataPath):
        metadata = np.load(metadataPath, allow_pickle=True)[0]

    for ticker in stock_used:
        text = getStockdata(ticker)
        if checkTextValid(text) == False:
            continue

        openprice, closeprice, low, high, volume, date = parseStockData(text)
        value = dict()
        value['open'] = openprice
        value['close'] = closeprice
        value['low'] = low
        value['high'] = high
        value['volume'] = volume
        value['date'] = date
        np.save("stocksdata/" + ticker + ".npy", np.array([value]))

        meta_value = dict()
        if metadata.get(ticker) != None:
            meta_value = metadata.get(ticker)
        
        meta_value['latest_date'] = date[-1]
        metadata[ticker] = meta_value

        np.save(metadataPath, np.array([metadata]))

    pass


def getAllStocksTicker():
    f = open("etorostocks.txt","r")
    text = f.read()
    f.close()

    ticker = []
    tickerString = ''

    dic = json.loads(text)
    lst = dic.get('InstrumentDisplayDatas')
    for item in lst:
        if item.get('InstrumentTypeID') == 5:
            ticker.append(item.get('SymbolFull'))
            if tickerString == '':
                tickerString = item.get('SymbolFull')
            else:
                tickerString = tickerString + ',' + item.get('SymbolFull')

    f = open('tickerlist.txt', 'w')
    f.write(tickerString)
    f.close()

    return ticker

if __name__ == "__main__":
    convertStocksData()
    pass