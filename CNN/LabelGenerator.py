import os
import pickle

class LabelGenerator:
    
    def __init__(self):
        self.folder = "../Calgary_PS_DTI_Dataset/"
        self.labelfname = "Bad750Volumes.csv"
        self.sliceStart = 96
        self.sliceEnd = 160
        self.niiFiles = list()
        self.sNames = dict()
        
        self.idList = list()
        self.labels = dict()
        self.maxVals = None
    
    def generateLabels(self):
        for dirpaths, dirs, files in os.walk(self.folder):
            for file in files:
                if file.endswith('.nii'):
                    filePath = os.path.join(dirpaths, file)
                    self.niiFiles.append(filePath)
                    sEnd = file.rfind('_')
                    if sEnd == -1:
                        sEnd = len(file)-4
                    sName = file[0:sEnd]
                    self.sNames[filePath] = sName

        #dict of bad volumes based on scan name
        print("Getting bad volumes from csv")
        badVols = dict()
        with open(self.labelfname) as f:
            lines = f.readlines()
            for i in range(1, len(lines)):
                line = lines[i].split(',')
                vols = line[1].strip()
                vols = vols.split(';')
                #subtract one for 0 indexing
                vols = [int(vol)-1 for vol in vols if vol != '']
                sName = line[0].upper().strip().replace('-','')
                badVols[sName] = vols

        print("Generating slice ids and labels")
        #ID format: (filepath, volume, direction, slice number)
        
        for file in self.niiFiles:
            sName = self.sNames[file]
            for volNum in range(35):
                label = 0
                if sName in badVols:
                    if volNum in badVols[sName]:
                        label = 1
                #64 slices centered around the middle assuming size 255
                for sliceNum in range(self.sliceStart,self.sliceEnd):
                    #sagittal
                    tempId = (file, volNum, 1, sliceNum)
                    self.idList.append(tempId)
                    self.labels[tempId] = label
                    #coronal
                    tempId = (file, volNum, 2, sliceNum)
                    self.idList.append(tempId)
                    self.labels[tempId] = label

        print("Getting max values from pickle file")
        
        with open ("maxVals.pickle", "rb") as f:
            self.maxVals = pickle.load(f)
        for file in self.niiFiles:
            for vol in range(35):
                self.maxVals[file, vol] = self.maxVals.pop((self.sNames[file], vol))
        print("Done")

        ##use idList, labels, and maxVals for machine learning part
    
    def get_idList(self):
        return self.idList
    def get_labels(self):
        return self.labels
    def get_maxVals(self):
        return self.maxVals
    def setSliceStart(self, sStart):
        self.sliceStart = sStart
    def setSliceEnd(self, sEnd):
        self.sliceEnd = sEnd