import os
import csv

class LabelTypes:
    """A class that holds label typing"""

    def __init__(self):
        self.labelData = dict()
        # Key: label category, Value: list of labels the category
        self.labelData = None  # {'Labels': ['Gap', 'Blur', 'Dim']}

    def getLabelKeys(self):
        """Return list of keys"""
        return self.labelData.keys()

    def getLabelValueByKey(self, key):
        """Return list of values for a given key"""
        if self.labelData is not None:
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


class BadVolumes:
    """Keeps track of bad volumes for a given nii file"""

    def __init__(self, controller):
        self.controller = controller
        self.filePath = None
        self.changed = False
        self.data = list()

    def append(self, value):
        self.data.append(value)
        self.changed = True

    def remove(self, value):
        self.data.remove(value)
        self.changed = True

    def setFilePath(self, file):
        self.filePath = file
        self.clear()
        self.changed = False
        self.readFromFile()

    def readFromFile(self):
        try:
            badVolumesFile = os.path.splitext(self.filePath)[0] + '_badvolumes.csv'
            rowCount = 0
            with open(badVolumesFile) as file:
                reader = csv.reader(file, delimiter=',')
                for row in reader:
                    if rowCount > 0:
                        self.data.append(int(row[0]))
                    rowCount += 1
        except:
            print('DEBUG: BadVolumes encountered error while reading from file.')

    def clear(self):
        self.data.clear()

    def saveToFile(self):
        try:
            badVolumesFile = os.path.splitext(self.filePath)[0] + '_badvolumes.csv'
            with open(badVolumesFile, mode='w') as file:
                writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['bad_volume_num'])

                for vol in self.data:
                    writer.writerow([vol])

            self.clear()
            return True

        except:
            print('DEBUG: BadVolumes encountered error while writing to file.')
            return False


class LabelData:
    """Keeps the current instance's label data for the .nii file that is open.
    This object is shared across all volumes for a given .nii file so that we don't save/read from disk each time
    the volume slider is moved, and allowing smooth scrubbing of the volume slider"""

    def __init__(self, controller):
        self.controller = controller
        self.filePath = None
        self.changed = False
        self.labelData = dict()  # Key: (volume, sliceType, sliceNum), Value: a dictionary containing:
        # Labels as keys and values for the corresponding label

    def setFilePath(self, file):
        self.filePath = file
        self.clear()
        self.changed = False
        self.readFromFile()

    def printLabelData(self):
        """Print content to console for debug"""
        print('Printing label data content for current file:')
        for key, val in self.labelData.items():
            print(f'=> {key}')
            for label, labelVal in self.labelData[key].items():
                print(f'===========> {label}:{labelVal}')

    def readFromFile(self):
        try:
            labelFile = os.path.splitext(self.filePath)[0] + '_labels.csv'
            rowCount = 0
            # print(f'DEBUG: Reading from filename {labelFile}')
            with open(labelFile) as file:
                reader = csv.reader(file, delimiter=',')
                for row in reader:
                    if rowCount > 0 and len(row) > 5:  # skips the header row 0
                        self.populateData(row)
                    rowCount += 1
        except:
            pass
        # self.printLabelData()

    def populateData(self, row):
        """Gets a row from the csv file (label data for one slice), parse the content and add to the self.labelData"""
        sagittal = row[0]
        coronal = row[1]
        axial = row[2]
        volume = row[3]
        labelString = row[4]
        comment = row[5]
        sliceType = None
        sliceNum = None
        vol = None

        if volume != '':
            vol = int(volume)

        if sagittal != '':
            sliceType = 'Sagittal'
            sliceNum = int(sagittal)
        elif coronal != '':
            sliceType = 'Coronal'
            sliceNum = int(coronal)
        elif axial != '':
            sliceType = 'Axial'
            sliceNum = int(axial)

        if labelString != '':
            labels = labelString.split('/')
            labelsDict = dict()
            for label in labels:
                if label != '':
                    labelsDict[label] = True
            self.labelData[(vol, sliceType, sliceNum)] = labelsDict

        self.changed = False  # self.setLabel automatically switch self.changed to True, we overwrite it here to False

    def saveToFile(self):
        """Writes content of self.labelData to csv file in the same directory as the .nii image
        Returns True if write is succesful, otherwise False"""
        try:
            labelFile = os.path.splitext(self.filePath)[0] + '_labels.csv'
            # print(f'DEBUG: Writting to filename {labelFile}')
            with open(labelFile, mode='w') as file:
                writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['slice_sagittal', 'slice_coronal', 'slice_axial', 'volume', 'labels', 'comment'])

                for (volume, sliceType, sliceNum) in self.labelData.keys():
                    output = self.formatForCSV(volume, sliceType, sliceNum)
                    if output is not None:
                        writer.writerow(output)

            self.clear()
            # print(f'DEBUG: Finished writing csv to file')
            return True
        except:
            # print(f'DEBUG: Error writing csv to file')
            return False

    def formatForCSV(self, volume, sliceType, sliceNum):
        """Create a list to be written to CSV as a row.
        This row format in csv is: slice_sagittal,slice_coronal,slice_axial,volume,labels,comment.
        The labels are separated by /"""
        output = list()
        labelsDict = self.labelData[(volume, sliceType, sliceNum)]
        labelString = ''
        comment = ''

        if 'comment' in labelsDict.keys():
            comment = labelsDict['comment']

        # create label string which has all positive labels separated by '/'
        for label in labelsDict.keys():
            if label != 'comment' and labelsDict[label] is True:
                labelString = labelString + label + '/'

        if sliceType == 'Axial':
            output = ['', '', sliceNum, volume, labelString, comment]
        elif sliceType == 'Sagittal':
            output = [sliceNum, '', '', volume, labelString, comment]
        elif sliceType == 'Coronal':
            output = ['', sliceNum, '', volume, labelString, comment]

        if labelString == '' and comment == '':
            return None
        else:
            return output

    def clear(self):
        self.labelData.clear()

    def setLabel(self, volume, sliceType, sliceNum, label, value):
        """Set a single label value for a slice, add/modify in data dictionary"""
        # print(f'DEBUG: Adding label {label}:{value} for vol {volume}, slice {sliceType} #{sliceNum}')
        self.changed = True

        sliceLabels = dict()

        if (volume, sliceType, sliceNum) in self.labelData.keys():
            sliceLabels = self.labelData[(volume, sliceType, sliceNum)]
        else:
            sliceLabels[label] = value

        self.labelData[(volume, sliceType, sliceNum)] = sliceLabels
        # self.printLabelData()

    def getLabelsForSlice(self, volume, sliceType, sliceNum):
        """Get values of all labels for a slice, returns a dictionary
            where the key contains label, value contains label value"""
        sliceLabels = dict()

        if (volume, sliceType, sliceNum) in self.labelData.keys():
            sliceLabels = self.labelData[(volume, sliceType, sliceNum)]

        return sliceLabels

