import utils

class Account:
    def __init__(self):
        self.__account_cash = 0
        self.__stocks_on_hold = []

    def addCash(self, amount):
        self.__account_cash += amount
    
    def addTrade(self, trade):
        self.__stocks_on_hold.append(trade)

    def getAsset(self):
        value = 0
        for stock in self.__stocks_on_hold:
            value += stock.get("value")
        return self.__account_cash + value

    def getCash(self):
        return self.__account_cash

    def getTrades(self):
        return len(self.__stocks_on_hold)

    def closeoutOutdatedStocks(self, time):
        for stock in self.__stocks_on_hold:
            if stock.get("closeout_time") == None:
                continue

            if utils.dateGreaterOrEqual(time, stock.get("closeout_time")):
                self.__account_cash += stock.get("value")
                self.__stocks_on_hold.remove(stock)

    def printInfo(self):
        print("Account Cash : ", self.__account_cash)
        for stock in self.__stocks_on_hold:
            print("Ticker:%s | %s | CashBack:%.2f | start:%s | closeout:%s | entry_price:%.2f | shares:%.2f | profit:%.2f" % (
            stock.get("ticker"),stock.get("action"),stock.get("value"),stock.get("start_time"),
            stock.get("closeout_time"),stock.get("entry_price"),stock.get("shares"),stock.get("profit")))
