import datetime
import utils
import scanner
import threading
import account
import signalfinder
import strategy


class TradeSimulator:

    def __init__(self, messageCallback, signalFinder, orderGenerator, fixed_investment, reinvest_scale):
        
        self.messageCallback = messageCallback
        self.orderGenerator = orderGenerator
        self.fixed_investment = fixed_investment
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

    def startSimulation(self, begintime, endtime=None):
        self.abort = False

        bt = datetime.datetime.strptime(begintime+" UTC-0400", "%Y-%m-%d %Z%z")
        oneday = datetime.timedelta(days=1)
        today = bt

        monthly_profit = 0
        monthly_loss = 0
        monthly_trades = 0
        monthly_win_trade = 1
        monthly_lose_trade = 1

        win_trade = 1
        lose_trade = 1

        fixed_investment = self.fixed_investment
        reinvest_scale = self.reinvest_scale

        accumulate_profit = 0
        accumulate_freecash = 0
        accumulate_fix_investment = 0

        while utils.dateGreaterOrEqual(endtime, today.strftime('%Y-%m-%d')) and self.abort == False:
            today += oneday
            today_str = today.strftime('%Y-%m-%d')


            if today.day == 1:
                #结算日
                free_cashflow = max(0, (monthly_profit - monthly_loss) * (1-reinvest_scale))

                self.account.addCash(fixed_investment)
                self.account.addCash(-free_cashflow)

                accumulate_freecash += free_cashflow
                accumulate_profit += monthly_profit - monthly_loss
                accumulate_fix_investment += fixed_investment

                message = dict()
                message['Date'] = today_str
                message['AccountCash'] = self.account.getCash()
                message['AccountAsset'] = self.account.getAsset()
                message['Winrate'] = win_trade / (win_trade+lose_trade)
                message['accumulate_fix_investment'] = accumulate_fix_investment
                message['accumulate_profit'] = accumulate_profit
                message['accumulate_freecash'] = accumulate_freecash

                message['monthly_profit'] = monthly_profit
                message['monthly_loss'] = monthly_loss
                message['monthly_freecash'] = free_cashflow
                message['monthly_trades'] = monthly_trades
                message['monthly_winrate'] = monthly_win_trade / (monthly_lose_trade+monthly_win_trade)

                self.messageCallback("MonthlyStatistics", message)

                monthly_profit = 0
                monthly_loss = 0
                monthly_trades = 0
                monthly_win_trade = 1
                monthly_lose_trade = 1
            else:
                message = dict()
                message['Date'] = today_str
                message['cash'] = self.account.getCash()
                message['assets'] = self.account.getAsset()

                self.messageCallback("DailyStatistics", message)


            self.account.closeoutOutdatedStocks(today_str)
            
            if self.account.getCash() < 50:
                continue

            self.lock = True
            self.signalScanner.scanAllTradeSignals(today.timestamp())
            while self.lock:
                pass

            stock_candidate = self.stock_candidate
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

                if entry_price > high[0] or entry_price < low[0]:
                    # 因为交易订单为限价单，如果价格没到订单指定的价格的话，交易不会被触发
                    continue

                profit = 0
                closeout_date = ""

                if action == 1:
                    stop_loss_percentage = 1 - stop_loss/entry_price

                    for i in range(1, len(openprice)):
                        if low[i] < stop_loss or i+1 >= len(low):
                            if openprice[i] > stop_loss:
                                profit = stop_loss - entry_price
                            else:
                                profit = openprice[i] - entry_price

                            closeout_date = date[i]
                            break

                        if high[i] > take_profit:
                            profit = take_profit - entry_price
                            closeout_date = date[i]
                            break

                        if tailing_stop and closeprice[i] > stop_loss/(1- stop_loss_percentage):
                            stop_loss = closeprice[i]*(1- stop_loss_percentage)

                    
                    cost = order.get('shares')*entry_price

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
                    self.account.addCash(-cost)

                    self.messageCallback("Trade", trade)
                    pass

                else:
                    stop_loss_percentage = stop_loss/entry_price - 1

                    for i in range(1, len(openprice)):
                        if high[i] > stop_loss or i+1 >= len(low):
                            if openprice[i] < stop_loss:
                                profit = entry_price - stop_loss
                            else:
                                profit = entry_price - openprice[i]
                            closeout_date = date[i]
                            break

                        if low[i] < take_profit:
                            profit = entry_price - take_profit
                            closeout_date = date[i]
                            break

                        # Trailing stop loss
                        if tailing_stop and closeprice[i] < stop_loss/(1+ stop_loss_percentage):
                            stop_loss = closeprice[i]*(1+ stop_loss_percentage)

                    # 做空交易要求持有股票购入金额的80%的现金
                    # 做空交易一交易，立马收入现金，因此总共cost是0.2
                    cash_increment = order.get('shares')*entry_price*(1-0.8)
                    self.account.addCash(cash_increment)

                    trade = dict()
                    trade["value"] = order.get('shares')*entry_price*0.8 - order.get('shares')*(entry_price-profit)
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

    print(msg_text)

    global logcontent
    logcontent = logcontent + '\n' + msg_text
    if len(logcontent) > 500:
        f = open('Simulation_MA.txt',"a")
        f.write(logcontent)
        f.close()

        logcontent = ""

   
if __name__ == "__main__":
    simulator = TradeSimulator(onMessage, signalfinder.movingAverageCrossover, strategy.orderGenerator, 750, 0.8)
    simulator.startSimulation("2014-01-01", "2020-3-1")

    pass