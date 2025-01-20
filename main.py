# coding=utf-8
import os
import platform
import threading
import json
import requests
from dotenv import load_dotenv
from HCNetSDK import *

def import_ENV():

    load_dotenv()
    # 读取环境变量
    info = {
        'project': os.getenv('DEV_PROJECT'),
        'ip': os.getenv('DEV_IP'),
        'port': int(os.getenv('DEV_PORT')),
        'username': os.getenv('DEV_USERNAME'),
        'password': os.getenv('DEV_PASSWORD')
    }
    # 打印环境变量以验证（仅用于调试）
    # print(f"【print调试】UserID: {info}")
    return info


offline_channels = []

def login_v40(ip, port, username, password):
    """
    设备登录V40 与V30功能一致
    @param ip:
    @param port:
    @param username:
    @param password:
    @return:
    """
    # 用户注册设备
    # c++传递进去的是byte型数据，需要转成byte型传进去，否则会乱码
    # 登录参数，包括设备地址、登录用户、密码等
    struLoginInfo = NET_DVR_USER_LOGIN_INFO()
    struLoginInfo.bUseAsynLogin = 0  # 同步登录方式 0- 否，1- 是
    struLoginInfo.sDeviceAddress = bytes(ip, "ascii")  # 设备IP地址
    struLoginInfo.wPort = port  # 设备服务端口
    struLoginInfo.sUserName = bytes(username, "ascii")  # 设备登录用户名
    struLoginInfo.sPassword = bytes(password, "ascii")  # 设备登录密码
    struLoginInfo.byLoginMode = 0

    # 设备信息, 输出参数
    struDeviceInfoV40 = NET_DVR_DEVICEINFO_V40()

    UserID = sdk.NET_DVR_Login_V40(byref(struLoginInfo), byref(struDeviceInfoV40))
    if UserID < 0:
        print("【print】Login failed, error code: %d" % sdk.NET_DVR_GetLastError())
        sdk.NET_DVR_Cleanup()
    else:
        print('【print】' + ip + '登录成功，设备序列号：%s' % str(struDeviceInfoV40.struDeviceV30.sSerialNumber, encoding="gbk"))
    return UserID


def SetSDKInitCfg():
    """
    设置SDK初始化依赖库路径
    @return:
    """
    strPath = os.getcwd().encode('utf-8')
    sdk_ComPath = NET_DVR_LOCAL_SDK_PATH()
    sdk_ComPath.sPath = strPath
    sdk.NET_DVR_SetSDKInitCfg(2, byref(sdk_ComPath))
    sdk.NET_DVR_SetSDKInitCfg(3, create_string_buffer(strPath + b'/libcrypto.so.1.1'))
    sdk.NET_DVR_SetSDKInitCfg(4, create_string_buffer(strPath + b'/libssl.so.1.1'))

def get_device_status(UserId):
    """
    获取设备在线状态
    @param UserId:
    @return:
    """
    devStatus = sdk.NET_DVR_RemoteControl(UserId, NET_DVR_CHECK_USER_STATUS, None, 0)
    if not devStatus:
        print("【print】设备不在线")


def getIPChannelInfo_async(UserID):
    """
    异步获取IP通道信息
    """
    pInt = c_int(0)
    m_strIpparaCfg = NET_DVR_IPPARACFG_V40()
    m_strIpparaCfg.dwSize = sizeof(m_strIpparaCfg)

    lpIpParaConfig = byref(m_strIpparaCfg)
    bRet = sdk.NET_DVR_GetDVRConfig(
        UserID, NET_DVR_GET_IPPARACFG_V40, 0, lpIpParaConfig, sizeof(m_strIpparaCfg), byref(pInt)
    )
    if not bRet:
        print("【print】获取IP接入配置参数失败，错误码：", sdk.NET_DVR_GetLastError())
        return
    # print("【print调试】起始数字通道号：", m_strIpparaCfg.dwStartDChan)
    # print("【print调试】数字通道总数：", m_strIpparaCfg.dwDChanNum)

    threads = []
    # 多线程循环
    # 循环参数修改：m_strIpparaCfg.dwDChanNum ==》  realChanNum
    realChanNum = len(m_strIpparaCfg.struStreamMode)
    print("【print】数字通道总数realChanNum：", realChanNum)
    for iChannum in range(realChanNum):
        channum = iChannum + m_strIpparaCfg.dwStartDChan
        strPicCfg = NET_DVR_PICCFG_V40()
        strPicCfg.dwSize = sizeof(NET_DVR_PICCFG_V40)

        # 创建线程检查通道状态
        thread = threading.Thread(
            target=check_channel_status, args=(UserID, channum, m_strIpparaCfg, strPicCfg)
        )
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()
    print("【print】所有通道状态检查完成")


def check_channel_status(UserID, channum, m_strIpparaCfg, strPicCfg):
    """
    检查单个通道状态的函数
    """
    pInt = c_int(0)
    offline = {}
    # ip起始值
    ipstart = '172.16'
    b_GetPicCfg = sdk.NET_DVR_GetDVRConfig(
        UserID, NET_DVR_GET_PICCFG_V40, channum, byref(strPicCfg), sizeof(strPicCfg), byref(pInt)
    )
    # print("【print调试】--------------第", channum, "个通道------------------")
    try:
        if m_strIpparaCfg.struStreamMode[channum - m_strIpparaCfg.dwStartDChan].byGetStreamType == 0:

            channel = (
                    m_strIpparaCfg.struStreamMode[channum - m_strIpparaCfg.dwStartDChan]
                    .uGetStream.struChanInfo.byIPID
                    + (
                            m_strIpparaCfg.struStreamMode[channum - m_strIpparaCfg.dwStartDChan]
                            .uGetStream.struChanInfo.byIPIDHigh
                            * 256
                    )
            )
            # print("channel:", channel)
            ip_addr = ''
            name = ''
            if channel > 0:
                ip_addr = bytes(
                    m_strIpparaCfg.struIPDevInfo[channel - 1].struIP.sIpV4
                ).decode("utf8").strip("\x00")
                # print("ip：", ip_addr)

                name = bytes(strPicCfg.sChanName).decode("gbk").strip("\x00")
                # print("name：", name)

            if (
                    m_strIpparaCfg.struStreamMode[channum - m_strIpparaCfg.dwStartDChan]
                            .uGetStream.struChanInfo.byEnable
                    == 0 and ip_addr.startswith(ipstart)
            ):
                # print("【print调试】IP通道", channum, "在线")
                # print("【print调试】IP通道", channum, "不在线")
                offline['ip'] = ip_addr
                offline['name'] = name

                offline_channels.append(offline)
    except Exception as e:
        print(f"【print】第{channum}个通道Caught an Exception: {e}")

def send_dingtalk_message(message):
    # 钉钉机器人webhook地址
    webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

    # 构建请求头部
    headers = {
        "Content-Type": "application/json",
    }

    # 构建请求数据
    data = {
        "msgtype": "text",  # 消息类型为文本
        "text": {
            "content": message  # 文本内容
        }
    }

    # 发送POST请求
    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))

    # 打印响应结果
    print("【print】钉钉推送：", response.json())


def output(project, offline):
    # 结构化输出
    result = f"项目名称：{project}\n"  # 添加项目名称
    if offline_channels:
        result += "离线摄像头：\n"  # 添加标题
        # 遍历 offline，添加每个摄像头的信息
        for index, channel in enumerate(offline, start=1):
            result += f'{index}、"ip":"{channel["ip"]}","name":"{channel["name"]}"\n'
    else:
        result += "所有通道都在线\n"
    return result
    # 打印结果
    # print(result)



if __name__ == '__main__':

    # 加载库,先加载依赖库

    os.chdir(r'/app/lib/linux')
    sdk = cdll.LoadLibrary(r'./libhcnetsdk.so')

    SetSDKInitCfg()  # 设置组件库和SSL库加载路径

    # 初始化
    sdk.NET_DVR_Init()
    # 启用SDK写日志
    sdk.NET_DVR_SetLogToFile(3, bytes('./SdkLog_Python/', encoding="gbk"), False)

    # 通用参数配置
    sdkCfg = NET_DVR_LOCAL_GENERAL_CFG()
    sdkCfg.byAlarmJsonPictureSeparate = 1
    sdk.NET_DVR_SetSDKLocalCfg(17, byref(sdkCfg))

    dev_info = import_ENV()
    # 登录设备
    UserID = login_v40(dev_info['ip'], dev_info['port'], dev_info['username'], dev_info['password'])
    get_device_status(UserID)   # 获取设备在线状态

    getIPChannelInfo_async(UserID)

    result = output(dev_info['project'], offline_channels)

    # 输出结果
    print("【print】\n", result)
    send_dingtalk_message(result)

    # 注销用户，退出程序时调用
    if sdk.NET_DVR_Logout(UserID):
        print("【print】退出程序")

    # 释放SDK资源，退出程序时调用
    sdk.NET_DVR_Cleanup()
