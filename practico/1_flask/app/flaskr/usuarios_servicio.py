#probar con http://127.0.0.1:5001/ingresar?
import os
from flask import Flask, jsonify, request,abort
from db import get_db


app = Flask(__name__)

#para ingresar los usuarios, solo si no esta lo ingresa. No se implementaron ni la actualizacion, ni el borrado de usuarios
@app.route("/ingresar", methods=["POST"])
def ingresar():
        print("pase por ingresar") 
        error = None
        api_key = request.headers.get("Authorization")
        usuario = request.json.get('usuario', '')
        contraseña = request.json.get('contraseña','')
        tipo = request.json.get('tipo','')
        if tipo != "FREEMIUM" and tipo != "PREMIUM":
           error = "Mal tipo"       
        elif api_key == None or api_key == "":       #controlo que tenga api_key para que el nuevo usuario tenga su api_key        
           error = "No tiene Api Key, fijese el Headers"
        elif usuario == None or usuario == "":       #controlo el usuario
           error = "No tiene usuario"              
        elif contraseña == None or contraseña == "": #controlo la contraseña
           error = "No tiene contraseña"                      
        else:
           encontro = get_db().usuario.find_one({"api_key": api_key})        
           if (encontro == None):          
              encontro = get_db().usuario.find_one({"usuario": usuario})
              if (encontro == None):                                        
                get_db().usuario.insert_one(
                  {"api_key":api_key,
                   "usuario": usuario, 
                   "contraseña": contraseña,
                   "tipo":tipo
                  })     
              else:   
                 error= "Encontro el usuario, no se puede ingresar"          
           else:   
                 error= "Existe el Api_key. Cada Api_key se asigna a un usuario"  
        if error:
            return(error)               
        return ("Se cargó el usuario exitosamente!")              

if __name__ == '__main__':
    app.run(port=5001)
