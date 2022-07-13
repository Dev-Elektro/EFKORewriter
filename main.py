import binascii
import sys
from PyQt5 import QtCore, QtWidgets, QtGui
import mainwindow
import about
import docx2txt
import re
from base64 import b64encode
import os
import json
import requests
import webbrowser
from datetime import datetime, timedelta

_version = 0.1

class CheckUpdate(QtCore.QThread):
    newVersion = QtCore.pyqtSignal(str)

    def run(self):
        try:
            uname = os.getlogin()
            pname = os.getenv('COMPUTERNAME')
            buf = {'uname': uname, 'pname': pname, 'ver': _version}
            url = "http://pool-srv.efko.ru/efkorewriter/checkupdate"
            data = {'version': b64encode(json.dumps(buf).encode('utf-8')).decode('utf-8')}
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            r = requests.post(url, data=json.dumps(data), headers=headers)
            if r.status_code == 200:
                buf = r.json()
                if buf['ver'] > _version:
                    self.newVersion.emit(str(buf['ver']))
        except:
            pass

class winAbout(QtWidgets.QDialog, about.Ui_Dialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.label_ver.setText(str(_version))

class App(QtWidgets.QMainWindow, mainwindow.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle('EFKO Rewriter v' + str(_version))
        self.copyright = QtWidgets.QLabel('Dev-Elektro © Якущенко С.Ю.')
        self.copyright.setStyleSheet("color: #909090;")
        self.statusBar().addPermanentWidget(self.copyright)

        self.action_open1.triggered.connect(self.openFile1)
        self.action_open2.triggered.connect(self.openFile2)
        self.text1.textChanged.connect(self.updateStatusBar)
        self.text2.textChanged.connect(self.updateStatusBar)
        self.but_run.clicked.connect(self.comparison)
        self.action_compare.triggered.connect(self.comparison)
        self.iFontSize.valueChanged.connect(self.iFontSizeChange)
        self.pFontSize.valueChanged.connect(self.pFontSizeChange)
        self.butFind.clicked.connect(self.findWord)
        self.action_format_clear.triggered.connect(self.clearFormat)
        self.action_find.triggered.connect(self.findWordQuick)

        self.wAbout = winAbout(self)
        self.action_about.triggered.connect(self.wAbout.show)

        self.urlUpdate = f'http://pool-srv.efko.ru/efkorewriter/checkupdate?ver={_version}'
        self.action_check_update.triggered.connect(lambda x:webbrowser.open(self.urlUpdate, autoraise=True))

        self.checkUpdate = CheckUpdate()
        self.checkUpdate.newVersion.connect(self.showMessageBox)
        self.checkUpdate.start()

    def showMessageBox(self, msg):
        r = QtWidgets.QMessageBox.information(self, 'Проверка новой версии',
            f'Доступна новая версия {msg}, перейти на сайт для загрузки?',
            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        if r == QtWidgets.QMessageBox.Ok:
            webbrowser.open(self.urlUpdate, autoraise=True)

    def clearFormat(self):
        self.text2.setText(self.text2.toPlainText())
        self.text1.setText(self.text1.toPlainText())

    def getCountWord(self, txt):
        return len(re.sub(r'\s+', ' ', re.sub(r'(?i)[^a-z а-я]*', '', txt)).split())

    def iFontSizeChange(self, value):
        font = QtGui.QFont()
        font.setPointSize(value)
        self.text1.setFont(font)

    def pFontSizeChange(self, value):
        font = QtGui.QFont()
        font.setPointSize(value)
        self.text2.setFont(font)

    def findWordQuick(self):
        text, okPressed = QtWidgets.QInputDialog.getText(self, "Введите ключевое слово", "Ключевое слово:", QtWidgets.QLineEdit.Normal, "")
        if okPressed and text != '':
            self.wordSearch.setText(text)
            self.findWord();

    def findWord(self):
        txt = self.wordSearch.text().lower()
        if not txt:
            QtWidgets.QMessageBox.warning(self, 'Ошибка', 'Введите ключевое слово!', QtWidgets.QMessageBox.Ok)
            return
        buf1 = self.text1.toPlainText().lower()
        buf2 = self.text2.toPlainText().lower()
        buf1 = re.sub(r'\s+', ' ', re.sub(r'(?i)[^a-z а-я]*', '', buf1))
        buf2 = re.sub(r'\s+', ' ', re.sub(r'(?i)[^a-z а-я]*', '', buf2))
        buf1CountAll = len(buf1.split())
        buf2CountAll = len(buf2.split())
        countWord1 = buf1.count(txt)
        countWord2 = buf2.count(txt)
        proc1 = 0
        proc2 = 0
        if countWord1 > 0:
            proc1 = round((countWord1 * 100)/buf1CountAll, 1)
        if countWord2 > 0:
            proc2 = round((countWord2 * 100)/buf2CountAll, 1)
        msg = f"Исходный текст: найдено совподений {countWord1}. Плотность: {proc1}%\n\n"
        msg += f"Переработанный текст: найдено совподений {countWord2}. Плотность: {proc2}%"
        QtWidgets.QMessageBox.information(self, 'Результат поиска по ключевому слову', msg, QtWidgets.QMessageBox.Ok)

    def clearFont(self, t):
        cursor = t.textCursor()
        cursor.select(QtGui.QTextCursor.Document)
        cursor.setCharFormat(QtGui.QTextCharFormat())
        cursor.clearSelection()
        t.setTextCursor(cursor)

    def comparison(self):
        coutnWord1 = self.getCountWord(self.text1.toPlainText())
        coutnWord2 = self.getCountWord(self.text2.toPlainText())
        if coutnWord1 < int(self.size_shingl.currentText()) or coutnWord2 < int(self.size_shingl.currentText()):
            QtWidgets.QMessageBox.information(self, 'Уведомление', 'Недостаточно текста для сравнения.', QtWidgets.QMessageBox.Ok)
            return
        self.clearFont(self.text2)
        cmp1 = self.genshingle(self.canonize(self.text1.toPlainText()))
        cmp2 = self.genshingle(self.canonize(self.text2.toPlainText()))
        proc = round(self.compaire(cmp1,cmp2), 1)
        umm = round(float(100 - proc)/100, 2)
        msg = f"Процент совпадения текстов: {proc}%\n\n"
        msg += f"Коэффициента переработки УММ: {umm}        "
        QtWidgets.QMessageBox.information(self, 'Результат проверки текстов', msg, QtWidgets.QMessageBox.Ok)
        cursor = self.text2.textCursor();
        cursor.setPosition(0);
        #cursor.setPosition(5, QtGui.QTextCursor.KeepAnchor)
        self.text2.setTextCursor(cursor)
        t1 = self.text1.toPlainText()
        t2 = self.text2.toPlainText()
        p1 = 0
        for n, a in enumerate(t2):
            QtCore.QCoreApplication.processEvents()
            if a in [' ', '\n', '\r'] or len(t2) == n+1:
                if t2[p1:n] in t1:
                    cursor.setPosition(n)
                else:
                    cursor.setPosition(n, QtGui.QTextCursor.KeepAnchor)
                    charFormat = cursor.charFormat()
                    charFormat.setBackground(QtGui.QColor(98, 217, 109))
                    cursor.mergeCharFormat(charFormat)
                    cursor.clearSelection()
                    self.text2.setTextCursor(cursor)
                    p1 = n+1

    def updateStatusBar(self):
        txt1 = self.text1.toPlainText()
        txt2 = self.text2.toPlainText()
        t1 = len(txt1)
        t2 = len(txt2)
        count_word1 = self.getCountWord(txt1)
        count_word2 = self.getCountWord(txt2)
        self.i_symbol.setText(f"{t1}")
        self.p_symbol.setText(f"{t2}")
        self.i_word.setText(f"{count_word1}")
        self.p_word.setText(f"{count_word2}")

    def openFile1(self):
        pathFile, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Открыть исходный файл', 'c:\\', 'Файлы (*.txt *.docx)')
        if not pathFile:
            return
        if pathFile.split('.')[-1] == 'docx':
            self.text1.clear()
            doc = docx2txt.process(pathFile)
            doc = re.sub(r'\s+', ' ', doc)
            self.text1.setText(doc)
        else:
            f = open(pathFile, "r")
            self.text1.clear()
            self.text1.setText(f.read())

    def openFile2(self):
        pathFile, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Открыть переписанный файл', 'c:\\', 'Файлы (*.txt *.docx)')
        if not pathFile:
            return
        if pathFile.split('.')[-1] == 'docx':
            self.text2.clear()
            doc = docx2txt.process(pathFile)
            doc = re.sub(r'\s+', ' ', doc)
            self.text2.setText(doc)
        else:
            f = open(pathFile, "r")
            self.text2.clear()
            self.text2.setText(f.read())


    def canonize(self, source):
        stop_symbols = '.,!?:;-\n\r()'

        stop_words = ('это', 'как', 'так',
        'и', 'в', 'над',
        'к', 'до', 'не',
        'на', 'но', 'за',
        'то', 'с', 'ли',
        'а', 'во', 'от',
        'со', 'для', 'о',
        'же', 'ну', 'вы',
        'бы', 'что', 'кто',
        'он', 'она')

        return ( [x for x in [y.strip(stop_symbols) for y in source.lower().split()] if x and ((x not in stop_words) or not self.delete_stop.isChecked())] )

    def genshingle(self, source):
        shingleLen = int(self.size_shingl.currentText()) #длина шингла
        out = []
        for i in range(len(source)-(shingleLen-1)):
            out.append (binascii.crc32(' '.join( [x for x in source[i:i+shingleLen]] ).encode('utf-8')))

        return out

    def compaire (self, source1, source2):
        same = 0
        for i in range(len(source1)):
            if source1[i] in source2:
                same = same + 1

        return float(same*2)/float(len(source1) + len(source2))*100

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = App()
    window.show()
    app.exec_()

if __name__ == '__main__':
    main()
