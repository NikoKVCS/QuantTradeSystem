import platform
import time
import numpy as np
from datetime import datetime, timedelta, timezone
import os
 


def _sample_pair(Y,_rand):
    n_class = np.size(Y,1)
    n_samples = np.size(Y,0)
    _rand.seed(n_samples)
    classes = _rand.permutation(n_class)
    

    class1 = classes[0]
    class2 = classes[1]
    p_candidate = np.where(Y[:,class1] == 1)[0]
    q_candidate = np.where(Y[:,class2] == 1)[0]

    p = _rand.choice(p_candidate)
    q = _rand.choice(q_candidate)

    return p,q
    
rand = np.random.RandomState(None)
index = rand.choice(6,size=6,replace=False)
index2 = rand.choice(6,size=6,replace=False)

nclass = 3
[class1, class2] = rand.choice(nclass,size=2,replace=False)

labels = np.array([[1,0,0],[0,1,0],[0,0,1],[1,0,0],[0,0,1],[0,1,0],[1,0,0],[1,0,0],[0,0,1],[0,1,0]])

Q1 = labels[:,class1]



Y = np.array([[0,1,2],[2,1,3],[8,9,7]])
print(Y[:,1])
Q = np.where(Y[:,1]==9)[0]
print(Q)

a =np.sum([[0,1,2],[2,1,3]],axis=0) / np.sum([[0,1,2],[2,1,3]])
print(a)

print(np.size([[0,1,2],[2,1,3]],1))

print(os.path.join("model", "file.txt")) 

selection = np.array(list(set(np.random.choice(120, size=120))))
print(selection)
print(len(selection))

def line_intersection(line1, line2):
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       return None

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y

A = (1,1)
B = (2,1)
C = (1,3)
D = (2,2)
print (line_intersection((A, B), (C, D)))

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

a = [1,2,3]
a = a[:-1]
print(a)