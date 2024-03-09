#probar con http://127.0.0.1:5003/logger?

import os
from flask import Flask, jsonify, request,abort
from db import get_db
import numpy as np
from datetime import datetime
import requests

# url de los servicios que se convocan
predictor_service_url = 'http://127.0.0.1:5000/predictor?'
app = Flask(__name__)

##servicios
#para grabar en la Bitácora
@app.route("/logger", methods=["POST"])
def logger():      
      print("pase por logger")
      colesterol = request.json.get('colesterol', '')
      presion = request.json.get('presion', '')
      glucosa = request.json.get('glucosa', '')
      edad = request.json.get('edad', '')
      sobrepeso = request.json.get('sobrepeso', '')
      tabaquismo = request.json.get('tabaquismo', '')                     
      param = np.array([[0,colesterol,presion,glucosa,edad,sobrepeso,tabaquismo]]).astype("float32")
      try:      
        strResul = requests.post(predictor_service_url, headers=request.headers, json=request.json)   ## lo busca en el servicio de predictor
        if strResul.status_code == 200:
           get_db().request_log.insert_one(        
             {  "timestamp": datetime.now().isoformat(), # formateo de la fecha
                "params": param[0].tolist(),  #capturamos los parámetros de la invocación
                "response": strResul.json(),  #capturamos el resultado
             })
        else:
            abort(500, description="No guardé en bitácora, controle json")  #aborta porque se considera un error grave

        return("guardé en bitácora exitosamente!")
      
      except requests.exceptions.ConnectionError:
        abort(503, description="No está activado el servicio http://127.0.0.1:5000/predictor?") 
  
if __name__ == '__main__':
    app.run(port=5003)
