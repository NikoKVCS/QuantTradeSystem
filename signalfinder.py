import talib as ta


def movingAverageCrossover(openprice, closeprice, low, high, volume):
    length = len(openprice)

    if length <= 0:
        return 0, None

    end = len(closeprice) - 1
    MA5 = ta.EMA(closeprice, timeperiod=14, ) # closeprice
    MA20 = ta.MA(closeprice, timeperiod=30) # closeprice

    ATR = ta.ATR(high, low, closeprice, timeperiod=14)
    ADXR = ta.ADXR(high, low, closeprice, timeperiod=14)
    CSI = ATR*ADXR

    sar_type = 0

    value_dict = dict()

    if MA5[end] > MA20[end] and MA5[end-1] < MA20[end-1]:
        sar_type = 1

        value_dict["entry_price"] = high[end]
        value_dict["stop_loss"] = high[end] - ATR[end] 
        value_dict["take_profit"] = high[end] + ATR[end] * 2
        value_dict["tailing_stop"] = False

    if MA5[end] < MA20[end] and MA5[end-1] > MA20[end-1]:
        sar_type = 2

        value_dict["entry_price"] = low[end]
        value_dict["stop_loss"] = low[end] + ATR[end]
        value_dict["take_profit"] = low[end] - ATR[end] * 2
        value_dict["tailing_stop"] = False
    
    if sar_type == 0:
        return 0, None

    value_dict['action'] = sar_type
    strength = CSI[end]

    return strength, value_dict
    
    
def bounceSwingSystem(openprice, closeprice, low, high, volume):
    pass