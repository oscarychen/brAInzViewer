import os
os.environ['KERAS_BACKEND']='plaidml.keras.backend'

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
labelGenerator.generateLabels()
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
          'batch_size': 64,
          'n_classes': 2,
          'n_channels': 1,
          'shuffle': True}

# Generators
training_generator = DataGenerator(train_listIDs, **params)
validation_generator = DataGenerator(val_listIDs, **params)

# Design model
layer_size = 16
NAME = '{}'.format(int(time.time()))  # model name with timestamp
model = Sequential()
tensorboard = TensorBoard(log_dir='logs/{}'.format(NAME))
checkpoint = ModelCheckpoint('weights/{}.h5'.format(NAME), monitor='val_loss', verbose=0, save_best_only=True, save_weights_only=False, mode='auto', period=1)
callbacks = [tensorboard, checkpoint]

#### Architecture ####
model.add(Conv2D(layer_size, (3,3), padding="same", activation="relu", input_shape=(128, 128, 1)))
model.add(BatchNormalization())
model.add(MaxPooling2D(pool_size=(3,3)))

for _ in range(2):
    model.add(Conv2D(layer_size, (3,3), padding="same", activation="relu"))
    model.add(BatchNormalization())
    model.add(Conv2D(layer_size, (3,3), padding="same", activation="relu"))
    model.add(BatchNormalization())
    model.add(MaxPooling2D(pool_size=(2,2)))
    model.add(Dropout(0.35))
    layer_size *= 2
    
model.add(Flatten())

layer_size *= 2

for _ in range(2):
    model.add(Dense(layer_size, activation='relu'))
    model.add(BatchNormalization())
    model.add(Dropout(0.6))

model.add(Dense(2))
model.add(Activation('sigmoid'))

model.compile(loss='categorical_crossentropy',
             optimizer=Adam(lr=0.008),
             metrics=['accuracy'])

# Train model on dataset
model.fit_generator(generator=training_generator,
                    validation_data=validation_generator,
                    use_multiprocessing=True,
                    workers=2)