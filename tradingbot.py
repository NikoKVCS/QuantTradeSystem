import collections
import inspect
import logging

from ibapi import wrapper
from ibapi import utils
from ibapi.client import EClient
from ibapi.utils import iswrapper

from ibapi.common import * # @UnusedWildImport
from ibapi.contract import * # @UnusedWildImport
from ibapi.order import * # @UnusedWildImport
from ibapi.order_state import * # @UnusedWildImport

# ! [socket_declare]
class IBClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)
        # ! [socket_declare]
        # 测试用的代码，test coverage
        # how many times a method is called to see test coverage
        self.clntMeth2callCount = collections.defaultdict(int)
        self.clntMeth2reqIdIdx = collections.defaultdict(lambda: -1)
        self.reqId2nReq = collections.defaultdict(int)
        self.setupDetectReqId()

    def countReqId(self, methName, fn):
        def countReqId_(*args, **kwargs):
            self.clntMeth2callCount[methName] += 1
            idx = self.clntMeth2reqIdIdx[methName]
            if idx >= 0:
                sign = -1 if 'cancel' in methName else 1
                self.reqId2nReq[sign * args[idx]] += 1
            return fn(*args, **kwargs)

        return countReqId_

    def setupDetectReqId(self):

        methods = inspect.getmembers(EClient, inspect.isfunction)
        for (methName, meth) in methods:
            if methName != "send_msg":
                # don't screw up the nice automated logging in the send_msg()
                self.clntMeth2callCount[methName] = 0
                # logging.debug("meth %s", name)
                sig = inspect.signature(meth)
                for (idx, pnameNparam) in enumerate(sig.parameters.items()):
                    (paramName, param) = pnameNparam # @UnusedVariable
                    if paramName == "reqId":
                        self.clntMeth2reqIdIdx[methName] = idx

                setattr(IBClient, methName, self.countReqId(methName, meth))

                # print("TestClient.clntMeth2reqIdIdx", self.clntMeth2reqIdIdx)


# ! [ewrapperimpl]
class IBWrapper(wrapper.EWrapper):
    # ! [ewrapperimpl]
    def __init__(self):
        wrapper.EWrapper.__init__(self)

        self.wrapMeth2callCount = collections.defaultdict(int)
        self.wrapMeth2reqIdIdx = collections.defaultdict(lambda: -1)
        self.reqId2nAns = collections.defaultdict(int)
        self.setupDetectWrapperReqId()

    # TODO: see how to factor this out !!

    def countWrapReqId(self, methName, fn):
        def countWrapReqId_(*args, **kwargs):
            self.wrapMeth2callCount[methName] += 1
            idx = self.wrapMeth2reqIdIdx[methName]
            if idx >= 0:
                self.reqId2nAns[args[idx]] += 1
            return fn(*args, **kwargs)

        return countWrapReqId_

    def setupDetectWrapperReqId(self):

        methods = inspect.getmembers(wrapper.EWrapper, inspect.isfunction)
        for (methName, meth) in methods:
            self.wrapMeth2callCount[methName] = 0
            # logging.debug("meth %s", name)
            sig = inspect.signature(meth)
            for (idx, pnameNparam) in enumerate(sig.parameters.items()):
                (paramName, param) = pnameNparam # @UnusedVariable
                # we want to count the errors as 'error' not 'answer'
                if 'error' not in methName and paramName == "reqId":
                    self.wrapMeth2reqIdIdx[methName] = idx

            setattr(IBWrapper, methName, self.countWrapReqId(methName, meth))

            # print("TestClient.wrapMeth2reqIdIdx", self.wrapMeth2reqIdIdx)

# ! [socket_init]
class IBApp(IBWrapper, IBClient):
    def __init__(self):
        IBWrapper.__init__(self)
        IBClient.__init__(self, wrapper=self)
        # ! [socket_init]
        self.nKeybInt = 0
        self.started = False
        self.nextValidOrderId = None
        self.permId2ord = {}
        self.reqId2nErr = collections.defaultdict(int)
        self.globalCancelOnly = False
        self.simplePlaceOid = None

    # 导出测试情况
    def dumpTestCoverageSituation(self):
        for clntMeth in sorted(self.clntMeth2callCount.keys()):
            logging.debug("ClntMeth: %-30s %6d" % (clntMeth,
                                                   self.clntMeth2callCount[clntMeth]))

        for wrapMeth in sorted(self.wrapMeth2callCount.keys()):
            logging.debug("WrapMeth: %-30s %6d" % (wrapMeth,
                                                   self.wrapMeth2callCount[wrapMeth]))

    # 导出测试情况
    def dumpReqAnsErrSituation(self):
        logging.debug("%s\t%s\t%s\t%s" % ("ReqId", "#Req", "#Ans", "#Err"))
        for reqId in sorted(self.reqId2nReq.keys()):
            nReq = self.reqId2nReq.get(reqId, 0)
            nAns = self.reqId2nAns.get(reqId, 0)
            nErr = self.reqId2nErr.get(reqId, 0)
            logging.debug("%d\t%d\t%s\t%d" % (reqId, nReq, nAns, nErr))

    @iswrapper
    def connectAck(self):
        if self.asynchronous:
            self.startApi()


    @iswrapper
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)

        #logging.debug("setting nextValidOrderId: %d", orderId)
        self.nextValidOrderId = orderId
        print("NextValidId:", orderId)
        self.start()


    @iswrapper
    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        super().error(reqId, errorCode, errorString)
        print("Error. Id:", reqId, "Code:", errorCode, "Msg:", errorString)
    

    @iswrapper
    def openOrder(self, orderId: OrderId, contract: Contract, order: Order,
                  orderState: OrderState):
        super().openOrder(orderId, contract, order, orderState)
        print("OpenOrder. PermId: ", order.permId, "ClientId:", order.clientId, " OrderId:", orderId, 
              "Account:", order.account, "Symbol:", contract.symbol, "SecType:", contract.secType,
              "Exchange:", contract.exchange, "Action:", order.action, "OrderType:", order.orderType,
              "TotalQty:", order.totalQuantity, "CashQty:", order.cashQty, 
              "LmtPrice:", order.lmtPrice, "AuxPrice:", order.auxPrice, "Status:", orderState.status)

        order.contract = contract
        self.permId2ord[order.permId] = order


    @iswrapper
    def openOrderEnd(self):
        super().openOrderEnd()
        print("OpenOrderEnd")

        logging.debug("Received %d openOrders", len(self.permId2ord))

    @iswrapper
    def orderStatus(self, orderId: OrderId, status: str, filled: float,
                    remaining: float, avgFillPrice: float, permId: int,
                    parentId: int, lastFillPrice: float, clientId: int,
                    whyHeld: str, mktCapPrice: float):
        super().orderStatus(orderId, status, filled, remaining,
                            avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice)
        print("OrderStatus. Id:", orderId, "Status:", status, "Filled:", filled,
              "Remaining:", remaining, "AvgFillPrice:", avgFillPrice,
              "PermId:", permId, "ParentId:", parentId, "LastFillPrice:",
              lastFillPrice, "ClientId:", clientId, "WhyHeld:",
              whyHeld, "MktCapPrice:", mktCapPrice)


    def start(self):
        if self.started:
            return

        self.started = True

        if self.globalCancelOnly:
            self.reqGlobalCancel()
        else:
            self.makeOrderOperations()

    def bracketOrder(self, parentOrderId:int, action:str, quantity:float, limitPrice:float, ATR:float):
        bracketOrder = []
        if action == "BUY":

            parent = Order()
            parent.orderId = parentOrderId
            parent.action = "BUY"
            parent.orderType = "STP LMT"
            parent.totalQuantity = quantity
            parent.lmtPrice = limitPrice + 0.1*ATR
            parent.auxPrice = limitPrice
            parent.transmit = False
            
            takeProfit = Order()
            takeProfit.orderId = self.nextOrderId()
            takeProfit.action = "SELL"
            takeProfit.orderType = "LMT"
            takeProfit.totalQuantity = quantity
            takeProfit.lmtPrice = limitPrice + ATR*2
            takeProfit.parentId = parentOrderId
            takeProfit.transmit = False
            
            stopLoss = Order()
            stopLoss.orderId = self.nextOrderId()
            stopLoss.action = "SELL"
            stopLoss.orderType = "STP"
            stopLoss.auxPrice = limitPrice - ATR
            stopLoss.totalQuantity = quantity
            stopLoss.parentId = parentOrderId
            stopLoss.transmit = True
            bracketOrder = [parent, takeProfit, stopLoss]
        else:
            
            parent = Order()
            parent.orderId = parentOrderId
            parent.action = "SELL"
            parent.orderType = "STP LMT"
            parent.totalQuantity = quantity
            parent.lmtPrice = limitPrice - 0.1*ATR
            parent.auxPrice = limitPrice
            parent.transmit = False
            
            takeProfit = Order()
            takeProfit.orderId = self.nextOrderId()
            takeProfit.action = "BUY"
            takeProfit.orderType = "LMT"
            takeProfit.totalQuantity = quantity
            takeProfit.lmtPrice = limitPrice - ATR*2
            takeProfit.parentId = parentOrderId
            takeProfit.transmit = False
            
            stopLoss = Order()
            stopLoss.orderId = self.nextOrderId()
            stopLoss.action = "BUY"
            stopLoss.orderType = "STP"
            stopLoss.auxPrice = limitPrice + ATR
            stopLoss.totalQuantity = quantity
            stopLoss.parentId = parentOrderId
            stopLoss.transmit = True
            
            bracketOrder = [parent, takeProfit, stopLoss]
        return bracketOrder

    def makeOrderOperations(self):
        # 为什么要调用这句
        self.reqIds(-1)

        contract = Contract()
        contract.symbol = "IBKR"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "ISLAND"

        bracket = self.bracketOrder(self.nextOrderId(), "BUY", 100, 30, 40, 20)
        for o in bracket:
            self.placeOrder(o.orderId, contract, o)
    
        pass

    def nextOrderId(self):
        oid = self.nextValidOrderId
        self.nextValidOrderId += 1
        return oid
    

def main():

    try:
        app = IBApp()
        app.connect("127.0.0.1", 4002, clientId=0)
        # 连接信息
        print("serverVersion:%s connectionTime:%s" % (app.serverVersion(), app.twsConnectionTime()))

        app.run()
        
    except:
        raise
    finally:
        #app.dumpTestCoverageSituation()
        #app.dumpReqAnsErrSituation()
        pass


if __name__ == "__main__":
    main()
