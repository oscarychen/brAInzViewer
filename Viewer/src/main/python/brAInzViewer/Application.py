#!/usr/bin/env python

import sys

from Controllers import Controller
from PyQt5.QtWidgets import QApplication


if __name__ == '__main__':
    app = QApplication(sys.argv)

    controller = Controller()
    sys.exit(app.exec_())