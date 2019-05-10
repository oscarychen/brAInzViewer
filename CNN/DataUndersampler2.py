'''
Randomly chooses nii files to be part of train and test
Pulls appropriate slices from the test and train nii files for test and train sets
'''
import numpy as np
import keras
from DataGeneratorSimple import DataGenerator
from LabelGenerator import LabelGenerator
import random
#%%
gap = 50
labelGenerator = LabelGenerator()
labelGenerator.setSliceStart(128-gap)
labelGenerator.setSliceEnd(128+gap)
labelGenerator.generateLabels()
idList = labelGenerator.get_idList()
labels = labelGenerator.get_labels()
maxVals = labelGenerator.get_maxVals()

#%%

# Parameters
params = {'labels': labels,
          'max_brightness': maxVals,
          'dim': (128,128),
          'batch_size': 32,
          'n_classes': 2,
          'n_channels': 1,
          'shuffle': True}

# Generators
dataGen = DataGenerator(idList, **params)

#%%
ratio = 0.5
trainTestSplit = 0.1
numSamples = 400000
maxSamples = len(idList)
width = 128
height = 128
print(maxSamples, "potential slices")
print(numSamples, "desired slices")


#%%
print("Generating Random Indices")
labelVals = [labels[tempId] for tempId in idList]
negativeSamples = set()
positiveSamples = set()

while len(negativeSamples) < int(numSamples * ratio):
    index = random.randint(1,maxSamples-1)
    if labelVals[index] == 0:
        negativeSamples.add(index)
while len(positiveSamples) < int(numSamples * ratio):
    index = random.randint(0,maxSamples-1)
    if labelVals[index] == 1:
        positiveSamples.add(index)
negativeLabels = [labelVals[index] for index in negativeSamples]
positiveLabels = [labelVals[index] for index in positiveSamples]
print(sum(negativeLabels), sum(positiveLabels))
allSamples = negativeSamples.union(positiveSamples)

#%%
#train test split
niiFiles = labelGenerator.get_niiFiles()
random.shuffle(niiFiles)
splitIndex = int(trainTestSplit*len(niiFiles))
testNiis = niiFiles[0:splitIndex]
numTestSamples = 0
for i in allSamples:
    tempId = idList[i]
    if tempId[0] in testNiis:
        numTestSamples += 1
print(numTestSamples, "test samples, ", numTestSamples/numSamples)

#%%
print("Pulling Slices")
X_train = np.zeros((numSamples-numTestSamples,width, height, 1), np.float32)
y_train = np.zeros((numSamples-numTestSamples,2), int)
X_test = np.zeros((numTestSamples,width, height, 1), np.float32)
y_test = np.zeros((numTestSamples,2), int)
count = 0
testIndex = 0
trainIndex = 0
for i in allSamples:
    if count%100 == 0:
        print(count)
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
print(testIndex+1, "test slices pulled", trainIndex+1, "train slices pulled")
#%%
prefix = "DataArrays/"
print("Saving split files")
np.save(prefix + "dataxtrain.npy", X_train)
np.save(prefix + "dataxtest.npy", X_test)
np.save(prefix + "dataytrain.npy", y_train)
np.save(prefix + "dataytest.npy", y_test)
print("Saved")