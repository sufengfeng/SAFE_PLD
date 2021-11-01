import xlrd
import xlwt
from PyQt5.QtWidgets import *


def read_excel(fileName,tableWidget3):
    # 打开文件
    workbook = xlrd.open_workbook(fileName)
    # 获取所有sheet
    # sheet2_name = workbook.sheet_names()[0]
    # 根据sheet索引或者名称获取sheet内容
    sheet1 = workbook.sheet_by_index(0)  # sheet索引从0开始
    # 获取第三列内容 品名
    rowslist = sheet1.row_values(0)
    # 获取整行和整列的值（数组）
    for i in range(len(rowslist)):
        colslist = sheet1.col_values(i)
        for j in range(len(colslist)):
            valType = type(colslist[j])
            if valType == float:
                val = int(colslist[j])
                tableWidget3.setItem(j, i, QTableWidgetItem(str(val)))
            elif valType == str:
                tableWidget3.setItem(j, i, QTableWidgetItem(str(colslist[j])))
            else:
                print("not recongise")



def saveExcelFile(fileName, tableWidget):
    book = xlwt.Workbook()
    sheet = book.add_sheet('ObjectDirect')
    for i in range(0, tableWidget.rowCount()):
        for j in range(0, tableWidget.columnCount()):
            try:
                sheet.write(i, j, tableWidget.item(i, j).text())
            except:
                continue
    try:
        book.save(fileName)
        return True
    except Exception as e:
        print(e)
        return False
