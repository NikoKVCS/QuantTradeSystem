import numpy as np 

import matplotlib.pyplot as plt

wins = np.load('Simulation_table_rec_win.npy', allow_pickle=True)
lose = np.load('Simulation_table_rec_lose.npy', allow_pickle=True)


print(np.mean(wins))
print(np.mean(lose))

print("ok")


"""
cash = np.load('Simulation_table_cash.npy', allow_pickle=True)

fig = plt.figure()
#plt.title(r'Assets')
sample = cash
x = np.linspace(1, len(sample), len(sample))
plt.plot(x, sample, label='Assets')
#plt.text(0, sample[0], "short",fontdict={'size':'8','color':'b'})
#plt.text(t+1, sample[t+1], "{:.4f}".format(profit/start_price),fontdict={'size':'8','color':'b'})
plt.xlabel('Trades')
plt.ylabel('Value')

plt.legend()
plt.show()
"""

asset = np.load('Simulation_table_asset.npy', allow_pickle=True)
print(asset[-1])

fig = plt.figure()
#plt.title(r'Assets')
sample = asset
x = np.linspace(1, len(sample), len(sample))
plt.plot(x, sample, label='Assets')
#plt.text(0, sample[0], "short",fontdict={'size':'8','color':'b'})
#plt.text(t+1, sample[t+1], "{:.4f}".format(profit/start_price),fontdict={'size':'8','color':'b'})
plt.xlabel('Trades')
plt.ylabel('Value')

plt.legend()
plt.show()



