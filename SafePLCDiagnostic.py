#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow

from ui_py.ui_main_window import Main_Form
# import pymysql
# conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd='su35102105',db='mysql')
# cursor = conn.cursor ()
# cursor.execute ("SELECT VERSION()")
# row = cursor.fetchone ()
# print("MySQL server version:", row[0])
# cursor.close ()
# conn.close ()


if __name__ == '__main__':

    app = QApplication(sys.argv)
    app.setApplicationName("PyQt MianWindow")
    app.setWindowIcon(QIcon("./images/icon.png"))

    MainWindow = Main_Form()
    MainWindow.show()
    sys.exit(app.exec_())



