# BrainScanMotionDetection

Developers, after cloning this repo, copy the 'Calgary_PS_DTI_Dataset' folder from the hard drive you were given, and place it in the root directory of the repo, as such:

- BrainScanMotionDetection
- - Calgary_PS_DTI_Dataset
- - Viewer
- - playground

This repo ignores the image and meta data files that came with the images, and only will included any additional files you have added that have different extensions (Details in .gitignore).

Our Viewier.py program will create a label.csv file for each .nii image file, so those label csv files will be added and pushed to the repo.

Please also send me your git username to be added so you have push permission to this repo. It is recommended that you create your own branch and merge to master branch, instead of pushing directly to the master branch. You may also fork the repo and do pull request to contribute if you prefer.


Dependencies:
- Python 3.7	(Included in Anaconda)
- PyQt5
- NiBabel
- Matplotlib	(Included in Anaconda)
- Numpy		(Included in Anaconda)
