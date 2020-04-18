import logging
import os
import time

def SetupLogger():
    if not os.path.exists("log"):
        os.makedirs("log")

    recfmt = '(%(threadName)s) %(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s'
    timefmt = '%y%m%d_%H:%M:%S'

    logging.basicConfig(filename=time.strftime("log/quant_trade_system.log"),
                        filemode="a",
                        level=logging.INFO,
                        format=recfmt, datefmt=timefmt)
    logger = logging.getLogger()
    return logger

logger = SetupLogger()
