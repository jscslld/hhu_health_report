# -*- coding: utf8 -*-

__author__ = "Lu Lidong"
__copyright__ = "Copyright (C) 2021 Lu Lidong"
__version__ = "1.3"

from requests_html import HTMLSession
import json
import re
import datetime
import requests
from random import Random
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import base64
import os
os.environ['TZ'] = 'Asia/Shanghai'


"""
用户信息
"""

USERNAME = '******'  # 学号
PASSWORD = '******'  # 密码

class AESCrypto(object):
    """AESCrypto."""

    def __init__(self, aes_key, aes_iv):
        if not isinstance(aes_key, bytes):
            aes_key = aes_key.encode()

        if not isinstance(aes_iv, bytes):
            aes_iv = aes_iv.encode()

        self.aes_key = aes_key
        self.aes_iv = aes_iv

    def encrypt(self, data, mode='cbc'):
        """encrypt."""
        func_name = '{}_encrypt'.format(mode)
        func = getattr(self, func_name)
        if not isinstance(data, bytes):
            data = data.encode()

        return func(data)

    def decrypt(self, data, mode='cbc'):
        """decrypt."""
        func_name = '{}_decrypt'.format(mode)
        func = getattr(self, func_name)

        if not isinstance(data, bytes):
            data = data.encode()

        return func(data)


    def ctr_encrypt(self, data):
        """ctr_encrypt."""
        cipher = Cipher(algorithms.AES(self.aes_key),
                        modes.CTR(self.aes_iv),
                        backend=default_backend())

        return cipher.encryptor().update(self.pkcs7_padding(data))

    def ctr_decrypt(self, data):
        """ctr_decrypt."""
        cipher = Cipher(algorithms.AES(self.aes_key),
                        modes.CTR(self.aes_iv),
                        backend=default_backend())

        uppaded_data = self.pkcs7_unpadding(cipher.decryptor().update(data))
        return uppaded_data.decode()

    def cbc_encrypt(self, data):
        """cbc_encrypt."""
        cipher = Cipher(algorithms.AES(self.aes_key),
                        modes.CBC(self.aes_iv),
                        backend=default_backend())

        return cipher.encryptor().update(self.pkcs7_padding(data))

    def cbc_decrypt(self, data):
        """cbc_decrypt."""
        cipher = Cipher(algorithms.AES(self.aes_key),
                        modes.CBC(self.aes_iv),
                        backend=default_backend())

        uppaded_data = self.pkcs7_unpadding(cipher.decryptor().update(data))
        return uppaded_data.decode()

    @staticmethod
    def pkcs7_padding(data):
        """pkcs7_padding."""
        padder = padding.PKCS7(algorithms.AES.block_size).padder()

        padded_data = padder.update(data) + padder.finalize()

        return padded_data

    @staticmethod
    def pkcs7_unpadding(padded_data):
        """pkcs7_unpadding."""
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        data = unpadder.update(padded_data)

        try:
            uppadded_data = data + unpadder.finalize()
        except ValueError:
            raise Exception('无效的加密信息!')
        else:
            return uppadded_data


def random_str(randomlength=8):
    str = ''
    chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str+=chars[random.randint(0, length)]
    return str

def process():
    user=USERNAME
    pwd=PASSWORD
    if pwd.isdigit():
        print("检测到密码为弱密码，使用老接口进行打卡")
        report()
        return
    s = HTMLSession()
    needCaptcha=s.get("http://authserver.hhu.edu.cn/authserver/needCaptcha.html?username="+user+"&pwdEncrypt2=pwdEncryptSalt&_=1630893279471");
    if needCaptcha.html.html == "true" :
        print("该用户登录需要验证码，暂时无法使用新系统，转用老系统")
        report()
        return
    else:
        response = s.get("http://authserver.hhu.edu.cn/authserver/login?service=http%3A%2F%2Fportal.hhu.edu.cn%2Fportal-web%2Fj_spring_cas_security_check")
        lt = response.html.xpath("//*[@id='casLoginForm']/input[1]")[0].attrs["value"]
        #dllt = response.html.xpath("//*[@id=\"casLoginForm\"]/input[2]")[0].attrs["value"]
        execution = response.html.xpath("//*[@id=\"casLoginForm\"]/input[3]")[0].attrs["value"]
        _eventId = response.html.xpath("//*[@id=\"casLoginForm\"]/input[4]")[0].attrs["value"]
        rmShown = response.html.xpath("//*[@id=\"casLoginForm\"]/input[5]")[0].attrs["value"]
        pwdDefaultEncryptSalt = response.html.xpath("//*[@id=\"casLoginForm\"]/input[6]")[0].attrs["value"]
        iv = random_str(16)
        prefix = random_str(64)
        crypto = AESCrypto(pwdDefaultEncryptSalt.encode("utf-8"), iv.encode("utf-8"))
        data={
            'username':user,
            'password':base64.encodebytes(crypto.encrypt(prefix+pwd)).decode('utf8').strip(),
            'lt':lt,
            'execution':execution,
            '_eventId':_eventId,
            'rmShown':rmShown
        }
        loginRes=s.post("http://authserver.hhu.edu.cn/authserver/login?service=http%3A%2F%2Fportal.hhu.edu.cn%2Fportal-web%2Fj_spring_cas_security_check",data=data)
        if "统一身份认证" in loginRes.html.html:
            print("登陆失败：用户名或密码错误")
            return
        print("登陆成功")
        s.get("http://dailyreport.hhu.edu.cn/pdc/form/list")
        res = s.get("http://dailyreport.hhu.edu.cn/pdc/formDesignApi/S/gUTwwojq")
        if "本科生健康打卡" not in res.html.html:
            print("读取打卡页面失败")
            return
        javascript = re.search('<script type="text\/javascript">([\w\W]*)<\/script>', res.html.html)[0]
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
        print("过往打卡数据读取成功")
        """
        开始打卡
        """
        postUrl = "http://dailyreport.hhu.edu.cn/pdc/formDesignApi/dataFormSave?wid=" + wid + "&userId=" + uid
        res = s.post(postUrl,data=postData)
        if json.loads(res.html.html)["result"] == True:
            print("打卡成功")
            print("打卡数据如下")
            for key in column.keys():
                print(column[key], data[key])
        else:
            print("打卡失败")

def report():
    """
    将SSO_COOKIE转换为打卡系统的COOKIE
    """
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
            cookieArr = json.loads(res.headers["ssoCookie"])
            print("登录成功")
            strCookie=cookieArr[0]["cookieName"] + "=" + cookieArr[0]["cookieValue"]
    except Exception as err:
        print('登录失败：\n', format(err))
        exit(2)
    cookie = strCookie
    s = HTMLSession()
    headers = {'Cookie': cookie,}
    s.get("http://form.hhu.edu.cn/pdc/form/list",headers=headers)
    res = s.get("http://form.hhu.edu.cn/pdc/formDesignApi/S/gUTwwojq")
    if "本科生健康打卡" not in res.html.html:
        print("读取打卡页面失败")
        return
    javascript = re.search('<script type="text\/javascript">([\w\W]*)<\/script>', res.html.html)[0]
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
    print("过往打卡数据读取成功")
    """
    开始打卡
    """
    postUrl = "http://form.hhu.edu.cn/pdc/formDesignApi/dataFormSave?wid=" + wid + "&userId=" + uid
    res = s.post(postUrl, data=postData)
    if json.loads(res.html.html)["result"] == True:
        print("打卡成功")
        print("打卡数据如下")
        for key in column.keys():
            print(column[key], data[key])
    else:
        print("打卡失败")
def main_handler(event, context):
    process()
# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    process()
