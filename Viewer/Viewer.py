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
from threading import Lock

VOX_MAX_VAL = 2500
viewUpdateLock = Lock()
labelWriteLock = Lock()
sliderLock = Lock()
sliceLabelLock = Lock()
buttonLock = Lock()

class Controller:

    def __init__(self):
        self.data = None
        self.labelTypes = LabelTypes()
        self.labelData = LabelData()

        self.niiPaths = list()
        self.openFolder()
        self.fileSelected = None

        self.axialSliceNum = 0
        self.sagittalSliceNum = 0
        self.coronalSliceNum = 0
        self.volumeNum = 0

        self.brightnessSelector = DisplayBrightnessSelectorView(self)

        self.axialLabelView = LabelView(self, 'Axial', self.labelTypes)
        self.sagittalLabelView = LabelView(self, 'Sagittal', self.labelTypes)
        self.coronalLabelView = LabelView(self, 'Coronal', self.labelTypes)

        self.axialView = SliceView(self, "Axial", self.axialSliceNum, self.axialLabelView)
        self.sagittalView = SliceView(self, "Sagittal", self.sagittalSliceNum, self.sagittalLabelView)
        self.coronalView = SliceView(self, "Coronal", self.coronalSliceNum, self.coronalLabelView)
        self.triPlaneView = TriPlaneView(self.axialView, self.sagittalView, self.coronalView)
        self.fileListView = FileListView(self, self.niiPaths)
        self.volumeSelectView = VolumeSelectView(self, self.triPlaneView, self.fileListView, self.brightnessSelector)
        self.fileListView.setCurrentRow(0)


        self.showView()

    def showView(self):
        """Called to show views after initialization"""
        self.volumeSelectView.show()
        self.updateViews()

    def openFolder(self):
        """Gets called upon Controller initialization to prompt for directory"""
        folder = QFileDialog.getExistingDirectory(None, caption='Select folder to open', directory='../')
        if folder:
            self.niiPaths = self.getNiiFilePaths(folder)
            if len(self.niiPaths) == 0:
                QMessageBox.about(self, "Error", "No Nii Files Found")
                print("No Nii Files Found")
                exit(0)
            self.fileSelected = self.niiPaths[0]
            nii = nib.load(self.fileSelected)
            self.data = nii.get_fdata()
            self.labelData.setFilePath(self.fileSelected)
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

    def updateVoxDisplayRange(self, minValue, maxValue):
        """Gets called by DisplayBrightnessSelectorView when the brightness sliders are moved"""
        self.axialView.canvas.setMinVoxVal(minValue)
        self.axialView.canvas.setMaxVoxVal(maxValue)
        self.coronalView.canvas.setMinVoxVal(minValue)
        self.coronalView.canvas.setMaxVoxVal(maxValue)
        self.sagittalView.canvas.setMinVoxVal(minValue)
        self.sagittalView.canvas.setMaxVoxVal(maxValue)
        self.updateViews()

    def checkSelectionRanges(self):
        """Verify and update the current selection values of sliders"""
        if self.axialSliceNum >= self.data.shape[2]:
            self.axialSliceNum = self.data.shape[2] - 1
        if self.sagittalSliceNum >= self.data.shape[0]:
            self.sagittalSliceNum = self.data.shape[0] - 1
        if self.coronalSliceNum >= self.data.shape[1]:
            self.coronalSliceNum = self.data.shape[1] - 1
        if self.volumeNum >= self.data.shape[3]:
            self.volumeNum = self.data.shape[3] - 1

    def changeFile(self, file):
        """Gets called by the FileListView when a file selection is changed"""
        self.fileSelected = file
        nii = nib.load(self.fileSelected)
        self.data = nii.get_fdata()
        self.volumeSelectView.fileLabel.setText(file)
        self.volumeSelectView.setMaxSlider(self.data.shape[3] - 1)

        self.labelData.saveToFile()     # save labelData to csv, and reset labelData
        self.labelData.setFilePath(self.fileSelected) # set labelData to read new file

        self.checkSelectionRanges()
        self.updateViews()

    def changeVolume(self, value):
        """Gets called by the VolumeSelectView when volume slider is moved"""
        self.volumeNum = value

        self.checkSelectionRanges()
        self.updateViews()

    def changeLabel(self, sliceType, label, value):
        """Gets called by the """
        sliceNum = self.getSliceNum(sliceType)
        self.labelData.setLabel(self.volumeNum, sliceType, sliceNum, label, value)

    def getLabelsForSlice(self, sliceType):
        """Returns a dictionary of Labels and their values"""
        sliceNum = self.getSliceNum(sliceType)
        return self.labelData.getLabels(self.volumeNum, sliceType, sliceNum)

    def changeSliceNum(self, name, sliceNum):
        """Gets called by the SliceView when slice slider is moved"""

        if name == 'Axial':
            self.axialSliceNum = sliceNum
            self.updateAxialView()
        elif name == 'Sagittal':
            self.sagittalSliceNum = sliceNum
            self.updateSagittalView()
        elif name == 'Coronal':
            self.coronalSliceNum = sliceNum
            self.updateCoronalView()

    def updateViews(self):
        """Updates View classes"""
        viewUpdateLock.acquire()
        self.volumeSelectView.updateView(self.volumeNum, self.fileSelected)

        self.axialView.setMaxSlider(self.data.shape[2] - 1)
        self.sagittalView.setMaxSlider(self.data.shape[0] - 1)
        self.coronalView.setMaxSlider(self.data.shape[1] - 1)

        self.updateAxialView()
        self.updateSagittalView()
        self.updateCoronalView()
        viewUpdateLock.release()

    def updateAxialView(self):
        self.axialView.canvas.setSliceIndex(self.axialSliceNum)
        self.axialView.setSliceLabel(self.axialSliceNum)
        self.axialView.setSlider(self.axialSliceNum)
        self.axialLabelView.updateButtons(self.getLabelsForSlice('Axial'))
        self.axialView.canvas.plot(self.getPlotData('Axial'))

    def updateSagittalView(self):
        self.sagittalView.canvas.setSliceIndex(self.sagittalSliceNum)
        self.sagittalView.setSliceLabel(self.sagittalSliceNum)
        self.sagittalView.setSlider(self.sagittalSliceNum)
        self.sagittalLabelView.updateButtons(self.getLabelsForSlice('Sagittal'))
        self.sagittalView.canvas.plot(self.getPlotData('Sagittal'))

    def updateCoronalView(self):
        self.coronalView.canvas.setSliceIndex(self.coronalSliceNum)
        self.coronalView.setSliceLabel(self.coronalSliceNum)
        self.coronalView.setSlider(self.coronalSliceNum)
        self.coronalLabelView.updateButtons(self.getLabelsForSlice('Coronal'))
        self.coronalView.canvas.plot(self.getPlotData('Coronal'))

    def getSliceNum(self, sliceType):
        """Returns the current slice number given slice type"""
        if sliceType == 'Axial':
            return self.axialSliceNum
        elif sliceType == 'Sagittal':
            return self.sagittalSliceNum
        elif sliceType == 'Coronal':
            return self.coronalSliceNum
        else:
            return 0

    def getAspectRatio(self, sliceType):
        """Returns the aspect ratio needed based on data shape"""
        if sliceType == 'Axial':
            return self.data.shape[0] / self.data.shape[1]
        elif sliceType == 'Sagittal':
            return self.data.shape[1] / self.data.shape[2]
        elif sliceType == 'Coronal':
            return self.data.shape[0] / self.data.shape[2]
        else:
            return 1

    def getPlotData(self, sliceType):
        """Produces data depending on the sliced view"""
        if sliceType == 'Axial':
            return self.data[:, :, self.axialSliceNum, self.volumeNum]
        elif sliceType == 'Sagittal':
            return self.data[self.sagittalSliceNum, :, :, self.volumeNum]
        elif sliceType == 'Coronal':
            return self.data[:, self.coronalSliceNum, :, self.volumeNum]


class LabelTypes:
    """A class that holds label typing data"""

    def __init__(self):
        self.labelData = dict()
        # Key: label category, Value: list of labels the category
        self.labelData = {'Labels': ['Blur', 'Gap/Line', 'Dimmed', 'Tunneling']}

    def getLabelKeys(self):
        """Return list of keys"""
        return self.labelData.keys()

    def getLabelValueByKey(self, key):
        """Return list of values for a given key"""
        return self.labelData[key]

    def addKey(self, category):
        """Add a new category"""
        if category not in self.labelData:
            self.labelData[category] = list()

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


class LabelData:
    """Keeps the current instance's label data for the .nii file that is open.
    This object is shared across all volumes for a given .nii file so that we don't save/read from disk each time
    the volume slider is moved, and allowing smooth scrubbing of the volume slider"""
    def __init__(self):
        self.filePath = None
        self.labelData = dict()   # Key: (volume, sliceType, sliceNum), Value: a dictionary containing label and values

    def setFilePath(self, file):
        self.filePath = file

    def saveToFile(self):
        pass ##TODO: save data to csv
        self.clear()

    def clear(self):
        self.labelData.clear()

    def setLabel(self, volume, sliceType, sliceNum, label, value):
        """Set a single label value for a slice"""

        labelWriteLock.acquire()
        sliceLabels = dict()
        if (volume, sliceType, sliceNum) in self.labelData.keys():
            sliceLabels = self.labelData[(volume, sliceType, sliceNum)]
        else:
            sliceLabels[label] = value
        self.labelData[(volume, sliceType, sliceNum)] = sliceLabels
        labelWriteLock.release()

    def getLabels(self, volume, sliceType, sliceNum):
        """Get values of all labels for a slice, returns a dictionary
            where the key contains label, value contains label value"""
        sliceLabels = dict()

        if (volume, sliceType, sliceNum) in self.labelData.keys():
            sliceLabels= self.labelData[(volume, sliceType, sliceNum)]

        return sliceLabels


class LabelView(QWidget):
    """label selector"""

    def __init__(self, controller, sliceType, labelTypes, parent=Controller):
        super(LabelView, self).__init__()
        self.controller = controller
        self.sliceType = sliceType
        self.labelTypes = labelTypes
        self.grid = QGridLayout()
        self.buttons = list()
        self.initUI()

    def initUI(self):

        self.setLayout(self.grid)

        # get list of buttons
        labels = self.labelTypes.getLabelValueByKey('Labels')

        positions = [(row, col) for row in range(5) for col in range(2)]

        # populate buttons in view
        for position, label in zip(positions, labels):
            button = QPushButton(label)
            self.buttons.append(button)
            button.setCheckable(True)

            button.setStyleSheet("color: black; background-color: rgb(150,170,200);")
            # button.setStyleSheet("QPushButton#DCButton:checked {color: black; background-color: green;")

            button.clicked[bool].connect(self.button_clicked)
            self.grid.addWidget(button, *position)

        self.show()

    def updateButtons(self, labels):
        """Called by Controller to update button state from labels
        (of type dictionary, key: label, value: label value)"""
        buttonLock.acquire()
        for button in self.buttons:
            if button.text() in labels.keys() and labels[button.text()] is True:
                button.setChecked(True)
            else:
                button.setChecked(False)
        buttonLock.release()


    @pyqtSlot()
    def button_clicked(self):
        buttonLock.acquire()
        source = self.sender()
        buttonText = source.text()
        buttonStates = self.controller.getLabelsForSlice(self.sliceType)

        for labelKey in self.labelTypes.getLabelKeys():  # for each label category
            for labelType in self.labelTypes.getLabelValueByKey(labelKey):  # for each label in the category

                if labelType == buttonText:  # button correspond to a label

                    if labelType in buttonStates.keys():
                        buttonStates[buttonText] = not (buttonStates[buttonText])  # flip the boolean
                    else:
                        buttonStates[buttonText] = True    # add label

                    self.controller.changeLabel(self.sliceType, buttonText, buttonStates[buttonText])
                    break

        buttonLock.release()

        # print(f'Button {buttonText} set to {self.buttonStates[buttonText]}')


class FileListView(QListWidget):
    def __init__(self, controller, niiPaths, parent=Controller):
        super(FileListView, self).__init__()
        self.controller = controller
        # self.fileList = QListWidget(self)
        for item in niiPaths:
            self.addItem(item)
        maxListWidth = 400
        if self.sizeHintForColumn(0) < maxListWidth:
            maxListWidth = self.sizeHintForColumn(0)
        self.setMinimumWidth(maxListWidth)
        self.itemSelectionChanged.connect(self.selectedFileChanged)

    def selectedFileChanged(self):
        file = self.currentItem().text()
        self.controller.changeFile(file)


class VolumeSelectView(QWidget):
    """Main window, contains other view classes, contains slider for Volume selection"""

    def __init__(self, controller, triPlaneView, fileListView, brightnessSelector, parent=Controller):
        super(VolumeSelectView, self).__init__()

        self.controller = controller
        self.setWindowTitle("Nii Viewer and Labeler")
        self.resize(1280, 600)

        self.fileLabel = QLabel('No file loaded.')
        self.volumeLabel = QLabel()

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(1)
        # self.slider.setSingleStep(1)
        # self.slider.setMaximum(0)
        self.slider.setMinimum(0)
        self.slider.valueChanged.connect(self.volumeChanged)

        self.volumeLabel.setText('0')

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

    def volumeChanged(self, value):
        sliderLock.acquire()
        self.volumeLabel.setText(str(value))
        self.controller.changeVolume(value)
        sliderLock.release()

    def setMaxSlider(self, value):
        self.slider.setMaximum(value)

    def updateView(self, sliderValue, fileLabel):
        self.fileLabel.setText(fileLabel)
        self.volumeLabel.setText(f'Volume: {sliderValue + 1}')
        self.slider.setValue(sliderValue)


class DisplayBrightnessSelectorView(QWidget):
    """The range (dual-value) slider for adjust voxel brightness."""

    def __init__(self, controller, parent=Controller):
        super(DisplayBrightnessSelectorView, self).__init__()
        self.label = QLabel('Voxel Display Boundaries')
        self.startProportion = 0.1  # the start slider's range proportion to the entire range length
        self.startSliderMaxValue = int(VOX_MAX_VAL * self.startProportion)  # the max value of the start slider
        self.endSliderMaxValue = int(VOX_MAX_VAL * (1 - self.startProportion))  # the max value of the end slider
        self.minDisplayVox = 0  # the converted min value for displaying voxel
        self.maxDisplayVox = VOX_MAX_VAL  # the converted max value for displaying voxel
        self.controller = controller
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

        # End Slider Widget
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

    def setStartSliderValue(self, value):
        self.startSlider.setValue(value)

    def setEndSliderValue(self, value):
        self.endSlider.setValue(value)


class TriPlaneView(QWidget):
    """View wrapper that contains 3 PlaneView objects"""

    def __init__(self, axial, sagittal, coronal, parent=Controller):
        super(TriPlaneView, self).__init__()

        self.controller = None
        grid = QGridLayout()
        grid.addWidget(axial, 0, 0)
        grid.addWidget(sagittal, 0, 1)
        grid.addWidget(coronal, 0, 2)

        self.setLayout(grid)


class SliceView(QWidget):
    """Wrapper class for PlotCanvas class, contains slider to adjust slices"""

    def __init__(self, controller, sliceType, numSlices, labelView, parent=Controller):
        super(SliceView, self).__init__()
        self.controller = controller
        self.sliceType = sliceType
        label = QLabel()
        label.setText(sliceType)
        self.sliceNumberLabel = QLabel()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(10)
        # self.slider.setSingleStep(1)
        self.slider.setMinimum(0)
        self.slider.setMaximum(numSlices)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.sliceChanged)

        self.canvas = PlotCanvas(self.controller, sliceType)
        vbox = QVBoxLayout()
        vbox.addWidget(label)
        vbox.addWidget(self.sliceNumberLabel)
        vbox.addWidget(self.slider)
        vbox.addWidget(self.canvas)
        vbox.addWidget(labelView)
        vbox.addStretch(1)
        self.setLayout(vbox)

    def setSlider(self, value):
        self.slider.setValue(value)

    def sliceChanged(self, value):
        sliderLock.acquire()
        self.controller.changeSliceNum(self.sliceType, value)
        sliderLock.release()

    def setMaxSlider(self, value):
        self.setSlider(self.controller.getSliceNum(self.sliceType))
        self.slider.setMaximum(value)

    def setSliceLabel(self, sliceNumber):
        sliceLabelLock.acquire()
        self.sliceNumberLabel.setText(f'Slice: {sliceNumber + 1}')
        sliceLabelLock.release()


class PlotCanvas(FigureCanvas):
    """Displays the image"""

    def __init__(self, controller, sliceType, parent=Controller):
        self.controller = controller
        self.sliceType = sliceType
        self.maxVoxVal = 0
        self.minVoxVal = 0
        fig = Figure()
        FigureCanvas.__init__(self, fig)
        FigureCanvas.setSizePolicy(self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

        self.ax = self.figure.add_subplot(111)

    def setSliceIndex(self, value):
        self.currentSliceNum = value

    def setMinVoxVal(self, value):
        self.minVoxVal = value

    def setMaxVoxVal(self, value):
        self.maxVoxVal = value

    def plot(self, plotData):
        self.ax.cla()
        self.ax.set_axis_off()

        # plotData = self.controller.getPlotData(self.sliceType, self.currentSliceNum, self.volume)
        self.ax.imshow(plotData.T, cmap='gray', origin='lower', aspect=self.controller.getAspectRatio(self.sliceType),
                       vmin=self.minVoxVal, vmax=self.maxVoxVal)

        self.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    controller = Controller()
    sys.exit(app.exec_())
