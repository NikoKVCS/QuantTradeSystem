import os
import numpy as np
import platform
import time
import datetime
import re
import requests
import analyzer
import utils
import talib as ta
from talib import MA_Type
from log import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def makeDataset(datasetPath, funcProcessed):

    f = open('s&p500TickerList.txt',"r")
    text = f.read()
    f.close()
    tickerlist = text.split(",")
        
    dataset = {'stock_used':[], 'traindata':dict(), 'testdata':dict()}
    if os.path.exists(datasetPath):
        dataset  = np.load(datasetPath, allow_pickle=True)[0]
        pass
    
    stock_used = dataset.get('stock_used')

    for ticker in tickerlist:
        if ticker in stock_used:
            continue
        
        datelist, openlist, closelist, highlist, lowlist, volumelist = getRawData(ticker)
        if len(datelist) == 0:
            continue

        data_input, data_output = funcProcessed(datelist, openlist, closelist, highlist, lowlist, volumelist)
        

        if np.random.rand(1)[0] < 0.9:
            continue
            
            traindata = dataset.get('traindata')
            if 'data_input' in traindata.keys():
                data_input = np.append(traindata.get('data_input'), data_input, axis=0)
                data_output = np.append(traindata.get('data_output'), data_output, axis=0)

            if np.random.rand(1)[0] < 0.6:
                # mess up the order again
                index = np.random.permutation(len(data_input))
                data_input = data_input[index]
                data_output = data_output[index]
                
            traindata['data_input'] = data_input
            traindata['data_output'] = data_output
            dataset['traindata'] = traindata
        else:
            testdata = dataset.get('testdata')
            if 'data_input' in testdata.keys():
                data_input = np.append(testdata.get('data_input'), data_input, axis=0)
                data_output = np.append(testdata.get('data_output'), data_output, axis=0)

            if np.random.rand(1)[0] < 0.6:
                # mess up the order again
                index = np.random.permutation(len(data_input))
                data_input = data_input[index]
                data_output = data_output[index]
                
            testdata['data_input'] = data_input
            testdata['data_output'] = data_output
            dataset['testdata'] = testdata
                    
        stock_used.append(ticker)
        dataset['stock_used'] = stock_used
        np.save(datasetPath, np.array([dataset]))

    pass



def getRawData(ticker):

    lowlist = np.zeros((0), dtype=np.float64)
    highlist = np.zeros((0), dtype=np.float64)
    openlist = np.zeros((0), dtype=np.float64)
    closelist = np.zeros((0), dtype=np.float64)
    volumelist = np.zeros((0), dtype=np.float64)
    datelist = []

    ticker_data_path = "stocksdata/"+ticker+".npy"

    if os.path.exists(ticker_data_path):
        svalue = np.load(ticker_data_path,allow_pickle=True)[0]

        lowlist = svalue.get('low')
        highlist = svalue.get('high')
        openlist = svalue.get('open')
        closelist = svalue.get('close')
        volumelist = svalue.get('volume')
        datelist = svalue.get('date')
    else:
        excel_path = "stocksexcel/%s.csv" % (ticker)
        if os.path.exists(excel_path) == False:
            OS = platform.system()
            chromeDriverPath = ""
            if OS == "Linux":
                chromeDriverPath = "chrome/linux/chromedriver"
            else:
                chromeDriverPath = "chrome/win/chromedriver.exe"

            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--headless')
            browser = webdriver.Chrome(chrome_options=chrome_options,executable_path=chromeDriverPath)

            period1 = int(datetime.datetime.strptime("1995-01-01", "%Y-%m-%d").timestamp())
            period2 = int(time.time())
            url = "https://finance.yahoo.com/quote/"+ticker+"/history?interval=1d&filter=history&frequency=1d&period1=" + str(period1) + "&period2=" + str(period2)
            browser.get(url)
            text = browser.page_source
            browser.quit()

            lst = re.findall(r'Fl\(end\) Mt\(3px\) Cur\(p\)([\s\S]*?)download="', text)
            if len(lst) == 0:
                return datelist, openlist, closelist, highlist, lowlist, volumelist

            downloadlink = re.findall(r'href="([\s\S]*?)"', lst[0])
            if len(downloadlink) == 0:
                return datelist, openlist, closelist, highlist, lowlist, volumelist

            downloadlink = downloadlink[0].replace("&amp;", "&")
            r = requests.get(downloadlink)
            with open(excel_path, "wb") as f:
                f.write(r.content)

        if os.path.exists(excel_path):
            f = open(excel_path,"r")   
            lines = f.readlines()
            firstLine = True
            for line in lines:
                line = line.replace("\n", "")
                span = line.split(',')

                if len(span) != 7:
                    continue

                if firstLine:
                    firstLine = False
                    continue

                try:

                    datestr = span[0]
                    openp = float(span[1])
                    high = float(span[2])
                    low = float(span[3])
                    closep = float(span[4])
                    avg = float(span[5])
                    volume = int(span[6])

                    openlist = np.append(openlist, openp)
                    highlist = np.append(highlist, high)
                    lowlist = np.append(lowlist, low)
                    closelist = np.append(closelist, closep)
                    volumelist = np.append(volumelist, volume)
                    datelist.append(datestr)
                except Exception as e:
                    logger.error(e)
                    continue

            f.close()

            svalue = dict()
            svalue['open'] = openlist
            svalue['close'] = closelist
            svalue['low'] = lowlist
            svalue['high'] = highlist
            svalue['volume'] = volumelist
            svalue['date'] = datelist
            np.save(ticker_data_path, np.array([svalue]))

    return datelist, openlist, closelist, highlist, lowlist, volumelist

def getProcessedDataV1(datelist, openprice, closeprice, high, low, volume):

    SAMPLE_LENGTH = 80

    dataset = np.vstack((
        openprice,
        closeprice,
        high,
        low,
        volume
    ))
    dataset = dataset.T

    ATR = ta.ATR(high, low, closeprice, timeperiod=14)

    data_input = np.empty((0,SAMPLE_LENGTH,dataset.shape[1]), np.float32)
    data_output = np.empty((0,3), np.float32)
    label = np.empty((0), np.float32)

    i = 100+SAMPLE_LENGTH
    while i + SAMPLE_LENGTH + 35 < len(closeprice):
        i += 5

        # Long position
        entry_price = high[i]
        stop_loss = high[i] - ATR[i] * 1
        take_profit = high[i] + ATR[i] * 2
        profit_long, closeoutdate_long = analyzer.analyzeTradeResult(datelist[i], 1, entry_price, stop_loss, take_profit, False, datelist[i+1:], openprice[i+1:], closeprice[i+1:], high[i+1:], low[i+1:])

        # Short position
        entry_price = low[i]
        stop_loss = low[i] + ATR[i] * 1
        take_profit = low[i] - ATR[i] * 2
        profit_short, closeoutdate_short = analyzer.analyzeTradeResult(datelist[i], 2, entry_price, stop_loss, take_profit, False, datelist[i+1:], openprice[i+1:], closeprice[i+1:], high[i+1:], low[i+1:])

        if profit_long > 0 and profit_long > profit_short:
            y = np.zeros((3), dtype=np.float32)
            y[1] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 1)
        elif profit_short > 0 and profit_short > profit_long:
            y = np.zeros((3), dtype=np.float32)
            y[2] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 2)
        else:
            y = np.zeros((3), dtype=np.float32)
            y[0] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 0)

        x = dataset[i+1-SAMPLE_LENGTH:i+1]
        data_input = np.append(data_input, np.array([x.astype(np.float32)]), axis=0)

    # messed up the data list order
    index = np.random.permutation(len(data_input))
    data_input = data_input[index]
    data_output = data_output[index]
    label = label[index]

    # 三种交易信号数量平均化
    signal_hold = np.where(label==0)[0]
    signal_buy = np.where(label==1)[0]
    signal_sell = np.where(label==2)[0]

    length = np.amin([len(signal_hold), len(signal_buy), len(signal_sell)])
    index = np.append(signal_hold[0:length], signal_buy[0:length])
    index = np.append(index, signal_sell[0:length])
    data_input = data_input[index]
    data_output = data_output[index]

    # messed up the data list order
    index = np.random.permutation(len(data_input))
    data_input = data_input[index]
    data_output = data_output[index]

    return data_input, data_output


def getProcessedDataV2(datelist, openprice, closeprice, high, low, volume):

    closeprice_processed = np.array(closeprice)

    k, d = ta.STOCHF(high, low, closeprice, fastk_period=5, fastd_period=3, fastd_matype=MA_Type.EMA)
    rsi = ta.RSI(closeprice, timeperiod=14) # independent
    sar = ta.SAR(high, low, acceleration=0.02, maximum=0.2)

    for i in range(len(closeprice)-1,0,-1):
        closeprice_processed[i] = closeprice[i] / closeprice[i-1]

    dataset = np.vstack((
        closeprice_processed,
        volume,
        k,
        d,
        rsi,
        sar/closeprice
    ))
    dataset = dataset.T

    SAMPLE_LENGTH = 50

    ATR = ta.ATR(high, low, closeprice, timeperiod=14)

    data_input = np.empty((0,SAMPLE_LENGTH,dataset.shape[1]), np.float32)
    data_output = np.empty((0,3), np.float32)
    label = np.empty((0), np.float32)

    i = 100+SAMPLE_LENGTH
    while i + SAMPLE_LENGTH + 35 < len(closeprice):
        i += 5

        if utils.dateGreaterThan(datelist[i], '2015-01-01') == False or utils.dateGreaterThan(datelist[i], '2018-01-01'):
            continue


        # Long position
        entry_price = high[i]
        stop_loss = high[i] - ATR[i] * 1
        take_profit = high[i] + ATR[i] * 2
        profit_long, closeoutdate_long = analyzer.analyzeTradeResult(datelist[i], 1, entry_price, stop_loss, take_profit, False, datelist[i+1:], openprice[i+1:], closeprice[i+1:], high[i+1:], low[i+1:])

        # Short position
        entry_price = low[i]
        stop_loss = low[i] + ATR[i] * 1
        take_profit = low[i] - ATR[i] * 2
        profit_short, closeoutdate_short = analyzer.analyzeTradeResult(datelist[i], 2, entry_price, stop_loss, take_profit, False, datelist[i+1:], openprice[i+1:], closeprice[i+1:], high[i+1:], low[i+1:])

        if profit_long > 0 and profit_long > profit_short:
            y = np.zeros((3), dtype=np.float32)
            y[1] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 1)
        elif profit_short > 0 and profit_short > profit_long:
            y = np.zeros((3), dtype=np.float32)
            y[2] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 2)
        else:
            y = np.zeros((3), dtype=np.float32)
            y[0] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 0)

        x = dataset[i+1-SAMPLE_LENGTH:i+1]
        data_input = np.append(data_input, np.array([x.astype(np.float32)]), axis=0)

    if len(data_input) == 0:
        return data_input, data_output
        
    # messed up the data list order
    index = np.random.permutation(len(data_input))
    data_input = data_input[index]
    data_output = data_output[index]
    label = label[index]

    # 三种交易信号数量平均化
    signal_hold = np.where(label==0)[0]
    signal_buy = np.where(label==1)[0]
    signal_sell = np.where(label==2)[0]

    length = np.amin([len(signal_hold), len(signal_buy), len(signal_sell)])
    index = np.append(signal_hold[0:length], signal_buy[0:length])
    index = np.append(index, signal_sell[0:length])
    data_input = data_input[index]
    data_output = data_output[index]

    # messed up the data list order
    index = np.random.permutation(len(data_input))
    data_input = data_input[index]
    data_output = data_output[index]

    return data_input, data_output


def getProcessedDataV3_Long(datelist, openprice, closeprice, high, low, volume):

    closeprice_processed = np.array(closeprice)

    k, d = ta.STOCHF(high, low, closeprice, fastk_period=5, fastd_period=3, fastd_matype=MA_Type.EMA)
    rsi = ta.RSI(closeprice, timeperiod=14) # independent
    sar = ta.SAR(high, low, acceleration=0.02, maximum=0.2)

    for i in range(len(closeprice)-1,0,-1):
        closeprice_processed[i] = closeprice[i] / closeprice[i-1]

    dataset = np.vstack((
        closeprice_processed,
        volume,
        k,
        d,
        rsi,
        sar/closeprice
    ))
    dataset = dataset.T

    SAMPLE_LENGTH = 50

    ATR = ta.ATR(high, low, closeprice, timeperiod=14)

    data_input = np.empty((0,SAMPLE_LENGTH,dataset.shape[1]), np.float32)
    data_output = np.empty((0,2), np.float32)
    label = np.empty((0), np.float32)

    EMA5 = ta.EMA(closeprice, timeperiod=5)
    EMA14 = ta.EMA(closeprice, timeperiod=14)

    i = 100+SAMPLE_LENGTH
    while i + SAMPLE_LENGTH + 35 < len(closeprice):
        i += 5

        if utils.dateGreaterThan(datelist[i], '2010-01-01') == False or utils.dateGreaterThan(datelist[i], '2016-12-01'):
            continue

        #if EMA5[i]<=EMA14[i] or EMA5[i-1]>=EMA14[i-1]:
        #    continue
        
        # Long position
        entry_price = high[i]
        stop_loss = high[i] - ATR[i] * 1
        take_profit = high[i] + ATR[i] * 2
        profit_long, closeoutdate_long = analyzer.analyzeTradeResult(datelist[i], 1, entry_price, stop_loss, take_profit, False, datelist[i+1:], openprice[i+1:], closeprice[i+1:], high[i+1:], low[i+1:])

        if profit_long > 0:
            y = np.zeros((2), dtype=np.float32)
            y[1] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 1)
        else:
            y = np.zeros((2), dtype=np.float32)
            y[0] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 0)

        x = dataset[i+1-SAMPLE_LENGTH:i+1]
        data_input = np.append(data_input, np.array([x.astype(np.float32)]), axis=0)

    if len(data_input) == 0:
        return data_input, data_output
    """
    # messed up the data list order
    index = np.random.permutation(len(data_input))
    data_input = data_input[index]
    data_output = data_output[index]
    label = label[index]
    
    # 三种交易信号数量平均化
    signal_hold = np.where(label==0)[0]
    signal_trade = np.where(label==1)[0]

    length = np.amin([len(signal_hold), len(signal_trade)])
    index = np.append(signal_hold[0:length], signal_trade[0:length])
    data_input = data_input[index]
    data_output = data_output[index]
    """
    # messed up the data list order
    index = np.random.permutation(len(data_input))
    data_input = data_input[index]
    data_output = data_output[index]

    return data_input, data_output


def getProcessedDataV3_Short(datelist, openprice, closeprice, high, low, volume):

    closeprice_processed = np.array(closeprice)

    k, d = ta.STOCHF(high, low, closeprice, fastk_period=5, fastd_period=3, fastd_matype=MA_Type.EMA)
    rsi = ta.RSI(closeprice, timeperiod=14) # independent
    sar = ta.SAR(high, low, acceleration=0.02, maximum=0.2)

    for i in range(len(closeprice)-1,0,-1):
        closeprice_processed[i] = closeprice[i] / closeprice[i-1]

    dataset = np.vstack((
        closeprice_processed,
        volume,
        k,
        d,
        rsi,
        sar/closeprice
    ))
    dataset = dataset.T

    SAMPLE_LENGTH = 50

    ATR = ta.ATR(high, low, closeprice, timeperiod=14)

    data_input = np.empty((0,SAMPLE_LENGTH,dataset.shape[1]), np.float32)
    data_output = np.empty((0,2), np.float32)
    label = np.empty((0), np.float32)

    EMA5 = ta.EMA(closeprice, timeperiod=5)
    EMA14 = ta.EMA(closeprice, timeperiod=14)

    i = 100+SAMPLE_LENGTH
    while i + SAMPLE_LENGTH + 35 < len(closeprice):
        i += 5

        if utils.dateGreaterThan(datelist[i], '2010-01-01') == False or utils.dateGreaterThan(datelist[i], '2016-12-01'):
            continue

        #if EMA5[i]>=EMA14[i] or EMA5[i-1]<=EMA14[i-1]:
        #    continue
        
        # Short position
        entry_price = low[i]
        stop_loss = low[i] + ATR[i] * 1
        take_profit = low[i] - ATR[i] * 2
        profit_short, closeoutdate_short = analyzer.analyzeTradeResult(datelist[i], 2, entry_price, stop_loss, take_profit, False, datelist[i+1:], openprice[i+1:], closeprice[i+1:], high[i+1:], low[i+1:])

        if profit_short > 0:
            y = np.zeros((2), dtype=np.float32)
            y[1] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 1)
        else:
            y = np.zeros((2), dtype=np.float32)
            y[0] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 0)

        x = dataset[i+1-SAMPLE_LENGTH:i+1]
        data_input = np.append(data_input, np.array([x.astype(np.float32)]), axis=0)

    if len(data_input) == 0:
        return data_input, data_output
        
    # messed up the data list order
    index = np.random.permutation(len(data_input))
    data_input = data_input[index]
    data_output = data_output[index]

    return data_input, data_output


def getProcessedDataV4_Long(datelist, openprice, closeprice, high, low, volume):

    closeprice_processed = np.array(closeprice)

    k, d = ta.STOCHF(high, low, closeprice, fastk_period=5, fastd_period=3, fastd_matype=MA_Type.EMA)
    rsi = ta.RSI(closeprice, timeperiod=14) # independent
    sar = ta.SAR(high, low, acceleration=0.02, maximum=0.2)

    for i in range(len(closeprice)-1,0,-1):
        closeprice_processed[i] = closeprice[i] / closeprice[i-1]

    dataset = np.vstack((
        closeprice_processed,
        volume,
        k,
        d,
        rsi,
        sar/closeprice
    ))
    dataset = dataset.T

    SAMPLE_LENGTH = 50

    ATR = ta.ATR(high, low, closeprice, timeperiod=14)

    data_input = np.empty((0,SAMPLE_LENGTH,dataset.shape[1]), np.float32)
    data_output = np.empty((0,2), np.float32)
    label = np.empty((0), np.float32)

    EMA5 = ta.EMA(closeprice, timeperiod=5)
    EMA14 = ta.EMA(closeprice, timeperiod=14)

    i = 100+SAMPLE_LENGTH
    while i + SAMPLE_LENGTH + 35 < len(closeprice):
        i += 1

        if utils.dateGreaterThan(datelist[i], '2010-01-01') == False or utils.dateGreaterThan(datelist[i], '2016-12-01'):
            continue

        if EMA5[i]<=EMA14[i] or EMA5[i-1]>=EMA14[i-1]:
            continue
        
        # Long position
        entry_price = high[i]
        stop_loss = high[i] - ATR[i] * 1
        take_profit = high[i] + ATR[i] * 2
        profit_long, closeoutdate_long = analyzer.analyzeTradeResult(datelist[i], 1, entry_price, stop_loss, take_profit, False, datelist[i+1:], openprice[i+1:], closeprice[i+1:], high[i+1:], low[i+1:])

        if profit_long > 0:
            y = np.zeros((2), dtype=np.float32)
            y[1] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 1)
        else:
            y = np.zeros((2), dtype=np.float32)
            y[0] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 0)

        x = dataset[i+1-SAMPLE_LENGTH:i+1]
        data_input = np.append(data_input, np.array([x.astype(np.float32)]), axis=0)

    if len(data_input) == 0:
        return data_input, data_output
    """
    # messed up the data list order
    index = np.random.permutation(len(data_input))
    data_input = data_input[index]
    data_output = data_output[index]
    label = label[index]
    
    # 三种交易信号数量平均化
    signal_hold = np.where(label==0)[0]
    signal_trade = np.where(label==1)[0]

    length = np.amin([len(signal_hold), len(signal_trade)])
    index = np.append(signal_hold[0:length], signal_trade[0:length])
    data_input = data_input[index]
    data_output = data_output[index]
    """
    # messed up the data list order
    index = np.random.permutation(len(data_input))
    data_input = data_input[index]
    data_output = data_output[index]

    return data_input, data_output


def getProcessedDataV4_Short(datelist, openprice, closeprice, high, low, volume):

    closeprice_processed = np.array(closeprice)

    k, d = ta.STOCHF(high, low, closeprice, fastk_period=5, fastd_period=3, fastd_matype=MA_Type.EMA)
    rsi = ta.RSI(closeprice, timeperiod=14) # independent
    sar = ta.SAR(high, low, acceleration=0.02, maximum=0.2)

    for i in range(len(closeprice)-1,0,-1):
        closeprice_processed[i] = closeprice[i] / closeprice[i-1]

    dataset = np.vstack((
        closeprice_processed,
        volume,
        k,
        d,
        rsi,
        sar/closeprice
    ))
    dataset = dataset.T

    SAMPLE_LENGTH = 50

    ATR = ta.ATR(high, low, closeprice, timeperiod=14)

    data_input = np.empty((0,SAMPLE_LENGTH,dataset.shape[1]), np.float32)
    data_output = np.empty((0,2), np.float32)
    label = np.empty((0), np.float32)

    EMA5 = ta.EMA(closeprice, timeperiod=5)
    EMA14 = ta.EMA(closeprice, timeperiod=14)

    i = 100+SAMPLE_LENGTH
    while i + SAMPLE_LENGTH + 35 < len(closeprice):
        i += 1

        if utils.dateGreaterThan(datelist[i], '2010-01-01') == False or utils.dateGreaterThan(datelist[i], '2016-12-01'):
            continue

        if EMA5[i]>=EMA14[i] or EMA5[i-1]<=EMA14[i-1]:
            continue
        
        # Short position
        entry_price = low[i]
        stop_loss = low[i] + ATR[i] * 1
        take_profit = low[i] - ATR[i] * 2
        profit_short, closeoutdate_short = analyzer.analyzeTradeResult(datelist[i], 2, entry_price, stop_loss, take_profit, False, datelist[i+1:], openprice[i+1:], closeprice[i+1:], high[i+1:], low[i+1:])

        if profit_short > 0:
            y = np.zeros((2), dtype=np.float32)
            y[1] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 1)
        else:
            y = np.zeros((2), dtype=np.float32)
            y[0] = 1
            data_output = np.append(data_output, np.array([y]), axis=0)
            label = np.append(label, 0)

        x = dataset[i+1-SAMPLE_LENGTH:i+1]
        data_input = np.append(data_input, np.array([x.astype(np.float32)]), axis=0)

    if len(data_input) == 0:
        return data_input, data_output
        
    # messed up the data list order
    index = np.random.permutation(len(data_input))
    data_input = data_input[index]
    data_output = data_output[index]

    return data_input, data_output


if __name__ == "__main__":
    #makeDataset('dataset_long_test.npy', getProcessedDataV4_Long)
    makeDataset('dataset_short_test.npy', getProcessedDataV4_Short)
    #makeDataset('dataset_long.npy', getProcessedDataV3_Long)
    #makeDataset('dataset_short.npy', getProcessedDataV3_Short)
    pass

