import numpy as np

#raw values from their software
bvalName = 'sample_bval_750.txt'
bvecName = 'sample_bvec_750.txt'

#generated from their software
bmatrixName = 'sample_bmatrix_750.txt'

bval = np.loadtxt(bvalName, dtype=float, delimiter=' ')
bvec = np.loadtxt(bvecName, dtype=float, delimiter=' ')
bmatrix = np.loadtxt(bmatrixName, dtype=float, delimiter='\t')
#%%
#try generating our own bmatrix from bval and bvec
X = np.zeros([bval.shape[0], 6])
for i in range(0, 6):
    X[:,i] = bval

#bmatrix = X .* Y
Y = np.zeros([bvec.shape[0], 6])
Y[:, 0] = np.multiply(bvec[:,0],bvec[:,0])
Y[:, 1] = np.multiply(2*bvec[:,0], bvec[:,1])
Y[:, 2] = np.multiply(2*bvec[:,0], bvec[:,2])
Y[:, 3] = np.multiply(bvec[:,1], bvec[:,1])
Y[:, 4] = np.multiply(2*bvec[:,1], bvec[:,2])
Y[:, 5] = np.multiply(bvec[:,2], bvec[:,2])

bmatrixCalced = np.multiply(X, Y)

##Check if they are equal. All elements should return true
print(np.isclose(bmatrixCalced, bmatrix))