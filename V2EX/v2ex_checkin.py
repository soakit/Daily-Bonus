# -*- coding: utf-8 -*-
# @File     : v2ex_checkin.py
# @Time     : 2021/04/08 09:43
# @Author   : Jckling

import os
import re
import time
from datetime import date, datetime

import requests
from lxml import html

# cookies
COOKIES = os.environ.get("V2EX_COOKIES")
SESSION = requests.Session()
msg = []

HEADERS = {
    "Accept": "*/*",
    # "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "cache-control": "no-cache",
    "Cookie": COOKIES,
    "pragma": "no-cache",
    "Referer": "https://www.v2ex.com/",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "Sec-Ch-Ua-Platform": "macOS",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


# 获取 once
def get_once():
    url = "https://www.v2ex.com/mission/daily"
    r = SESSION.get(url, headers=HEADERS)

    global msg
    if "你要查看的页面需要先登录" in r.text:
        msg += [
            {"name": "登录信息", "value": "登录失败，Cookie 可能已经失效"}
        ]
        return "", False
    elif "每日登录奖励已领取" in r.text:
        msg += [
            {"name": "登录信息", "value": "每日登录奖励已领取，" + re.search(r"已连续登录 \d+ 天", r.text)[0]}
        ]
        return "", True

    match = re.search(r"once=(\d+)", r.text)
    if match:
        try:
            once = match.group(1)
            msg += [{"name": "登录信息", "value": "登录成功"}]
            return once, True
        except IndexError:
            return "", False
    else:
        return "", False


# 签到
def check_in(once):
    # 无内容返回
    url = "https://www.v2ex.com/mission/daily/redeem?once=" + once
    SESSION.get(url, headers=HEADERS)


# 查询
def query_balance():
    url = "https://www.v2ex.com/balance"
    r = SESSION.get(url, headers=HEADERS)
    tree = html.fromstring(r.content)

    # 签到结果
    global msg
    checkin_day_str = tree.xpath('//small[@class="gray"]/text()')[0]
    checkin_day = datetime.now().astimezone().strptime(checkin_day_str, '%Y-%m-%d %H:%M:%S %z')
    if checkin_day.date() == date.today():
        # 签到奖励
        bonus = re.search(r'\d+ 的每日登录奖励 \d+ 铜币', r.text)[0]
        msg += [
            {"name": "签到信息", "value": bonus}
        ]
    else:
        msg += [
            {"name": "签到信息", "value": "签到失败"}
        ]

    # 余额
    balance = tree.xpath('//div[@class="balance_area bigger"]/text()')
    if len(balance) == 2:
        balance = ['0'] + balance

    golden, silver, bronze = [s.strip() for s in balance]
    msg += [
        {"name": "账户余额", "value": f"{golden} 金币，{silver} 银币，{bronze} 铜币"}
    ]


def main():
    for i in range(3):
        try:
            once, success = get_once()
            if once:
                check_in(once)
            if success:
                query_balance()
        except AttributeError:
            if i < 3:
                time.sleep(3)
                print("checkin failed, try #{}".format(i + 1))
                continue
            else:
                raise
        break

    global msg
    return "\n".join([f"{one.get('name')}: {one.get('value')}" for one in msg])


if __name__ == '__main__':
    print(" V2EX 签到开始 ".center(60, "="))
    print(main())
    print(" V2EX 签到结束 ".center(60, "="), "\n")
