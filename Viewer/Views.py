from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QSizePolicy,
                             QWidget, QPushButton, QSlider, QHBoxLayout,
                             QGridLayout, QLabel, QListWidget, QFrame, QLayout, QAction)
from PyQt5.QtCore import Qt, pyqtSlot, QMetaObject, QSize

from PyQt5 import QtGui

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

VOX_MAX_VAL = 5000


class View(QMainWindow):
    """Main view window wrapper class"""

    def __init__(self, controller, volumeSelectView):
        super().__init__()
        self.parent = controller
        self.controller = controller
        self.volumeSelectView = volumeSelectView
        self.setCentralWidget(self.volumeSelectView)

        mainMenu = self.menuBar()
        mainMenu.setNativeMenuBar(False)  # Needed for Mac OS
        fileMenu = mainMenu.addMenu('Options')

        analyzeButton = QAction('Analyze Volumes', self)
        analyzeButton.triggered.connect(self.analyzeButtonPressed)
        fileMenu.addAction(analyzeButton)
        self.resize(1280, 600)
        self.show()

    def analyzeButtonPressed(self):
        self.controller.detectBadVolumes()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        """Triggered when the window is being closed"""
        self.controller.exitProgram()


class LabelView(QWidget):
    """label selector"""

    def __init__(self, controller, sliceType, labelTypes):
        super(LabelView, self).__init__()
        self.parent = controller
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

        # self.show()

    def updateButtons(self, labels):
        """Called by Controller to update button state from labels
        (of type dictionary, key: label, value: label value)"""
        for button in self.buttons:
            if button.text() in labels.keys() and labels[button.text()] is True:
                button.setChecked(True)
            else:
                button.setChecked(False)

    @pyqtSlot()
    def button_clicked(self):
        source = self.sender()
        buttonText = source.text()
        buttonStates = self.controller.getLabelsForSlice(self.sliceType)

        for labelKey in self.labelTypes.getLabelKeys():  # for each label category
            for labelType in self.labelTypes.getLabelValueByKey(labelKey):  # for each label in the category

                if labelType == buttonText:  # button correspond to a label

                    if labelType in buttonStates.keys():
                        buttonStates[buttonText] = not (buttonStates[buttonText])  # flip the boolean
                    else:
                        buttonStates[buttonText] = True  # add label

                    self.controller.changeLabel(self.sliceType, buttonText, buttonStates[buttonText])
                    break

        # print(f'Button {buttonText} set to {self.buttonStates[buttonText]}')


class FileListView(QListWidget):
    def __init__(self, controller, niiPaths):
        super(FileListView, self).__init__()
        self.parent = controller
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

    def selectItem(self, text):
        """Selects an item from the file list by providing a text string that matches the list item"""
        items = self.findItems(text, Qt.MatchExactly)
        if len(items) > 0:
            self.setCurrentRow(self.row(items[0]))


class SliderTicker(QWidget):
    """A widget that sits over/under sliders to add indicator to slider items, such as label existence"""

    def __init__(self):
        super(QWidget, self).__init__()
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

    def setTicks(self, list):
        """Receives a list of characters to be displayed"""
        self.clearTicks()
        for item in list:
            label = QLabel(str(item))
            self.layout().addWidget(label)

    def clearTicks(self):
        """Removes items currently in display"""
        for i in reversed(range(self.layout().count())):
            # self.layout().itemAt(i).widget().setParent(None)
            self.layout().itemAt(i).widget().deleteLater()


class VolumeSelectView(QWidget):
    """Top QWidget class, contains other view classes, contains slider for Volume selection"""

    def __init__(self, controller, triPlaneView, fileListView, brightnessSelector):
        super(VolumeSelectView, self).__init__()
        self.parent = controller
        self.controller = controller
        self.setWindowTitle("Nii Viewer and Labeler")

        self.fileLabel = QLabel('No file loaded.')
        self.volumeLabel = QLabel()

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)
        self.slider.setTickInterval(1)
        self.slider.setContentsMargins(0, 0, 0, 0)
        self.slider.setMinimum(0)
        self.slider.valueChanged.connect(self.volumeChanged)

        self.sliderUpperTicker = SliderTicker()
        self.sliderUpperTicker.setContentsMargins(0, 0, 0, 0)

        self.sliderLowerTicker = SliderTicker()
        self.sliderLowerTicker.setContentsMargins(0, 0, 0, 0)

        self.volumeLabel.setText('0')

        # Left-half: data display area
        vbox = QVBoxLayout()
        vbox.addWidget(self.fileLabel)
        vbox.addWidget(self.volumeLabel)
        vbox.addWidget(self.sliderUpperTicker)
        vbox.addWidget(self.slider)
        vbox.addWidget(self.sliderLowerTicker)
        vbox.addWidget(triPlaneView)
        vbox.addWidget(brightnessSelector)

        # Right-half: file list area
        hbox = QHBoxLayout()
        hbox.addLayout(vbox)
        hbox.addWidget(fileListView)
        self.setLayout(hbox)

    def volumeChanged(self, value):
        self.volumeLabel.setText(str(value))
        self.controller.changeVolume(value)

    def setMaxSlider(self, value):
        self.slider.setMaximum(value)

    def updateView(self, sliderValue, fileLabel):
        self.fileLabel.setText(fileLabel)
        self.volumeLabel.setText(f'Volume: {sliderValue + 1}')
        self.slider.setValue(sliderValue)
        self.updateSliderTicks()

    def updateSliderTicks(self):
        """Called upon by Controller, passes a list of characters to displayed over the volume slider"""
        self.sliderLowerTicker.setTicks(self.controller.getVolumeSliderLowerTicksData())
        self.sliderUpperTicker.setTicks(self.controller.getVolumeSliderUpperTicksData())


class DisplayBrightnessSelectorView(QWidget):
    """The range (dual-value) slider for adjust voxel brightness."""

    def __init__(self, controller):
        super(DisplayBrightnessSelectorView, self).__init__()
        self.parent = controller
        self.label = QLabel('Voxel Display Boundaries')
        self.startProportion = 0.03  # the start slider's range proportion to the entire range length
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

        # self.show()

    def updateLabel(self):
        # print(f'Voxel sliders: {self.minDisplayVox}, {self.maxDisplayVox}')
        self.label.setText(f'Voxel Brightness Range:({self.minDisplayVox},{self.maxDisplayVox})')

    @pyqtSlot(int)
    def handleStartSliderValueChange(self, value):
        self.minDisplayVox = self.convertMinSliderToMinVox(value)
        self.updateLabel()
        self.controller.updateVoxDisplayRange(self.minDisplayVox, self.maxDisplayVox)

    @pyqtSlot(int)
    def handleEndSliderValueChange(self, value):
        self.maxDisplayVox = self.convertMaxSliderToMaxVox(value)
        self.updateLabel()
        self.controller.updateVoxDisplayRange(self.minDisplayVox, self.maxDisplayVox)

    def setStartSliderValue(self, value):
        self.startSlider.setValue(value)

    def setEndSliderValue(self, value):
        self.endSlider.setValue(value)


class TriPlaneView(QWidget):
    """View wrapper that contains 3 PlaneView objects"""

    def __init__(self, axial, sagittal, coronal):
        super(TriPlaneView, self).__init__()
        self.controller = None
        grid = QGridLayout()
        grid.addWidget(axial, 0, 0)
        grid.addWidget(sagittal, 0, 1)
        grid.addWidget(coronal, 0, 2)

        self.setLayout(grid)


class SliceView(QWidget):
    """Wrapper class for PlotCanvas class, contains slider to adjust slices"""

    def __init__(self, controller, sliceType, numSlices, labelView):
        super(SliceView, self).__init__()
        self.parent = controller
        self.controller = controller
        self.sliceType = sliceType
        label = QLabel()
        label.setText(sliceType)
        self.sliceNumberLabel = QLabel()
        self.slider = QSlider(Qt.Horizontal)
        self.setSliderStyle()
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
        self.controller.changeSliceNum(self.sliceType, value)

    def setMaxSlider(self, value):
        self.setSlider(self.controller.getSliceNum(self.sliceType))
        self.slider.setMaximum(value)

    def setSliceLabel(self, sliceNumber):
        self.sliceNumberLabel.setText(f'Slice: {sliceNumber + 1}')

    def setSliderStyle(self):

        sliderHandleColor = None

        if self.sliceType == 'Axial':

            self.slider.setStyleSheet("""
                                QSlider::groove:horizontal {
                                border: 1px solid #999999;
                                height: 1px; /* the groove expands to the size of the slider by default. by giving it a height, it has a fixed size */
                                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                                margin: 2px 0;
                                }

                                QSlider::handle:horizontal {
                                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #ed2a2a);
                                border: 1px solid #999999;
                                width: 15px;
                                margin: -8px 0; /* handle is placed by default on the contents rect of the groove. Expand outside the groove */
                                border-radius: 8px;
                                }
                                """)

        elif self.sliceType == 'Sagittal':

            self.slider.setStyleSheet("""
                                QSlider::groove:horizontal {
                                border: 1px solid #999999;
                                height: 1px;
                                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                                margin: 2px 0;
                                }

                                QSlider::handle:horizontal {
                                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #005dff);
                                border: 1px solid #999999;
                                width: 15px;
                                margin: -8px 0;
                                border-radius: 8px;
                                }
                                """)

        elif self.sliceType == 'Coronal':

            self.slider.setStyleSheet("""
                               QSlider::groove:horizontal {
                               border: 1px solid #999999;
                               height: 1px;
                               background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);
                               margin: 2px 0;
                               }

                               QSlider::handle:horizontal {
                               background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #ffffff, stop:1 #12e82b);
                               border: 1px solid #999999;
                               width: 15px;
                               margin: -8px 0;
                               border-radius: 8px;
                               }
                               """)


class PlotCanvas(FigureCanvas):
    """Displays the image"""

    def __init__(self, controller, sliceType):
        self.parent = controller
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

        self.ax.imshow(plotData.T, cmap='gray', origin='lower', aspect=self.controller.getAspectRatio(self.sliceType),
                       vmin=self.minVoxVal, vmax=self.maxVoxVal)
        self.draw()

    def clearPlot(self):
        self.ax.cla()
        self.ax.set_axis_off()
        self.draw()

    def plotLines(self, **lines):
        """Plots slice indicator lines"""

        linewidth = 1
        linestyle = '-'

        if 'sagittal_v' in lines.keys():
            self.ax.axvline(x=lines['sagittal_v'], color='blue', linewidth=linewidth, linestyle=linestyle)

        if 'coronal_h' in lines.keys():
            self.ax.axhline(y=lines['coronal_h'], color='green', linewidth=linewidth, linestyle=linestyle)

        if 'axial_h' in lines.keys():
            self.ax.axhline(y=lines['axial_h'], color='red', linewidth=linewidth, linestyle=linestyle)

        if 'coronal_v' in lines.keys():
            self.ax.axvline(x=lines['coronal_v'], color='green', linewidth=linewidth, linestyle=linestyle)

        self.draw()

