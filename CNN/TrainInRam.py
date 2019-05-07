import numpy as np
import time
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten, Conv2D, MaxPooling2D, ZeroPadding2D, BatchNormalization
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint
from tensorflow.keras.callbacks import TensorBoard

#%%
prefix = "C:/Users/Eiden/Desktop/BrainScanMotionDetection/CNN/DataArrays/4/"
X_train = np.load(prefix + "dataxtrain.npy")
X_test = np.load(prefix + "dataxtest.npy")
y_train = np.load(prefix + "dataytrain.npy")
y_test = np.load(prefix + "dataytest.npy")
#%%

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

for _ in range(4):
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
model.fit(X_train, y_train,validation_data=(X_test, y_test), batch_size=128, epochs=3, callbacks=callbacks)