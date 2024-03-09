#probar con http://127.0.0.1:5002/auth?
#probar con http://127.0.0.1:5002/ingresarApi? No usado para el práctico ya que se uso un conjunto de apis 

import os
from flask import Flask, jsonify, request,abort
from db import get_db
api_keys = {
     "mariela", "mariela2","mariela3","luiz", " luizrr", "ana"
}
app = Flask(__name__)

##servivios    

@app.route("/ingresarApi", methods=["PUT"])
def ingresarApi():
      print("Pase por ingresar api-key") 
      error = None
      api_key = request.headers.get("Authorization")
      if api_key == None or api_key == "":   #controlo que tenga api_key        
         error = "no tiene Api Key"
      else:
         encontro = get_db().apikey.find_one({"api_key": api_key})  #controlo que no existe ese api_key      
         if (encontro == None):          
            get_db().apikey.insert_one(
                  {"api_key":api_key,})     
         else:   
            error= "Existe el Api_key"        
      if error:
         abort(409, description=error)        
      return ("Ya se cargó el api key") 
        

#para controlar que la api_key esta o no autorizada, se basa en un conjunto de api_keys autorizadas.
@app.route("/auth", methods=["POST"])
def auth():
      print("pase por auth")
      api_key = request.headers.get("Authorization")
      if api_key not in api_keys:
         abort(401, description="API key no autorizada")      
      return ("API key autorizada") 
        

if __name__ == '__main__':
    app.run(port=5002)