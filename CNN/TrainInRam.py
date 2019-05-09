'''
Loads datasets to RAM instead of using generating data batches on the fly
'''
import numpy as np
import time
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten, Conv2D, MaxPooling2D, BatchNormalization
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint
from keras.callbacks import TensorBoard


#%%
print("Loading data...")
prefix = "DataArrays/under400_2/"
X_train = np.load(prefix + "dataxtrain.npy")
X_test = np.load(prefix + "dataxtest.npy")
y_train = np.load(prefix + "dataytrain.npy")
y_test = np.load(prefix + "dataytest.npy")

y_train = y_train[:,1]
y_test = y_test[:,1]
print("Loaded")
#%%
print("Setting up model")
batchSize = 128
numGroups = 4
# Design model
layer_size = 32

NAME = 'b{}_{}_{}'.format(batchSize,numGroups,int(time.time()))  # model name with timestamp
model = Sequential()

tensorboard = TensorBoard(log_dir='logs/{}'.format(NAME))
checkpoint = ModelCheckpoint('weights/{}.h5'.format(NAME), monitor='val_loss', verbose=0, save_best_only=True, save_weights_only=False, mode='auto', period=1)
callbacks = [tensorboard, checkpoint]

#### Architecture ####
model.add(Conv2D(layer_size, (3,3), padding="same", activation="relu", input_shape=(128, 128, 1)))
model.add(BatchNormalization())
model.add(MaxPooling2D(pool_size=(3,3)))

for _ in range(numGroups):
    model.add(Conv2D(layer_size, (3,3), padding="same", activation="relu"))
    model.add(BatchNormalization())
    model.add(Conv2D(layer_size, (3,3), padding="same", activation="relu"))
    model.add(BatchNormalization())
    model.add(MaxPooling2D(pool_size=(2,2)))
    model.add(Dropout(0.2))
    layer_size *= 2
    
model.add(Flatten())

layer_size *= 2

for _ in range(2):
    model.add(Dense(layer_size, activation='relu'))
    model.add(BatchNormalization())
    model.add(Dropout(0.5))

model.add(Dense(1))
model.add(Activation('sigmoid'))
model.compile(loss='binary_crossentropy',
             optimizer=Adam(lr=0.008),
             metrics=['accuracy'])

#model.add(Dense(2))
#model.add(Activation('softmax'))

#model.compile(loss='categorical_crossentropy',
#             optimizer=Adam(lr=0.008),
#             metrics=['accuracy'])

# Train model on dataset
model.fit(X_train, y_train,validation_data=(X_test, y_test), batch_size=batchSize, epochs=100, callbacks = callbacks)

#%%