# -*- coding: utf-8 -*-
"""「imbalanced_classification」的副本

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1wU5ZUertX2t0EAkrhBa7-vnbFexRK1Ws

### 掛載雲端硬碟
"""

from google.colab import drive
drive.mount('/content/drive')

"""## 1.將資料向量化"""

import csv
import numpy as np
import tensorflow as tf
# Get the real data from https://www.kaggle.com/mlg-ulb/creditcardfraud/
fname = "/content/drive/MyDrive/creditcard.csv"

all_features = []
all_targets = []
with open(fname) as f:
    for i, line in enumerate(f):
        if i == 0:
            print("HEADER:", line.strip())
            continue  # Skip header
        fields = line.strip().split(",")
        all_features.append([float(v.replace('"', "")) for v in fields[:-1]])
        all_targets.append([int(fields[-1].replace('"', ""))])
        if i == 1:
            print("EXAMPLE FEATURES:", all_features[-1])

features = np.array(all_features, dtype="float32")
targets = np.array(all_targets, dtype="uint8")
print("features.shape:", features.shape)
print("targets.shape:", targets.shape)

"""## 2.準備驗證資料"""

num_val_samples = int(len(features) * 0.2)
train_features = features[:-num_val_samples]
train_targets = targets[:-num_val_samples]
val_features = features[-num_val_samples:]
val_targets = targets[-num_val_samples:]

print("Number of training samples:", len(train_features))
print("Number of validation samples:", len(val_features))

"""## 3.分析不平衡資料 (少數資料)"""

counts = np.bincount(train_targets[:, 0])
print(
    "Number of positive samples in training data: {} ({:.2f}% of total)".format(
        counts[1], 100 * float(counts[1]) / len(train_targets)
    )
)

weight_for_0 = 1.0 / counts[0]
weight_for_1 = 1.0 / counts[1]

"""## 4.統計資料"""

mean = np.mean(train_features, axis=0)
train_features -= mean
val_features -= mean
std = np.std(train_features, axis=0)
train_features /= std
val_features /= std

"""## 5.建立模型"""

from tensorflow import keras

model = keras.Sequential(
    [
        keras.layers.Dense(
            256, activation="relu", input_shape=(train_features.shape[-1],)
        ),
        keras.layers.Dense(256, activation="relu"),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(256, activation="relu"),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(1, activation="sigmoid"),
    ]
)
model.summary()

"""### 6.評估指標:F1Score、Recall、Precision"""

from sklearn.metrics import classification_report, accuracy_score
class Metrics(tf.keras.callbacks.Callback):
    def __init__(self, val_data):
        super(Metrics, self).__init__()
        self.x_val = val_data[0]
        self.y_val = val_data[1]

    def on_epoch_end(self, epoch, logs=None):
        y_pred = self.model.predict(self.x_val, batch_size=64)
        y_pred = np.argmax(y_pred, axis=1)
        y_val = np.argmax(self.y_val, axis=1)
        result = classification_report(y_val, y_pred)      

        print(result)
        return

"""## 7.使用class_weight訓練模型"""

metrics = [
    keras.metrics.FalseNegatives(name="fn"),
    keras.metrics.FalsePositives(name="fp"),
    keras.metrics.TrueNegatives(name="tn"),
    keras.metrics.TruePositives(name="tp"),
    keras.metrics.Precision(name="precision"),
    keras.metrics.Recall(name="recall"),
]

model.compile(
    optimizer=keras.optimizers.Adam(1e-2), loss="binary_crossentropy", metrics=metrics
)

# callbacks = [keras.callbacks.ModelCheckpoint("fraud_model_at_epoch_{epoch}.h5")]
class_weight = {0: weight_for_0, 1: weight_for_1}

model.fit(
    train_features,
    train_targets,
    batch_size=128,
    epochs=30,
    verbose=2,
    callbacks=Metrics(val_data=(val_features, val_targets)),
    validation_data=(val_features, val_targets),
    class_weight=class_weight,
)