'''
Randomly chooses nii files to be part of train and test
Pulls appropriate slices from the test and train nii files for test and train sets
'''
import numpy as np
import keras
from DataGeneratorSimple import DataGenerator
from LabelGenerator import LabelGenerator
import random
import os

outputPath = "DataArrays/"
#fraction of bad slices (bad slice = positive classification)
badFraction = 0.5
#Train test split
trainTestSplit = 0.2
#Number of total samples
numSamples = 600000
#allowable distance from the middle of the volume to select slices from
gap = 50

#%%
labelGenerator = LabelGenerator()
labelGenerator.setSliceStart(128-gap)
labelGenerator.setSliceEnd(128+gap)
labelGenerator.generateLabels()

#Dictionary of IDs. 
#ID format: (filepath, volume, direction, slice number)
idList = labelGenerator.get_idList()
#Dictionary of labels with the ID as the key
labels = labelGenerator.get_labels()
#maximum values for each volume of each nii file
maxVals = labelGenerator.get_maxVals()

maxSamples = len(idList)
print(maxSamples, "potential slices")
print(numSamples, "desired slices\n")

#%%
# Parameters for data generator
params = {'labels': labels,
          'max_brightness': maxVals,
          'dim': (128,128),
          'batch_size': 32,
          'n_classes': 2,
          'n_channels': 1,
          'shuffle': True}

# Generator used to pull resized and normalized slices from the nii files
dataGen = DataGenerator(idList, **params)

#%%
testPositiveFraction = 0
while (testPositiveFraction < badFraction-0.025) or (testPositiveFraction > badFraction+0.025):
    print("Selecting positive and negative indices for train and test sets")
    
    #all labels in list form
    labelVals = [labels[tempId] for tempId in idList]
    
    #all potential negative and positive indices
    allNegativeIndices = [i for i, x in enumerate(labelVals) if x == 0]
    allPositiveIndices = [i for i, x in enumerate(labelVals) if x == 1]
    
    #randomly choose some indices
    positiveChoices = random.sample(range(len(allPositiveIndices)), int(numSamples*badFraction))
    negativeChoices = random.sample(range(len(allNegativeIndices)), int(numSamples*(1-badFraction)))
    
    #subset of indices randomly chosen
    negativeSamples = [allNegativeIndices[i] for i in negativeChoices]
    positiveSamples = [allPositiveIndices[i] for i in positiveChoices]
    
    print(len(negativeSamples), "negative samples")
    print(len(positiveSamples), "positive samples")
    
    #allSamples = negativeSamples.union(positiveSamples)
    allSamples = negativeSamples + positiveSamples
    
    ##Train Test Split 
    niiFiles = labelGenerator.get_niiFiles()
    random.shuffle(niiFiles)
    splitIndex = int(trainTestSplit*len(niiFiles))
    testNiis = niiFiles[0:splitIndex]
    
    ##Count number of test samples for sanity
    numTestSamples = 0
    numTestPositive = 0
    for i in allSamples:
        tempId = idList[i]
        if tempId[0] in testNiis:
            numTestSamples += 1
            if labels[tempId] == 1:
                numTestPositive += 1
    testPositiveFraction = numTestPositive/numTestSamples
    print(numTestSamples, "test samples, ", numTestSamples/numSamples*100, "percent test size")
    print(numTestPositive, "test positive samples, ", testPositiveFraction*100, "percent test positive\n")
    if (testPositiveFraction < badFraction-0.025) or (testPositiveFraction > badFraction+0.025):
        print("****Selecting slices again, test positive fraction out of range*****\n")

#%%
##Initialize train and test arrays

#dimensions of the resized images
width = 128
height = 128

print("Pulling slices from generated indices using data generator")
X_train = np.zeros((numSamples-numTestSamples,width, height, 1), np.float32)
y_train = np.zeros((numSamples-numTestSamples,2), int)
X_test = np.zeros((numTestSamples,width, height, 1), np.float32)
y_test = np.zeros((numTestSamples,2), int)
count = 0
testIndex = 0
trainIndex = 0

## Use the data generator to pull a resized and normalized slice for every
## slice index
for i in allSamples:
    if count%1000 == 0:
        print(count, "slices pulled")
    tempId = idList[i]
    label = labels[tempId]
    if tempId[0] in testNiis:
        X_test[testIndex,:,:,0] = dataGen.load_nii_slice(*tempId)
        y_test[testIndex,] = keras.utils.to_categorical(label,2)
        testIndex+=1
    else:
        X_train[trainIndex,:,:,0] = dataGen.load_nii_slice(*tempId)
        y_train[trainIndex,] = keras.utils.to_categorical(label,2)
        trainIndex+=1
    count+=1
print(testIndex+1, "test slices pulled")
print(trainIndex+1, "train slices pulled")
#%%
##Save to npy files
if not os.path.exists(outputPath):
    os.makedirs(outputPath)
print("Saving split files")
np.save(outputPath + "dataxtrain.npy", X_train)
np.save(outputPath + "dataxtest.npy", X_test)
np.save(outputPath + "dataytrain.npy", y_train)
np.save(outputPath + "dataytest.npy", y_test)
print("Saved")