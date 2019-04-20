from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox,
                             QWidget, QPushButton, QSlider, QHBoxLayout, QGroupBox, QRadioButton,
                             QGridLayout, QLabel, QInputDialog, QFileDialog, QListWidget)
from PyQt5.QtCore import Qt

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import nibabel as nib
import sys
import os

class VolumeSelectView(QWidget):
    def __init__(self, parent=None):
        super(VolumeSelectView, self).__init__(parent)

        self.setWindowTitle("Nii Viewer and Labeler")
        self.resize(1280, 600)

        self.file_label = QLabel('No file loaded.')
        self.volume_label = QLabel()
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(1)
        # self.slider.setSingleStep(1)
        self.slider.setMinimum(0)
        self.slider.valueChanged.connect(self.set_volume)

        self.data = None
        self.niiPaths = None
        self.openFolderDialog()

        self.triplane = TriPlaneView(self.data)
        self.volume_label.setText('0')
        self.slider.setMaximum(self.data.shape[3]-1)
        #self.slider.setMaximum(35)

        vbox = QVBoxLayout()
        vbox.addWidget(self.file_label)
        vbox.addWidget(self.volume_label)
        vbox.addWidget(self.slider)
        vbox.addWidget(self.triplane)

        self.file_list = QListWidget(self)
        for item in self.niiPaths:
            self.file_list.addItem(item)
        self.file_list.setMinimumWidth(self.file_list.sizeHintForColumn(0))
        self.file_list.itemSelectionChanged.connect(self.selectedFileChanged)

        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(self.file_list)
        self.setLayout(hbox)
    
    def selectedFileChanged(self):
        self.triplane.clearPlot()
        self.changeNiiFile(self.file_list.currentItem().text())
        self.triplane.setData(self.data)
        self.triplane.replot()

    def changeNiiFile(self, file):
        print(file)
        print("Opening file...")
        nii = nib.load(file)
        print("Loading data...")
        self.data = nii.get_fdata()
        print("Data loaded")
        self.file_label.setText(file)

    def openFolderDialog(self):
        folder = QFileDialog.getExistingDirectory(self, caption='Select folder to open', directory='../')
        if folder:
            self.niiPaths = self.getNiiPaths(folder)
            if len(self.niiPaths) == 0:
                QMessageBox.about(self, "Error", "No Nii Files Found")
                print("No Nii Files Found")
                exit(0)
            file = self.niiPaths[0]
            self.changeNiiFile(file)
        else:
            exit(0)

    
    def getNiiPaths(self, folder):
        """Scan the folder and its sub-dirs, return a list of .nii files found."""
        nii_list = []
        for dirpaths, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith('.nii'):
                    file_path = os.path.join(dirpaths, file)
                    nii_list.append(file_path)
        return nii_list
    
    def set_volume(self, value):
        self.volume_label.setText(str(value))
        self.triplane.axialView.set_volume(value)
        self.triplane.sagittalView.set_volume(value)
        self.triplane.coronalView.set_volume(value)


class TriPlaneView(QWidget):
    def __init__(self, data, parent=None):
        super(TriPlaneView, self).__init__(parent)

        self.data = data
        grid = QGridLayout()
        self.axialView = PlaneView("Axial", self.data, 0, 53)
        self.sagittalView = PlaneView("Sagittal", self.data, 0, 255)
        self.coronalView = PlaneView("Coronal", self.data, 0, 255)
        grid.addWidget(self.axialView, 0, 0)
        grid.addWidget(self.sagittalView, 0, 1)
        grid.addWidget(self.coronalView, 0, 2)

        self.setLayout(grid)

        self.axialView.set_slider(26)
        self.sagittalView.set_slider(128)
        self.coronalView.set_slider(128)
    
    def replot(self):
        self.axialView.replot()
        self.sagittalView.replot()
        self.coronalView.replot()
    
    def clearPlot(self):
        self.axialView.clearPlot()
        self.sagittalView.clearPlot()
        self.coronalView.clearPlot()

    def setData(self, data):
        self.axialView.setData(data)
        self.sagittalView.setData(data)
        self.coronalView.setData(data)


class PlaneView(QWidget):
    def __init__(self, name, data, volume, numslices, parent=None):
        super(PlaneView, self).__init__(parent)
        self.data = data
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
    
    def replot(self):
        self.canvas.plot()
    
    def clearPlot(self):
        self.canvas.clearPlot()

    def setData(self, data):
        self.canvas.setData(data)

class PlotCanvas(FigureCanvas):
    def __init__(self, slicetype, data, volume, parent=None):
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

    def clearPlot(self):
        self.ax.cla()
        self.ax.set_axis_off()
        self.draw()
    
    def setData(self, data):
        self.data = data


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VolumeSelectView()
    window.show()
    sys.exit(app.exec_())