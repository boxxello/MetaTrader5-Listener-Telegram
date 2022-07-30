import datetime
import logging
import os
import random
import re
from os.path import isfile, join
import dateutil.relativedelta

def check_pattern(text: str):
    PATTERN = """
        ([A-Z]+[\/|I][A-Z]+)
        (buy|sell):((?:\d+\.)*\d+)
        Tp:((?:\d+-?)*)
        SL:(\d+)
        Tp1:((?:\d+\.)*\d+)
        Tp2:((?:\d+\.)*\d+)
        Tp3:((?:\d+\.)*\d+)
        SL:((?:\d+\.)*\d+)
    """
    PATTERN2 = """
            ([A-Z]+[\/|I][A-Z]+)
            (buy|sell):((?:\d+\.)*\d+)
            Tp1:((?:\d+\.)*\d+)
            Tp2:((?:\d+\.)*\d+)
            Tp3:((?:\d+\.)*\d+)
            SL:((?:\d+\.)*\d+)
        """
    flag_img = False
    pattern = PATTERN.replace("\n", "").replace(" ", "")
    match = re.match(pattern, text)
    if not match:
        logging.error(f"Match not found: {text}")
        pattern2=PATTERN2.replace("\n", "").replace(" ", "")
        match=re.match(pattern2, text)
        flag_img=True
        if not match:
            return False
    groups = list(match.groups())
    symbol = groups[0]
    if len(symbol) == 7:
        symbol = symbol[:3] + symbol[4:]
    if symbol[5] == 'E':
        symbol = symbol[:-1] + 'F'
    if not flag_img:

        data = {
            "symbol": symbol,
            "type": groups[1],
            "price": groups[2],
            "tp1": float(groups[5]),
            "tp2": float(groups[6]),
            "tp3": float(groups[7]),
            "sl": float(groups[8])
        }
    else:

        data = {
            "symbol": symbol,
            "type": groups[1],
            "price": groups[2],
            "tp1": float(groups[3]),
            "tp2": float(groups[4]),
            "tp3": float(groups[5]),
            "sl": float(groups[6])
        }

    logging.info(f"Data extracted: {data}")
    return data


def count_decimals(f: str):
    return len(f.split(".")[1])


def sign(x: float):
    if x >= 0:
        return 1
    else:
        return -1


def get_random_img_str_from_dir(dir: str) -> str:
    return random.choice([f for f in os.listdir(dir) if isfile(join(dir, f))])


def percentage(part: float, whole: float) -> float:
    percentage_v = (100 * float(part) / float(whole))
    return percentage_v


def percentage_from_percent(percent: float, whole: float) -> float:
    return (percent * whole) / 100.0


def last_day_of_previous_month():

    return datetime.date.today().replace(day=1) - datetime.timedelta(days=1)


def last_day_of_month():
    next_month = datetime.date.today().replace(day=28) + datetime.timedelta(days=4)
    return next_month - datetime.timedelta(days=next_month.day)


def is_first_day_of_month():
    today = datetime.datetime.now()
    return True if today.day == 1 else False
