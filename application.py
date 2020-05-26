import sys
from PyQt4 import QtGui, QtCore
import scanner
import datetime
from signalfinder import proximityForestPredict
import math
import time


class Communicate(QtCore.QObject):
    uiSignal = QtCore.pyqtSignal(str) 
    

class Application:

    def __init__(self):
            
        f = open('s&p500TickerList.txt',"r")
        text = f.read()
        f.close()
        tickerlist = text.split(",")
        self.tickerlist = tickerlist[:100]
        
        self.stock_candidate = dict()
        self.lock = False
        self.signalScanner = scanner.TradeSignalScanner(self.onProgress, self.onTradeSignal, proximityForestPredict,simulation=False)
        self.text = ""
        self.main()
        pass
   
    def onProgress(self, ticker, updateDate):
        line = "\n" + ticker + " 股票数据更新至： " + updateDate
        self.text += line
        self.c.uiSignal.emit(self.text + "\n扫描市场交易信号中...")
        pass

    def onTradeSignal(self, ticker, strength, value_dict, ending):
        if ending == True:
            self.lock = False
            self.text += "\n\n市场交易信号扫描完毕"
            self.c.uiSignal.emit(self.text)
            return

        self.stock_candidate[strength] = value_dict

        action = "多头" if value_dict.get('action') == 1 else "空头"
        line = "\n\n获得交易信号：\n" + "信号强度：%f\n股票代号:%s\n操作：%s\n限价单:%.1f\n止损价：%.1f\n止盈价:%.1f" % (strength,ticker,action,value_dict.get('entry_price'),value_dict.get('stop_loss'),value_dict.get('take_profit'))

        self.text += line
        self.c.uiSignal.emit(self.text + "\n扫描市场交易信号中...")
            

    def scanSignals(self):
        if self.lock:
            return
        self.lock = True
        self.le.setText(self.text + "\n扫描市场交易信号中...")
        self.signalScanner.scanAllTradeSignals(time.time(),tickerlist=self.tickerlist)
        #today = datetime.datetime.strptime("2020-05-25"+" UTC-0400", "%Y-%m-%d %Z%z")
        #self.signalScanner.scanAllTradeSignals(today.timestamp(),tickerlist=self.tickerlist)

    def getStrategy(self):
        """
        if self.lock:
            return
        if not self.stock_candidate:
            return
        """
        text, ok = QtGui.QInputDialog.getText(self.w , '对话框', '请输入现金数目和持有股票的价值，用空格隔开:')

        if not ok:
            return

        cash, assets = str(text).split(" ")
        cash = int(cash)
        assets = int(assets)


        stock_candidate = self.stock_candidate

        strengthlist = sorted(stock_candidate.keys(),reverse=True)
        if len(strengthlist) <= 0:
            self.text += "\n\n当前无可用交易信号"
            self.c.uiSignal.emit(self.text)
            return
            
        risk_current = assets * 0.02
        risk_maximum = (cash+assets)*0.1
        if risk_current >= risk_maximum:
            self.text += "\n\n当前交易的潜在亏损风险已到达上限，暂时不建议发起新交易"
            self.c.uiSignal.emit(self.text)
            return

        risk_per_trade = (cash+assets) * 0.01
        trade_num = math.floor((risk_maximum - risk_current) / risk_per_trade)

        if trade_num == 0:
            self.text += "\n\n当前交易的潜在亏损风险已到达上限，暂时不建议发起新交易"
            self.c.uiSignal.emit(self.text)
            return

        cash_used = 0
        orderlist = []

        for i in range(trade_num):
            if i >= len(strengthlist):
                break
            
            if cash - cash_used < 50:
                break
            
            stock_data = stock_candidate.get(strengthlist[i])
            risk_per_share = abs(stock_data.get('entry_price') - stock_data.get('stop_loss'))
            shares = risk_per_trade / risk_per_share
            cost = shares * stock_data.get('entry_price')

            cost_real = min(cost, cash - cash_used - 50)
            shares_real = cost_real / stock_data.get('entry_price')

            if cost_real < 50:
                continue

            cash_used += cost_real

            order = stock_data
            order['shares'] = shares_real

            orderlist.append(order)


        if len(orderlist) == 0:
            self.text += "\n\n当前现金不足，暂时不建议发起新交易"
            self.c.uiSignal.emit(self.text)
            return

        line = ""
        for i in range(len(orderlist)):
            value_dict = orderlist[i]
            action = "多头" if value_dict.get('action') == 1 else "空头"
            line = line + "\n交易序号：%d-股票代号：%s-操作：%s-限价单：%.1f-止损价：%.1f-止盈价：%.1f-份额：%.1f" % (i,value_dict.get('ticker'),action,value_dict.get('entry_price'),value_dict.get('stop_loss'),value_dict.get('take_profit'),value_dict.get('shares'))

        self.text += "\n\n最佳如下交易策略" + line
        self.c.uiSignal.emit(self.text) 
        pass

    def setText(self,text):
        self.le.setText(text)

    def main(self):
        
        app = QtGui.QApplication(sys.argv)

        self.c = Communicate()
        self.c.uiSignal.connect(self.setText)    

        w = QtGui.QWidget()
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        btn = QtGui.QPushButton('扫描市场信号', w)
        btn.clicked.connect(self.scanSignals)
        grid.addWidget(btn, 0,0)
        
        btn = QtGui.QPushButton('确定交易策略', w)
        btn.clicked.connect(self.getStrategy)
        grid.addWidget(btn, 0,1)

        self.le = QtGui.QTextEdit(w)
        grid.addWidget(self.le, 1,0, 5,5)


        w.setLayout(grid) 
        w.resize(600,400)
        w.setWindowTitle('Simple')
        w.show()

        self.w = w
        
        sys.exit(app.exec_())


if __name__ == '__main__':
    
    app = Application()

