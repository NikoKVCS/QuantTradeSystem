import re
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import platform

OS = platform.system()
chromeDriverPath = ""
if OS == "Linux":
    chromeDriverPath = "chrome/linux/chromedriver"
else:
    chromeDriverPath = "chrome/win/chromedriver.exe"

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options,executable_path=chromeDriverPath)
browser.get('https://www.nasdaq.com/market-activity/quotes/nasdaq-ndx-index')
text = browser.page_source
browser.quit()

lst = re.findall(r'firstCell([\s\S]*?)/a>', text)
tickerList = ""
for item in lst:
    td = re.findall(r'>([\s\S]*?)<', item)
    if len(td) < 1:
        continue
    if tickerList == "":
        tickerList = td[0]
    else:
        tickerList = tickerList + "," + td[0]

f = open('nasdaq100TickerList.txt','w')
f.write(tickerList)
f.close()

