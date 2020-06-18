import numpy as np
import matplotlib.pyplot as plt
import dataset
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import platform
import os

OS = platform.system()
chromeDriverPath = ""
if OS == "Linux":
    chromeDriverPath = "chrome/linux/chromedriver"
else:
    chromeDriverPath = "chrome/win/chromedriver.exe"

chrome_options = webdriver.ChromeOptions()
prefs = {'profile.default_content_settings.popups': 0, 'download.default_directory': os.path.join(os.getcwd(), "stocksexcel")}
chrome_options.add_experimental_option('prefs', prefs)
chrome_options.add_argument('--headless')
browser = webdriver.Chrome(chrome_options=chrome_options,executable_path=chromeDriverPath)


ticker = "SPY"
datelist, openlist, closeprice, highlist, lowlist, volume = dataset.getRawData(ticker,browser)
browser.quit()

x = np.linspace(1, len(closeprice), len(closeprice))

fig = plt.figure()
plt.title('S&P500')

ax1 = fig.add_subplot(111)
ax1.plot(x, closeprice, label='Close')
ax1.set_ylabel('Close')

ax2 = ax1.twinx()  # this is the important function
ax2.plot(x, volume, 'r',label='Volume')
ax2.set_ylabel('Volume' )
ax2.set_xlabel('Days')

plt.legend()
plt.show()