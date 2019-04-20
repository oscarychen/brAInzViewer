from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox,
                             QWidget, QPushButton, QSlider, QHBoxLayout, QGroupBox, QRadioButton,
                             QGridLayout, QLabel, QInputDialog, QFileDialog)
from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import nibabel as nib
import sys


class VolumeSelectView(QWidget):
    def __init__(self, parent=None):
        super(VolumeSelectView, self).__init__(parent)

        self.file_label = QLabel('No file loaded.')
        self.volume_label = QLabel()

        self.data = None
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(1)
        # self.slider.setSingleStep(1)
        self.slider.setMinimum(0)
        self.slider.valueChanged.connect(self.set_volume)

        self.openFileNameDialog()

        self.triplane = TriPlaneView(self.data)

        vbox = QVBoxLayout()
        vbox.addWidget(self.file_label)
        vbox.addWidget(self.volume_label)
        vbox.addWidget(self.slider)
        vbox.addWidget(self.triplane)

        self.setLayout(vbox)

    def openFileNameDialog(self):
        options = QFileDialog.Options()
        file, _ = QFileDialog.getOpenFileName(self, caption='Select file to open',
                                              directory='../../', filter='.nii files(*.nii)',
                                              options=options)
        if file:
            nii = nib.load(file)
            self.data = nii.get_fdata()
            self.file_label.setText(file)
            self.slider.setMaximum(self.data.shape[3]-1)
            self.volume_label.setText('0')
        else:
            exit(0)

    def set_volume(self, value):
        self.volume_label.setText(str(value))
        self.triplane.axialView.set_volume(value)
        self.triplane.sagittalView.set_volume(value)
        self.triplane.coronalView.set_volume(value)



class TriPlaneView(QWidget):
    def __init__(self, data, parent=None):
        super(TriPlaneView, self).__init__(parent)
        # nii = nib.load('../../Calgary_PS_DTI_Dataset/10001/PS14_006/b750/PS14_006_750.nii')
        # self.data = nii.get_fdata()
        # self.openFileNameDialog()

        self.data = data
        grid = QGridLayout()
        self.axialView = PlaneView("Axial", self.data, 0, 53)
        self.sagittalView = PlaneView("Sagittal", self.data, 0, 255)
        self.coronalView = PlaneView("Coronal", self.data, 0, 255)
        grid.addWidget(self.axialView, 0, 0)
        grid.addWidget(self.sagittalView, 0, 1)
        grid.addWidget(self.coronalView, 0, 2)

        self.setLayout(grid)
        self.setWindowTitle("MRI Viewer")
        self.resize(1280, 600)

        self.axialView.set_slider(26)
        self.sagittalView.set_slider(128)
        self.coronalView.set_slider(128)

    # def openFileNameDialog(self):
    #     options = QFileDialog.Options()
    #     file, _ = QFileDialog.getOpenFileName(self, caption='Select file to open',
    #                                           directory='../../', filter='.nii files(*.nii)',
    #                                           options=options)
    #     if file:
    #         nii = nib.load(file)
    #         self.data = nii.get_fdata()
    #     else:
    #         exit(0)


class PlaneView(QWidget):
    def __init__(self, name, data, volume, numslices, parent=None):
        super(PlaneView, self).__init__(parent)
        self.data = data
        self.type = name
        label = QLabel()
        label.setText(name)
        self.slice_num_label = QLabel()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(10)
        # self.slider.setSingleStep(1)
        self.slider.setMinimum(0)
        self.slider.setMaximum(numslices)
        self.slider.valueChanged.connect(self.value_changed)

        self.canvas = PlotCanvas(name, self.data, volume)
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.slice_num_label)
        vbox.addWidget(self.slider)
        vbox.addWidget(self.canvas)
        vbox.addStretch(1)
        self.setLayout(vbox)

    def set_slider(self, value):
        self.slider.setValue(value)

    def value_changed(self, value):
        self.canvas.setSliceIndex(value)
        self.slice_num_label.setText(str(value))

    def set_volume(self, value):
        self.canvas.setVolume(value)


class PlotCanvas(FigureCanvas):
    def __init__(self, slicetype, data, volume, parent=None, width=5, height=4, dpi=100):
        self.slicetype = slicetype
        self.data = data
        self.volume = volume
        fig = Figure()
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        print(self.data.shape)
        self.cur_slice = 0
        self.ax = self.figure.add_subplot(111)
        self.plot()

    def setVolume(self, value):
        self.volume = value
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
            curslice = self.data[:, :, self.cur_slice, self.volume]
            self.ax.imshow(curslice.T, cmap="gray", origin="lower", vmin=0, vmax=2000)
        elif self.slicetype == "Sagittal":
            curslice = self.data[self.cur_slice, :, :, self.volume]
            self.ax.imshow(curslice.T, cmap="gray", origin="lower", aspect=256.0 / 54.0, vmin=0, vmax=2000)
        elif self.slicetype == "Coronal":
            curslice = self.data[:, self.cur_slice, :, self.volume]
            self.ax.imshow(curslice.T, cmap="gray", origin="lower", aspect=256.0 / 54.0, vmin=0, vmax=2000)
        self.draw()


if __name__ == '__main__':
    if sys.platform != 'win32':
        app = QApplication(sys.argv)
    window = VolumeSelectView()
    window.show()
    if sys.platform != 'win32':
        sys.exit(app.exec_())
