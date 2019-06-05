from fbs_runtime.application_context import ApplicationContext, cached_property
from PyQt5.QtWidgets import QMainWindow
# from code.Controllers import Controller
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'code'))
from Controllers import Controller

class AppContext(ApplicationContext):           # 1. Subclass ApplicationContext
    
    def __init__(self, *args, **kwargs):
        super(AppContext, self).__init__(*args, **kwargs)

        self.window = Controller(self)

    def run(self):
        # self.window.show()
        return self.app.exec_()


if __name__ == '__main__':
    appctxt = AppContext()
    exit_code = appctxt.run()
    sys.exit(exit_code)