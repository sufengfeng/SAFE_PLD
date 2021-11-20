import tkinter.messagebox   #这个是消息框，对话框的关键
import tkinter.filedialog   #文件打开对话框
import os                   #文件目录相关
import datetime             #获取系统时间
import windnd               #文件拖拽使用,需安装windnd
import win32api             #释放DLL动态库使用,需安装pywin32
import _thread
import time
import signal
import sys
import platform
import ctypes
import struct

from tkinter import *
from tkinter import ttk     #下拉菜单使用
from tkinter.scrolledtext import ScrolledText
from ctypes import *
from sys import version

CANINDEX = 0

class VCI_CAN_OBJ(Structure):
    _fields_ = [
            ('ID', c_uint),
            ('TimeStamp', c_uint),
            ('TimeFlag', c_byte),
            ('SendType', c_byte),
            ('RemoteFlag', c_byte),
            ('ExternFlag', c_byte),
            ('DataLen', c_byte),
            ('Data', c_ubyte * 8),
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

'''
#请使用命令"pip install windnd"  安装windnd库
#请使用命令"pip install pywin32" 安装pywin32库
'''
#CrcCalcDLL = cdll.LoadLibrary("C:/Users/xiaobin/Documents/visual studio 2012/Projects/CrcCalc/Release/CrcCalc.dll")

#初始化编码选择下拉框和文件打开按钮
def InitCRCCalcParam():
    global FileName
    CRC_value.set('')
    if 1 == CalcType.get():
        LoadFile.place_forget()
        contents.config(state=NORMAL) #打开文本输入框编辑状态
        contents.delete(1.0, END)
        contents.insert(1.0,'请输入字符串')
        contents.insert(END,'\n\n启用C库=OFF 使用Pyhon计算CRC,速度较慢。')
        contents.insert(END,'\n启用C库=On  使用C语言计算，速度极快，但需\n            本目录下的CrcCalc.dll文件。')
        contents.insert(END,'\n\n\n\n')
        contents.config(bg = 'white')
        cmb_CodeType.place(x=60*2, y=0, width=60, height=24)
        cmb_CodeType_desc.place(x=60*3, y=0, width=96, height=24)
        FileName = ''
    else:
        LoadFile.place(x=0, y=8, width=120, height=36)
        contents.delete(1.0, END)
        contents.insert(1.0,'请通过[打开.bin文件]按钮载入.bin文件。')
        contents.config(state=DISABLED) #关闭文本输入框编辑状态
        contents.config(bg = 'gainsboro')
        cmb_CodeType.place_forget()
        cmb_CodeType_desc.place_forget()
    return 0

#初始化C语言库选择框状态

def Contents_ScrolledText_Set():
    global FileName
    global FileSize
    FileSize = os.path.getsize(FileName)
    contents.config(state=NORMAL) #打开文本输入框编辑状态
    contents.delete(1.0, END)
    contents.insert(1.0, FileName)  #也是从文本头插入
    contents.insert(END, '\n文件大小=%d字节'%FileSize)   #也是从文本尾插入
    contents.config(state=DISABLED) #关闭文本输入框编辑状态
    return FileName

def OpenFile():
    global FileName
    global FileSize
    FileName_t  = tkinter.filedialog.askopenfilename()    #取消后是返回一个空字符串
    if not FileName_t:
        FileSize_t = 0
        #print("未选择文件")
    else:
        FileName = FileName_t
        Contents_ScrolledText_Set()
        CRCClac()
        OTACanMoto()
    return FileName

def Dragged_file(files):
    global FileName
    global FileSize
    #print(len(files))  #len()返回成员个数
    #str(btyes, encoding = "gbk") #字符数组转字符串 
    FileName = str(files[0], encoding = "gbk")  #windows默认编码为gbk，win10不知道是不是改成utf-8了

    #print(type(files[0])) #type()打印对象类型
    Contents_ScrolledText_Set()
    return FileName

def Print_Radiobutton():
    #print("CalcTypeg=%d:" % CalcType.get(), end="")
    #if 1 == CalcType.get():
        #print("计算字符串CRC  ", end="")
        #print("%s编码" % cmb_CodeType.get())
    #else:
        #print("计算文件CRC  ")
    InitCRCCalcParam()
    return 0

def CheckSumAdd08Anti(buffer, length):
    addsum08 = 0x0000
    
    for uc in range(length):
        addsum08 = addsum08 + buffer[uc] 
    addsum08 = ~addsum08
    return addsum08

def CrcCalc16_XMODEM(Buffer, Len):
    wCRCin = 0x0000
    wCPoly = 0x1021

    for j in range(Len):
        char = Buffer[j]
        #print('j=%d char=%c' % (j, char))
        wCRCin ^= ((char << 8) & 0xffff)
        for i in range(8):
            if(wCRCin & 0x8000):
                wCRCin = ((wCRCin << 1) ^ wCPoly) & 0xffff
            else:
                wCRCin = (wCRCin << 1) & 0xffff
    return wCRCin

def LinkCrcCalcFunc(buffer, Len):
    if 'CRC16' == cmb_CRCType.get():
        if 0 == CLibEnable.get():   #如果不启用dll动态库
            #CRC = (CrcCalc16_XMODEM(buffer, Len) & 0xffff)
            CRC = (CheckSumAdd08Anti(buffer, Len) & 0xffff)
        else:
            CRC = (CrcCalcDLL.GetCRC16(buffer,Len) & 0xffff)
        CRC_value.set("0x%04X" % CRC)
    return CRC


def CRCClac():
    global CanCrc
    global FileName
    global FileSize
    CRC = 0x0
    if 1 == CalcType.get(): #计算字符串
        if 'UTF8' == cmb_CodeType.get():
            buffer = contents.get(0.0, END).encode('utf-8')
        if 'GBK' == cmb_CodeType.get():
            buffer = contents.get(0.0, END).encode('gbk')
        FileSize = len(buffer)-1
        CRC=LinkCrcCalcFunc(buffer,FileSize)
    else:   #计算文件
        if not FileName:
            tkinter.messagebox.showwarning('警告','亲，请先选择文件~')
        elif 0 == FileSize:
            tkinter.messagebox.showwarning('警告','亲，请正确选择文件~')
        else:
            contents.config(state=NORMAL) #打开文本输入框编辑状态
            time = datetime.datetime.now().strftime('%T')
            contents.insert(END, '\n%s 开始计算CRC'%time)   #也是从文本尾插入
            with open(FileName, 'rb') as file:
                buffer = file.read(FileSize)
                CRC=LinkCrcCalcFunc(buffer,FileSize)
            file.close()    
            time = datetime.datetime.now().strftime('%T')
            contents.insert(END, '\n%s 计算完成CRC=0x%X'%(time,CRC))   #也是从文本尾插入
            contents.update()
            contents.see(END)
            contents.config(state=DISABLED) #关闭文本输入框编辑状态
        
    #print("CRC=0x%08X" % CRC)
    CanCrc = CRC
    return CRC

def SendCanData(bufer):
    global CANINDEX
    global so
    # 发送参数定义
    send_msg = VCI_CAN_OBJ(ID = 1, DataLen = 8, ExternFlag = 0, RemoteFlag = 0, SendType = 0, TimeFlag = 1, TimeStamp = 0x12345678)
    send_msg.Data[0] = bufer[0]
    send_msg.Data[1] = bufer[1]
    send_msg.Data[2] = bufer[2]
    send_msg.Data[3] = bufer[3]
    send_msg.Data[4] = bufer[4]
    send_msg.Data[5] = bufer[5]
    send_msg.Data[6] = bufer[6]
    send_msg.Data[7] = bufer[7]
    # 发送函数
    ret = so.VCI_Transmit (4, 0, CANINDEX, byref(send_msg), 1)
    return

def SendCanDataCmd(bufer,MotoId,Cmd):
    global CANINDEX
    global so
    # 发送参数定义
    send_msg = VCI_CAN_OBJ(DataLen = 8, ExternFlag = 0, RemoteFlag = 0, SendType = 0, TimeFlag = 1, TimeStamp = 0x12345678)
    send_msg.ID = MotoId | (Cmd & 0xF0)
    send_msg.Data[0] = bufer[0]
    send_msg.Data[1] = bufer[1]
    send_msg.Data[2] = bufer[2]
    send_msg.Data[3] = bufer[3]
    send_msg.Data[4] = bufer[4]
    send_msg.Data[5] = bufer[5]
    send_msg.Data[6] = bufer[6]
    send_msg.Data[7] = bufer[7]
    # 发送函数
    #if Cmd == 0xA0:
    print("%d %d %d %d - %02x %02x %02x %02x %02x %02x %02x %02x"%(send_msg.ID,MotoId,Cmd,(Cmd & 0xF),send_msg.Data[0],send_msg.Data[1],send_msg.Data[2],send_msg.Data[3],send_msg.Data[4],send_msg.Data[5],send_msg.Data[6],send_msg.Data[7]))
    ret = so.VCI_Transmit (4, 0, CANINDEX, byref(send_msg), 1)
    return

def OTACanMoto():
    global CANINDEX
    global CanId
    global so
    global CanCrc
    global FileName
    global FileSize
    if not FileName:
        tkinter.messagebox.showwarning('警告','亲，请先选择文件~')
    elif 0 == FileSize:
        tkinter.messagebox.showwarning('警告','亲，请正确选择文件~')
    else:
        contents.config(state=NORMAL) #打开文本输入框编辑状态
        timestr = datetime.datetime.now().strftime('%T')
        contents.insert(END, '\n%s 电机固件更新开始'%timestr)   #也是从文本尾插入
        contents.update()
        so = ctypes.windll.LoadLibrary("./ControlCAN.dll")
        # 打开设备
        #print ("opendevice result:", so.VCI_OpenDevice(4, 0, 0))
        so.VCI_OpenDevice(4, 0, 0)

        # 初始化参数设置
        init_config = VCI_INIT_CONFIG(AccCode = 0, AccMask = 0xffffffff, Timing0=0x00, Timing1=0x1C)

        # 初始化can通道
        #print ("initcan result:", so.VCI_InitCAN(4, 0, 0, pointer(init_config)))
        #print ("initcan result:", so.VCI_InitCAN(4, 0, 1, pointer(init_config)))
        so.VCI_InitCAN(4, 0, 0, pointer(init_config))
        so.VCI_InitCAN(4, 0, 1, pointer(init_config))

        # 启动can通道
        #print ("startcan result:", so.VCI_StartCAN (4, 0, 0))
        #print ("startcan result:", so.VCI_StartCAN (4, 0, 1))
        so.VCI_StartCAN (4, 0, 0)
        so.VCI_StartCAN (4, 0, 1)
        # 接收参数定义
        recv_msg = VCI_CAN_OBJ()
        buffer = [0x01,0x09,0x00,0x00,0x00,0x00,0x00,0x00] # 获取电机版本号
        #buffer = [0x01,0x7d,0x00,0x00,0x00,0x00,0x00,0x00] # 获取电机版本号
        buffer_index = 0xffffffff
        for i in range(1,14):
            buffer[0] = i
            #print("获取%d号电机版本号"%i)
            SendCanData(buffer) # 发送获取版本信息数据
            print("send:%d %d %d %d %d %d %d %d "%(buffer[0],buffer[1],buffer[2],buffer[3],buffer[4],buffer[5],buffer[6],buffer[7]))
            recvnum = so.VCI_Receive(4, 0, CANINDEX, pointer(recv_msg), 1, 200) # 200毫秒超时接收
            print(recvnum, recv_msg.ID, recv_msg.Data[0],recv_msg.Data[1],recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5],recv_msg.Data[6],recv_msg.Data[7])
            #if recvnum > 0 and recvnum != 0xffffffff: # 读取到返回帧，并且没有失败
            if recvnum == 1 and recv_msg.Data[1] == 9:
                CanId=recv_msg.Data[0]
                #print(recvnum, recv_msg.ID, recv_msg.Data[0],recv_msg.Data[1],recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5],recv_msg.Data[6],recv_msg.Data[7])
                timestr = datetime.datetime.now().strftime('%T')
                contents.insert(END, '\n%s 获取到CAN ID=%d电机的版本号:0x%02x%02x%02x%02x'%(timestr,CanId,recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5]))   #也是从文本尾插入
                #contents.insert(END, '\n%s 获取到CAN ID=%d 电机的版本号'%(time,CanId))   #也是从文本尾插入
                contents.update()
                contents.see(END)
                #print("获取电机版本号break")
                break
            #print("获取%d号电机版本号"%i)
            SendCanData(buffer) # 发送获取版本信息数据
            recvnum = so.VCI_Receive(4, 0, CANINDEX, pointer(recv_msg), 1, 200) # 200毫秒超时接收
            #print(recvnum, recv_msg.ID, recv_msg.Data[0],recv_msg.Data[1],recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5],recv_msg.Data[6],recv_msg.Data[7])
            #if recvnum > 0 and recvnum != 0xffffffff: # 读取到返回帧，并且没有失败
            if recvnum == 1 and recv_msg.Data[1] == 9:
                CanId=recv_msg.Data[0]
                #print(recvnum, recv_msg.ID, recv_msg.Data[0],recv_msg.Data[1],recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5],recv_msg.Data[6],recv_msg.Data[7])
                timestr = datetime.datetime.now().strftime('%T')
                contents.insert(END, '\n%s 获取到CAN ID=%d电机的版本号:0x%02x%02x%02x%02x'%(timestr,CanId,recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5]))   #也是从文本尾插入
                #contents.insert(END, '\n%s 获取到CAN ID=%d 电机的版本号'%(time,CanId))   #也是从文本尾插入
                contents.update()
                contents.see(END)
                #print("获取电机版本号break")
                break            

        import time
        time.sleep(0.1) # 延时100ms            
        buffer[0] = CanId
        buffer[1] = 0x16 # 禁用电机
        while True:
            SendCanData(buffer) # 发送禁用电机命令
            print("send:%d %d %d %d %d %d %d %d "%(buffer[0],buffer[1],buffer[2],buffer[3],buffer[4],buffer[5],buffer[6],buffer[7]))
            recvnum = so.VCI_Receive(4, 0, CANINDEX, pointer(recv_msg), 1, 100) # 100毫秒超时接收
            print(recvnum, recv_msg.ID, recv_msg.Data[0],recv_msg.Data[1],recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5],recv_msg.Data[6],recv_msg.Data[7])
            if recvnum == 1 and recv_msg.Data[1] == 0x16:
                timestr = datetime.datetime.now().strftime('%T')
                contents.insert(END, '\n%s 禁用电机'%timestr)   #也是从文本尾插入
                contents.update()
                contents.see(END)
                #print("禁用电机break")
                break
            else:
                import time
                time.sleep(0.1) # 延时100ms
        import time
        time.sleep(0.1) # 延时100ms        
        buffer[0] = CanId
        buffer[1] = 0x7e # 电机升级类型
        buffer[3] = 0x00 # 升级电机驱动，非BOOT
        while True:
            print("电机升级类型")
            SendCanData(buffer) # 发送禁用电机命令
            print("send:%d %d %d %d %d %d %d %d "%(buffer[0],buffer[1],buffer[2],buffer[3],buffer[4],buffer[5],buffer[6],buffer[7]))
            recvnum = so.VCI_Receive(4, 0, CANINDEX, pointer(recv_msg), 1, 100) # 100毫秒超时接收
            #print(recvnum, recv_msg.ID, recv_msg.Data[0],recv_msg.Data[1],recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5],recv_msg.Data[6],recv_msg.Data[7])
            if recvnum == 1 and recv_msg.Data[1] == 0x7e:
                time = datetime.datetime.now().strftime('%T')
                contents.insert(END, '\n%s 设置电机升级类型'%time)   #也是从文本尾插入
                contents.update()
                contents.see(END)
                print("设置电机升级类型break")
                break
            else:
                import time
                time.sleep(0.1) # 延时100ms
        FileWordNum = FileSize >> 2
        can_data = FileWordNum.to_bytes(4, byteorder='big', signed=False)
        can_crc = CanCrc.to_bytes(4, byteorder='big', signed=False)
        buffer[0] = can_data[0]
        buffer[1] = can_data[1]
        buffer[2] = can_data[2]
        buffer[3] = can_data[3]
        buffer[4] = can_crc[0]
        buffer[5] = can_crc[1]
        buffer[6] = can_crc[2]
        buffer[7] = can_crc[3]
        print(FileSize,CanCrc,buffer[0],buffer[1],buffer[2],buffer[3],buffer[4],buffer[5],buffer[6],buffer[7])
        while True:
            SendCanDataCmd(buffer,CanId,0xA0) # CAN1_SEND_UPDATE_INIT     0xA0
            print("send:%d %d %d %d %d %d %d %d "%(buffer[0],buffer[1],buffer[2],buffer[3],buffer[4],buffer[5],buffer[6],buffer[7]))
            recvnum = so.VCI_Receive(4, 0, CANINDEX, pointer(recv_msg), 1, 100) # 100毫秒超时接收
            print(recvnum, recv_msg.ID, recv_msg.Data[0],recv_msg.Data[1],recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5],recv_msg.Data[6],recv_msg.Data[7])
            if recvnum == 1 and (recv_msg.ID & 0xFF0) == 0xB0:  # CAN1_RECV_EXPET_PACK_NO   0xB0
                temp_buf = [0x00,0x00,0x00,0x00]
                temp_buf[0] = recv_msg.Data[0]
                temp_buf[1] = recv_msg.Data[1]
                temp_buf[2] = recv_msg.Data[2]
                temp_buf[3] = recv_msg.Data[3]
                buffer_index = int.from_bytes(temp_buf,byteorder='big',signed=True)
                time = datetime.datetime.now().strftime('%T')
                contents.insert(END, '\n%s 设置电机升级字节总数和校验和'%time)   #也是从文本尾插入
                contents.update()
                contents.see(END)
                print("设置电机升级字节总数和校验和break,buffer_index = %d"%buffer_index)
                break
            else:
                import time
                time.sleep(0.1) # 延时100ms

        with open(FileName, 'rb') as file:
            #buffer = file.read(FileSize)
            updata_ok = 0
            loop_num = 0
            for i in range(0,FileSize,4):
                bufferbin = file.read(4) #每次输出4个字节
                index_byte = buffer_index.to_bytes(4, byteorder='big', signed=False)
                buffer[0] = index_byte[0]
                buffer[1] = index_byte[1]
                buffer[2] = index_byte[2]
                buffer[3] = index_byte[3]
                buffer[4] = bufferbin[3]
                buffer[5] = bufferbin[2]
                buffer[6] = bufferbin[1]
                buffer[7] = bufferbin[0]
                print("---%d--"%i)
                while True:
                    SendCanDataCmd(buffer,CanId,0xC0) # CAN1_SEND_UPDATE_INIT     0xC0
                    print("send:%d %d %d %d %d %d %d %d "%(buffer[0],buffer[1],buffer[2],buffer[3],buffer[4],buffer[5],buffer[6],buffer[7]))
                    recvnum = so.VCI_Receive(4, 0, CANINDEX, pointer(recv_msg), 1, 100) # 100毫秒超时接收
                    #if i > 125770:
                    print("%d %d - %02x %02x %02x %02x %02x %02x %02x %02x"%(recvnum, recv_msg.ID, recv_msg.Data[0],recv_msg.Data[1],recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5],recv_msg.Data[6],recv_msg.Data[7]))
                    if recvnum == 1 and (recv_msg.ID & 0xFF0) == 0xB0:  # CAN1_RECV_EXPET_PACK_NO   0xB0
                        temp_buf = [255,255,255,255]
                        temp_buf[0] = recv_msg.Data[0]
                        temp_buf[1] = recv_msg.Data[1]
                        temp_buf[2] = recv_msg.Data[2]
                        temp_buf[3] = recv_msg.Data[3]                        
                        buffer_indexcur = int.from_bytes(temp_buf,byteorder='big',signed=True)
                        if buffer_indexcur ==  buffer_index+1:
                            loop_num = loop_num + 1
                            if loop_num > 499:
                                time = datetime.datetime.now().strftime('%T')
                                contents.insert(END, '\n%s 电机升级第%d帧'%(time,buffer_index))   #也是从文本尾插入
                                contents.update()
                                contents.see(END)
                                print("电机升级第%d帧 %d"%(buffer_index,i))
                                loop_num = 0
                            buffer_index = buffer_indexcur
                            break
                    elif recvnum == 1 and (recv_msg.ID & 0xFF0) == 0xD0:  # CAN1_RECV_PACK_TOTAL      0xD0
                        temp_buf = [0x00,0x00,0x00,0x00]
                        temp_buf[0] = recv_msg.Data[0]
                        temp_buf[1] = recv_msg.Data[1]
                        temp_buf[2] = recv_msg.Data[2]
                        temp_buf[3] = recv_msg.Data[3]
                        buffer_total = int.from_bytes(temp_buf,byteorder='big',signed=True)
                        temp_buf[0] = recv_msg.Data[4]
                        temp_buf[1] = recv_msg.Data[5]
                        temp_buf[2] = recv_msg.Data[6]
                        temp_buf[3] = recv_msg.Data[7]
                        buffer_checksum = int.from_bytes(temp_buf,byteorder='big',signed=True)
                        time = datetime.datetime.now().strftime('%T')
                        contents.insert(END, '\n%s 电机升级最后一帧,电机反馈文件总长%d字节，电机反馈校验和%d'%(time,buffer_total,buffer_checksum))   #也是从文本尾插入
                        contents.update()
                        contents.see(END)
                        print("电机升级最后一帧,电机反馈文件总长%d字节，电机反馈校验和%d"%(buffer_total,buffer_checksum))
                        updata_ok = 1
                        break
                    else:
                        import time
                        time.sleep(0.01) # 延时100ms
                if updata_ok == 1:
                    print("电机升级结束")
                    break
            print("电机升级结束--%d  FileSize=%d buffer_index = %d"%(i,FileSize,buffer_index))
        time = datetime.datetime.now().strftime('%T')
        contents.insert(END, '\n%s 电机等待重启'%time)   #也是从文本尾插入
        contents.update()
        contents.see(END)
        print("电机等待重启")
        file.close()
        import time
        time.sleep(2) # 延时2s 

        buffer[0] = CanId
        buffer[1] = 0x7d # 电机重启命令
        buffer[2] = 0x00
        buffer[3] = 0x00
        buffer[4] = 0x00
        buffer[5] = 0x00
        buffer[6] = 0x00
        buffer[7] = 0x00
        SendCanData(buffer)
        import time
        time.sleep(0.2) # 延时200ms
        SendCanData(buffer)
        import time
        time.sleep(0.2) # 延时200ms

        time = datetime.datetime.now().strftime('%T')
        contents.insert(END, '\n%s 电机升级结束,重启中'%time)   #也是从文本尾插入
        contents.update()
        contents.see(END)
        print("电机升级结束,重启中")
        
        break_flag = 0
        buffer = [0x01,0x09,0x00,0x00,0x00,0x00,0x00,0x00] # 获取电机版本号
        buffer_index = 0xffffffff
        for i in range(1,14):
            buffer[0] = i
            print("获取%d号电机版本号"%i)
            for j in range(10):
                SendCanData(buffer) # 发送获取版本信息数据
                print("send:%d %d %d %d %d %d %d %d "%(buffer[0],buffer[1],buffer[2],buffer[3],buffer[4],buffer[5],buffer[6],buffer[7]))
                recvnum = so.VCI_Receive(4, 0, CANINDEX, pointer(recv_msg), 1, 200) # 200毫秒超时接收
                print(recvnum, recv_msg.ID, recv_msg.Data[0],recv_msg.Data[1],recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5],recv_msg.Data[6],recv_msg.Data[7])
                #if recvnum > 0 and recvnum != 0xffffffff: # 读取到返回帧，并且没有失败
                if recvnum == 1 and recv_msg.Data[1] == 9:
                    CanId=recv_msg.Data[0]
                    #print(recvnum, recv_msg.ID, recv_msg.Data[0],recv_msg.Data[1],recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5],recv_msg.Data[6],recv_msg.Data[7])
                    timestr = datetime.datetime.now().strftime('%T')
                    contents.insert(END, '\n%s 获取到CAN ID=%d电机的更新固件后版本号:0x%02x%02x%02x%02x'%(timestr,CanId,recv_msg.Data[2],recv_msg.Data[3],recv_msg.Data[4],recv_msg.Data[5]))   #也是从文本尾插入
                    #contents.insert(END, '\n%s 获取到CAN ID=%d 电机的更新固件后版本号'%(time,CanId))   #也是从文本尾插入
                    contents.update()
                    contents.see(END)
                    print("获取电机版本号break")
                    break_flag = 1
                    break
            if break_flag == 1:
                break
              
        timestr = datetime.datetime.now().strftime('%T')
        contents.insert(END, '\n%s 电机固件更新完成'%timestr)   #也是从文本尾插入
        contents.update()
        contents.see(END)
        contents.config(state=DISABLED) #关闭文本输入框编辑状态
    return

top = Tk()
top.title("电机OTA工具")
#top.geometry("322x234")
top.geometry("499x480")

CanCrc=0
CanId=1
FileName=''
FileSize=0
CrcCalcDLL=None
DllFileName = 'CrcCalc.dll'
#SysBit=''
MyPath = './'

so = ctypes.windll.LoadLibrary("./ControlCAN.dll")
#CRC计算按钮

ClacCrc = Button()
ClacCrc.config(text='CRC计算', command=CRCClac)
#ClacCrc.place(x=2, y=26, width=60, height=24)


#下拉菜单
cmb_CRCType = ttk.Combobox(state="readonly")
#cmb_CRCType.place(x=64, y=26, width=64, height=24)
cmb_CRCType['value'] = ('CRC16','CRC32')
cmb_CRCType.current(0)
#Label(text="=").place(x=130, y=26, width=16, height=24)

#CRC显示框
CRC_value = StringVar()
#CRC_value.set('123456789')
CRCVal = Entry(textvariable = CRC_value)
#CRCVal.place(x=146, y=26, width=90, height=24)
#CRCVal.config(state=DISABLED) #关闭文本输入框编辑状态


#字符串输入框，文件路径输入框
#CRCStr = StringVar()
#CRCStr.set('请输入字符串') 
contents = ScrolledText()
#contents.insert(0.0,'请输入字符串')
contents.place(x=2, y=52, width=469, height=419)


#计算类型选择单选
CalcType = IntVar()
CalcType.set(2)
#radio_Str = Radiobutton(text="字符串",anchor="w", variable=CalcType, value=1, command=Print_Radiobutton)
radio_File = Radiobutton(text="文件",anchor="w", variable=CalcType, value=2, command=Print_Radiobutton)
#radio_Str.place(x=0, y=0, width=60, height=24)
#radio_File.place(x=60*1, y=0, width=60, height=24)

#编码选择下拉框
cmb_CodeType = ttk.Combobox(state="readonly")
cmb_CodeType.place(x=60*2, y=0, width=60, height=24)
cmb_CodeType['value'] = ('GBK','UTF8')
cmb_CodeType.current(0)
cmb_CodeType_desc = Label(text="(字符串编码格式)")
cmb_CodeType_desc.place(x=60*3, y=0, width=96, height=24)

#打开文件按钮
LoadFile = Button()
LoadFile.config(text='打开.bin文件', command=OpenFile)

#初始化编码选择和打开文件按钮
InitCRCCalcParam()


#采用内置函数还是C动态库
CLibEnable = IntVar()
CLibEnable.set(0)
#CLibCheck = Checkbutton(top, text = "使用C库", variable = CLibEnable, onvalue=1, offvalue=0, command=DealDLL)
#CLibCheck.place(x=236, y=26, width=90, height=24)
#初始化C库选择
#InitCLibEnable()

#拖放文件函数
windnd.hook_dropfiles(top, func=Dragged_file)




mainloop()
