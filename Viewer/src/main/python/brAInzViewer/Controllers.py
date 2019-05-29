from Views import *
from Models import LabelData, LabelTypes, BadVolumes
from MachineLearning import MotionDetector
from PyQt5.QtWidgets import QWidget, QMainWindow
from keras.models import load_model
import nibabel as nib
import os
import numpy as np
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QProgressDialog
from PyQt5.QtCore import QThread, pyqtSignal


class Controller(QMainWindow):

    def __init__(self):
        super().__init__()
        self.data = None

        self.detectConfidenceThreshold = 0.7
        self.detectSliceNumProportionThreshold = 0.5
        halfWidth = 50
        lowerRange = 128 - halfWidth
        upperRange = 128 + halfWidth
        self.detectSliceRange = (lowerRange, upperRange)
        self.detectResizeDimension = (128, 128)
        self.detectorModelPath = '../../resources/model_v3.h5'
        self.motionDetector = MotionDetector()
        self.volumeWithLabelsList = list()  # A list of volumes with labels

        self.labelTypes = LabelTypes()
        self.labelData = LabelData(self)
        self.badVolumes = BadVolumes(self)

        self.niiPaths = list()
        self.nii = None
        self.rootFolder = None
        self.openFolder()
        self.fileSelected = None

        self.exportRootFolder = None

        self.showSlicing = True
        self.axialSliceNum = self.data.shape[2] // 2  # Default axial slice
        self.sagittalSliceNum = self.data.shape[0] // 2  # Default sagittal slice
        self.coronalSliceNum = self.data.shape[1] // 2  # Default coronal slice
        self.volumeNum = 0  # Default volume

        self.brightnessSelector = DisplayBrightnessSelectorView(self)

        self.axialLabelView = LabelView(self, 'Axial', self.labelTypes)
        self.sagittalLabelView = LabelView(self, 'Sagittal', self.labelTypes)
        self.coronalLabelView = LabelView(self, 'Coronal', self.labelTypes)

        self.axialView = SliceView(self, "Axial", self.data.shape[2], self.axialLabelView)
        self.sagittalView = SliceView(self, "Sagittal", self.data.shape[0], self.sagittalLabelView)
        self.coronalView = SliceView(self, "Coronal", self.data.shape[1], self.coronalLabelView)
        self.triPlaneView = TriPlaneView(self, self.axialView, self.sagittalView, self.coronalView)
        self.fileListView = FileListView(self, self.niiPaths)
        self.volumeSelectView = VolumeSelectView(self, self.triPlaneView, self.fileListView, self.brightnessSelector)

        self.mainWindow = View(self, self.volumeSelectView)
        self.updateViews()
        self.fileListView.setCurrentRow(0)  # Default file

        # Default brightness
        self.currentUpperBrightness = np.percentile(self.data[:, :, :, self.volumeNum], 90)
        self.brightnessSelector.endSlider.setValue(self.currentUpperBrightness)

        self.mainWindow.setStatusMessage('')

    def openFolder(self):
        """Gets called upon Controller initialization to prompt for directory"""
        self.rootFolder = QFileDialog.getExistingDirectory(None, caption='Select folder to open', directory='../')
        print(f'DEBUG: opening directory: {self.rootFolder}')
        if self.rootFolder:
            self.niiPaths = self.getNiiFilePaths(self.rootFolder)
            if len(self.niiPaths) == 0:
                w = QWidget()
                QMessageBox.warning(w, "Error", "No Nii Files Found")
                w.show()
                # print("No Nii Files Found")
                exit(0)
            self.fileSelected = self.niiPaths[0]
            print(f'DEBUG: File selected: {self.fileSelected}')
            nii = nib.load(self.fileSelected)
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
        self.volumeWithLabelsList.clear()

        if self.labelData.changed is False and self.badVolumes.changed is False:  # no need to save changes to file
            self.loadNewFile(file)

        else:
            # save labels to csv file before switching file
            saveSuccess = self.labelData.saveToFile() and self.badVolumes.saveToFile()
            if saveSuccess is False:  # Unsuccesful writing label data to file
                w = QWidget()
                QMessageBox.warning(w, 'Warning', 'Error encountered while saving files related to ' +
                                    f'file {self.fileSelected}. ' +
                                    'Please make sure you have write permission to the directories.')
                w.show()
            else:  # Succesfully wrote label data to file, load next file
                self.loadNewFile(file)

    def loadNewFile(self, file):
        """Loads a new file into view"""
        self.clearPlots()
        self.fileSelected = file
        self.nii = nib.load(self.fileSelected)
        self.data = self.nii.get_fdata()
        self.volumeSelectView.fileLabel.setText(file)
        self.volumeSelectView.setMaxSlider(self.data.shape[3] - 1)
        self.labelData.setFilePath(self.fileSelected)  # set labelData to read new file
        self.badVolumes.setFilePath(self.fileSelected)  # set badVolumes to read new file
        self.checkSelectionRanges()
        self.updateViews()

    # def writeLabelsToFile(self):
    #     """Writes label data to csv file, returns True if write is successful"""
    #     return self.labelData.saveToFile()

    def changeVolume(self, value):
        """Gets called by the VolumeSelectView when volume slider is moved"""
        self.volumeNum = value

        currentSliderValue = self.brightnessSelector.endSlider.value() + self.brightnessSelector.startSliderMaxValue
        newUpperBrightness = np.percentile(self.data[:, :, :, self.volumeNum], 90)
        newSliderValue = newUpperBrightness / self.currentUpperBrightness * currentSliderValue - self.brightnessSelector.startSliderMaxValue
        self.brightnessSelector.endSlider.setValue(newSliderValue)
        # print(f'DEBUG: currentSliderValue={currentSliderValue}, newSliderValue={newSliderValue}, currentUpperBrightness={self.currentUpperBrightness}, newUpperBrightness={newUpperBrightness}, , ')
        self.currentUpperBrightness = newUpperBrightness
        self.checkSelectionRanges()
        self.updateViews()

    def markVolumeForExclusion(self):
        """Called upon by view to mark a volume for exclusion, add/remove vol number"""
        if self.volumeNum not in self.badVolumes.data:  # Add
            self.badVolumes.append(self.volumeNum)
            self.triPlaneView.updateButtonState(True)
        else:  # Remove
            self.badVolumes.remove(self.volumeNum)
            self.triPlaneView.updateButtonState(False)

        self.volumeSelectView.updateSliderTicks()

        print(f'BadVolumes: {self.badVolumes.data}')

    def getExcludedVolumeList(self):
        return self.badVolumes.data

    def changeLabel(self, sliceType, label, value):
        """Gets called by the LabelView"""
        sliceNum = self.getSliceNum(sliceType)
        self.labelData.setLabel(self.volumeNum, sliceType, sliceNum, label, value)
        # print(f'DEBUG: label {label} changed to {value}.')
        self.volumeSelectView.updateSliderTicks()

    def getLabelsForSlice(self, sliceType):
        """Returns a dictionary of Labels and their values"""
        sliceNum = self.getSliceNum(sliceType)
        return self.labelData.getLabelsForSlice(self.volumeNum, sliceType, sliceNum)

    def changeSliceNum(self, name, sliceNum):
        """Gets called by the SliceView when slice slider is moved"""

        if name == 'Axial':
            self.axialSliceNum = sliceNum
        elif name == 'Sagittal':
            self.sagittalSliceNum = sliceNum
        elif name == 'Coronal':
            self.coronalSliceNum = sliceNum
        self.updateViews()

    def clearPlots(self):
        self.axialView.canvas.clearPlot()
        self.sagittalView.canvas.clearPlot()
        self.coronalView.canvas.clearPlot()
        self.triPlaneView.repaint()

    def updateViews(self):
        """Updates View classes"""
        self.volumeSelectView.updateView(self.volumeNum, self.fileSelected)

        if self.volumeNum in self.badVolumes.data:
            self.triPlaneView.updateButtonState(True)
        else:
            self.triPlaneView.updateButtonState(False)

        self.axialView.setMaxSlider(self.data.shape[2] - 1)
        self.sagittalView.setMaxSlider(self.data.shape[0] - 1)
        self.coronalView.setMaxSlider(self.data.shape[1] - 1)

        self.updateAxialView()
        self.updateSagittalView()
        self.updateCoronalView()

    def updateAxialView(self):
        self.axialView.canvas.setSliceIndex(self.axialSliceNum)
        self.axialView.setSliceLabel(self.axialSliceNum)
        self.axialView.setSlider(self.axialSliceNum)
        self.axialLabelView.updateButtons(self.getLabelsForSlice('Axial'))
        self.axialView.canvas.plot(self.getPlotData('Axial'))

        if self.showSlicing:
            self.axialView.canvas.plotLines(sagittal_v=self.sagittalSliceNum, coronal_h=self.coronalSliceNum)

        self.axialLabelView.repaint()

    def updateSagittalView(self):
        self.sagittalView.canvas.setSliceIndex(self.sagittalSliceNum)
        self.sagittalView.setSliceLabel(self.sagittalSliceNum)
        self.sagittalView.setSlider(self.sagittalSliceNum)
        self.sagittalLabelView.updateButtons(self.getLabelsForSlice('Sagittal'))
        self.sagittalView.canvas.plot(self.getPlotData('Sagittal'))

        if self.showSlicing:
            self.sagittalView.canvas.plotLines(axial_h=self.axialSliceNum, coronal_v=self.coronalSliceNum)

        self.sagittalView.repaint()

    def updateCoronalView(self):
        self.coronalView.canvas.setSliceIndex(self.coronalSliceNum)
        self.coronalView.setSliceLabel(self.coronalSliceNum)
        self.coronalView.setSlider(self.coronalSliceNum)
        self.coronalLabelView.updateButtons(self.getLabelsForSlice('Coronal'))
        self.coronalView.canvas.plot(self.getPlotData('Coronal'))

        if self.showSlicing:
            self.coronalView.canvas.plotLines(axial_h=self.axialSliceNum, sagittal_v=self.sagittalSliceNum)

        self.coronalView.repaint()

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

    def exitProgram(self):
        """Gets called by view when views are closed"""
        self.labelData.saveToFile()
        self.badVolumes.saveToFile()

    def getNumberOfVolumes(self):
        return self.data.shape[3]

    def getNumberOfAxialSlices(self):
        return self.data.shape[2]

    def getNumberOfSagittalSlices(self):
        return self.data.shape[0]

    def getNumberOfCoronalSlices(self):
        return self.data.shape[1]

    def getVolumeSliderLabelIndicatorTicksData(self):
        """Returns a list of characters to be placed in the view for volume slider lower ticks"""
        ticks = list()
        defaultTick = ' '
        markerTick = '\u25b2'  # triangle pointing up

        for v in range(self.getNumberOfVolumes()):
            ticks.append(defaultTick)

        for key, labels in self.labelData.labelData.items():
            volume, _, _ = key
            labelFlag = defaultTick
            for label, value in labels.items():
                if value is True:
                    labelFlag = markerTick
            ticks[volume] = labelFlag
        # print(f'ticks {ticks}')
        return ticks

    def getVolumeSliderExclusionTicksData(self):
        """Return a list of characters to be placed on the volume slider indicating volumes to be excluded"""
        ticks = list()
        defaultTick = ' '
        markerTick = '\u25b2'

        for v in range(self.getNumberOfVolumes()):
            ticks.append(defaultTick)

        for row in self.badVolumes.data:
            ticks[row] = markerTick

        return ticks

    def getCurrentVolumeExclusionState(self):
        """Returns true if the current volume is in exclusion list"""
        if self.volumeNum in self.badVolumes.data:
            return True
        else:
            return False

    def getVolumeSliderPredictionScoreTicksData(self):
        """Returns a list of characters to be placed in the view for volume slider upper ticks"""
        # print(f'DEBUG: badVolumeList: {self.badVolumeList}')
        return self.volumeWithLabelsList

    def saveNillFile(self):

        if self.exportRootFolder is None:
            self.setExportDirectory()

        relPath = os.path.relpath(self.fileSelected, self.rootFolder)
        exportPath = os.path.join(self.exportRootFolder, relPath)
        print(f'DEUBG: exportPath={exportPath}')

        os.makedirs(os.path.dirname(exportPath), exist_ok=True)

        badVolumes = self.badVolumes.data

        print(f'DEBUG: badVolumes={badVolumes}')

        goodVolumes = [vol for vol in range(self.data.shape[3]) if vol not in badVolumes]

        newData = self.data[:, :, :, goodVolumes]
        affine = self.nii.affine
        header = self.nii.header
        newNii = nib.Nifti1Image(newData, affine, header)
        newNii.to_filename(exportPath)

    def setExportDirectory(self):
        self.exportRootFolder = QFileDialog.getExistingDirectory(None, caption='Select folder to export to',
                                                                 directory='../')

    def loadPredictionModel(self):
        try:
            self.thread = LoadModel(self.motionDetector, self.detectorModelPath, self.detectSliceRange,
                                    self.detectResizeDimension)
            self.thread.results.connect(self.runDetection)
            self.thread.start()
        except:
            print('DEBUG: Failed to load model')

    def detectBadVolumes(self):
        """Runs the bad volume detector on the current file"""
        self.fileListView.lockView(True)
        self.progress = QProgressDialog()
        self.progress.setWindowTitle("Detection")
        self.progress.setLabelText("Loading Model...")
        self.progress.setRange(0, self.data.shape[3])
        self.progress.setValue(0)
        # self.progress.setCancelButtonText("Close")
        # self.progress.canceled.connect(self.progress.close)
        self.progress.setAutoClose(True)
        self.progress.setCancelButton(None)
        # self.progress.setWindowFlags(Qt.FramelessWindowHint)
        self.progress.show()

        if self.motionDetector.model is None:
            self.loadPredictionModel()
        else:
            self.runDetection()

    def runDetection(self):
        print("\nStarting predictions...")
        self.progress.setLabelText("Detecting Motion...")
        self.predictions = []
        self.thread = RunModel(self.data, self.motionDetector)
        self.thread.results.connect(self.updateDetectionResults)
        self.thread.start()

    def processPredictions(self):
        self.volumeWithLabelsList.clear()
        self.mainWindow.setStatusMessage('Running detection model. Please wait...')
        numVols = self.data.shape[3]
        badVolCount = 0

        for v in range(numVols):
            volume = self.data[:, :, :, v]
            totalSliceCount = 0
            badSliceCount = 0
            sliceConfidenceAccum = 0

            prediction = self.predictions[v]
            # Loop through each slice within the volume
            if prediction is not None:
                for slicePrediction in prediction:
                    score = slicePrediction[0]

                    if score > self.detectConfidenceThreshold:
                        badSliceCount += 1

                    sliceConfidenceAccum += score
                    totalSliceCount += 1

            # Summarizing predictin scores for the volume

            if badSliceCount >= self.detectSliceNumProportionThreshold * totalSliceCount:

                volumeScore = int(sliceConfidenceAccum / totalSliceCount * 100)
                self.volumeWithLabelsList.append(volumeScore)
                badVolCount += 1
            else:
                self.volumeWithLabelsList.append(' ')  # Good volume ticker
        self.mainWindow.setStatusMessage('Detection complete. Potential volumes with motion: {}'.format(badVolCount))
        self.volumeSelectView.updateSliderTicks()
        self.fileListView.lockView(False)

    def updateDetectionResults(self, prediction):
        self.predictions.append(prediction)
        self.progress.setValue(len(self.predictions))
        self.mainWindow.setStatusMessage('Detecting on volume {}'.format(len(self.predictions)))
        if len(self.predictions) == self.data.shape[3]:
            self.processPredictions()


class LoadModel(QThread):
    results = pyqtSignal()

    def __init__(self, motionDetector, detectorModelPath, detectSliceRange, detectResizeDimension):
        QThread.__init__(self)
        self.motionDetector = motionDetector
        self.detectorModelPath = detectorModelPath
        self.detectSliceRange = detectSliceRange
        self.detectResizeDimension = detectResizeDimension

    def loadModel(self):
        # model = load_model(self.detectorModelPath)
        self.motionDetector.setModel(self.detectorModelPath, self.detectSliceRange, self.detectResizeDimension)
        self.results.emit()

    def run(self):
        self.loadModel()


class RunModel(QThread):
    results = pyqtSignal(object)

    def __init__(self, data, motionDetector):
        QThread.__init__(self)
        self.data = data
        self.motionDetector = motionDetector

    def runModel(self):
        numVols = self.data.shape[3]
        for v in range(numVols):
            print("Detecting slices in volume", v)
            volume = self.data[:, :, :, v]
            self.motionDetector.setMaxBrightness(np.amax(volume))  # Set normalization parameter
            prediction = self.motionDetector.predictVolume(volume)
            self.results.emit(prediction)

    def run(self):
        self.runModel()
