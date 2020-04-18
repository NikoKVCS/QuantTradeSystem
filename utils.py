import datetime

def dateGreaterThan(date1, date2):
    date_num1 = date1.split("-")
    date_num2 = date2.split("-")

    for i in range(3):
        if int(date_num1[i]) > int(date_num2[i]):
            return True
        elif int(date_num1[i]) < int(date_num2[i]):
            return False

    return False


def dateGreaterOrEqual(date1, date2):
    date_num1 = date1.split("-")
    date_num2 = date2.split("-")

    for i in range(3):
        if int(date_num1[i]) > int(date_num2[i]):
            return True
        elif int(date_num1[i]) < int(date_num2[i]):
            return False

    return True


def dayBetweenDate(date1, date2):
    d1 = datetime.datetime.strptime(date1, "%Y-%m-%d")
    d2 = datetime.datetime.strptime(date2, "%Y-%m-%d")
    return (d2-d1).days


