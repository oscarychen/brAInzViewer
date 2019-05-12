import numpy as np
from keras.models import load_model
from sklearn.metrics import f1_score, accuracy_score, recall_score, precision_score

#%%
def calcScores(y, pred):
    averageType = 'macro'
    accuracy = accuracy_score(y, pred)
    print("Accuracy: %0.4f" % (accuracy))
    recall = recall_score(y, pred, average=averageType)
    print("Recall: %0.4f" % recall)
    precision = precision_score(y, pred, average=averageType)
    print("Precision: %0.4f" % precision)
    f1 = f1_score(y, pred, average=averageType)
    print("F-Score: %0.4f" % f1)
    return accuracy, recall, precision, f1

#%%
print("Loading data...")
prefix = "DataArrays/under400_2/"
X_train = np.load(prefix + "dataxtrain.npy")
X_test = np.load(prefix + "dataxtest.npy")
y_train = np.load(prefix + "dataytrain.npy")
y_test = np.load(prefix + "dataytest.npy")

y_train = y_train[:,1]
y_test = y_test[:,1]
print("Loaded")

#%%

model = load_model('weights/model_v3.h5')

#%%
print("Predicting Train...")
prob_train = model.predict(X_train)
#%%
print("Predicting Test...")
prob_test = model.predict(X_test)
print("Done predictions")
#%%
pred_train = [1 if prob > 0.5 else 0 for prob in prob_train]
pred_test = [1 if prob > 0.5 else 0 for prob in prob_test]

#%%
print("Train Scores")
train_scores = calcScores(y_train, pred_train)

print ("\nTest Scores")
test_scores = calcScores(y_test, pred_test)


