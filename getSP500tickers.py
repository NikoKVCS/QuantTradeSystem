import re
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

chromeDriverPath = "chrome/linux/chromedriver"
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options,executable_path=chromeDriverPath)
browser.get('https://www.slickcharts.com/sp500')
text = browser.page_source


lst = re.findall(r'<tr>([\s\S]*?)</tr>', text)
tickerList = ""
for item in lst:
    td = re.findall(r'<a href="/symbol/([\s\S]*?)">', item)
    if len(td) < 2:
        continue
    if tickerList == "":
        tickerList = td[0]
    else:
        tickerList = tickerList + "," + td[0]

f = open('s&p500TickerList.txt','w')
f.write(tickerList)
f.close()

