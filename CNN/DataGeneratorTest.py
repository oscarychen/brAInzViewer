import numpy as np
import random
import time
from keras.models import Sequential
from keras.utils import Sequence
from keras.layers import Dense, Dropout, Activation, Flatten, Conv2D, MaxPooling2D, ZeroPadding2D, BatchNormalization
from DataGenerator import DataGenerator
from LabelGenerator import LabelGenerator
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint
from tensorflow.keras.callbacks import TensorBoard

labelGenerator = LabelGenerator()
idList = labelGenerator.get_idList()
labels = labelGenerator.get_labels()
maxVals = labelGenerator.get_maxVals()

random.seed(1)
random.shuffle(idList)

train_listIDs= idList[:int(len(idList)*0.05)]
val_listIDs = idList[int(len(idList)*0.05):]

# Parameters
params = {'labels': labels,
          'max_brightness': maxVals,
          'dim': (128,128),
          'batch_size': 8,
          'n_classes': 2,
          'n_channels': 1,
          'shuffle': True}

# Generators
training_generator = DataGenerator(train_listIDs, **params)
validation_generator = DataGenerator(val_listIDs, **params)
