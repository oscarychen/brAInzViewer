# BrainScanMotionDetection
An easy way to explore .nii volumes and slices.

- Use the file selector to quickily switch between .nii files:
![](Demo/browse_files.gif)

- Use the volume and slice sliders to explore the volumes and slices:
![](Demo/explore_volumes.gif)

- Automated analysis of volumes for motion-induced damage in images:
![](Demo/analyze.gif)

Our built-in analyzer uses advanced A.I. algorithm to estimate the amount of damage induced by moving subjects during the scan.

- Flag the volumes you would like to exclude and export a new file:
![](Demo/export.gif)

- Video demo:
https://youtu.be/HMPbxrktTrA

# Download Installers
- OS X: [download](https://drive.google.com/file/d/1v6TZJHUCbZFDeAg8_MgzdRlFzSJmXwF3/view?usp=sharing)
- Windows: Link coming soon
- Linux: Link coming soon

# To run/build from source
- Python 3.6 is recommended to run or build from source
- Install all required dependencies from the requirements.txt:
	```
	pip install -r requirements.txt
	```
- Navigate to the Viewer folder:
	```
	cd Viewer
	```
- Run from source:
	```
	fbs run
	```
- Freeze code:
	```
	fbs freeze
	```

Sometimes fbs fails to copy some dependencies, you may need to manually copy the following packages from your environment/lib/python3.6/site-packagers/:
 -- tensorflow
 -- tensorflow_core
 -- absl
 -- astor
 -- google

 Copy the above packages to Viewer/target/brAInzViewer/

 On Mac, you should also copy the above packages to Viewer/target/brAInzViewer.app/Contents/MacOS/

- Compile installer:
	```
	fbs installer
	```
