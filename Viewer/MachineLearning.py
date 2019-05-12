import numpy as np
import cv2
import tensorflow as tf
graph = tf.get_default_graph()
from keras.models import load_model

class MotionDetector:

    def __init__(self):
        self.model = None
        self.detectSliceRange = None
        self.maxBright = None  # used for normalizing voxel brightness values
        self.dim = None

    def setModel(self, modelPath, sliceRange, dimension):
        #self.model = model
        global graph
        with graph.as_default():
            self.model = load_model(modelPath)
        self.detectSliceRange = sliceRange
        self.dim = dimension

    def setDetectSliceRange(self, rangeVal):
        self.detectSliceRange = rangeVal

    def setMaxBrightness(self, value):
        self.maxBright = value

    def normalize(self, volume):
        return volume / np.amax(volume)

    def resize(self, volume):
        #numSlices = self.detectSliceRange[1] - self.detectSliceRange[0]
        resized = np.zeros((20, self.dim[0], self.dim[1], 1))
        i = 0
        for s in range(self.detectSliceRange[0], self.detectSliceRange[1], 10):  # for each sagittal slice
            img = volume[s, :, :]
            img = cv2.resize(img, (self.dim[0], self.dim[1]), interpolation=cv2.INTER_NEAREST)
            resized[i, :, :, 0] = img
            i += 1
        for s in range(self.detectSliceRange[0], self.detectSliceRange[1], 10):  # for each coronal slice
            img = volume[:, s, :]
            img = cv2.resize(img, (self.dim[0], self.dim[1]), interpolation=cv2.INTER_NEAREST)
            resized[i, :, :, 0] = img
            i += 1
        return resized

    def predictVolume(self, volume):
        slices = self.resize(self.normalize(volume))
        try:
            global graph
            with graph.as_default():
                prediction = self.model.predict(slices)
            
            # print(f'DEBUG: Predictions: {predictions}')
            return prediction
        except Exception as e:
            print('DEBUG: failed to run detection model.')
            print(e)

