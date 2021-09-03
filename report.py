# -*- coding: utf8 -*-
__author__ = "Lu Lidong"
__copyright__ = "Copyright (C) 2021 Lu Lidong"
__version__ = "1.1"

import json
import re
import datetime
import requests

"""
用户信息
"""

USERNAME = '******'  # 学号
PASSWORD = '******'  # 密码

"""
登录
"""


def login():
    loginUrl = 'http://mids.hhu.edu.cn/_ids_mobile/login18_9'
    formData = {
        "username": USERNAME,
        "password": PASSWORD
    }
    try:
        res = requests.post(url=loginUrl, data=formData)
        if "loginErrCode" in res.headers.keys():
            print("用户名或密码错误")
            exit(2)
        else:
            cookie = json.loads(res.headers["ssoCookie"])
            return cookie[0]["cookieName"] + "=" + cookie[0]["cookieValue"]
    except Exception as err:
        print('登录失败：\n', format(err))
        exit(2)


"""
打卡
"""


def report():
    """
    将SSO_COOKIE转换为打卡系统的COOKIE
    """
    cookie = login()
    initUrl = "http://form.hhu.edu.cn/pdc/form/list"
    headers = {"cookie": cookie}
    res = requests.get(url=initUrl, headers=headers)
    cookies = res.cookies
    cookie = requests.utils.dict_from_cookiejar(cookies)
    """
    同步上一次打卡记录
    """
    syncUrl = "http://form.hhu.edu.cn/pdc/formDesignApi/S/gUTwwojq"
    res = requests.get(url=syncUrl, cookies=cookie)
    javascript = re.search('<script type="text\/javascript">([\w\W]*)<\/script>', res.text)[0]
    wid = re.search("(?<=_selfFormWid = \')(.*?)(?=\')", javascript)[0]
    uid = re.search("(?<=_userId = \')(.*?)(?=\')", javascript)[0]
    fillDetail = re.search("(?<=fillDetail = )(.*?)(?=\;)", javascript)[0]
    dataDetail = re.search("(?<=dataDetail = )(.*?)(?=\]\,)", javascript)[0] + "]"
    data = {
        **json.loads(fillDetail)[0],
        **json.loads(dataDetail)[0]
    }
    column = {
        "XGH_336526": "学号",
        "XM_1474": "姓名",
        "SFZJH_859173": "身份证号",
        "SELECT_941320": "学院",
        "SELECT_459666": "年级",
        "SELECT_814855": "专业",
        "SELECT_525884": "班级",
        "SELECT_125597": "宿舍楼",
        "TEXT_950231": "宿舍号",
        "TEXT_937296": "手机号",
        "RADIO_6555": "您的体温情况？",
        "RADIO_535015": "您今天是否在校？",
        "RADIO_891359": "本人健康情况？",
        "RADIO_372002": "同住人健康情况？",
        "RADIO_618691": "本人及同住人14天内是否有中高风险地区旅居史或接触过中高风险地区人员？"
    }
    postData = {"DATETIME_CYCLE": datetime.date.today().strftime('%Y/%m/%d')}
    for key in column.keys():
        postData[key] = data[key]
    """
    开始打卡
    """
    postUrl = "http://form.hhu.edu.cn/pdc/formDesignApi/dataFormSave?wid=" + wid + "&userId=" + uid
    res = requests.post(url=postUrl, data=postData, cookies=cookie)
    if json.loads(res.text)["result"] == True:
        print("打卡成功")
        print("打卡数据如下")
        for key in column.keys():
            print(column[key], data[key])
    else:
        print("打卡失败:", res.text)


def main_handler(event, context):
    report()


if __name__ == '__main__':
    report()
