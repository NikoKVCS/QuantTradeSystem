import talib as ta
import numpy as np
from simforest import simforest_long, simforest_short
from talib import MA_Type

def simForestPredict(openprice, closeprice, low, high, volume):
    end = len(closeprice) - 1

    EMA5 = ta.EMA(closeprice, timeperiod=5)
    EMA14 = ta.EMA(closeprice, timeperiod=14)

    if (EMA5[end] - EMA14[end]) * (EMA5[end-1] - EMA14[end-1]) > 0:
        return 0,None
    

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
    x = dataset[len(dataset)-50:len(dataset)]
    if np.shape(x) != (50,6):
        return 0,None
    
    if EMA5[end]>EMA14[end] and EMA5[end-1]<EMA14[end-1]:
        y = simforest_long.predict(x)
        y = np.exp(y)/sum(np.exp(y))
        print("yooo")
        if np.argmax(y) != 1:
            return 0, None
        
        ATR = ta.ATR(high, low, closeprice, timeperiod=14)

        value_dict = dict()
        value_dict['action'] = 1
        value_dict["entry_price"] = high[end]
        value_dict["stop_loss"] = high[end] - ATR[end] * 1
        value_dict["take_profit"] = high[end] + ATR[end] * 2
        value_dict["tailing_stop"] = False
        return y[1], value_dict

    if EMA5[end]>EMA14[end] and EMA5[end-1]<EMA14[end-1]:
        y = simforest_short.predict(x)
        y = np.exp(y)/sum(np.exp(y))
        print("yooo")
        if np.argmax(y) != 1:
            return 0, None
        
        ATR = ta.ATR(high, low, closeprice, timeperiod=14)

        value_dict = dict()
        value_dict['action'] = 2
        value_dict["entry_price"] = high[end]
        value_dict["stop_loss"] = low[end] + ATR[end] * 1
        value_dict["take_profit"] = low[end] - ATR[end] * 2
        value_dict["tailing_stop"] = False
        return y[1], value_dict

    return 0,None


def MACrossover(openprice, closeprice, low, high, volume):
    length = len(openprice)

    if length <= 0:
        return 0, None

    end = len(closeprice) - 1
    MA5 = ta.MA(closeprice, timeperiod=5) # closeprice
    MA20 = ta.MA(closeprice, timeperiod=20) # closeprice

    ATR = ta.ATR(high, low, closeprice, timeperiod=14)
    ADXR = ta.ADXR(high, low, closeprice, timeperiod=14)
    CSI = ATR*ADXR

    sar_type = 0

    value_dict = dict()

    if MA5[end] > MA20[end] and MA5[end-1] < MA20[end-1]:
        sar_type = 1

        value_dict["entry_price"] = high[end]
        value_dict["stop_loss"] = high[end] * (1-0.01)
        value_dict["take_profit"] = high[end] * (1+0.03)
        value_dict["tailing_stop"] = True

    if MA5[end] < MA20[end] and MA5[end-1] > MA20[end-1]:
        sar_type = 2

        value_dict["entry_price"] = low[end]
        value_dict["stop_loss"] = low[end] * (1+0.01)
        value_dict["take_profit"] = low[end] * (1-0.03)
        value_dict["tailing_stop"] = True
    
    if sar_type == 0:
        return 0, None

    value_dict['action'] = sar_type
    strength = CSI[end]

    return strength, value_dict

def movingAverageCrossover(openprice, closeprice, low, high, volume):
    length = len(openprice)

    if length <= 0:
        return 0, None

    end = len(closeprice) - 1
    MA5 = ta.EMA(closeprice, timeperiod=14) # closeprice
    MA20 = ta.MA(closeprice, timeperiod=30) # closeprice

    ATR = ta.ATR(high, low, closeprice, timeperiod=14)
    ADXR = ta.ADXR(high, low, closeprice, timeperiod=14)
    CSI = ATR*ADXR

    sar_type = 0

    value_dict = dict()

    if MA5[end] > MA20[end] and MA5[end-1] < MA20[end-1]:
        sar_type = 1

        value_dict["entry_price"] = high[end]
        value_dict["stop_loss"] = high[end] - ATR[end] * 2
        value_dict["take_profit"] = high[end] + ATR[end] * 4
        value_dict["tailing_stop"] = False

    if MA5[end] < MA20[end] and MA5[end-1] > MA20[end-1]:
        sar_type = 2

        value_dict["entry_price"] = low[end]
        value_dict["stop_loss"] = low[end] + ATR[end] * 2
        value_dict["take_profit"] = low[end] - ATR[end] * 4
        value_dict["tailing_stop"] = False
    
    if sar_type == 0:
        return 0, None

    value_dict['action'] = sar_type
    strength = CSI[end]

    return strength, value_dict
    
    
def bounceSwingSystem(openprice, closeprice, low, high, volume):
    pass


def bounce18days(openprice, closeprice, low, high, volume):
    EMA18 = ta.EMA(closeprice, timeperiod=18)
    EMA50 = ta.EMA(closeprice, timeperiod=50)
    EMA100 = ta.EMA(closeprice, timeperiod=100)
    EMA130 = ta.EMA(closeprice, timeperiod=130)

    ATR = ta.ATR(high, low, closeprice, timeperiod=14)

    latest = len(openprice) - 1

    # long trade :
    if EMA18[latest] > EMA50[latest] and EMA50[latest] > EMA100[latest] and EMA100[latest] > EMA130[latest]:
        if low[latest-2] > EMA18[latest-2] and low[latest-1] < EMA18[latest-1]:
            if openprice[latest-1] > EMA18[latest-1] and closeprice[latest-1] > EMA18[latest-1]:
                if closeprice[latest] > high[latest-1] and closeprice[latest] > openprice[latest-1]:
                    macd_18, signal_18, _ = ta.MACD(closeprice, fastperiod=18, slowperiod=50, signalperiod=9)
                    macd_50, signal_50, _ = ta.MACD(closeprice, fastperiod=50, slowperiod=100, signalperiod=9)
                    if macd_18[latest] > signal_18[latest] and macd_50[latest] > signal_50[latest] and signal_18[latest] > 0 and signal_50[latest] > 0:
                        k, d = ta.STOCHF(high, low, closeprice, fastk_period=5, fastd_period=3, fastd_matype=MA_Type.EMA)
                        if (k[latest] <= 30 and d[latest] <= 30) or (k[latest-1] <= 30 and d[latest-1] <= 30) or (k[latest-2] <= 30 and d[latest-2] <= 30):

                            value_dict = dict()              
                            value_dict["entry_price"] = high[latest]
                            value_dict["stop_loss"] = high[latest] - ATR[latest] * 1
                            value_dict["take_profit"] = high[latest] + ATR[latest] * 2
                            value_dict["tailing_stop"] = False
                            value_dict['action'] = 1

                            return np.random.rand(1)[0], value_dict
    # short trade：
    if EMA18[latest] < EMA50[latest] and EMA50[latest] < EMA100[latest] and EMA100[latest] < EMA130[latest]:
        if high[latest-2] < EMA18[latest-2] and high[latest-1] > EMA18[latest-1]:
            if openprice[latest-1] < EMA18[latest-1] and closeprice[latest-1] < EMA18[latest-1]:
                if closeprice[latest] < low[latest-1] and closeprice[latest] < openprice[latest-1]:
                    macd_18, signal_18, _ = ta.MACD(closeprice, fastperiod=18, slowperiod=50, signalperiod=9)
                    macd_50, signal_50, _ = ta.MACD(closeprice, fastperiod=50, slowperiod=100, signalperiod=9)
                    if macd_18[latest] < signal_18[latest] and macd_50[latest] < signal_50[latest] and signal_18[latest] < 0 and signal_50[latest] < 0:
                        k, d = ta.STOCHF(high, low, closeprice, fastk_period=5, fastd_period=3, fastd_matype=MA_Type.EMA)
                        if (k[latest] >= 70 and d[latest] >= 70) or (k[latest-1] >= 70 and d[latest-1] >= 70) or (k[latest-2] >= 70 and d[latest-2] >= 70):

                            value_dict = dict()              
                            value_dict["entry_price"] = low[latest]
                            value_dict["stop_loss"] = low[latest] + ATR[latest] * 1
                            value_dict["take_profit"] = low[latest] - ATR[latest] * 2
                            value_dict["tailing_stop"] = False
                            value_dict['action'] = 2

                            return np.random.rand(1)[0], value_dict

    return 0, None

def candlePattern(candle):
    return 0

def isSwingHighOrSwingLow(type, high, low, index):
    latest = len(low) - 1
    if index >= latest:
        return False
    
    if type == 1:
        # Swing high
        if high[index] > high[index-1] and high[index] > high[index-2] and high[index] > high[index+1]:
            if index == latest - 1:
                return True
            elif high[index] > high[index+2]:
                return True
    elif type == 2:
        # Swing low
        if low[index] < low[index-1] and low[index] < low[index-2] and low[index] < low[index+1]:
            if index == latest - 1:
                return True
            elif high[index] < high[index+2]:
                return True

    return False

# line只包含y值
def isLineIntersect(line1, line2):
    if len(line1) != len(line2):
        return True

    for i in range(len(line1) - 1):
        diffA = line1[i] - line2[i]
        diffB = line1[i+1] - line2[i+1]
        if diffA * diffB <= 0:
            return True
    return False

def createLine(x1,y1, x2,y2):

    a = (y2-y1)/(x2-x1)
    b = (x2*y1-x1*y2)/(x2-x1)

    line = []
    for i in range(x1+1, x2, 1):
        line.append(a*i+b)

    return line

    
def MacdDivergence(openprice, closeprice, low, high, volume):
    EMA18 = ta.EMA(closeprice, timeperiod=18)
    EMA50 = ta.EMA(closeprice, timeperiod=50)
    EMA100 = ta.EMA(closeprice, timeperiod=100)

    ATR = ta.ATR(high, low, closeprice, timeperiod=14)

    latest = len(openprice) - 1

    # up trend :
    if EMA18[latest] > EMA50[latest] and EMA50[latest] > EMA100[latest] and isSwingHighOrSwingLow(1, high, low, latest-1):
        macd, _, _ = ta.MACD(closeprice, fastperiod=12, slowperiod=26, signalperiod=9)
        for i in range(latest-2, latest-100, -1):
            if isSwingHighOrSwingLow(1, high, low, i):
                # divergence condition
                if (high[i] >= high[latest-1]) or (macd[i] <= macd[latest-1]):
                    continue

                # no intersection allowed
                line = createLine(i, high[i], latest-1, high[latest-1])
                macd_line = createLine(i, macd[i], latest-1, macd[latest-1])
                
                intersect1 = isLineIntersect(line, high[i+1:latest-1])
                intersect2 = isLineIntersect(line, low[i+1:latest-1])
                intersect3 = isLineIntersect(macd_line, macd[i+1:latest-1])

                if intersect1 == False and intersect2 == False and intersect3 == False:
                    value_dict = dict()              
                    value_dict["entry_price"] = high[latest]
                    value_dict["stop_loss"] = high[latest] - ATR[latest] * 1
                    value_dict["take_profit"] = high[latest] + ATR[latest] * 2
                    value_dict["tailing_stop"] = True
                    value_dict['action'] = 1

                    return np.random.rand(1)[0], value_dict
        pass

    # down trend : 
    if EMA18[latest] < EMA50[latest] and EMA50[latest] < EMA100[latest] and isSwingHighOrSwingLow(2, high, low, latest-1):
        macd, _, _ = ta.MACD(closeprice, fastperiod=12, slowperiod=26, signalperiod=9)
        for i in range(latest-2, latest-100, -1):
            if isSwingHighOrSwingLow(2, high, low, i):
                # divergence condition
                if (low[i] <= low[latest-1]) or (macd[i] >= macd[latest-1]):
                    continue

                # no intersection allowed
                line = createLine(i, low[i], latest-1, low[latest-1])
                macd_line = createLine(i, macd[i], latest-1, macd[latest-1])
                
                intersect1 = isLineIntersect(line, high[i+1:latest-1])
                intersect2 = isLineIntersect(line, low[i+1:latest-1])
                intersect3 = isLineIntersect(macd_line, macd[i+1:latest-1])

                if intersect1 == False and intersect2 == False and intersect3 == False:
                    value_dict = dict()              
                    value_dict["entry_price"] = low[latest]
                    value_dict["stop_loss"] = low[latest] + ATR[latest] * 1
                    value_dict["take_profit"] = low[latest] - ATR[latest] * 2
                    value_dict["tailing_stop"] = True
                    value_dict['action'] = 2

                    return np.random.rand(1)[0], value_dict
        pass


    return 0, None

if __name__ == "__main__":
    print(MA_Type.EMA)
    pass