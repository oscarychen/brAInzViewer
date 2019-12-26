import numpy as np
from keras.models import load_model
from sklearn.metrics import f1_score, accuracy_score, recall_score, precision_score, confusion_matrix
import seaborn as sn
import pandas as pd
import matplotlib.pyplot as plt

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
prefix = "DataArrays/400000/"
X_train = np.load(prefix + "dataxtrain.npy")
X_test = np.load(prefix + "dataxtest.npy")
y_train = np.load(prefix + "dataytrain.npy")
y_test = np.load(prefix + "dataytest.npy")

y_train = y_train[:,1]
y_test = y_test[:,1]
print("Loaded")

#%%

model = load_model('models/model_v4.h5')

#%%
print("Predicting Train Set...")
prob_train = model.predict(X_train)
#%%
print("Predicting Test Set...")
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

#%%

def normalizeCM(cm):
    cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    return cm

def createCmDf(cm):
    df_cm = pd.DataFrame(cm, index = ["Motion", "No Motion"], columns = ["Motion", "No Motion"])
    return df_cm

cm_train = confusion_matrix(y_train, pred_train, labels = [1, 0])
cm_test = confusion_matrix(y_test,pred_test, labels = [1, 0])

cm_train = normalizeCM(cm_train)
cm_test = normalizeCM(cm_test)

df_train = createCmDf(cm_train)
df_test = createCmDf(cm_test)

fig, (ax1,ax2) = plt.subplots(ncols=2, figsize=(10, 4))
fmt = '10.2f'
im = sn.heatmap(df_train, ax=ax1, annot=True, cmap='coolwarm', fmt=fmt)
ax1.set_title("Train")
ax1.set_xlabel("Predicted")
ax1.set_ylabel("True")
sn.heatmap(df_test, ax=ax2, annot=True, cmap='coolwarm', fmt=fmt)
ax2.set_title("Test")
ax2.set_xlabel("Predicted")
ax2.set_ylabel("True")
fig.suptitle('Confusion Matrices', fontsize=16)
plt.savefig('ConfusionMatrices.png')
fig.show()