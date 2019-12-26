README
Place nii files in ../Data
Create a csv of bad volumes called Inputs/badVolumes.csv
*Note badVolumes.csv is 1-indexed to maintain consistency with other programs (first volume is numbered 1) 
*Inside the code everything is 0-indexed

Steps to run training
1.	MaxGenerator.py – Pulls maximum value from every volume of the scan and puts it into /Inputs/maxVals.pickle
2.	DataUndersample.py – Pregenerates resized and normalized slices for use in training
3.	TrainInRam.py – Loads pregenerated data to RAM and begins training