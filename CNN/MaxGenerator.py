'''
Pulls the maximum value of each volume for each nii file and puts it into the
maxVals.pickle file
'''
from Utils import formatScanName
import os
import nibabel as nib
import numpy as np
import pickle

folders = ["../Data/CombinedData"]
niiFiles = list()
sNames = dict()
for folder in folders:
    for dirpaths, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.nii'):
                filePath = os.path.join(dirpaths, file)
                niiFiles.append(filePath)
                sNames[filePath] = formatScanName(file)
            
maxVals = dict()
count = 0
for file in niiFiles:
    count+=1
    sName = sNames[file]
    print(file, sName, count)
    nii = nib.load(file)
    data = nii.get_fdata()
    for vol in range(data.shape[3]):
        maxVal = np.max(data[:,:,:,vol])
        maxVals[sName, vol] = maxVal
#%%
with open('Inputs/maxVals.pickle', 'wb+') as f:
    pickle.dump(maxVals, f)
print("Complete")