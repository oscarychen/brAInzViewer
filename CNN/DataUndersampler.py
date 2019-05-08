import numpy as np
import keras
from DataGeneratorSimple import DataGenerator
from LabelGenerator import LabelGenerator
import random
#%%

labelGenerator = LabelGenerator()
labelGenerator.setSliceStart(112)
labelGenerator.setSliceEnd(144)
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
numSamples = 100000
maxSamples = len(idList)
width = 128
height = 128
print(maxSamples, "potential slices")
print(numSamples, "desired slices")


#%%
labelVals = [labels[tempId] for tempId in idList]
negativeSamples = set()
positiveSamples = set()

while len(negativeSamples) < int(numSamples * ratio):
    index = random.randint(1,maxSamples)
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
X = np.zeros((numSamples,width, height, 1), np.float32)
y = np.zeros((numSamples,2), int)
count = 0
for i in allSamples:
    if count%100 == 0:
        print(count)
    tempId = idList[i]
    X[count,:,:,0] = dataGen.load_nii_slice(*tempId)
    label = labels[tempId]
    y[count,] = keras.utils.to_categorical(label,2)
    count+=1
#%%
prefix = "C:/Users/Eiden/Desktop/BrainScanMotionDetection/CNN/DataArrays/under/"
np.save(prefix + "datax.npy", X)
np.save(prefix + "datay.npy", y)
#%%
#X = np.load(prefix + "datax.npy")
#y = np.load(prefix + "datay.npy")
#%%
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)
#%%
np.save(prefix + "dataxtrain.npy", X_train)
np.save(prefix + "dataxtest.npy", X_test)
np.save(prefix + "dataytrain.npy", y_train)
np.save(prefix + "dataytest.npy", y_test)