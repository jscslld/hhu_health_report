## 程序说明

本程序使用E河海App登录接口代替原来的老信息门户接口，比其他版本的自动打卡系统更加稳定；支持自动解析上次打卡内容，无需额外配置打卡信息，即可自动完成打卡；支持腾讯云函数，Github Actions，服务器部署等部署方式，实现无人值守自动打卡。

## 运行环境

python 3.6+

## 更新日志
[2021/09/07] 1.3

由于新接口dailyreport.hhu.edu.cn不支持弱密码，故新增弱密码检测，若密码为纯数字，默认使用老接口进行打卡。

修复老接口form.hhu.edu.cn在部分环境下出现Cookie丢失的Bug。

将Crypto包修改为cryptography，便于安装。

将时区固定为GMT +8，避免部分环境下因日期获取错误导致的打卡失败。

[2021/09/06] 1.2

由于form.hhu.edu.cn外网访问不稳定，故新增dailyreport.hhu.edu.cn打卡接口。

目前逻辑如下：

优先使用dailyreport.hhu.edu.cn打卡，若dailyreport.hhu.edu.cn需要验证码登录，则使用form.hhu.edu.cn打卡

[2021/09/03] 1.1

修正了因学校打卡系统修改打卡字段而导致程序崩溃的Bug

[2021/08/25] 1.0

第一版上线，较以往版本修改登录接口，新增解析打卡内容功能


## 部署教程

### 服务器部署

1.修改report.py第11行和第12行的用户信息

```python
USERNAME='信息门户用户名'
PASSWORD='信息门户密码'
```
2.运行`pip install -r requirements.txt`安装依赖

2.使用crontab添加定时任务，定时调用`python report.py`即可

### 腾讯云函数部署（推荐）

1.修改report.py第11行和第12行的用户信息
```python
USERNAME='信息门户用户名'
PASSWORD='信息门户密码'
```

2.进入 https://console.cloud.tencent.com/scf/list 创建一个云函数。

创建时请选择自定义创建，函数类型选择事件函数，地域建议选择上海，运行环境建议选择Python3.6，函数代码部分将report.py修改好的内容复制进去，其他选项保持默认，点击完成。

3.在函数管理 - 函数配置中，修改函数执行超时时间为300秒。（学校服务器有时会抽风）

4.在触发管理中，创建触发器。触发周期选择自定义触发，填入crontab表达式即可。

5.在函数管理 - 函数代码中，点击编辑器菜单栏的终端 - 新终端，在弹出的命令行中依次输入
```
cd src
pip install requests_html -t .
```
安装依赖完成后，点击部署，将其部署在云中。

常用crontab表达式

```
0 0 6 * * * *       #每天6点触发
0 30 6 * * * *      #每天6点半触发
0 0 7 * * * *       #每天7点触发
```

### Github Actions部署（强烈不推荐）

该部署方式违反Github Actions的TOS，故不做详细介绍
