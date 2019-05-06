import os
import nibabel as nib
import numpy as np
import pickle

#folders = ["..\\Calgary_PS_DTI_Dataset\\", "..\\b2000\\"]
folders = ["../Calgary_PS_DTI_Dataset/"]
niiFiles = list()
sNames = dict()
for folder in folders:
    for dirpaths, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.nii'):
                filePath = os.path.join(dirpaths, file)
                niiFiles.append(filePath)
                sEnd = file.rfind('_')
                if sEnd == -1:
                    sEnd = len(file)-4
                sName = file[0:sEnd]
                sNames[filePath] = sName
            
maxVals = dict()
count = 0
for file in niiFiles:
    count+=1
    sName = sNames[file]
    print(file, sName, count)
    nii = nib.load(file)
    data = nii.get_fdata()
    for vol in range(35):
        maxVal = np.max(data[:,:,:,vol])
        maxVals[sName, vol] = maxVal
#%%
with open('maxVals.pickle', 'wb+') as f:
    pickle.dump(maxVals, f)