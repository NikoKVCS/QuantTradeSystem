import platform
import time
import numpy as np
from datetime import datetime, timedelta, timezone

print(platform.system())

metaPath = "stocksdata/meta.npy"
meta = dict()
meta = np.load(metaPath, allow_pickle=True)[0]

#f = open('tickerlist.txt',"w")
#f.write(','.join(meta.keys()) )
#f.close()
#print(meta)

print("abc","asd","123")

import datetime
timeArray = datetime.datetime.strptime("2020-04-16 07:00:10 UTC-0400", "%Y-%m-%d %H:%M:%S %Z%z")
period1 = int(timeArray.timestamp())
#print(period1)
#print(int(time.time()))
#print("good")


# 参数根据要转换的时区来确定，时区是UTC+2 时hours=2， UTC-3时hours=-3
ts = int(time.time())
td = timedelta(hours=-4) # UTC-0400 即美国东部时间
tz = timezone(td)
dt = datetime.datetime.fromtimestamp(ts, tz)
oneday = datetime.timedelta(days=1)
print((dt-oneday).strftime('%Y-%m-%d %H:%M:%S'))

abc = [1,2,3]
k = abc
abc = []
print(k)
print(abc)