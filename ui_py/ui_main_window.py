#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os

import sys
from idlelib import query

from PyQt5 import QtWidgets
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

import handle_excel
from ui.main_window import Ui_MainWindow

# def ReceiveData(name,_self):
#     while _self.m_bIsRunning:
from usbcan_winpy import VCI_CAN_OBJ, pointer, ConnectControlCan, StopControlCan, StartControlCan, DisConnectControlCan
from ctypes import *
import xlwt


def get_data_str(str_data, len):
    retStr = ""
    for i in range(len):
        value = str_data[i] & 0xff
        retStr = retStr + "  " + str('%02x' % (value))
    return retStr


_READ = 0
# 对象字典
Direct_form = [
    [0x2000, 0x01, _READ, "版本", ],  # g_sGlobalStatusParam.m_nVersion), 4},
    [0x2000, 0x02, _READ, "设备类型", ],  # g_sGlobalFuncParam.m_eDeviceType), 4},
    [0x2000, 0x03, _READ, "温度", ],  # g_sGlobalStatusParam.m_fTemperature), 4},
    [0x2000, 0x04, _READ, "状态机", ],  # g_sGlobalStatusParam.m_eCurrentStatus), 4},

    [0x2000, 0x05, _READ, "错误码", ],  # g_sGlobalStatusParam.m_nInterErrCode), 4},

    [0x2001, 0x01, _READ, "编码器3速度", ],  # g_sGlobalStatusParam.m_sEncodeInfor[3].m_nCurrentSpeed), 4},
    [0x2001, 0x02, _READ, "编码器3速度等级", ],
    # g_sGlobalStatusParam.m_sEncodeInfor[3].m_nCurrentSpeedLevel), 4},
    [0x2001, 0x03, _READ, "编码器4速度", ],  # g_sGlobalStatusParam.m_sEncodeInfor[4].m_nCurrentSpeed), 4},
    [0x2001, 0x04, _READ, "编码器4速度等级", ],
    # g_sGlobalStatusParam.m_sEncodeInfor[4].m_nCurrentSpeedLevel), 4},

    [0x2002, 0x01, _READ, "机器人速度", ],  # g_sGlobalStatusParam.m_sRobotBasicnfo.m_nCurrentSpeed), 4},
    [0x2002, 0x02, _READ, "机器人速度等级", ],  # g_sGlobalStatusParam.m_sRobotBasicnfo.m_nSpeedLevle), 4},
    [0x2002, 0x03, _READ, "左右轮差速", ],  # g_sGlobalStatusParam.m_sRobotBasicnfo.m_nSpeedDiff), 4},
    [0x2002, 0x04, _READ, "左右轮差速等级", ],  # g_sGlobalStatusParam.m_sRobotBasicnfo.m_nSpeedDiffLevle), 4},

    [0x2002, 0x05, _READ, "机器人方向", ],  # g_sGlobalStatusParam.m_sRobotBasicnfo.m_nDirection), 4},
]

ExcelFILENAME = "./ObjectDirect.xls"


class Main_Form(QtWidgets.QMainWindow, Ui_MainWindow):
    signal_TestControl = pyqtSignal(int)

    def __init__(self):
        super(Main_Form, self).__init__()
        self.setupUi(self)
        self.m_bIsConnected = False
        self.m_bIsStarted = False
        self.m_sControlCan = ''
        self.m_nFrameCounter = 0
        self.m_nNodeID = 20

        self.m_bIsupload = False  # 是否上传机器人信息
        pix = QPixmap(":/images/shut.png")
        self.setWindowIcon(QIcon(pix))

        # 创建两个线程
        # try:
        #     _thread.start_new_thread(ReceiveData, ("Thread-1", self,))
        #     pass
        # except Exception as e:
        #     print("Error: 无法启动线程" + str(e))

        # 定时接收数据
        self.timer_recv = QTimer()  # 初始化定时器
        self.timer_recv.timeout.connect(self.on_timeout_recv)
        self.timer_recv.start(1)
        # 更新变量值
        self.timer_update = QTimer()  # 初始化定时器
        self.timer_update.timeout.connect(self.on_timer_update)

        # self.actionGIS_2.triggered.connect(self.OpenGis)
        # self.action_setup.triggered.connect(self.OpenSetup)
        self.checkBox_Upload.clicked.connect(self.on_upload_check)

        self.pushButton_Connect.clicked.connect(self.on_connected)
        self.pushButton_start.clicked.connect(self.on_started)
        self.pushButton_clear.clicked.connect(self.on_clear_tablewidge)
        self.tableWidget_Frame.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget_Frame.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tableWidget_Frame.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tableWidget_Frame.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tableWidget_Frame.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tableWidget_Frame.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        for i in range(200):
            self.tableWidget_Info.insertRow(0)  # 插入到第一列

        reg = QRegExp('[a-zA-z0-9]+$')
        validator = QRegExpValidator(self)
        validator.setRegExp(reg)
        self.lineEdit_UploadPeriod.setValidator(validator)
        self.lineEdit_filter_min.setValidator(validator)
        self.lineEdit_filter_max.setValidator(validator)

        handle_excel.read_excel(ExcelFILENAME,self.tableWidget_Info)

        for i in range(self.tableWidget_Info.columnCount()):
            print(self.tableWidget_Info.cellWidget(0, i))

        self.tableWidget_Info.itemClicked.connect(self.outSelect)  # 单击获取单元格中的内容

        # self.pushButton_SetPath.clicked.connect(self.setBrowerPath)
        self.pushButton_save.clicked.connect(self.savefile)
        self.pushButton_update.clicked.connect(self.on_updateTable)

    def on_updateTable(self):
        handle_excel.read_excel(ExcelFILENAME, self.tableWidget_Info)

    # def setBrowerPath(self):  # 选择文件夹进行存储
    #     download_path = QtWidgets.QFileDialog.getExistingDirectory(None, "浏览", "/home")
    #     self.lineEdit_fileName.setText(download_path)

    def savefile(self):

        if handle_excel.saveExcelFile(ExcelFILENAME, self.tableWidget_Info):
            self.statusbar.showMessage("save file successfully",3000)
        else:
            self.statusbar.showMessage("save file faied", 3000)
    def outSelect(self, Item=None):
        if Item == None:
            return
        print(Item.text())

    def on_clear_tablewidge(self):
        for i in range(len(Direct_form)):
            self.tableWidget_Info.setItem(i, 5, QTableWidgetItem(str("")))

    # 是否上传复选框
    def on_upload_check(self, check):
        self.m_bIsupload = check
        if self.m_bIsupload:
            period = self.lineEdit_UploadPeriod.text()
            if period != "":
                self.timer_update.start(int(period, 10))
        else:
            self.timer_update.stop()

    # 更新信息定时器
    def on_timer_update(self):
        send_msg = VCI_CAN_OBJ(ID=0x64, DataLen=8, ExternFlag=0, RemoteFlag=0, SendType=0, TimeFlag=1,
                               TimeStamp=0x12345678)
        send_msg.ID = 0x600 + self.m_nNodeID

        send_msg.Data[0] = 0x40
        send_msg.Data[1] = 0
        send_msg.Data[2] = 0
        send_msg.Data[3] = 0
        send_msg.Data[4] = 0
        send_msg.Data[5] = 0
        send_msg.Data[6] = 0
        send_msg.Data[7] = 0
        if self.m_bIsStarted:
            for i in range(len(Direct_form)):
                value1 = Direct_form[i][0] & 0xff
                send_msg.Data[1] = value1

                value2 = Direct_form[i][0] // 0xff
                send_msg.Data[2] = value2

                value3 = Direct_form[i][1]
                send_msg.Data[3] = value3

                self.insert_frame(send_msg, False)
                ret = self.m_sControlCan.VCI_Transmit(4, 0, 0, byref(send_msg), 1)

    def on_timeout_recv(self):
        # 接收参数定义
        if self.m_bIsStarted:
            recv_msg = VCI_CAN_OBJ()
            recvnum = self.m_sControlCan.VCI_Receive(4, 0, 0, pointer(recv_msg), 1, 0)
            if recvnum != 0:
                print(recvnum, '%#x' % (recv_msg.ID), recv_msg.Data[0], recv_msg.Data[1], recv_msg.Data[2],
                      recv_msg.Data[3], recv_msg.Data[4], recv_msg.Data[5], recv_msg.Data[6], recv_msg.Data[7])
                self.insert_frame(recv_msg, True)  # 插入帧列表
                if recv_msg.ID > 0x580:
                    self.handle_sdo(recv_msg)
            elif recvnum == 0xFF:
                pass
        # self.textBrowser_RobotInfor.clear()
        # self.textBrowser_RobotInfor.insertPlainText(str(sdiskio))
        # self.textBrowser_RobotInfor.insertPlainText(str("\n"))

    def filt_frame(self, recv_msg):
        filter_min = self.lineEdit_filter_min.text()
        filter_max = self.lineEdit_filter_max.text()
        if (filter_min == ""):
            filter_min = 0
        if (filter_max == ""):
            filter_max = 255

        if (recv_msg.ID < int(filter_min)):
            return False
        if (recv_msg.ID > int(filter_max)):
            return False
        return True

    # 插入数据帧
    def insert_frame(self, recv_msg, isUp):
        # 调用setTextAlignment()方法，设置文本居中显示
        if self.filt_frame(recv_msg) != True:
            return

        self.tableWidget_Frame.insertRow(0)  # 插入到第一列
        if self.tableWidget_Frame.rowCount() > 200:
            self.tableWidget_Frame.removeRow(200)
        self.m_nFrameCounter = self.m_nFrameCounter + 1

        self.tableWidget_Frame.setItem(0, 0, QTableWidgetItem(str(self.m_nFrameCounter)))
        self.tableWidget_Frame.setItem(0, 1, QTableWidgetItem(str(recv_msg.TimeStamp)))
        str_show = ""
        if isUp:
            str_show = "接收"
        else:
            str_show = "发送"
        self.tableWidget_Frame.setItem(0, 2, QTableWidgetItem(str(str_show)))
        self.tableWidget_Frame.setItem(0, 3, QTableWidgetItem(str('%#x' % (recv_msg.ID))))

        self.tableWidget_Frame.setItem(0, 4, QTableWidgetItem(str(recv_msg.DataLen)))

        # 位置为第0行，第0列，后面为QTableWidgetItem对象，可以为str类型，int类型

        strData = get_data_str(recv_msg.Data, recv_msg.DataLen)
        self.tableWidget_Frame.setItem(0, 5, QTableWidgetItem(str(strData)))

    def find_index(self, index, subindex):
        for i in range(len(Direct_form)):
            if Direct_form[i][0] == index and Direct_form[i][1] == subindex:
                return i
        return 0xFF

    def handle_sdo(self, recv_msg):
        node_id = recv_msg.ID - 0x580
        if (node_id == self.m_nNodeID):
            value1 = recv_msg.Data[1] & 0xff
            value2 = recv_msg.Data[2] & 0xff
            index = value2 * 256 + value1
            subindex = recv_msg.Data[3] & 0xff
            dictIndex = self.find_index(index, subindex)
            if dictIndex != 0xff:
                self.tableWidget_Info.setItem(dictIndex, 0, QTableWidgetItem(str(Direct_form[dictIndex][3])))
                self.tableWidget_Info.setItem(dictIndex, 1, QTableWidgetItem(str(1)))
                self.tableWidget_Info.setItem(dictIndex, 2, QTableWidgetItem(str('%#x' % (index))))
                self.tableWidget_Info.setItem(dictIndex, 3, QTableWidgetItem(str('%#x' % (subindex))))
                value = 0
                for i in range(4):
                    value = value * 256
                    tmp_value = recv_msg.Data[7 - i] & 0xff
                    value = value + tmp_value
                self.tableWidget_Info.setItem(dictIndex, 5, QTableWidgetItem(str(value)))
            else:
                print("not find " + str(index) + " " + str(subindex))

    def on_connected(self):
        if self.m_bIsConnected:
            DisConnectControlCan(self.m_sControlCan)
            self.m_bIsConnected = False
            self.pushButton_Connect.setText("Connect")
            self.statusbar.showMessage("disconnected...", 3000)
        else:
            self.m_sControlCan, iRet01, iRet02 = ConnectControlCan()
            if iRet01 == 1 and iRet02 == 1:
                self.m_bIsConnected = True
                self.pushButton_Connect.setText("Disconnect")
                self.statusbar.showMessage("connected...", 3000)

    def on_started(self):
        if self.m_bIsConnected:
            if self.m_bIsStarted:
                iRet = StopControlCan(self.m_sControlCan, 0)
                if iRet == 1:
                    self.pushButton_start.setText("Start")
                    self.m_bIsStarted = False
            else:
                iRet = StartControlCan(self.m_sControlCan, 0)
                if iRet == 1:
                    self.m_bIsStarted = True
                    self.pushButton_start.setText("Stop")

    def on_TestPrepare(self):
        pass

    def closeEvent(self, event):  # 函数名固定不可变
        sys.exit(0)  # 状态码


if __name__ == "__main__":
    app = QApplication(sys.argv)
    sys.exit(app.exec_())
