#from pymongo import MongoClient
import pymongo
#from flask import current_app, g
from flask import g
def get_db():
    if 'db' not in g:
        print("registramos una conexión")
        #si se tiene instalado en la maquina de trabajo                  
        #CONNECTION_STRING = "mongodb://localhost:27017"   
        CONNECTION_STRING = "mongodb+srv://mariela:mariela@cluster0.bfxlyqw.mongodb.net/?retryWrites=true&w=majority"    
        dbClient = pymongo.MongoClient(CONNECTION_STRING) 
        dbName="Práctico"
        db = dbClient[dbName]
        g.db=db  
    return g.db
   