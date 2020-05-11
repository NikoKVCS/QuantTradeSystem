import datetime
import utils
import scanner
import threading
import account
import signalfinder
import strategy
import analyzer


class TradeSimulator:

    def __init__(self, messageCallback, signalFinder, orderGenerator, fixed_invest, investment, reinvest_scale):
        
        self.messageCallback = messageCallback
        self.orderGenerator = orderGenerator
        self.fixed_invest = fixed_invest
        self.investment = investment
        self.reinvest_scale = reinvest_scale
        self.stock_candidate = dict()
        self.lock = False

        self.signalScanner = scanner.TradeSignalScanner(self.onProgress, self.onTradeSignal, signalFinder,simulation=True)
        self.account = account.Account()
        pass
            
    def onProgress(self, ticker, updateDate):
        pass

    def onTradeSignal(self, ticker, strength, value_dict, ending):
        if ending == True:
            self.lock = False
            return

        self.stock_candidate[strength] = value_dict

    def startSimulation(self, begintime, endtime=None, tickerList=None):
        self.abort = False

        bt = datetime.datetime.strptime(begintime+" UTC-0400", "%Y-%m-%d %Z%z")
        oneday = datetime.timedelta(days=1)
        today = bt

        monthly_profit = 0
        monthly_loss = 0
        monthly_trades = 0
        monthly_win_trade = 1
        monthly_lose_trade = 1
        monthly_signals = 0

        win_trade = 1
        lose_trade = 1

        reinvest_scale = self.reinvest_scale

        accumulate_profit = 0
        accumulate_freecash = 0
        accumulate_investment = 0

        if self.fixed_invest == False:
            accumulate_investment = self.investment
            self.account.addCash(self.investment)

        while utils.dateGreaterOrEqual(endtime, today.strftime('%Y-%m-%d')) and self.abort == False:
            today += oneday
            today_str = today.strftime('%Y-%m-%d')

            if today_str == "2016-01-06":
                print(today_str)

            if today.day == 1:
                #结算日
                free_cashflow = max(0, (monthly_profit - monthly_loss) * (1-reinvest_scale))

                if self.fixed_invest:
                    self.account.addCash(self.investment)
                    accumulate_investment += self.investment

                self.account.addCash(-free_cashflow)

                accumulate_freecash += free_cashflow
                accumulate_profit += monthly_profit - monthly_loss

                message = dict()
                message['Date'] = today_str
                message['AccountCash'] = self.account.getCash()
                message['AccountAsset'] = self.account.getAsset()
                message['Winrate'] = win_trade / (win_trade+lose_trade)
                message['accumulate_investment'] = accumulate_investment
                message['accumulate_profit'] = accumulate_profit
                message['accumulate_freecash'] = accumulate_freecash

                message['monthly_profit'] = monthly_profit
                message['monthly_loss'] = monthly_loss
                message['monthly_freecash'] = free_cashflow
                message['monthly_trades'] = monthly_trades
                #message['monthly_signals'] = monthly_signals
                message['monthly_winrate'] = monthly_win_trade / (monthly_lose_trade+monthly_win_trade)

                self.messageCallback("MonthlyStatistics", message)

                monthly_profit = 0
                monthly_loss = 0
                monthly_trades = 0
                monthly_signals = 0
                monthly_win_trade = 1
                monthly_lose_trade = 1
            else:
                message = dict()
                message['Date'] = today_str
                message['cash'] = self.account.getCash()
                message['assets'] = self.account.getAsset()

                self.messageCallback("DailyStatistics", message)


            msg = self.account.closeoutOutdatedStocks(today_str)
            message = dict()
            message['cashback'] = msg
            self.messageCallback("cashback", message)
            
            if self.account.getCash() <= 50:
                continue

            self.lock = True
            self.signalScanner.scanAllTradeSignals(today.timestamp(),tickerlist=tickerList)
            while self.lock:
                pass

            stock_candidate = self.stock_candidate
            monthly_signals += len(stock_candidate)
            self.stock_candidate = dict()
            orderlist = self.orderGenerator(stock_candidate, self.account)
            
            if len(orderlist) == 0:
                continue
            
            for order in orderlist:
                future_data = order.get('future_data')
                if future_data == None:
                    continue
                    
                openprice = future_data.get('open')
                closeprice = future_data.get('close')
                high = future_data.get('high')
                low = future_data.get('low')
                volume = future_data.get('volume')
                date = future_data.get('date')

                if len(openprice) < 2:
                    continue

                action = order.get('action')
                entry_price = order.get('entry_price')
                stop_loss = order.get('stop_loss')
                take_profit = order.get('take_profit')
                tailing_stop = order.get('tailing_stop')

                profit, closeout_date = analyzer.analyzeTradeResult(order.get('order_created_date'), action, entry_price, stop_loss, take_profit, tailing_stop, date, openprice, closeprice, high, low)

                # 交易未成功被触发 -- 限价单未被成功filled
                if closeout_date == "":
                    continue 

                if action == 1:
                    
                    cost = order.get('shares')*entry_price
                    self.account.addCash(-cost)

                    trade = dict()
                    trade["value"] = order.get('shares')*(entry_price + profit)
                    trade["ticker"] = order.get("ticker")
                    trade["start_time"] = today_str
                    trade["closeout_time"] = closeout_date
                    trade["action"] = "BUY" if order.get('action') == 1 else "SELL"
                    trade["entry_price"] = entry_price
                    trade["shares"] = order.get('shares')
                    trade["profit"] = profit * order.get('shares')
                    self.account.addTrade(trade)

                    self.messageCallback("Trade", trade)
                    pass

                else:

                    # 做空交易一交易，立马收入现金
                    # 但是账户应保留做空卖出的收入额，因为平仓的时候需要用到这部分现金去平仓，
                    # 甚至平仓的时候可能亏损，因此除了要保留收入额，还要预留亏损额的现金
                    preserved_for_loss = (stop_loss - entry_price) * order.get('shares')
                    self.account.addCash(-preserved_for_loss)

                    trade = dict()
                    trade["value"] = preserved_for_loss + order.get('shares')*profit
                    trade["ticker"] = order.get("ticker")
                    trade["start_time"] = today_str
                    trade["closeout_time"] = closeout_date
                    trade["action"] = "BUY" if order.get('action') == 1 else "SELL"
                    trade["entry_price"] = entry_price
                    trade["shares"] = order.get('shares')
                    trade["profit"] = profit * order.get('shares')
                    self.account.addTrade(trade)

                    self.messageCallback("Trade", trade)
                    pass


                monthly_trades += 1

                if profit > 0:
                    win_trade += 1
                    monthly_win_trade += 1
                    monthly_profit += order.get('shares')*profit
                else:
                    lose_trade += 1
                    monthly_lose_trade += 1
                    monthly_loss += -order.get('shares')*profit

            pass

        pass

    def stopSimulation(self):
        self.abort = True


logcontent = ""

def onMessage(event, message):
    msg_text = ""
    if event == "MonthlyStatistics":
        msg_text = "================\n"
        for key,value in message.items():
            msg_text = msg_text + str(key) + ":" +str(value) + '\n' 
        msg_text = msg_text + "================"

    elif event == "DailyStatistics":
        for (key,value) in message.items():
            msg_text = msg_text  + '\n' + str(key) + ":" +str(value)

    elif event == "Trade":
        msg_text = "Ticker:%s | %s | CashBack:%.2f | start:%s | closeout:%s | entry_price:%.2f | shares:%.2f | profit:%.2f" % (
            message.get("ticker"),message.get("action"),message.get("value"),message.get("start_time"),
            message.get("closeout_time"),message.get("entry_price"),message.get("shares"),message.get("profit"))

    elif event == "cashback":
        msg_text = message.get("cashback")

    print(msg_text)

    global logcontent
    logcontent = logcontent + '\n' + msg_text
    if len(logcontent) > 500:
        f = open('Simulation_Simforest.txt',"a")
        f.write(logcontent)
        f.close()

        logcontent = ""

   
if __name__ == "__main__":

    f = open('s&p500TickerList.txt',"r")
    text = f.read()
    f.close()
    tickerlist = text.split(",")
    tickerlist = tickerlist[:100]

    simulator = TradeSimulator(onMessage, signalfinder.simForestPredict, strategy.orderGenerator, False, 10000, 1)
    simulator.startSimulation("2019-12-17", "2020-04-01", tickerList=tickerlist)

    pass