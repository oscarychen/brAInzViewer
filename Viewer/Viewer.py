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

VOX_MAX_VAL = 2500


class LabelTypes:
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


class LabelsView(QWidget):
    """label selector"""

    def __init__(self):
        self.labelTypes = None

    def setDataLabelTypes(self, labelTypes):
        self.labelTypes = labelTypes


class Controller:

    def __init__(self):
        self.data = None
        self.niiPaths = None
        self.openFolder()

        self.brightnessSelector = DisplayBrightnessSelectorView()
        self.axialView = PlaneView(self, "Axial", 0, self.data.shape[2] - 1)  # name, data, volume #, slice #
        self.sagittalView = PlaneView(self, "Sagittal", 0, self.data.shape[0] - 1)
        self.coronalView = PlaneView(self, "Coronal", 0, self.data.shape[1] - 1)
        self.triPlaneView = TriPlaneView(self.axialView, self.sagittalView, self.coronalView)
        self.fileListView = FileListView(self.niiPaths)
        self.view = View(self.triPlaneView, self.fileListView, self.brightnessSelector)
        self.setController()
        self.showView()

    def setController(self):
        self.view.setController(self)
        self.brightnessSelector.setController(self)
        # self.axialView.setController(self)
        # self.sagittalView.setController(self)
        # self.coronalView.setController(self)
        self.triPlaneView.setController(self)
        self.fileListView.setController(self)

    def updateVoxDisplayRange(self, minValue, maxValue):
        self.axialView.canvas.setMinVoxVal(minValue)
        self.axialView.canvas.setMaxVoxVal(maxValue)
        self.coronalView.canvas.setMinVoxVal(minValue)
        self.coronalView.canvas.setMaxVoxVal(maxValue)
        self.sagittalView.canvas.setMinVoxVal(minValue)
        self.sagittalView.canvas.setMaxVoxVal(maxValue)
        self.replot()

    def replot(self):
        self.axialView.setMaxSlider(self.data.shape[2]-1)
        self.axialView.replot()
        self.sagittalView.setMaxSlider(self.data.shape[0]-1)
        self.sagittalView.replot()
        self.coronalView.setMaxSlider(self.data.shape[1]-1)
        self.coronalView.replot()

    def clearPlot(self):
        self.axialView.clearPlot()
        self.sagittalView.clearPlot()
        self.coronalView.clearPlot()

    def selectFile(self, file):
        self.clearPlot()
        nii = nib.load(file)
        self.data = nii.get_fdata()
        self.view.fileLabel.setText(file)
        self.replot()

    def openFolder(self):
        folder = QFileDialog.getExistingDirectory(None, caption='Select folder to open', directory='../')
        if folder:
            self.niiPaths = self.getNiiFilePaths(folder)
            if len(self.niiPaths) == 0:
                QMessageBox.about(self, "Error", "No Nii Files Found")
                print("No Nii Files Found")
                exit(0)
            file = self.niiPaths[0]
            nii = nib.load(file)
            self.data = nii.get_fdata()
        else:
            exit(0)

    def getNiiFilePaths(self, folder):
        """Scan the folder and its sub-dirs, return a list of .nii files found."""
        niiList = []
        for dirpaths, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith('.nii'):
                    filePath = os.path.join(dirpaths, file)
                    niiList.append(filePath)
        return niiList

    def showView(self):
        self.view.show()


class FileListView(QListWidget):
    def __init__(self, niiPaths):
        super(FileListView, self).__init__()
        self.controller = None
        # self.fileList = QListWidget(self)
        for item in niiPaths:
            self.addItem(item)
        maxListWidth = 400
        if self.sizeHintForColumn(0) < maxListWidth:
            maxListWidth = self.sizeHintForColumn(0)
        self.setMinimumWidth(maxListWidth)
        self.itemSelectionChanged.connect(self.selectedFileChanged)

    def setController(self, controller):
        self.controller = controller

    def selectedFileChanged(self):
        file = self.currentItem().text()
        self.controller.selectFile(file)


class View(QWidget):
    """Main window"""
    def __init__(self, triPlaneView, fileListView, brightnessSelector, parent=None):
        super(View, self).__init__(parent)

        self.controller = None
        self.setWindowTitle("Nii Viewer and Labeler")
        self.resize(1280, 600)

        self.fileLabel = QLabel('No file loaded.')
        self.volumeLabel = QLabel()

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(1)
        # self.slider.setSingleStep(1)
        self.slider.setMinimum(0)
        self.slider.valueChanged.connect(self.setVolume)


        self.volumeLabel.setText('0')
        # self.slider.setMaximum(self.data.shape[3] - 1)
        # self.slider.setMaximum(35)

        # Left-half: data display area
        vbox = QVBoxLayout()
        vbox.addWidget(self.fileLabel)
        vbox.addWidget(self.volumeLabel)
        vbox.addWidget(self.slider)
        vbox.addWidget(triPlaneView)
        vbox.addWidget(brightnessSelector)

        # Right-half: file list area
        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(fileListView)
        self.setLayout(hbox)


    def changeNiiFile(self, file):
        # print("Debug: Opening file: " + file)
        nii = nib.load(file)
        self.data = nii.get_fdata()
        # print("Data loaded: " + str(self.data.shape))
        self.fileLabel.setText(file)

    # def openFolderDialog(self):
        # folder = QFileDialog.getExistingDirectory(self, caption='Select folder to open', directory='../')
        # if folder:
        #     self.niiPaths = self.getNiiPaths(folder)
        #     if len(self.niiPaths) == 0:
        #         QMessageBox.about(self, "Error", "No Nii Files Found")
        #         print("No Nii Files Found")
        #         exit(0)
        #     file = self.niiPaths[0]
        #     self.changeNiiFile(file)
        # else:
        #     exit(0)

    def setController(self, controller):
        self.controller = controller

    # def getNiiPaths(self, folder):
    #     """Scan the folder and its sub-dirs, return a list of .nii files found."""
    #     niiList = []
    #     for dirpaths, dirs, files in os.walk(folder):
    #         for file in files:
    #             if file.endswith('.nii'):
    #                 filePath = os.path.join(dirpaths, file)
    #                 niiList.append(filePath)
    #     return niiList

    def setVolume(self, value):
        self.volumeLabel.setText(str(value))
        self.triPlaneView.axialView.setVolume(value)
        self.triPlaneView.sagittalView.setVolume(value)
        self.triPlaneView.coronalView.setVolume(value)


class DisplayBrightnessSelectorView(QWidget):
    """The range (dual-value) slider for adjust voxel brightness."""
    def __init__(self):
        super().__init__()
        self.label = QLabel('Voxel Display Boundaries')
        self.startProportion = 0.1  # the start slider's range proportion to the entire range length
        self.startSliderMaxValue = int(VOX_MAX_VAL * self.startProportion)  # the max value of the start slider
        self.endSliderMaxValue = int(VOX_MAX_VAL * (1 - self.startProportion))  # the max value of the end slider
        self.minDisplayVox = 0  # the converted min value for displaying voxel
        self.maxDisplayVox = VOX_MAX_VAL  # the converted max value for displaying voxel
        self.controller = None
        self.setupUi(self)

    def convertMinSliderToMinVox(self, value):
        """Converts the value from the start slider (inverted) to min voxel value"""
        return int(VOX_MAX_VAL * self.startProportion - value)

    def convertMaxSliderToMaxVox(self, value):
        """Converts the value from the end slider to max voxel value"""
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
        self.startSlider.setMinimumSize(QSize(100, 20))
        self.startSlider.setMaximumSize(QSize(16777215, 20))

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
        self.endSlider.setMinimumSize(QSize(100, 20))
        self.endSlider.setMaximumSize(QSize(16777215, 20))
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
        # print(f'Voxel sliders: {self.minDisplayVox}, {self.maxDisplayVox}')
        self.label.setText(f'Voxel Brightness Range:({self.minDisplayVox},{self.maxDisplayVox})')

    @pyqtSlot(int)
    def handleStartSliderValueChange(self, value):
        self.startSlider.setValue(value)
        self.minDisplayVox = self.convertMinSliderToMinVox(value)
        self.updateLabel()
        self.controller.updateVoxDisplayRange(self.minDisplayVox, self.maxDisplayVox)


    @pyqtSlot(int)
    def handleEndSliderValueChange(self, value):
        self.endSlider.setValue(value)
        self.maxDisplayVox = self.convertMaxSliderToMaxVox(value)
        self.updateLabel()
        self.controller.updateVoxDisplayRange(self.minDisplayVox, self.maxDisplayVox)

    def setController(self, controller):
        self.controller = controller


class TriPlaneView(QWidget):
    def __init__(self, axial, sagittal, coronal, parent=None):
        super(TriPlaneView, self).__init__(parent)

        self.controller = None
        grid = QGridLayout()
        grid.addWidget(axial, 0, 0)
        grid.addWidget(sagittal, 0, 1)
        grid.addWidget(coronal, 0, 2)

        self.setLayout(grid)

    def setData(self, data):
        self.data = data

    def setController(self, controller):
        self.controller = controller


class PlaneView(QWidget):
    def __init__(self, controller, name, volume, numSlices, parent=None):
        super(PlaneView, self).__init__(parent)
        self.controller = controller
        label = QLabel()
        label.setText(name)
        self.sliceNumberLabel = QLabel()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(10)
        # self.slider.setSingleStep(1)
        self.slider.setMinimum(0)
        self.slider.setMaximum(numSlices)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.valueChanged)

        self.canvas = PlotCanvas(self.controller, name, volume)
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.sliceNumberLabel)
        vbox.addWidget(self.slider)
        vbox.addWidget(self.canvas)
        vbox.addStretch(1)
        self.setLayout(vbox)

    def setSlider(self, value):
        self.slider.setValue(value)

    def valueChanged(self, value):
        self.canvas.setSliceIndex(value)
        self.setSliceLabel(value)

    def setVolume(self, value):
        self.canvas.setVolume(value)

    def replot(self):
        self.canvas.plot()

    def clearPlot(self):
        self.canvas.clearPlot()

    def setMaxSlider(self, value):
        self.setSlider(0)
        self.slider.setMaximum(value)

    def setSliceLabel(self, value):
        self.sliceNumberLabel.setText(str(value))

    # def setController(self, controller):
    #     self.controller = controller


class PlotCanvas(FigureCanvas):
    def __init__(self, controller, sliceType, volume, parent=None):

        self.controller = controller
        self.sliceType = sliceType
        self.maxVoxVal = 0
        self.minVoxVal = 0
        self.volume = volume
        fig = Figure()
        FigureCanvas.__init__(self, fig)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.currentSliceNum = 0
        self.ax = self.figure.add_subplot(111)
        self.plot()

    def setVolume(self, value):
        self.volume = value
        self.plot()

    def forwards(self):
        self.currentSliceNum += 1
        self.plot()

    def setSliceIndex(self, value):
        self.currentSliceNum = value
        self.plot()

    def setMinVoxVal(self, value):
        self.minVoxVal = value

    def setMaxVoxVal(self, value):
        self.maxVoxVal = value

    def plot(self):
        self.ax.cla()
        self.ax.set_axis_off()

        if self.sliceType == "Axial":

            curSlice = self.controller.data[:, :, self.currentSliceNum, self.volume]
            self.ax.imshow(curSlice.T, cmap="gray", origin="lower", vmin=self.minVoxVal, vmax=self.maxVoxVal)

        elif self.sliceType == "Sagittal":

            curSlice = self.controller.data[self.currentSliceNum, :, :, self.volume]
            self.ax.imshow(curSlice.T, cmap="gray", origin="lower", aspect=256.0 / 54.0, vmin=self.minVoxVal,
                           vmax=self.maxVoxVal)

        elif self.sliceType == "Coronal":

            curSlice = self.controller.data[:, self.currentSliceNum, :, self.volume]
            self.ax.imshow(curSlice.T, cmap="gray", origin="lower", aspect=256.0 / 54.0, vmin=self.minVoxVal,
                           vmax=self.maxVoxVal)

        self.draw()

    def clearPlot(self):
        self.ax.cla()
        self.ax.set_axis_off()
        self.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    controller = Controller()
    sys.exit(app.exec_())
