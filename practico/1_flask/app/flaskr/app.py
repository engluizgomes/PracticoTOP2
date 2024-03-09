#probar con http://127.0.0.1:5000/predict?
#probar con http://127.0.0.1:5000/predictor?

# url de los servicios que se convocan
usuarios_servicio  =  'http://127.0.0.1:5001/ingresar?'
auth_service_url   =  'http://127.0.0.1:5002/auth?'
logger_service_url =  'http://127.0.0.1:5003/logger?'

# Conexión a Redis
import redis
cx = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

import os
import multiprocessing
from flask import (
    Flask,
    request,
    Response,
    abort,
    jsonify,
)  # se importa la librería principal de flask
import numpy as np
import tensorflow as tf
from db import get_db
from datetime import datetime, timedelta
from bson.json_util import dumps
from requests_oauthlib import OAuth1
import time
from bson import json_util
from requests_cache import CachedSession
import requests
import redis
import subprocess
from functools import lru_cache



app = Flask(__name__)

##funciones
def ejecutar_programa():
    subprocess.call(["python", "programa.py"])

def formatearSalida(strResul):          
     strResul = strResul.replace("[", "")
     strResul = strResul.replace("]", "")
     numero = float(strResul)
     porcentaje = numero * 100
     resultadoFinal = "Tiene un riesgo de " + str(porcentaje) + " %"         
     return (resultadoFinal)

def get_user_type(api_key):
    encontro = get_db().usuario.find_one({"api_key": api_key})
    if encontro != None:
         tipo = encontro["tipo"]
    else:
         tipo = None       
    return(tipo)
    

def validarTiempo(api_key, start_time):
    user_key = f"user_rate_limit:{api_key}"
    current_time = datetime.now()
    
    if not cx.exists(user_key):
        # Si el usuario no existe en Redis, lo inicializamos.
        tipo = get_user_type(api_key)
        if tipo == None:
           return 8                                                                    # No existe el api_key, es decir, no existe un usuario con esa api_key
        cx.hmset(user_key, {"start_time": str(start_time), "count": 1, "tipo": tipo})
        cx.expire(user_key, 60)                                                         # Establece un TTL de 60 segundos.
        return 9                                                                        # Primer acceso, registro exitoso.
    
    # Si el usuario ya existe, actualizamos la cuenta y verificamos los límites.
    user_data = cx.hgetall(user_key)
    count = int(user_data["count"])
    tipo = user_data["tipo"]
    start_time = datetime.strptime(user_data["start_time"], '%Y-%m-%d %H:%M:%S.%f')
    
    # Verifica si ha pasado más de un minuto desde la primera consulta.
    if current_time - start_time > timedelta(minutes=1):
        cx.hmset(user_key, {"start_time": str(current_time), "count": 1, "tipo": tipo})
        return 2  # Reinicia el conteo después de un minuto.
    
    # Incrementa la cuenta y verifica los límites basados en el tipo de usuario.
    count += 1
    cx.hset(user_key, "count", count)
    
    if tipo == "FREEMIUM" and count > 5:
        return 0  # Límite para usuarios FREEMIUM superado.
    elif tipo == "PREMIUM" and count > 50:
        return 1  # Límite para usuarios PREMIUM superado.
     
    return 9  # Consulta exitosa dentro del límite.


    
    
#Se optimiza con el uso de caché el buscar el modelo y predecir, es decir, si no cambia los parámetros se supone que es la misma predicción.
@lru_cache()
def predictorFunc(colesterol=0,presion=0,glucosa=0,edad=0,sobrepeso=0,tabaquismo=0):            
    param = np.array([[0,colesterol,presion,glucosa,edad,sobrepeso,tabaquismo]]).astype("float32")        
    #toma el modelo        
    model = tf.keras.models.load_model("/practico/0_ML/model.keras")
    result = model.predict(param)            
    return(str(result))
    
#Función que valida los parámetros. Primero valida que estén todos y despues el rango de los mismos
def validarParametros(colesterol,presion, glucosa,edad,sobrepeso,tabaquismo):
        error = None 
        ## Verifificar esten todos los parametros           
        if colesterol is None or colesterol == '':
            error = "Se requiere colesterol"
        elif presion is None or presion == '':
            error = "Se requiere la presion Arterial"
        elif glucosa is None or glucosa == '':
            error = "Se requiere la Glucosa"
        elif edad is None or edad == '':
            error = "Se requiere la edad"
        elif sobrepeso is None or sobrepeso == '':
            error = "Se requiere el sobrepeso"
        elif tabaquismo is None or tabaquismo == '':
            error = "Se requiere el tabaquismo"

        ## Verifificar si los parametros tienen el rango correcto               
        elif   (float(colesterol) < 1 or float(colesterol) > 3):
                error = "El rango del colesterol debe estar entre (1.0, 3.0) "
        elif (float(presion) < 0.6 or float(presion) > 1.8): 
                error = "El rango del presion debe estar entre (0.6, 1.8) "
        elif (float(glucosa) < 0.5 or  float(glucosa) > 2.0): 
                error = "El rango del glucosa debe estar entre (0.5, 2.0) "
        elif (float(edad) < 0 or  float(edad) > 99): 
                error = "El rango del edad debe estar entre (0,99) "
        elif (float(sobrepeso) != 1 and float(sobrepeso) != 0): 
                error = "El sobrepeso debe ser 0(no) o 1(si) "
        elif (float(tabaquismo) != 1 and float(tabaquismo) != 0): 
                error = "El tabaquismo debe ser 0(no) o 1(si) "     

        return error

##servicios

# a simple page that says hello
@app.route("/hello")
def hello():
        return "Hello, World!"
    
#Solo para predecir el modelo, tomando los parámetros del json. 
@app.route("/predictor", methods=["POST"])
def predictor():      
      colesterol = request.json.get('colesterol', '')
      presion = request.json.get('presion', '')
      glucosa = request.json.get('glucosa', '')
      edad = request.json.get('edad', '')
      sobrepeso = request.json.get('sobrepeso', '')
      tabaquismo = request.json.get('tabaquismo', '')    
      error = None     
      error= validarParametros(colesterol,presion,glucosa,edad,sobrepeso,tabaquismo) ## Verififica que esten todos los parametros                             
      if error:
        abort(400, description=error)  #mal los parametros podria considerarse un error grave    
      else:  
        result = predictorFunc(colesterol,presion,glucosa,edad,sobrepeso,tabaquismo)      
        return(str(result))
        
       
    
    
        
#Para predecir.
#Pasos: 1) Autentifica esa api_key        2) Obtiene la api_key      3)Valida el tiempo contra el tipo de usuario   
#       4) Predice (predictor)            5) Guarda en la bitácora y 6) Formatea el resultado
#Aclaracion: se valida que esten los todos los parámetros y dentro del rango correcto cuando predice (predictor)
@app.route("/predict", methods=["POST"])
def predict():          
        try:     
          print("pase por predict")      
          respuesta = requests.post(auth_service_url, headers=request.headers)   ## lo busca en el servicio de autorizacion. Autentifica contra la api_key autorizadas.               
          if respuesta.status_code == 200:
             api_key = request.headers.get("Authorization")          #Toma api_key de Postman, ya que es autorizada                          
             error=validarTiempo(api_key,start_time=datetime.now())  #Valida el tiempo usando REDIS (caché). La variable error la funcion la inicializa con None  
             if error == 0 or error == 1 or error == 8:              #0= supero en un minuto las 5 consultas un FREEMIUM. 1= es PREMIUM y superó las 50 consultas.  8= no existe api_key
                 descripcion  = "Superó las 5 " if error == 0 else ("Superó las 50 " if error == 1 else "No está el api_key")
                 descripcion2 = "consultas, el usuario " + get_user_type(api_key) if error !=8 else "  "
                 descripcion = descripcion + descripcion2
                 abort(409, description = descripcion)              
             else:
                 strResul = predictor()                      #Predice:  este valida los parámetros y predice en base a esos parámetros.  
                 if isinstance(strResul, str): 
                    respuesta = requests.post(logger_service_url, headers=request.headers, json=request.json)   ## lo busca en el servicio de logger, guarda en la Bitácora              
                    if respuesta.status_code == 200:
                       return (formatearSalida(strResul))    #funcion que formatea la salida    
                    else:
                       abort(409, description="No se pudo escribir en la Bitácora")  
                 else:
                    abort(400, description= " No es válido el resultado")     
                 
          else:
              abort(401, description="Api no autorizada")           
                                            
        except requests.exceptions.ConnectionError:            
            abort(503, description= " Verifique que tiene todos los servicios disponibles. Tiene /auth o /logger activados ?)")  

@app.route("/ingresarUsuarios", methods=["POST"])
def ingresarUsuarios():          
    try:      
        print("pase por ingresarUsuarios")      
        respuesta = requests.post(usuarios_servicio, headers=request.headers, json=request.json)  ## lo busca en el servicio de usuarios para ingresar los usuarios. 
        if respuesta.status_code == 200:
           return(respuesta.text)  
        else:
           abort(409, description="No se pudo ingresar el usuario")   
    
    except requests.exceptions.ConnectionError:            
       abort(503, description= " Verifique que tiene el servicio usuarios activado.")  
              
if __name__ == '__main__':
    app.run(port=5000)

     