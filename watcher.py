#!/usr/bin/python3.4
__author__ = 'allen'

import requests
import re
import webbrowser
import functools
import logging
import sys
from os import path
from time import sleep
from PyQt4 import QtGui

directory = path.abspath(path.dirname(__file__))
refs = path.join(directory, "refs.txt")
good_icon = path.join(directory, "goodTW.png")
bad_icon = path.join(directory, "badTW.png")

logging.basicConfig(filename=directory+'/tw.log',
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S')
logging.info('Start')


def check_connection():
    try:
        requests.get("http://www.google.ru")
        return True
    except:
        return False


def parse_title(ref):
    req = requests.get(ref)
    expr = re.compile('<title>.*</title>')
    title = expr.search(req.text).group()[7:-8]
    expr = re.compile('[^/]*/')
    name = expr.search(title).group()[:-1]
    expr = re.compile('\d+\sиз')
    if expr.search(title) is not None:
        number = expr.search(title).group()[:-3]
    else:
        expr = re.compile('\d+\s[(]')
        number = expr.search(title).group()[:-2]
    return [name, number]


def change_line(filename, cur, new):
    file = open(filename, 'r')
    text = file.read()
    file.close()
    file = open(filename, 'w')
    file.write(text.replace(cur, new))
    file.close()


class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, parent=None):
        icon = QtGui.QIcon(good_icon)
        QtGui.QSystemTrayIcon.__init__(self, icon, parent)

        self.menu = QtGui.QMenu(parent)
        self.menu.addAction("Add").triggered.connect(self.add)
        self.watchers = QtGui.QMenu("Watchers", self.menu)
        self.menu.addMenu(self.watchers)
        self.menu.addAction("Update").triggered.connect(self.update)
        self.menu.addAction("Remove").triggered.connect(self.remove)
        self.menu.addSeparator()
        self.menu.addAction("Exit").triggered.connect(QtGui.qApp.quit)
        self.setContextMenu(self.menu)
        logging.info("GUI initialized")

        self.changing = []
        self.update()

    def add(self):
        file = open(refs, 'r+')
        file.read()
        text, ok = QtGui.QInputDialog.getText(QtGui.QInputDialog(), 'Add watcher', 'Enter URL:')
        if ok:
            try:
                title = parse_title(str(text))
                file.write(str(text)+'\n')
                file.write(title[0]+"||| "+title[1]+'\n')
                self.watchers.addAction(title[0]+"||| "+title[1])
                file.flush()
                logging.info(str(text)+" added")
            except requests.exceptions.MissingSchema:
                logging.warning("Wrong URL: "+str(text))

    def update(self):
        if check_connection():
            self.changing = []
            file = open(refs, 'r')
            self.watchers.clear()
            logging.info("Update started...")
            try:
                for line in file:
                    if line[:4] == "http":
                        url = line[:-1]
                        new_title = parse_title(line[:-1])
                    elif new_title[0]+"||| "+new_title[1] == line[:-1]:
                        self.watchers.addAction(line[:-1]).\
                            triggered.connect(functools.partial(webbrowser.open_new_tab, url))
                    elif line[0] != '\n':
                        self.setIcon(QtGui.QIcon(bad_icon))
                        self.changing.append([line, new_title[0]+"||| "+new_title[1]+'\n', url])
                        self.watchers.addAction(line[:-1]+" >>> "+new_title[1]).\
                            triggered.connect(functools.partial(self.change, len(self.changing)-1))
            except:
                logging.critical("Wrong URL in refs.txt")
        else:
            logging.critical("No connection to Internet, can't update")

    def change(self, i):
        self.setIcon(QtGui.QIcon(good_icon))
        change_line(refs, self.changing[i][0], self.changing[i][1])
        webbrowser.open_new_tab(self.changing[i][2])
        sleep(0.5)
        self.update()

    def remove(self):
        text, ok = QtGui.QInputDialog.getText(QtGui.QInputDialog(), 'Remove watcher', 'Remove URL:')
        file = open(refs, 'r')
        if ok:
            st = ''
            flag = False
            for line in file:
                if flag:
                    st = line
                    flag = False
                if line == str(text)+'\n':
                    flag = True
            if st != '':
                change_line(refs, st, '')
                change_line(refs, str(text)+'\n', '')
            logging.info(str(text)+" removed")
            self.update()


def main():
    if check_connection():
        app = QtGui.QApplication(sys.argv)
        QtGui.QApplication.setQuitOnLastWindowClosed(False)
        tray = SystemTrayIcon()
        tray.show()
        sys.exit(app.exec_())
    else:
        logging.critical("No connection to Internet")
        exit()

if __name__ == "__main__":
    main()
