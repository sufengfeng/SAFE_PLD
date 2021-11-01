# coding:utf-8
from ctypes import *
import _thread
import time
import signal
import sys
import ctypes


class VCI_CAN_OBJ(Structure):
    _fields_ = [
        ('ID', c_uint),
        ('TimeStamp', c_uint),
        ('TimeFlag', c_byte),
        ('SendType', c_byte),
        ('RemoteFlag', c_byte),
        ('ExternFlag', c_byte),
        ('DataLen', c_byte),
        ('Data', c_byte * 8),
        ('Reserved', c_byte * 3)
    ]


class VCI_INIT_CONFIG(Structure):
    _fields_ = [
        ('AccCode', c_ulong),
        ('AccMask', c_ulong),
        ('Reserved', c_ulong),
        ('Filter', c_ubyte),
        ('Timing0', c_ubyte),
        ('Timing1', c_ubyte),
        ('Mode', c_ubyte),
    ]


class VCI_BOARD_INFO(Structure):
    _fields_ = [
        ('hw_Version', c_ushort),
        ('fw_Version', c_ushort),
        ('dr_Version', c_ushort),
        ('in_Version', c_ushort),
        ('irq_Num', c_ushort),
        ('can_Num', c_ubyte),
        ('str_Serial_Num', c_byte * 20),
        ('str_hw_Type', c_byte * 40),
        ('Reserved', c_ushort * 4)
    ]


class VCI_ERR_INFO(Structure):
    _fields_ = [
        ('ErrCode', c_uint),
        ('Passive_ErrData', c_byte * 3),
        ('ArLost_ErrData', c_byte)
    ]


breakflag = 0


def exit_can(flag):
    timet = 0
    if flag != 1:
        global breakflag
        breakflag = 1
        while True:
            if breakflag == 2 or breakflag == 0:
                break
            time.sleep(1)
            timet = timet + 1
            if timet > 5:
                break

        breakflag = 0

    ControlCAN.VCI_ResetCAN(4, 0, 0)
    ControlCAN.VCI_ResetCAN(4, 0, 1)
    ControlCAN.VCI_CloseDevice(4, 0)
    sys.exit()


def handler(signum, frame):
    exit_can(0)


def send_data_th(i):
    i = 0
    # 发送参数定义
    send_msg = VCI_CAN_OBJ(ID=0x64, DataLen=8, ExternFlag=0, RemoteFlag=0, SendType=0, TimeFlag=1, TimeStamp=0x12345678)
    byte8 = c_byte * 8
    tmp1 = ord('1')

    while True:
        i = i + 1
        global breakflag
        if breakflag > 0:
            breakflag = 2
            return

        time.sleep(0.01)
        if i > 0 and i < 50:
            tmp1 = tmp1 + 1
            send_msg.Data[0] = 1
            send_msg.Data[1] = 2
            send_msg.Data[2] = 3
            send_msg.Data[3] = 4
            send_msg.Data[4] = 5
            send_msg.Data[5] = 6
            send_msg.Data[6] = 7
            send_msg.Data[7] = tmp1
            # 发送函数
            ret = ControlCAN.VCI_Transmit(4, 0, 1, byref(send_msg), 1)
            if ret == 0:
                break
        else:
            i = 0

    exit_can(1)
    return


# 初始化ControlCan
def ConnectControlCan():
    # 加载dll动态库 依赖库kerneldlls 需要放置到python二进制文件目录中。
    # so = CDLL("./ControlCAN.dll")
    _ControlCAN = ctypes.windll.LoadLibrary("ControlCAN.dll")
    # 打开设备
    iRet01 = _ControlCAN.VCI_OpenDevice(4, 0, 0)
    print("opendevice result:", iRet01)

    # 初始化参数设置

    init_config = VCI_INIT_CONFIG(AccCode=0, AccMask=0xffffffff, Timing0=0x00, Timing1=0x1C)

    # 初始化can通道
    iRet02 = _ControlCAN.VCI_InitCAN(4, 0, 0, pointer(init_config))
    print("initcan result:", iRet02)
    return _ControlCAN, iRet01, iRet02


# 断开设备
def DisConnectControlCan(_ControlCAN):
    _ControlCAN.VCI_CloseDevice(4, 0)


# 启动Can通道
def StartControlCan(_ControlCAN, CANIndex):
    return _ControlCAN.VCI_StartCAN(4, 0, CANIndex)


# 停止通道
def StopControlCan(_ControlCAN, CANIndex):
    return _ControlCAN.VCI_ResetCAN(4, 0, CANIndex)


if __name__ == "__main__":
    # 加载dll动态库 依赖库kerneldlls 需要放置到python二进制文件目录中。
    # so = CDLL("./ControlCAN.dll")
    ControlCAN = ctypes.windll.LoadLibrary("./ControlCAN.dll")
    # 打开设备
    print("opendevice result:", ControlCAN.VCI_OpenDevice(4, 0, 0))

    # 初始化参数设置
    init_config = VCI_INIT_CONFIG(AccCode=0, AccMask=0xffffffff, Timing0=0x00, Timing1=0x1C)

    # 初始化can通道
    print("initcan result:", ControlCAN.VCI_InitCAN(4, 0, 0, pointer(init_config)))
    print("initcan result:", ControlCAN.VCI_InitCAN(4, 0, 1, pointer(init_config)))

    # 启动can通道
    print("startcan result:", ControlCAN.VCI_StartCAN(4, 0, 0))
    print("startcan result:", ControlCAN.VCI_StartCAN(4, 0, 1))
    signal.signal(signal.SIGINT, handler)

    # 发送线程
    # _thread.start_new_thread(send_data_th, (1,))

    # 接收参数定义
    recv_msg = VCI_CAN_OBJ()
    while True:
        # 循环接收数据 并打印接收到的帧数 id 及数据内容
        recvnum = ControlCAN.VCI_Receive(4, 0, 0, pointer(recv_msg), 1, 0)
        if recvnum != 0:
            print(recvnum, '%#x' % (recv_msg.ID), recv_msg.Data[0], recv_msg.Data[1], recv_msg.Data[2],
                  recv_msg.Data[3], recv_msg.Data[4], recv_msg.Data[5], recv_msg.Data[6], recv_msg.Data[7])
        elif recvnum == 0xFF:
            pass

        time.sleep(0.001)
