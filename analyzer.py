import utils

# 从第二天的数据开始分析（即下标数组为1），默认第一天为交易设立的时候
def analyzeTradeResult(order_date, action, entry_price, stop_loss, take_profit, tailing_stop, date, openprice, closeprice, high, low):

    profit = 0
    closeout_date = ""

    if utils.dayBetweenDate(order_date, date[0]) > 1:
        # 由于下单后 第二天未开盘，导致订单过期失效
        return 0, ""

    if entry_price > high[0] or entry_price < low[0]:
        # 因为交易订单为限价单，如果价格没到订单指定的价格的话，交易不会被触发
        return 0, ""

    if action == 1:
        stop_loss_percentage = 1 - stop_loss/entry_price
        
        if closeprice[0] < stop_loss:
            profit = stop_loss - entry_price
            return profit, date[0]

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

        pass

    else:
        stop_loss_percentage = stop_loss/entry_price - 1

        if closeprice[0] > stop_loss:
            profit = entry_price - stop_loss
            return profit, date[0]

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

    return profit, closeout_date
