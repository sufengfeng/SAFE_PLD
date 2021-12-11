#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
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

def HandlUpgradeCmd():

    pass