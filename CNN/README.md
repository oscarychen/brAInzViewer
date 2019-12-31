# CNN Training Steps

Note that training should be run using a GPU supported by Tensorflow. The Tensorflow in the requirements folder is CPU only. Additional libraries and tools must be installed for GPU Tensorflow.

 - Place nii files in ../Data
 - Create a csv of bad volumes called Inputs/badVolumes.csv (Example provided)
   - Note badVolumes.csv is 1-indexed to maintain consistency with other programs (first volume is numbered 1) Inside the code everything is 0-indexed
 - Modify paths inside MaxGenerator.py and run
   - This script pulls the maximum value from every volume of the scan and puts it into /Inputs/maxVals.pickle
 - Modify paths and values inside DataUndersampler.py and run
   - This script pregenerates resized and normalized slices for use in training 
 - Modify file paths in TrainInRam.py and run
   - Loads pregenerated data to RAM and begins training
 - During training, run `tensorboard --logdir logs` and navigate to localhost:6006 in a web browser to monitor training