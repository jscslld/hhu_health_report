import hashlib
import logging
import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr

import cv2
import easyocr
import requests_html

from log import config_logging
import os
def mail(smtp_host,smtp_port,smtp_username,smtp_password,subject,content,my_user):
    print(smtp_host)
    ret = True
    try:
        msg = MIMEText(content, 'html', 'utf-8')
        msg['From'] = formataddr(["河海大学自动打卡系统", smtp_username])  # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        msg['To'] = my_user  # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        msg['Subject'] = subject  # 邮件的主题，也可以说是标题

        server = smtplib.SMTP_SSL(smtp_host, smtp_port)  # 发件人邮箱中的SMTP服务器，端口是25
        server.login(smtp_username, smtp_password)  # 括号中对应的是发件人邮箱账号、邮箱密码
        server.sendmail(smtp_username, [my_user, ], msg.as_string())  # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.quit()  # 关闭连接
    except Exception:  # 如果 try 中的语句没有执行，则会执行下面的 ret=False
        ret = False
    return ret
def main():
    username = os.environ.get("username")
    if not username:
        raise Exception("未在Github Environments中配置用户名")
    password = os.environ.get("password")
    if not password:
        raise Exception("未在Github Environments中配置密码")
    needSend = True
    email = os.environ.get("email")
    if not email:
        needSend = False
    sender = os.environ.get("sender")
    smtp_host = ""
    smtp_port = 465
    smtp_username = ""
    smtp_password = ""
    if not sender:
        needSend = False
    else:
        sender_info = sender.split(" ")
        if len(sender_info) != 4:
            logging.fatal("smtp服务信息解析失败")
            exit(1)
        smtp_host = sender_info[0]
        smtp_port = sender_info[1]
        smtp_username = sender_info[2]
        smtp_password = sender_info[3]
    '''
    # 配置日志输出和表单模板，初始化请求会话
    '''
    config_logging("debug.log")
    add_form_template = ['__EVENTTARGET', '__EVENTARGUMENT', '__VIEWSTATE', '__VIEWSTATEGENERATOR',
                         '__VIEWSTATEENCRYPTED', 'tbrq', 'twqk', 'twqkdm', 'sfzx', 'sfzxdm', 'brjkqk', 'brjkqkdm',
                         'tzrjkqk', 'tzrjkqkdm', 'sfjczgfx', 'sfjczgfxdm', 'jkmys', 'jkmysdm', 'xcmqk', 'xcmqkdm',
                         'brcnnrss', 'ck_brcnnrss', 'uname', 'czsj', 'pzd_lock', 'pzd_lock2', 'pzd_lock3', 'pzd_lock4',
                         'pzd_lock5', 'pzd_y', 'xdm', 'bjhm', 'xh', 'xm', 'qx_r', 'qx_i', 'qx_u', 'qx_d', 'qx2_r',
                         'qx2_i', 'qx2_u', 'qx2_d', 'databcxs', 'databcdel', 'xzbz', 'pkey', 'pkey4', 'xs_bj', 'bdbz',
                         'dcbz', 'cw', 'hjzd', 'xqbz', 'ndbz', 'st_xq', 'st_nd', 'mc', 'smbz', 'fjmf', 'psrc', 'pa',
                         'pb', 'pc', 'pd', 'pe', 'pf', 'pg', 'msie', 'tkey', 'tkey4', 'pczsj', 'jjzt', 'lszt', 'bczt',
                         'colordm']
    log_template = dict(czsj="操作时间", uname="操作人", bjhm="班级号码", xh="学号", tbrq="填报日期", twqk="您的体温情况", sfzx="您今天是否在校",
                        brjkqk="本人健康情况", tzrjkqk="同住人健康情况", sfjczgfx="本人及同住人14天内是否有中高风险地区旅居史或接触过中高风险地区人", jkmys="健康码颜色",
                        xcmqk="行程码是否带*号")
    add_form = {}

    session = requests_html.HTMLSession()
    session.headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
    }

    '''
    # 获取登录页面信息
    '''
    try_times = 0
    password = password.upper()
    while True:
        try_times += 1
        if try_times > 3:
            logging.fatal("验证码识别错误次数太多，停止OCR")
            exit(0)
        r = session.get('http://smst.hhu.edu.cn/Mobile/login.aspx')
        logging.info("开始获取登录信息")
        data = {"__VIEWSTATE": r.html.xpath('//*[@id="__VIEWSTATE"]')[0].attrs["value"],
                "__VIEWSTATEGENERATOR": r.html.xpath('//*[@id="__VIEWSTATEGENERATOR"]')[0].attrs["value"],
                "__VIEWSTATEENCRYPTED": r.html.xpath('//*[@id="__VIEWSTATEENCRYPTED"]')[0].attrs["value"], "cw": "",
                "xzbz": "1", "pas2s": hashlib.md5(password.encode(encoding='UTF-8')).hexdigest().upper(),
                "yxdm": r.html.xpath('//*[@id="yxdm"]')[0].attrs["value"], "userbh": username, "vcode": ""}

        '''
        # 获取验证码信息
        '''
        logging.info("开始获取验证码信息")
        vcode = session.get('http://smst.hhu.edu.cn/vcode.aspx')
        with open("vcode.aspx", 'wb') as f:  # 图片信息是二进制形式，所以要用wb写入
            f.write(vcode.content)  # 将请求图片获取到的二进制响应内容写入文件中

        '''
        # 利用openCV加强验证码，便于OCR识别
        '''
        logging.info("开始处理验证码")
        img = cv2.imread("vcode.aspx", 1)
        im_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, im_inv = cv2.threshold(im_gray, 210, 255, cv2.THRESH_BINARY_INV)
        im = cv2.resize(im_inv, (0, 0), fx=5, fy=5, interpolation=cv2.INTER_NEAREST)
        cv2.imwrite("vcode.png", im)

        '''
        # OCR识别验证码
        '''
        reader = easyocr.Reader(['en'], gpu=False, verbose=False,model_storage_directory="./model")
        result = reader.readtext('vcode.png')
        data["vcode"] = result[0][1].replace(' ', '')
        logging.info("处理完成，验证码识别结果为：" + data["vcode"])
        '''
        # 开始登陆
        '''
        login = session.post("http://smst.hhu.edu.cn/Mobile/login.aspx", data)
        logging.info("开始登陆")
        if "login" in login.url:
            reason = login.html.xpath('//*[@id="cw"]')[0].attrs["value"]
            if reason != '4':
                logging.fatal("登陆失败，" + reason.replace("\r", ""))
            else:
                logging.info("登陆成功，提示：请关注企业微信，在微信里免登录直接进入系统,实时接收学校下发的通知、审批提示信息等。")
                break
            if "验证码" in reason:
                pass
            else:
                exit(0)
        else:
            logging.info("登陆成功")
            break
    '''
    # 获取历史打卡记录
    '''
    logging.info("开始获取历史打卡信息")
    jkdk = session.get("http://smst.hhu.edu.cn/Mobile/rsbulid/r_3_3_st_jkdk.aspx")
    for key in add_form_template:
        try:
            add_form[key] = jkdk.html.xpath('//*[@id="' + key + '"]')[0].attrs["value"]
        except:
            add_form[key] = ""

    '''
    # 拼接打卡记录
    '''
    add_form['__EVENTTARGET'] = 'dcbc'  # 修改为databc
    #add_form['__EVENTTARGET'] = 'databc'

    '''
    # 打卡
    '''
    jkdk = session.post("http://smst.hhu.edu.cn/Mobile/rsbulid/r_3_3_st_jkdk.aspx", add_form)

    '''
    # 获取打卡结果
    '''
    result = jkdk.html.xpath('//*[@id="cw"]')[0].attrs["value"]
    if "成功" in result:
        logging.info("打卡成功[首次]")
        content = ""
        # for key, value in log_template.items():
            # logging.info(value + ":" + jkdk.html.xpath('//*[@id="' + key + '"]')[0].attrs["value"])
            # content += value + ":" + jkdk.html.xpath('//*[@id="' + key + '"]')[0].attrs["value"]+"<br/>"
        if needSend:
            mail(smtp_host,smtp_port,smtp_username,smtp_password,Header("今日打卡成功", 'utf-8').encode(), content,email)
    elif "已存在" in result:
        logging.info("打卡成功[非首次]")
        # for key, value in log_template.items():
        #     logging.info(value + ":" + jkdk.html.xpath('//*[@id="' + key + '"]')[0].attrs["value"])
    else:
        if needSend:
            mail(smtp_host,smtp_port,smtp_username,smtp_password,Header("今日打卡失败", 'utf-8').encode(), "打卡失败，服务器返回：" + result, email)
        logging.fatal("打卡失败，服务器返回：" + result)


if __name__ == "__main__":
    main()
