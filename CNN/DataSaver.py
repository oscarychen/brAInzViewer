import numpy as np
import keras
from keras.models import Sequential
from keras.utils import Sequence
from keras.layers import Dense, Dropout, Activation, Flatten, Conv2D, MaxPooling2D, ZeroPadding2D, BatchNormalization
from DataGeneratorSimple import DataGenerator
from LabelGenerator import LabelGenerator

#%%
    
labelGenerator = LabelGenerator()
labelGenerator.setSliceStart(124)
labelGenerator.setSliceEnd(132)
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
width = 128
height = 128
numSamples = len(idList)
print(numSamples, "slices to generate")
X = np.zeros((numSamples,width, height, 1), np.float32)
y = np.zeros((numSamples,2), int)

#%%
for i in range(numSamples):
    if i%100 == 0:
        print(i)
    tempId = idList[i]
    X[i,:,:,0] = dataGen.load_nii_slice(*tempId)
    label = labels[tempId]
    y[i,] = keras.utils.to_categorical(label,2)
#%%
prefix = "C:/Users/Eiden/Desktop/BrainScanMotionDetection/CNN/DataArrays/"
np.save(prefix + "datax.npy", X)
np.save(prefix + "datay.npy", y)
#%%
#X = np.load("datax.npy")
#y = np.load("datay.npy")
from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)
#%%
np.save(prefix + "dataxtrain.npy", X_train)
np.save(prefix + "dataxtest.npy", X_test)
np.save(prefix + "dataytrain.npy", y_train)
np.save(prefix + "dataytest.npy", y_test)