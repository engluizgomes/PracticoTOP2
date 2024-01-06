#probar con http://127.0.0.1:5000/predict?colesterol=2.4&presion=1.4&glucosa=1.8&edad=72&sobrepeso=0&tabaquismo=0
#probar con http://127.0.0.1:5000/ingresar?usuario=mariela&contraseña=mariela&tipo=PREMIUM
#probar con http://127.0.0.1:5000/logger?colesterol=2.4&presion=1.4&glucosa=1.8&edad=72&sobrepeso=0&tabaquismo=0
#probar con http://127.0.0.1:5000/auth
#probar con http://127.0.0.1:5000/predictor?colesterol=2.4&presion=1.4&glucosa=1.8&edad=72&sobrepeso=0&tabaquismo=0

import os
from flask import (
    Flask,
    request,
    Response,
    abort,
    jsonify,
)  # se importa la librería principal de flask
import numpy as np
import tensorflow as tf
from flaskr.db import get_db
from datetime import datetime
from bson.json_util import dumps
from requests_oauthlib import OAuth1
import time
from bson import json_util
from requests_cache import CachedSession
import requests
import redis
import subprocess
from functools import lru_cache

def ejecutar_programa():
    subprocess.call(["python", "programa.py"])
api_keys = {
     "mariela", "mariela2","mariela3","luiz"
}
    
def validarTiempo(api_key,start_time):
    # devueve 0= Cuando superó 5  consultas un usuario FREEMIUM
    #         1= Cuando superó 50 consultas un usuario PREMIUM
    #         2= Cuando la diferencia de la primera consulta y la ultima consulta es mayor a 1 minuto y reinicia el conteo
    #         8= Cuando no encuentra el usuario
    #         9= Actualiza la cantidad de consultas y realiza un retorno exitoso   
    cx=redis.Redis('localhost')
    cantCons=0
    data=cx.lrange("datosCache",0,-1)                                    #devuelve todos los elementos guardados de la tabla hash
    if data ==[]:                                                        #cuando no tiene nada en la tabla guarda la api_key, el dato fecha/hora, el tipo de usuario y la cant.consultas
        encontro = get_db().usuario.find_one({"api_key": api_key})
        if encontro != None:
           tipo = encontro["tipo"]
           cx.lpush("datosCache",cantCons)
           cx.lpush("datosCache",tipo)
           cx.lpush("datosCache",str(start_time))
           cx.lpush("datosCache",api_key)        
        else:
           return(8)                                                     #no encontro un usuario con esa api_key
        
    data=cx.lrange("datosCache",0,-1)                                    #devuelve todos los elementos guardados de la tabla hashes, puede que se haya actualizado, si estaba vacia.
    #los convierte en string
    elemento=[]           
    for eleme  in data:
                 elemento.append(eleme.decode('ascii'))                  #los transforma a ascii porque tiene un formato string binario 
    #recupera los datos almacenados             
    #dato api_key
    elemento0 = elemento[0]    
    #dato fecha    
    elemento1 = elemento[1]     
    #dato tipo de usuario
    tipo = elemento[2] 
    #dato cantidad de consulta
    cantCons = int(elemento[3])              
    
    #cambio de api_key, es decir, viene otro api_key en el header
    if (elemento0 != api_key):  
        cx.flushall()  #borra todo lo de la cache, solo tiene una base de datos acá
        encontro = get_db().usuario.find_one({"api_key": api_key})
        if encontro != None:  #encontro en la tabla de usuarios, esa api_key nueva
           cantCons= "0"
           tipo = encontro["tipo"]
           cx.lpush("datosCache",cantCons)
           cx.lpush("datosCache",tipo)
           cx.lpush("datosCache",str(start_time))
           cx.lpush("datosCache",api_key)        
           data=cx.lrange("datosCache",0,-1) 
           elemento=[]           
           for eleme  in data:
             elemento.append(eleme.decode('ascii'))
        else:
            return(8)    #no encontro esa api_key, es decir no hay un usuario con asa api_key
        
    #recupera los datos almacenados nuevamente porque puede que se hayan actualizado    
    #dato api_key
    elemento0 = elemento[0]            
    #dato fecha
    elemento1 = elemento[1] 
    #dato tipo de usuario
    tipo = elemento[2] 
    #dato cantidad de consulta
    cantCons = int(elemento[3])         
    
    #calcula la diferencia entre la fecha/hora cargada en la chaché y la ultima fecha/hora
    hoy = start_time
    fecha = datetime.strptime(elemento1, '%Y-%m-%d %H:%M:%S.%f')   #debe transformar el string a fecha/hora
    diferencia = hoy - fecha       
    if diferencia.total_seconds() <= 60:                           #evalua la diferencia si es menor a un minuto
        print("La diferencia es menor a 1 minuto")
        match tipo:
             case "FREEMIUM":
                    if float(cantCons) >= 5:
                       print("ojo con sus consultas, es FREEMIUM, superó su limite de 5")
                       return (0)
             case "PREMIUM":
                    if float(cantCons) >= 50:
                       print("ojo con sus consultas, es PREMIUM, superó su limite de 50")
                       return (1)       
    else:       
        print("La diferencia es mayor a 1 minuto")          
        cantCons = 1
        fechaNueva= datetime.now()        
        encontro = get_db().usuario.find_one({"api_key": api_key}) # inicia el conteo de las consultas, guardando la fecha/hora de esa consulta como primera
        if encontro!= None:
           tipo = encontro["tipo"]
           cx.lset("datosCache", 3, str(cantCons))
           cx.lset("datosCache", 2, tipo)           
           cx.lset("datosCache", 1, str(fechaNueva))        
           return (2)
        else:
           return(8) #no existe un usuario con esa api_key
    
    cantCons = cantCons + 1
    cx.lset("datosCache", 3, str(cantCons))   
    return(9) 
    
#Se optimiza con el uso de caché el buscar el modelo y predecir, es decir, si no cambia los parámetros se supone que es la misma predicción.
@lru_cache()
def predictorFunc(colesterol=0,presion=0,glucosa=0,edad=0,sobrepeso=0,tabaquismo=0):            
    param = np.array([[0,colesterol,presion,glucosa,edad,sobrepeso,tabaquismo]]).astype("float32")        
    #toma el modelo        
    model = tf.keras.models.load_model("../../0_ML/model.keras")
    result = model.predict(param)            
    return(str(result))
    
#Función que valida los parámetros. Primero valida que estén todos y despues el rango de los mismos
def validarParametros(colesterol,presion, glucosa,edad,sobrepeso,tabaquismo):
        error = None 
        ## Verifificar esten todos los parametros   
        if not colesterol:
            error = "Se requiere colesterol"
        elif not presion:
            error = "Se requiere la presion Arterial"
        elif not glucosa:
            error = "Se requiere la Glucosa"
        elif not edad:
            error = "Se requiere la edad"
        elif not sobrepeso:
            error = "Se requiere el sobrepeso"
        elif not tabaquismo:
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

        ## Validar Usuario
        #elif validar() == False:
        #   error = "usuario No registrado"
        return error


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # a simple page that says hello
    @app.route("/hello")
    def hello():
        return "Hello, World!"
    
    #para controlar que la api_key esta o no autorizada, se basa en un conjunto de api_keys autorizadas.
    @app.route("/auth", methods=["POST"])
    def auth():
      print("pase por auth")
      api_key = request.headers.get("Authorization")
      if api_key not in api_keys:
        return abort(401, description="API key no autorizada")
      
      return ("API key autorizada")         

    #para predecir el modelo 
    @app.route("/predictor", methods=["POST"])
    def predictor():      
      print("pase por predictor")      
      colesterol = request.args.get("colesterol")
      presion = request.args.get("presion")
      glucosa = request.args.get("glucosa")
      edad = request.args.get("edad")
      sobrepeso = request.args.get("sobrepeso")
      tabaquismo = request.args.get("tabaquismo")      
      ## Verififica que esten todos los parametros                       
      error = None             
      error= validarParametros(colesterol,presion,glucosa,edad,sobrepeso,tabaquismo)
      if error:
        abort(404, description=error)      
      result = predictorFunc(colesterol,presion,glucosa,edad,sobrepeso,tabaquismo)
      return(str(result))
    
    #para ingresar los usuarios, solo si no esta lo ingresa. No se implementaron ni la actualizacion, ni el borrado de usuarios
    @app.route("/ingresar", methods=["PUT"])
    def ingresar():
        print("pase por ingresar") 
        error = None
        api_key = request.headers.get("Authorization")
        usuario = request.args.get("usuario")
        contraseña = request.args.get("contraseña")
        tipo = request.args.get("tipo")
        match tipo:
             case "FREEMIUM":
                  print('FREEMIUM')
             case "PREMIUM":
                  print('PREMIUM')
             case _:
                  error = "Mal tipo"       
        if error:
            abort(409, description=error)
        encontro = get_db().usuario.find_one({"api_key": api_key})
        print(encontro)
        if (encontro == None):                                                   
            get_db().usuario.insert_one(
                {"api_key":api_key,
                 "usuario": usuario, 
                 "contraseña": contraseña,
                 "tipo":tipo
                }
                )     
                 
        return ("Ya se cargó el usuario")      

        
    #para grabar en la Bitácora
    @app.route("/logger", methods=["POST"])
    def logger():      
      print("pase por logger")
      colesterol = request.args.get("colesterol")
      presion = request.args.get("presion")
      glucosa = request.args.get("glucosa")
      edad = request.args.get("edad")
      sobrepeso = request.args.get("sobrepeso")
      tabaquismo = request.args.get("tabaquismo")      
      param = np.array([[0,colesterol,presion,glucosa,edad,sobrepeso,tabaquismo]]).astype("float32")              
      
      #va a Validar  
      strResul=predictor()
      
      # get_db()     -> resuelve una conexión a la base de datos
      # request_log  -> es una colección en la base de datos
      # insert_one() -> persiste el JSON que recibe como parámetro 
      get_db().request_log.insert_one(        
            {
                "timestamp": datetime.now().isoformat(), # formateo de la fecha
                "params": param[0].tolist(),  #capturamos los parámetros de la invocación
                "response": strResul, #capturamos el resultado
            }
        )
      return("guardé en bitácora")

    #Para predecir
    #Pasos: 1) Autentifica esa api_key        2) Obtiene la api_key      3)Valida el tiempo contra el tipo de usuario   
    #       4) Predice (predictor)            5) Guarda en la bitácora y 6) Formatea el resultado
    #Aclaracion: se valida que esten los todos los parámetros y dentro del rango correcto cuando predice (predictor)
    @app.route("/predict", methods=["POST"])
    def predict():          
        print("pase por predict")      
        #Toma la fecha/hora
        start_time = datetime.now()  
        # Autentifica contra la api_key autorizadas.
        if auth():
           #Toma api_key de Postman, ya que es autorizada
           api_key = request.headers.get("Authorization")                 
           #Valida el tiempo usando REDIS (caché)
           error=None
           error=validarTiempo(api_key,start_time)               
           if error == 0: #cuando supero un minuto y hizo mas de 5 consultas cuando es FREMIUM
               abort(409, description="Superó las 5 consultas, usted es FREEMIUM")
           elif error == 1: #cuando supero un minuto y hizo mas de 5 consultas cuando es PREMIUM
               abort(409, description="Superó las 50 consultas, usted es PREMIUM")
           elif error == 8: #No existe el api_key, es decir, un usuario con esa api_key
               abort(409, description="No esta el usuario")        
           #va a Predecir 
           strResul=predictor()        
           #guarda en la Bitácora
           if logger():
              #Formatea la salida
              strResul = strResul.replace("[", "")
              strResul = strResul.replace("]", "")
              numero = float(strResul)
              porcentaje = numero * 100
              resultadoFinal = "Tiene un riesgo de " + str(porcentaje) + " %"                           
              return (resultadoFinal)
        
    @app.route('/requests',methods=['GET', 'POST'])
    def requests():
        result=get_db().request_log.find()
        # se convierte el cursor a una lista
        list_cur = list(result)         
        # se serializan los objetos
        json_data = dumps(list_cur, indent = 2)  
        #retornamos la rista con los metadatos adecuados
        return Response(json_data,mimetype='application/json')

    return app


     