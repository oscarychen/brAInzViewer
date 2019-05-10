from Views import *
from Models import LabelData, LabelTypes
from MachineLearning import MotionDetector

from PyQt5.QtWidgets import QMainWindow
from keras.models import load_model
import nibabel as nib
import os
import numpy as np
from PyQt5.QtWidgets import QFileDialog, QMessageBox


class Controller(QMainWindow):

    def __init__(self):
        super().__init__()
        self.data = None

        self.detectConfidenceThreshold = 0.7
        self.detectSliceThreshold = 0
        self.detectSliceRange = (112, 144)
        self.detectResizeDimension = (128, 128)
        self.detectorModelPath = '../CNN/weights/1557280788.h5'
        self.motionDetector = MotionDetector(self)
        self.badVolumeList = list()

        self.labelTypes = LabelTypes()
        self.labelData = LabelData(self)

        self.niiPaths = list()
        self.openFolder()
        self.fileSelected = None

        self.showSlicing = True
        self.axialSliceNum = self.data.shape[2] // 2        # Default axial slice
        self.sagittalSliceNum = self.data.shape[0] // 2     # Default sagittal slice
        self.coronalSliceNum = self.data.shape[1] // 2      # Default coronal slice
        self.volumeNum = 0                                  # Default volume

        self.brightnessSelector = DisplayBrightnessSelectorView(self)

        self.axialLabelView = LabelView(self, 'Axial', self.labelTypes)
        self.sagittalLabelView = LabelView(self, 'Sagittal', self.labelTypes)
        self.coronalLabelView = LabelView(self, 'Coronal', self.labelTypes)

        self.axialView = SliceView(self, "Axial", self.data.shape[2], self.axialLabelView)
        self.sagittalView = SliceView(self, "Sagittal", self.data.shape[0], self.sagittalLabelView)
        self.coronalView = SliceView(self, "Coronal", self.data.shape[1], self.coronalLabelView)
        self.triPlaneView = TriPlaneView(self.axialView, self.sagittalView, self.coronalView)
        self.fileListView = FileListView(self, self.niiPaths)
        self.volumeSelectView = VolumeSelectView(self, self.triPlaneView, self.fileListView, self.brightnessSelector)

        self.mainWindow = View(self, self.volumeSelectView)
        self.updateViews()
        self.fileListView.setCurrentRow(0)      # Default file

        # Default brightness
        self.brightnessSelector.handleEndSliderValueChange(np.amax(self.data[:,:,:,self.volumeNum])//6)


    def openFolder(self):
        """Gets called upon Controller initialization to prompt for directory"""
        folder = QFileDialog.getExistingDirectory(None, caption='Select folder to open', directory='../')
        if folder:
            self.niiPaths = self.getNiiFilePaths(folder)
            if len(self.niiPaths) == 0:
                w = QWidget()
                QMessageBox.warning(w, "Error", "No Nii Files Found")
                w.show()
                # print("No Nii Files Found")
                exit(0)
            self.fileSelected = self.niiPaths[0]
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
        self.badVolumeList.clear()

        if self.labelData.changed is False:  # no need to save label changes to file
            self.loadNewFile(file)

        else:  # save labels to csv file before switching file
            saveSuccess = self.labelData.saveToFile()
            if saveSuccess is False:  # Unsuccesful writing label data to file
                w = QWidget()
                QMessageBox.warning(w, 'Warning', 'Error encountered while saving labels related to ' +
                                    f'file {self.fileSelected}. Please make sure you have write permission to the directory.')
                w.show()
            else:  # Succesfully wrote label data to file, load next file
                self.loadNewFile(file)

    def loadNewFile(self, file):
        """Loads a new file into view"""
        self.clearPlots()
        self.fileSelected = file
        nii = nib.load(self.fileSelected)
        self.data = nii.get_fdata()
        self.volumeSelectView.fileLabel.setText(file)
        self.volumeSelectView.setMaxSlider(self.data.shape[3] - 1)
        self.labelData.setFilePath(self.fileSelected)  # set labelData to read new file
        self.checkSelectionRanges()
        self.updateViews()

    def writeLabelsToFile(self):
        """Writes label data to csv file, returns True if write is successful"""
        return self.labelData.saveToFile()

    def changeVolume(self, value):
        """Gets called by the VolumeSelectView when volume slider is moved"""
        self.volumeNum = value
        self.checkSelectionRanges()
        self.updateViews()

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

    def getNumberOfVolumes(self):
        return self.data.shape[3]

    def getNumberOfAxialSlices(self):
        return self.data.shape[2]

    def getNumberOfSagittalSlices(self):
        return self.data.shape[0]

    def getNumberOfCoronalSlices(self):
        return self.data.shape[1]

    def getVolumeSliderLowerTicksData(self):
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

    def getVolumeSliderUpperTicksData(self):
        """Returns a list of characters to be placed in the view for volume slider upper ticks"""
        # print(f'DEBUG: badVolumeList: {self.badVolumeList}')
        return self.badVolumeList

    def detectBadVolumes(self):
        """Runs the bad volume detector on the current file"""

        if self.motionDetector.model is None:
            self.loadPredictionModel()

        self.badVolumeList.clear()

        for v in range(self.data.shape[3]):
            volume = self.data[:, :, :, v]
            badSliceCount = 0

            self.motionDetector.setMaxBrightness(np.amax(volume))  # Set normalization parameter

            prediction = self.motionDetector.predictVolume(volume)

            if prediction is not None:
                for slicePrediction in prediction:
                    # print(f'DEBUG: slicePrediction: {slicePrediction}')
                    if slicePrediction[0] > self.detectConfidenceThreshold:
                        badSliceCount += 1

            if badSliceCount > self.detectSliceThreshold:
                self.badVolumeList.append('\u2690')  # Bad volume ticker
            else:
                self.badVolumeList.append(' ')  # Good volume ticker

        self.volumeSelectView.updateSliderTicks()

    def loadPredictionModel(self):
        try:
            model = load_model(self.detectorModelPath)
            self.motionDetector.setModel(model, self.detectSliceRange, self.detectResizeDimension)
        except:
            print('DEBUG: Failed to load model')