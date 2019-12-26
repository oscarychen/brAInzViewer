"""
Match scan filenames to filenames in label file
"""

import os
import csv

def formatScanName(name):
    return name.strip().replace('.nii','').replace('_750','').upper()

niiFiles = []
folder = "../Data/CombinedData/"
labelfname = "AllScans.csv"

#find all nii file names
for dirpaths, dirs, files in os.walk(folder):
    for file in files:
        if file.endswith('.nii'):
            filePath = os.path.join(dirpaths, file)
            fileName = formatScanName(file)
            niiFiles.append(fileName)
niiFiles.sort()

#find all scan names listed in label file
scanNames = []          
with open(folder+labelfname) as f:
    lines = f.readlines()
    for i in range(1, len(lines)):
        line = formatScanName(lines[i])
        scanNames.append(line)
scanNames.sort()
  
# prints the missing and additional elements in scanNames
missingScans = set(scanNames).difference(niiFiles)
print("Labels without nii files:", missingScans, len(missingScans))

missingLabels = set(niiFiles).difference(scanNames)
print("Nii files without labels:", missingLabels, len(missingLabels)) 
