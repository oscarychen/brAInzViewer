from PyQt5.QtWidgets import (QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox,
                             QWidget, QPushButton, QSlider, QHBoxLayout, QGroupBox, QRadioButton,
                             QGridLayout, QLabel, QInputDialog, QFileDialog, QListWidget, QFrame, QLayout)
from PyQt5.QtCore import Qt, pyqtSlot, QMetaObject, QSize

from PyQt5 import QtGui

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import nibabel as nib
import sys
import os
import numpy as np

VOX_MAX_VAL = 2500


class LabelData:
    """A class that holds label data"""

    def __init__(self):
        self.labelData = dict()
        # Key: label category, Value: list of labels the category
        self.labelData = {'Motion Types': ['Blur', 'Gap/Line', 'Dimmed', 'Tunneling']}

    def getLabelKeys(self):
        """Return list of keys"""
        return self.labelData.keys()

    def getLabelValueByKey(self, category):
        """Return list of values for a given key"""
        return self.labelData.get(category, default=None)

    def addKey(self, category):
        """Add a new category"""
        if category not in self.labelData:
            self.labelData[category] = None

    def removeKey(self, category):
        """Remove a category"""
        if category in self.labelData:
            del self.labelData[category]

    def addKeyValue(self, category, label):
        """Adds a label to an existing category's list of labels"""
        labels = self.labelData[category]
        if label not in labels:
            labels.append(label)
            self.labelData[category] = labels

    def removeValue(self, category, label):
        """Removes a label from an existing category's list of labels"""
        labels = self.labelData[category]
        if label in labels:
            labels.remove(label)
            self.labelData[category] = labels


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
        self.slider.setMaximum(self.data.shape[3] - 1)
        # self.slider.setMaximum(35)

        # Left-half: data display area
        vbox = QVBoxLayout()
        vbox.addWidget(self.file_label)
        vbox.addWidget(self.volume_label)
        vbox.addWidget(self.slider)
        vbox.addWidget(self.triplane)
        vbox.addWidget(DisplayRangeSelector(self.triplane))

        # Right-half: file list area
        self.file_list = QListWidget(self)
        for item in self.niiPaths:
            self.file_list.addItem(item)
        max_list_width = 600
        if self.file_list.sizeHintForColumn(0) < max_list_width:
            max_list_width = self.file_list.sizeHintForColumn(0)
        self.file_list.setMinimumWidth(max_list_width)
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
        # print("Debug: Opening file: " + file)
        nii = nib.load(file)
        self.data = nii.get_fdata()
        # print("Data loaded: " + str(self.data.shape))
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


class DisplayRangeSelector(QWidget):

    def __init__(self, triplane):
        super().__init__()
        self.label = QLabel('Voxel Display Boundaries')
        self.triplane = triplane
        self.startProportion = 0.2  # the start slider's range proportion to the entire range length
        self.startSliderMaxValue = VOX_MAX_VAL * self.startProportion  # the max value of the start slider
        self.endSliderMaxValue = VOX_MAX_VAL * (1 - self.startProportion)  # the max value of the end slider
        self.minDisplayVox = 0  # the converted min value for displaying voxel
        self.maxDisplayVox = VOX_MAX_VAL  # the converted max value for displaying voxel

        self.setupUi(self)

    def convertMinSliderToMinVox(self, value):
        return int(VOX_MAX_VAL * self.startProportion - value)

    def convertMaxSliderToMaxVox(self, value):
        return int(value + VOX_MAX_VAL * self.startProportion)

    def setupUi(self, RangeSlider):
        RangeSlider.setObjectName("RangeSlider")
        RangeSlider.resize(1000, 65)
        RangeSlider.setMaximumSize(QSize(16777215, 65))
        self.RangeBarVLayout = QVBoxLayout(RangeSlider)
        self.RangeBarVLayout.setContentsMargins(5, 0, 5, 0)
        self.RangeBarVLayout.setSpacing(0)
        self.RangeBarVLayout.setObjectName("RangeBarVLayout")

        self.slidersFrame = QFrame(RangeSlider)
        self.slidersFrame.setMaximumSize(QSize(16777215, 25))
        self.slidersFrame.setFrameShape(QFrame.StyledPanel)
        self.slidersFrame.setFrameShadow(QFrame.Raised)
        self.slidersFrame.setObjectName("slidersFrame")
        self.horizontalLayout = QHBoxLayout(self.slidersFrame)
        self.horizontalLayout.setSizeConstraint(QLayout.SetMinimumSize)
        self.horizontalLayout.setContentsMargins(5, 2, 5, 2)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName("horizontalLayout")

        ## Start Slider Widget
        self.startSlider = QSlider(self.slidersFrame)
        self.startSlider.setMaximum(self.startSliderMaxValue)
        self.startSlider.setMinimumSize(QSize(100, 5))
        self.startSlider.setMaximumSize(QSize(16777215, 10))

        font = QtGui.QFont()
        font.setKerning(True)

        self.startSlider.setFont(font)
        self.startSlider.setAcceptDrops(False)
        self.startSlider.setAutoFillBackground(False)
        self.startSlider.setOrientation(Qt.Horizontal)
        self.startSlider.setInvertedAppearance(True)
        self.startSlider.setObjectName("startSlider")
        self.startSlider.setValue(self.startSliderMaxValue)
        self.startSlider.valueChanged.connect(self.handleStartSliderValueChange)

        ## End Slider Widget
        self.endSlider = QSlider(self.slidersFrame)
        self.endSlider.setMaximum(self.endSliderMaxValue)
        self.endSlider.setMinimumSize(QSize(100, 5))
        self.endSlider.setMaximumSize(QSize(16777215, 10))
        self.endSlider.setTracking(True)
        self.endSlider.setOrientation(Qt.Horizontal)
        self.endSlider.setObjectName("endSlider")
        self.endSlider.setValue(self.endSliderMaxValue)
        self.endSlider.valueChanged.connect(self.handleEndSliderValueChange)

        # self.endSlider.sliderReleased.connect(self.handleEndSliderValueChange)
        self.horizontalLayout.addWidget(self.startSlider, int(self.startProportion * 100))
        self.horizontalLayout.addWidget(self.endSlider, int(100 - 100 * self.startProportion))
        self.RangeBarVLayout.addWidget(self.label)
        self.RangeBarVLayout.addWidget(self.slidersFrame)

        # self.retranslateUi(RangeSlider)
        QMetaObject.connectSlotsByName(RangeSlider)

        self.show()

    def updateLabel(self):
        print(f'Voxel sliders: {self.minDisplayVox}, {self.maxDisplayVox}')
        self.label.setText(f'Voxel Display Boundaries:({self.minDisplayVox},{self.maxDisplayVox})')

    @pyqtSlot(int)
    def handleStartSliderValueChange(self, value):
        self.startSlider.setValue(value)
        self.minDisplayVox = self.convertMinSliderToMinVox(value)
        self.triplane.voxDisplayUpdate(self.minDisplayVox, self.maxDisplayVox)
        self.updateLabel()

    @pyqtSlot(int)
    def handleEndSliderValueChange(self, value):
        self.endSlider.setValue(value)
        self.maxDisplayVox = self.convertMaxSliderToMaxVox(value)
        self.updateLabel()
        self.triplane.voxDisplayUpdate(self.minDisplayVox, self.maxDisplayVox)


class TriPlaneView(QWidget):
    def __init__(self, data, parent=None):
        super(TriPlaneView, self).__init__(parent)

        self.data = data
        grid = QGridLayout()
        self.axialView = PlaneView("Axial", self.data, 0, self.data.shape[2] - 1)  # name, data, volume #, slice #
        self.sagittalView = PlaneView("Sagittal", self.data, 0, self.data.shape[0] - 1)
        self.coronalView = PlaneView("Coronal", self.data, 0, self.data.shape[1] - 1)
        grid.addWidget(self.axialView, 0, 0)
        grid.addWidget(self.sagittalView, 0, 1)
        grid.addWidget(self.coronalView, 0, 2)

        self.setLayout(grid)

        self.axialView.set_slider(self.data.shape[2] // 2)  # Initial slider position
        self.sagittalView.set_slider(self.data.shape[0] // 2)  # Initial slider position
        self.coronalView.set_slider(self.data.shape[1] // 2)  # Initial slider position

    def voxDisplayUpdate(self, minValue, maxValue):
        self.axialView.canvas.setMinVoxVal(minValue)
        self.axialView.canvas.setMaxVoxVal(maxValue)
        self.coronalView.canvas.setMinVoxVal(minValue)
        self.coronalView.canvas.setMaxVoxVal(maxValue)
        self.sagittalView.canvas.setMinVoxVal(minValue)
        self.sagittalView.canvas.setMaxVoxVal(maxValue)
        self.replot()

    def replot(self):
        # print('Debug: Update axial slider max to ' + str(self.data.shape[2]-1))
        self.axialView.setMaxSlider(self.data.shape[2] - 1)
        self.axialView.set_slider(self.data.shape[2] // 2)  # Slider position when loading a new file
        self.axialView.replot()

        # print('Debug: Update sagittal slider max to ' + str(self.data.shape[0] - 1))
        self.sagittalView.setMaxSlider(self.data.shape[0] - 1)
        self.sagittalView.set_slider(self.data.shape[0] // 2)
        self.sagittalView.replot()

        # print('Debug: Update coronal slider max to ' + str(self.data.shape[1] - 1))
        self.coronalView.setMaxSlider(self.data.shape[1] - 1)
        self.coronalView.set_slider(self.data.shape[1] // 2)
        self.coronalView.replot()

    def clearPlot(self):
        self.axialView.clearPlot()
        self.sagittalView.clearPlot()
        self.coronalView.clearPlot()

    def setData(self, data):
        self.data = data
        self.axialView.setData(data)
        self.sagittalView.setData(data)
        self.coronalView.setData(data)


class LabelSelector(QWidget):
    """label selector"""

    def __init__(self):
        pass


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
        self.setSliceLabel(value)

    def set_volume(self, value):
        self.canvas.setVolume(value)

    def replot(self):
        self.canvas.plot()

    def clearPlot(self):
        self.canvas.clearPlot()

    def setData(self, data):
        self.data = data
        self.canvas.setData(data)

    def setMaxSlider(self, value):
        self.slider.setMaximum(value)

    def setSliceLabel(self, value):
        self.slice_num_label.setText(str(value))


class PlotCanvas(FigureCanvas):
    def __init__(self, slicetype, data, volume, parent=None):

        self.slicetype = slicetype
        self.data = data
        self.maxVoxVal = np.amax(self.data)
        self.minVoxVal = np.amin(self.data)
        self.volume = volume
        fig = Figure()
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
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

    def setMinVoxVal(self, value):
        self.minVoxVal = value

    def setMaxVoxVal(self, value):
        self.maxVoxVal = value

    def plot(self):
        self.ax.cla()
        self.ax.set_axis_off()

        if self.slicetype == "Axial":

            curslice = self.data[:, :, self.cur_slice, self.volume]
            self.ax.imshow(curslice.T, cmap="gray", origin="lower", vmin=self.minVoxVal, vmax=self.maxVoxVal)

        elif self.slicetype == "Sagittal":

            curslice = self.data[self.cur_slice, :, :, self.volume]
            self.ax.imshow(curslice.T, cmap="gray", origin="lower", aspect=256.0 / 54.0, vmin=self.minVoxVal,
                           vmax=self.maxVoxVal)

        elif self.slicetype == "Coronal":

            curslice = self.data[:, self.cur_slice, :, self.volume]
            self.ax.imshow(curslice.T, cmap="gray", origin="lower", aspect=256.0 / 54.0, vmin=self.minVoxVal,
                           vmax=self.maxVoxVal)

        self.draw()

    def clearPlot(self):
        self.ax.cla()
        self.ax.set_axis_off()
        self.draw()

    def setData(self, data):
        self.data = data
        self.maxVoxVal = np.amax(self.data)
        self.minVoxVal = np.amin(self.data)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VolumeSelectView()
    window.show()
    sys.exit(app.exec_())
