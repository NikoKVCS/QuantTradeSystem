from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
import numpy as np
from proximityforest import proxforest_short, proxforest_long

def compare_short():

    dataset = np.load('dataset_short_mini.npy', allow_pickle=True)[0]
    traindata = dataset.get('traindata')
    testdata = dataset.get('testdata')

    proxforest_short.test(testdata.get('data_input'), testdata.get('data_output'))
    #proxforest_long.test(testdata.get('data_input'), testdata.get('data_output'))


    X = traindata.get('data_input')
    t = []
    for i in range(len(X)):
        t.append(np.hstack(X[i]))

    traindata['data_input'] = np.array(t)

    Y = traindata.get('data_output')[:,1] == 1
    traindata['data_output'] = Y



    X = testdata.get('data_input')
    t = []
    for i in range(len(X)):
        t.append(np.hstack(X[i]))

    testdata['data_input'] = np.array(t)

    Y = testdata.get('data_output')[:,1] == 1
    testdata['data_output'] = Y


    ### SVC
    clf = SVC(C=1.0, kernel='rbf', gamma='auto', shrinking=True, probability=False)
    clf.fit(traindata.get('data_input'), traindata.get('data_output'))
    Y_P = clf.predict(testdata.get('data_input'))

    print("SVM")
    labels  = np.array(testdata.get('data_output')).astype(int)
    predictions  = np.array(Y_P).astype(int)
    wins = np.where((labels-predictions)==0)[0]
    print("accuracy:", len(wins)/len(labels))

    trades = 0
    win_trades = 0

    for i in range(len(labels)):
        if predictions[i]==1:
            trades+=1
            if labels[i]==1:
                win_trades += 1
    if trades > 0:
        print(win_trades,trades, win_trades/trades)

    ### RF

    clf = RandomForestClassifier(n_estimators=1,criterion='gini',bootstrap=True,max_features='auto')

    clf.fit(traindata.get('data_input'), traindata.get('data_output'))
    Y_P = clf.predict(testdata.get('data_input'))

    print("RF")
    labels  = np.array(testdata.get('data_output')).astype(int)
    predictions  = np.array(Y_P).astype(int)
    wins = np.where((labels-predictions)==0)[0]
    print("accuracy:", len(wins)/len(labels))

    trades = 0
    win_trades = 0

    for i in range(len(labels)):
        if predictions[i]==1:
            trades+=1
            if labels[i]==1:
                win_trades += 1
    if trades > 0:
        print(win_trades,trades, win_trades/trades)

def compare_long():

    dataset = np.load('dataset_long_mini.npy', allow_pickle=True)[0]
    traindata = dataset.get('traindata')
    testdata = dataset.get('testdata')

    proxforest_long.test(testdata.get('data_input'), testdata.get('data_output'))


    X = traindata.get('data_input')
    t = []
    for i in range(len(X)):
        t.append(np.hstack(X[i]))

    traindata['data_input'] = np.array(t)

    Y = traindata.get('data_output')[:,1] == 1
    traindata['data_output'] = Y



    X = testdata.get('data_input')
    t = []
    for i in range(len(X)):
        t.append(np.hstack(X[i]))

    testdata['data_input'] = np.array(t)

    Y = testdata.get('data_output')[:,1] == 1
    testdata['data_output'] = Y


    ### SVC
    clf = SVC(C=1.0, kernel='rbf', gamma='auto', shrinking=True, probability=False)
    clf.fit(traindata.get('data_input'), traindata.get('data_output'))
    Y_P = clf.predict(testdata.get('data_input'))

    print("SVM")
    labels  = np.array(testdata.get('data_output')).astype(int)
    predictions  = np.array(Y_P).astype(int)
    wins = np.where((labels-predictions)==0)[0]
    print("accuracy:", len(wins)/len(labels))

    trades = 0
    win_trades = 0

    for i in range(len(labels)):
        if predictions[i]==1:
            trades+=1
            if labels[i]==1:
                win_trades += 1
    if trades > 0:
        print(win_trades,trades, win_trades/trades)

    ### RF

    clf = RandomForestClassifier(n_estimators=1,criterion='gini',bootstrap=True,max_features='auto')

    clf.fit(traindata.get('data_input'), traindata.get('data_output'))
    Y_P = clf.predict(testdata.get('data_input'))

    print("RF")
    labels  = np.array(testdata.get('data_output')).astype(int)
    predictions  = np.array(Y_P).astype(int)
    wins = np.where((labels-predictions)==0)[0]
    print("accuracy:", len(wins)/len(labels))

    trades = 0
    win_trades = 0

    for i in range(len(labels)):
        if predictions[i]==1:
            trades+=1
            if labels[i]==1:
                win_trades += 1
    if trades > 0:
        print(win_trades,trades, win_trades/trades)

if __name__ == "__main__":
    compare_long()