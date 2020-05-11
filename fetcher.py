import platform
import time
import datetime
import os
import re
import utils
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from log import logger

def fetchBatch(tickerList):
    OS = platform.system()
    chromeDriverPath = ""
    if OS == "Linux":
        chromeDriverPath = "chrome/linux/chromedriver"
    else:
        chromeDriverPath = ""

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    browser = webdriver.Chrome(chrome_options=chrome_options,executable_path=chromeDriverPath)

    queue_finish = []
    queue_finish_date = []

    month_dic = {
        "Apr":"04",
        "Mar":"03",
        "Feb":"02",
        "Jan":"01",
        "Dec":"12",
        "Nov":"11",
        "Oct":"10",
        "Sep":"09",
        "Aug":"08",
        "Jul":"07",
        "Jun":"06",
        "May":"05",
    }
    
    for ticker in tickerList:

        lowlist = np.zeros((0), dtype=np.float64)
        highlist = np.zeros((0), dtype=np.float64)
        openlist = np.zeros((0), dtype=np.float64)
        closelist = np.zeros((0), dtype=np.float64)
        volumelist = np.zeros((0), dtype=np.float64)
        datelist = []
        latest_date = "2018-01-01"

        ticker_data_path = "stocksdata/"+ticker+".npy"
        if os.path.exists(ticker_data_path):
            svalue = np.load(ticker_data_path,allow_pickle=True)[0]

            lowlist = svalue.get('low')
            highlist = svalue.get('high')
            openlist = svalue.get('open')
            closelist = svalue.get('close')
            volumelist = svalue.get('volume')
            datelist = svalue.get('date')

            latest_date = datelist[-1]
        
        #指定日期为美国东部时间，即为 UTC标准时间减去4小时 UTC - 0400
        timeArray = datetime.datetime.strptime(latest_date+" UTC-0400", "%Y-%m-%d %Z%z")
        period1 = int(timeArray.timestamp())
        period2 = int(time.time())

        url = "https://finance.yahoo.com/quote/"+ticker+"/history?interval=1d&filter=history&frequency=1d&period1=" + str(period1) + "&period2=" + str(period2)
        logger.info(url)
        browser.get(url)

        text = browser.page_source
        lst = re.findall(r'<tr class="BdT Bdc[\s\S]*?</tr>', text)
        if len(lst) <= 0:
            continue

        lst.reverse()
        for item in lst:
            if 'Dividend' in item:
                continue
            try:
                span = re.findall(r'<span data-reactid=[\s\S]*?>([\s\S]*?)</span>', item)
                if len(span) != 7:
                    continue
                date = span[0].replace(",", "").split(" ")
                month = month_dic.get(date[0])
                if month == None:
                    logger.error("fetchBatch: month can't convert to number." + ticker + " | date:" + span[0])
                    continue

                datestr = date[2] + "-" + month + "-" + date[1]
                if utils.dateGreaterThan(datestr, latest_date) == False:
                    continue
                latest_date = datestr

                openp = float(span[1].replace(",",""))
                high = float(span[2].replace(",",""))
                low = float(span[3].replace(",",""))
                closep = float(span[4].replace(",",""))
                avg = float(span[5].replace(",",""))
                volume = int(span[6].replace(",",""))

                openlist = np.append(openlist, openp)
                highlist = np.append(highlist, high)
                lowlist = np.append(lowlist, low)
                closelist = np.append(closelist, closep)
                volumelist = np.append(volumelist, volume)

                datelist.append(datestr)

            except Exception as e:
                logger.error(e)
                continue

        svalue = dict()
        svalue['open'] = openlist
        svalue['close'] = closelist
        svalue['low'] = lowlist
        svalue['high'] = highlist
        svalue['volume'] = volumelist
        svalue['date'] = datelist
        np.save(ticker_data_path, np.array([svalue]))

        queue_finish.append(ticker)
        queue_finish_date.append(datelist[-1])

        #print(browser.page_source)
        f = open("stocksraw/"+ticker+'.html',"w")
        f.write(browser.page_source)
        f.close()

    browser.quit()
    return queue_finish, queue_finish_date



if __name__ == "__main__":
    fetchBatch(["NKE", "IBKR"])