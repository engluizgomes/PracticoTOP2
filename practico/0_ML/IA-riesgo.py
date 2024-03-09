##########################################
from tensorflow.keras import models #Crear/entrenar/evaluar el modelo
import tensorflow as tf
from tensorflow.keras.layers import Dense, Dropout #Capas densas para la red
from tensorflow.keras.optimizers import Adam #Optimizador a utilizar
import numpy as np #Manejar los arreglos con los datos
import pandas as pd #Tomar el dataset y convertir datos categoricos
from sklearn.model_selection import train_test_split #Para separar train de test
import matplotlib.pyplot as plt #Para graficar
#preproceso los datos
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import normalize

from sklearn.preprocessing import (
    MaxAbsScaler,
    MinMaxScaler,
    Normalizer,
    PowerTransformer,
    QuantileTransformer,
    RobustScaler,
    StandardScaler,
    minmax_scale,
)
from sklearn.linear_model import LogisticRegression

#----------------------------------------------------------------------------------

# Importar el conjunto de datos
data = pd.read_csv('datos_de_pacientes_5000.csv')


# Divide el conjunto de datos en conjuntos de entrenamiento y prueba
###Scaling numerical variables
scaler = StandardScaler()
# Separo los datos de entrada X y los datos de salida Y
# Separate the data from the target labels
X = data.drop(['riesgo_cardiaco'], axis=1)
y = np.array(data['riesgo_cardiaco'])
# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
#For training set
scaled_X_train = scaler.fit_transform(X_train)
scaled_X_train = pd.DataFrame(scaled_X_train, columns=X_train.columns)
#For testing set
scaled_X_test = scaler.fit_transform(X_test)
scaled_X_test = pd.DataFrame(scaled_X_test, columns=X_test.columns)
scaled_X_train.head()
scaled_X_test.head()

## Complete in this cell: train a logistic regression, assign to `log_reg` variable
log_reg = LogisticRegression(max_iter = 10000, C = 0.01).fit(scaled_X_train, y_train)
lr_predictions = log_reg.predict(scaled_X_test)
lr_predict_proba = log_reg.predict_proba(scaled_X_test)

# Normaliza los datos
X_train_norm = normalize(X_train, norm='l2')
X_test_norm = normalize(X_test, norm='l2')


# Define la arquitectura de la red neuronal
model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(12, activation='relu'),
    tf.keras.layers.Dense(260, activation='relu'),
    tf.keras.layers.Dense(1, activation='sigmoid')
])

# Compila el modelo
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Entrena el modelo
model.fit(X_train, y_train, epochs=150)

# Evalua el modelo
score = model.evaluate(X_test, y_test, verbose=0)
print('Precisión:', score[1])

# Guarda el modelo en model.keras
import pickle
model_pkl_file = "model.pkl"  
with open(model_pkl_file, 'wb') as file:  
    pickle.dump(model, file)
model.save("model.keras")

# Prueba individual
prediccion = model.predict( [[1,2.4,1.4,1.8,72,0,0]])
print(prediccion)

