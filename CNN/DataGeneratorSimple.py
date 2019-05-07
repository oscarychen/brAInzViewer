import numpy as np
import nibabel as nib
import keras
import cv2

class DataGenerator(keras.utils.Sequence):
    """Generates data for Keras to process.nii files"""
    def __init__(self, list_IDs, labels, max_brightness, batch_size=64, dim=(128,64,1), n_channels=1,
                 n_classes=10, shuffle=True):
        """- list_IDs should be a list of tupples, each tupples consists of (file_path, vol_num, slice_type, slice_num).
           - labels should be a dictionary, the key is a tupple of (file_path, vol_num, slice_type, slice_num), and value
            is the label.
           - max_brightness should be a dictionary, the key is tuple of (file_path and vol_num), value is max voxel brightness of the volume, 
           used for normalizaing image data in the volume.
        """
        
        'Initialization'
        self.dim = dim
        self.batch_size = batch_size
        self.labels = labels
        self.list_IDs = list_IDs
        self.max_vox_val = max_brightness
        self.n_channels = n_channels
        self.n_classes = n_classes
        self.shuffle = shuffle
        self.on_epoch_end()

    def __len__(self):
        'Denotes the number of batches per epoch'
        return int(np.floor(len(self.list_IDs) / self.batch_size))

    def __getitem__(self, index):
        'Generate one batch of data'
        # Generate indexes of the batch
        indexes = self.indexes[index*self.batch_size:(index+1)*self.batch_size]

        # Find list of IDs
        list_IDs_temp = [self.list_IDs[k] for k in indexes]

        # Generate data
        X, y = self.__data_generation(list_IDs_temp)

        return X, y

    def on_epoch_end(self):
        'Updates indexes after each epoch'
        self.indexes = np.arange(len(self.list_IDs))
        if self.shuffle == True:
            np.random.shuffle(self.indexes)
            
    def __normalize(self, img, file_path, vol_num):
        """Normalize slices in a volume by the vox brightness value provided in self.max_vox_val"""
        maxVal = self.max_vox_val.get((file_path,vol_num), np.amax(img))
        return img/maxVal
    
    def __resize(self, img):
        """Ensure consistent size of each slice of data"""
        return cv2.resize(img, (self.dim[0],self.dim[1]), interpolation=cv2.INTER_NEAREST)
    
    def load_nii_slice(self, file_path, vol_num, slice_type, slice_num):
        """Load a single slice from nii file"""
        nii_file = nib.load(file_path)
        
        if slice_type == 0:  # Axial slice
            img = nii_file.dataobj[:,:,slice_num,vol_num]
        elif slice_type == 1:  # Sagittal slice
            img = nii_file.dataobj[slice_num,:,:,vol_num]
        elif slice_type == 2:  # Coronal slice
            img = nii_file.dataobj[:,slice_num,:,vol_num]
        
        normalized = self.__normalize(img, file_path, vol_num)
        
        return self.__resize(normalized)
    
    def __get_slice_label(self, file_path, vol_num, slice_type, slice_num):
        """Look for slice label given file_path, volume, slice_type, and slice_num,
        returns a default_label value if the label not found in the dictionary"""
        default_label = 0
        return self.labels.get((file_path, vol_num, slice_type, slice_num), default_label)
    
    def __data_generation(self, list_IDs_temp):
        'Generates data containing batch_size samples' # X : (n_samples, *dim, n_channels)
        # Initialization
        X = np.empty((self.batch_size, *self.dim, self.n_channels))
        y = np.empty((self.batch_size), dtype=int)

#         # Generate data for standard images
#         for i, ID in enumerate(list_IDs_temp):
#             # Store sample
#             X[i,] = np.load('data/' + ID + '.npy')
#             # Store class
#             y[i] = self.labels[ID]

        # Generate data for nii slices
        for i, ID in enumerate(list_IDs_temp):
            file_path, vol_num, slice_type, slice_num = ID
            X[i,:,:,0] = self.__load_nii_slice(file_path, vol_num, slice_type, slice_num)
            y[i] = self.__get_slice_label(file_path, vol_num, slice_type, slice_num)

        return X, keras.utils.to_categorical(y, num_classes=self.n_classes)