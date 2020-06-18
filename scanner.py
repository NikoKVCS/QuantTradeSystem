import fetcher
import datetime
import time
import os
import utils
import _thread
import signalfinder
from log import logger
import numpy as np
from datetime import timedelta, timezone

class TradeSignalScanner:

    def __init__(self, progressCallback, tradeSignalCallback, signalFinder, simulation=False):
        self.queue_data_updated = []
        self.signal_date_update_finished = False
        self.tradeSignalCallback = tradeSignalCallback
        self.progressCallback = progressCallback
        self.signalFinder = signalFinder
        self.simulation = simulation
        self.dataset = dict()
        self.metaPath = "stocksdata/meta.npy"
        self.meta = dict()

        if os.path.exists(self.metaPath):
            self.meta = np.load(self.metaPath, allow_pickle=True)[0]

        # 更新 meta 文件
        for filename in os.listdir(r'stocksdata'):
            if "meta.npy" == filename:
                continue

            ticker = ""
            parts = filename.split('.')[:-1]
            ticker = parts[0]
            if len(parts) > 1:
                for i in range(1,len(parts)):
                    ticker = ticker + "." + parts[i]
            
            rawdata = np.load("stocksdata/" + ticker + ".npy", allow_pickle=True)[0]
            if 'date' not in rawdata.keys() or len(rawdata.get('date')) <= 0:
                continue

            mvalue = dict()
            mvalue['latest_date'] = rawdata.get('date')[-1]
            self.meta[ticker] = mvalue

            if self.simulation:
                self.dataset[ticker] = rawdata
        
        np.save(self.metaPath, np.array([self.meta]))
            
    def dataUpdate(self,tickerlist,final_date):
        
        batch_request = []
        for index in range(len(tickerlist)):
            ticker = tickerlist[index]

            if self.meta.get(ticker) != None:
                mvalue = self.meta.get(ticker)
                latest_date = mvalue.get("latest_date")
                if utils.dateGreaterOrEqual(latest_date, final_date): 
                    self.queue_data_updated.append(ticker)
                    continue

            batch_request.append(ticker)
            if (len(batch_request) > 3 or index > len(tickerlist) - 3) and self.simulation == False:
                listTicker, listUpdateDate = fetcher.fetchBatch(batch_request)
                for i in range(len(listTicker)):
                    mvalue = dict()
                    mvalue['latest_date'] = listUpdateDate[i]
                    self.meta[listTicker[i]] = mvalue
                    np.save(self.metaPath, np.array([self.meta]))

                    self.progressCallback(listTicker[i], listUpdateDate[i])

                    self.queue_data_updated.append(listTicker[i])

                batch_request = []

        self.signal_date_update_finished = True

    def tradeSignal(self, final_date):
        ending = False

        while self.signal_date_update_finished == False or len(self.queue_data_updated) > 0:
            if len(self.queue_data_updated) == 0:
                continue
            ticker = self.queue_data_updated.pop()

            rawdata = dict()
            if self.simulation:
                if self.dataset.get(ticker) == None:
                    rawdata = np.load( "stocksdata/"+ticker+".npy", allow_pickle=True)[0]
                    self.dataset[ticker] = rawdata
                else:
                    rawdata = self.dataset[ticker] 
                pass
            else:
                rawdata = np.load( "stocksdata/"+ticker+".npy", allow_pickle=True)[0]

            datelist = rawdata.get('date')
            index = 0
            for i in range(len(datelist)-1, 0, -1):
                if utils.dateGreaterOrEqual(datelist[i], final_date) and utils.dateGreaterOrEqual(datelist[i-1], final_date) == False:
                    if datelist[i] == final_date:
                        index = i
                        break
                    else:
                        days = utils.dayBetweenDate(datelist[i-1], final_date)
                        if days > 0:
                            index = 0
                            break
                        else:
                            index = i - 1
                            break

            if index == 0:
                # 无效信号
                continue

            start = max(0, index - 150)

            openprice = rawdata.get('open')[start:index + 1]
            closeprice = rawdata.get('close')[start:index + 1]
            high = rawdata.get('high')[start:index + 1]
            low = rawdata.get('low')[start:index + 1]
            volume = rawdata.get('volume')[start:index + 1]

            strength, value_dict = self.signalFinder(ticker, openprice, closeprice, low, high, volume)
            if value_dict == None or strength == 0:
                continue

            future_data = dict()
            if index + 1 < len(rawdata.get('open')):
                future_data['open'] = rawdata.get('open')[index+1:]
                future_data['close'] = rawdata.get('close')[index+1:]
                future_data['low'] = rawdata.get('low')[index+1:]
                future_data['high'] = rawdata.get('high')[index+1:]
                future_data['volume'] = rawdata.get('volume')[index+1:]
                future_data['date'] = rawdata.get('date')[index+1:]

            value_dict['ticker'] = ticker
            value_dict['future_data'] = future_data
            value_dict['order_created_date'] = datelist[index]

            self.tradeSignalCallback(ticker, strength, value_dict, False)

        self.tradeSignalCallback("", 0, dict(), True)
        pass

    def scanAllTradeSignals(self, timestamp, tickerlist = None):

        if tickerlist == None:
            tickerlist = list(self.meta.keys())

        self.queue_data_updated = []
        self.signal_date_update_finished = False
        
        tz = timezone(timedelta(hours=-4))# UTC-0400 即美国东部时间
        today = datetime.datetime.fromtimestamp(int(timestamp), tz)
        final_date = ""
        if today.weekday() >= 5:
            # 今天是周六周日，股市不开盘
            offset = datetime.timedelta(days= today.weekday() - 4)
            final_date = (today-offset).strftime('%Y-%m-%d') # 数据应该被更新到这一天才是最新数据
        else:
            if today.hour > 16:
                # 今天已经闭盘了 所以今天的数据已经出来的了
                final_date = today.strftime('%Y-%m-%d')
            else:
                # 今天还没闭盘了 最新的数据是昨天的数据
                offset = datetime.timedelta(days=1) if today.weekday() != 0 else datetime.timedelta(days=3)
                final_date = (today-offset).strftime('%Y-%m-%d')

        try:
            _thread.start_new_thread( self.tradeSignal, (final_date,) )
        except:
            logger.error("scanAllTradeSignals: failed to start thread")
            return
            
        try:
            _thread.start_new_thread( self.dataUpdate, (tickerlist,final_date,) )
        except:
            logger.error("scanAllTradeSignals: failed to start thread")
            return
        
            
def onProgress(ticker, updateDate):
    print(ticker, " updated at ", updateDate)

def onTradeSignal(ticker, strength, value_dict, ending):
    print(ticker, strength, value_dict.get('action'), value_dict.get('entry_price'), value_dict.get('stop_loss'), value_dict.get('take_profit'), value_dict.get('tailing_stop'), ending)

if __name__ == "__main__":
    scanner = TradeSignalScanner(onProgress, onTradeSignal, signalfinder.movingAverageCrossover)
    scanner.scanAllTradeSignals(time.time())
    pass