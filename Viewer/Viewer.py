from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, 
                             QWidget, QPushButton, QSlider, QHBoxLayout, QGroupBox, QRadioButton, 
                             QGridLayout, QLabel)
from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import nibabel as nib
import sys


class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        nii = nib.load('../../Calgary_PS_DTI_Dataset/10001/PS14_006/b750/PS14_006_750.nii')
        self.data = nii.get_fdata()
        
        grid = QGridLayout()
        axialView = PlaneView("Axial", self.data, 53)
        sagittalView = PlaneView("Sagittal", self.data, 255)
        coronalView = PlaneView("Coronal", self.data, 255)
        grid.addWidget(axialView, 0, 0)
        grid.addWidget(sagittalView, 0, 1)
        grid.addWidget(coronalView, 0, 2)
        
        self.setLayout(grid)
        self.setWindowTitle("MRI Viewer")
        self.resize(1280, 600)
        
        axialView.set_slider(26)
        sagittalView.set_slider(128)
        coronalView.set_slider(128)

class PlaneView(QWidget):
    def __init__(self, name, data, numslices, parent=None):
        super(PlaneView, self).__init__(parent)
        self.data = data
        self.type = name
        label = QLabel()
        label.setText(name)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(10)
        #self.slider.setSingleStep(1)
        self.slider.setMinimum(0)
        self.slider.setMaximum(numslices)
        self.slider.valueChanged.connect(self.value_changed)
        
        self.canvas = PlotCanvas(name, self.data)
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.slider)
        vbox.addWidget(self.canvas)
        vbox.addStretch(1)
        self.setLayout(vbox)
    
    def set_slider(self, value):
        self.slider.setValue(value)
        
    def value_changed(self, value):
        self.canvas.setSliceIndex(value)
        
class PlotCanvas(FigureCanvas):
    def __init__(self, slicetype, data, parent=None, width=5, height=4, dpi=100):
        self.slicetype = slicetype
        self.data = data
        fig = Figure()
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        print(self.data.shape)
        self.cur_slice = 0;
        self.ax = self.figure.add_subplot(111)
        self.plot()
 
    def forwards(self):
        self.cur_slice += 1
        self.plot()
        
    def setSliceIndex(self, value):
        self.cur_slice = value
        self.plot()
        
    def plot(self):
        self.ax.cla()
        self.ax.set_axis_off()
        if self.slicetype == "Axial":
            curslice = self.data[:, :, self.cur_slice, 1]
            self.ax.imshow(curslice.T, cmap="gray", origin="lower", vmin=0, vmax=2000)
        elif self.slicetype == "Sagittal":
            curslice = self.data[self.cur_slice, :, :, 1]
            self.ax.imshow(curslice.T, cmap="gray", origin="lower", aspect=256.0/54.0, vmin=0, vmax=2000)
        elif self.slicetype == "Coronal":
            curslice = self.data[:, self.cur_slice, :, 1]
            self.ax.imshow(curslice.T, cmap="gray", origin="lower", aspect=256.0/54.0, vmin=0, vmax=2000)
        self.draw()

if __name__ == '__main__':
    if sys.platform != 'win32':
        app = QApplication(sys.argv)
    window = Window()
    window.show()
    if sys.platform != 'win32':
        sys.exit(app.exec_())