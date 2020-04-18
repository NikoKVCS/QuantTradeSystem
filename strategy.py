import account

def orderGenerator(stock_candidate, account:account.Account):
    if account.getCash() < 50:
        return []

    if account.getTrades() >= 10:
        return []

    strengthlist = sorted(stock_candidate.keys(),reverse=True)
    if len(strengthlist) <= 0:
        return []
    
    risk_per_trade = account.getAsset() * 0.01
    trade_num = 10 - account.getTrades()
    cash = account.getCash()
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

    return orderlist


    

    