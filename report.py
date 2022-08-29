# -*- coding: utf8 -*-

__author__ = "Lu Lidong"
__copyright__ = "Copyright (C) 2021-2022 Lu Lidong"
__version__ = "2.0.1"

import base64
import datetime
import json
import re
import time
from random import Random

from urllib.parse import urlparse
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from requests_html import HTMLSession
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
os.environ['TZ'] = 'Asia/Shanghai'

"""
打卡信息配置
"""
ReportList=[
    # 无需收信的范例
    {
        "username":"信息门户用户名1",
        "password":"信息门户密码1",
    },
    # 需要收信的范例（需要收信的请完善下面的发信服务器配置信息）
    {
        "username":"信息门户用户名2",
        "password":"信息门户密码2",
        "email":"收信邮箱"
    },
]


"""
发信服务配置信息
"""
SMTP_USERNAME='SMTP用户名'
SMTP_PASSWORD='SMTP密码'
SMTP_HOST='SMTP服务器地址'
SMTP_PORT=465



"""
AES加密类
"""
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

"""
自动打卡类
"""
class Report(object):
    """
    构造函数
    """
    def __init__(self, username, password,email=None):
        self.username = username
        self.password = password
        self.email = email
        self.s = HTMLSession()
        self.log = ""
        self.ua = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
        self.ColumnUnder = {
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
        self.ColumnPost = {
            "XGH_566872": "学号",
            "XM_140773": "姓名",
            "SFZJH_402404": "身份证号",
            "SZDW_439708": "学院",
            "ZY_878153": "专业",
            "GDXW_926421": "攻读学位",
            "DSNAME_606453":"导师",
            "PYLB_253720": "培养类别",
            "SELECT_172548": "宿舍楼",
            "TEXT_91454": "宿舍号",
            "TEXT_24613": "手机号",
            "TEXT_826040": "紧急联系人电话",
            "RADIO_799044": "您的体温情况？",
            "RADIO_384811": "您今天是否在校？",
            "RADIO_907280": "本人健康情况？",
            "RADIO_716001": "同住人健康情况？",
            "RADIO_248990": "本人及同住人14天内是否有中高风险地区旅居史或接触过中高风险地区人员？"
        }
    """
    增加日志
    """
    def AddLog(self,level,log):
        self.log += "["+str(level)+"] [" + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))+"] "+str(log)+"\n"
        print("["+str(level)+"]\t[" + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))+"]\t"+str(log))
    """
    定长随机字符串生成，用于填充iv和data
    """
    def RandomStr(self,randomlength=8):
        str = ''
        chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
        length = len(chars) - 1
        random = Random()
        for i in range(randomlength):
            str += chars[random.randint(0, length)]
        return str
    """
    新版门户打卡
    """
    def NewReport(self):
        self.AddLog("INFO", "正在使用新版门户进行打卡")
        response = self.s.get(
            "http://authserver.hhu.edu.cn/authserver/login",headers = {"User-Agent":self.ua})
        lt = response.html.xpath("//*[@id='casLoginForm']/input[1]")[0].attrs["value"]
        execution = response.html.xpath("//*[@id=\"casLoginForm\"]/input[3]")[0].attrs["value"]
        _eventId = response.html.xpath("//*[@id=\"casLoginForm\"]/input[4]")[0].attrs["value"]
        dllt = response.html.xpath("//*[@id=\"casLoginForm\"]/input[2]")[0].attrs["value"]
        rmShown = response.html.xpath("//*[@id=\"casLoginForm\"]/input[5]")[0].attrs["value"]
        pwdDefaultEncryptSalt = response.html.xpath("//*[@id=\"casLoginForm\"]/input[6]")[0].attrs["value"]
        iv = self.RandomStr(16)
        prefix = self.RandomStr(64)
        crypto = AESCrypto(pwdDefaultEncryptSalt.encode("utf-8"), iv.encode("utf-8"))
        data = {
            'username': self.username,
            'password': base64.encodebytes(crypto.encrypt(prefix + self.password)).decode('utf8').strip(),
            'lt': lt,
            'dllt':dllt,
            'execution': execution,
            '_eventId': _eventId,
            'rmShown': rmShown
        }
        loginRes = self.s.post(
            "http://authserver.hhu.edu.cn/authserver/login",
            data=data,headers = {"User-Agent":self.ua})
        if loginRes.url != "http://authserver.hhu.edu.cn/authserver/index.do":
            try:
                msg = loginRes.html.xpath("//*[@id=\"msg\"]")[0].text
            except:
                msg = "未知原因"
            self.AddLog("FATAL", "新版门户登录失败，远程服务器返回：" + str(msg))
            return False
        else:
            self.AddLog("INFO","新版门户登录成功")
            res=self.s.get("http://dailyreport.hhu.edu.cn/pdc/form/list")
            if "健康打卡" not in res.html.html:
                self.AddLog("FATAL", "dailyreport.hhu.edu.cn识别失败，当前url：" + str(res.url))
                return False
            else:
                if "本科生健康打卡" in res.html.html:
                    self.AddLog("INFO", "dailyreport.hhu.edu.cn识别成功，身份：本科生")
                    self.Report("http://dailyreport.hhu.edu.cn/pdc/formDesignApi/S/gUTwwojq", self.ColumnUnder)
                    return True
                elif "研究生健康打卡" in res.html.html:
                    self.AddLog("INFO", "dailyreport.hhu.edu.cn识别成功，身份：研究生")
                    self.Report("http://dailyreport.hhu.edu.cn/pdc/formDesignApi/S/xznuPIjG", self.ColumnPost)
                    return True
                else:
                    self.AddLog("FATAL", "dailyreport.hhu.edu.cn识别失败，身份：未知")
                    return False
    """
    E河海接口打卡
    """
    def OldReport(self):
        self.AddLog("INFO", "正在使用E河海进行打卡")
        data = {
            "username": self.username,
            "password": self.password
        }
        loginRes = self.s.post(
            "http://mids.hhu.edu.cn/_ids_mobile/login18_9",
            data=data)
        if "loginErrCode" in loginRes.headers.keys():
            self.AddLog("FATAL", "E河海登录失败，远程服务器返回：" + str(loginRes.headers.loginErrCode))
            return False
        else:
            self.AddLog("INFO", "E河海登录成功")
            cookieArr = json.loads(loginRes.headers["ssoCookie"])
            strCookie=""
            for item in cookieArr:
                strCookie += item["cookieName"] + "=" + item["cookieValue"]+";"
            headers = {'Cookie': strCookie, }
            res=self.s.get("http://form.hhu.edu.cn/pdc/form/list", headers=headers)
            if "健康打卡" not in res.html.html:
                self.AddLog("FATAL", "form.hhu.edu.cn识别失败，当前url：" + str(res.url))
                return False
            else:
                if "本科生健康打卡" in res.html.html:
                    self.AddLog("INFO", "form.hhu.edu.cn识别成功，身份：本科生")
                    self.Report("http://form.hhu.edu.cn/pdc/formDesignApi/S/gUTwwojq",self.ColumnUnder)
                elif "研究生健康打卡" in res.html.html:
                    self.AddLog("INFO", "form.hhu.edu.cn识别成功，身份：研究生")
                    self.Report("http://form.hhu.edu.cn/pdc/formDesignApi/S/xznuPIjG", self.ColumnPost)
                    return True
                else:
                    self.AddLog("FATAL", "form.hhu.edu.cn识别失败，身份：未知")
                    return False
    """
    通用打卡接口
    """
    def Report(self,url,column):
        res = self.s.get(url)
        if res.url == url:
            if "未知原因" in res.html.html:
                self.AddLog("FATAL", "打卡系统存在异常")
                return False
            else:
                try:
                    javascript = re.search('<script type="text\/javascript">([\w\W]*)<\/script>', res.html.html)[0]
                    wid = re.search("(?<=_selfFormWid = \')(.*?)(?=\')", javascript)[0]
                    uid = re.search("(?<=_userId = \')(.*?)(?=\')", javascript)[0]
                    fillDetail = re.search("(?<=fillDetail = )(.*?)(?=\;)", javascript)[0]
                    dataDetail = re.search("(?<=dataDetail = )(.*?)(?=\]\,)", javascript)[0] + "]"
                    data = {
                        **json.loads(dataDetail)[0],
                        **json.loads(fillDetail)[0]
                    }
                    postData = {"DATETIME_CYCLE": datetime.date.today().strftime('%Y/%m/%d')}
                    for key in column.keys():
                        postData[key] = data[key]
                    self.AddLog("INFO", "上一次打卡数据解析成功")
                except:
                    self.AddLog("FATAL", "上一次打卡数据解析失败")
                    return False
                postUrl = urlparse(url).scheme+"://"+urlparse(url).netloc+"/pdc/formDesignApi/dataFormSave?wid=" + wid + "&userId=" + uid
                res = self.s.post(postUrl, data=postData)
                if json.loads(res.html.html)["result"] == True:
                    self.AddLog("INFO", "打卡成功")
                    self.AddLog("INFO", "打卡数据如下")
                    for key in column.keys():
                        self.AddLog("INFO", str(column[key])+":"+str(data[key]))
                else:
                    self.AddLog("FATAL", "打卡失败，远程服务器返回："+res.html.html)
                    return False
        else:
            self.AddLog("FATAL", "系统异常，被跳转至"+res.url)
            return False
    def AutoReport(self):
        if self.password.isdigit():
            self.AddLog("WARNING", "该用户密码为弱密码，无法从新版门户进入打卡系统，切换到E河海打卡接口")
            self.OldReport()
            return True
        needCaptcha = self.s.get(
            "http://authserver.hhu.edu.cn/authserver/needCaptcha.html?username=" + self.username + "&pwdEncrypt2=pwdEncryptSalt&_=1630893279471")
        if needCaptcha.html.html == "true":
            self.AddLog("WARNING", "该用户需输入验证码方可登录新版门户，切换到E河海打卡接口")
            self.OldReport()
            return True
        self.NewReport()

    def Send(self):
        msg = MIMEText(self.log, 'plain', 'utf-8')
        msg['From'] = SMTP_USERNAME
        msg['To'] = self.email
        msg['Subject'] = Header("[" + str(time.strftime("%Y-%m-%d", time.localtime()))+"]今日打卡情况反馈", 'utf-8').encode()
        server = smtplib.SMTP_SSL(SMTP_HOST,SMTP_PORT )
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        try:
            server.sendmail(SMTP_USERNAME, [self.email], msg.as_string())
            self.AddLog("INFO", "发信成功")
        except Exception as e:
            self.AddLog("FATAL", "发信失败，原因："+str(e))
        finally:
            server.quit()
def main_handler(event, context):
    i = 1
    for User in ReportList:
        print("[" + str("INFO") + "]\t[" + str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + "]\t" + str(
            "正在处理第" + str(i) + "个用户的打卡"))
        try:
            R = Report(User["username"], User["password"], None if "email" not in User.keys() else User["email"])
            R.AutoReport()
            if "email" in User.keys():
                R.Send()
        except:
            pass
        finally:
            i += 1

if __name__ == '__main__':
    main_handler(None,None)
