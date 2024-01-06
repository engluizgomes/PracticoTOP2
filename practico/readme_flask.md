
# Se debe instalar:
-----------------
1) Python  (version 3.11 para arriba)
2) Visual studio 
3) Redis   (es copiar y pegar la carpeta)
4) Postman (es instalarlo o en versión on line)

# Para instalarlo se debe hacer todo lo que sigue:
------------------------------------------------
1) Borrar la carpeta .env.: Aca guarda "instalaciones" como redis, pymongo.
   (es: en \practico\1_flask\app\.venv)
2) Instalar las dependencias de Python desde visual Studio.
3) Ir a 0_ML  (cd 0_ml). Cuando entras a la consola de visual tenes que ir a esa carpeta.
4) luego instalas:
   pip install tensorflow scikit-learn matplotlib
   pip install pandas
   pip  sklearn --> no me dejo! se instala el de abajo
   pip install scikit-learn
5) Actualizar: 
   python.exe -m pip install --upgrade pip
6) En la consola de visual escribir, para guardar la prediccion (en practico\0_ML): 
   python .\IA-riesgo.py

#  Para activar la apps:
-------------------------
7) ir a app ( cd .\1_flask\app)
8) Crear la carpeta de entorno:
   python -m venv .venv
9) Para activar el entorno:
    .\.venv\Scripts\activate    
10) Instalar lo que sigue en el ambiente de trabajo ".venv", porque crece en tamñano:

primero python.exe -m pip install --upgrade pip
pip install Flask
pip install --upgrade Flask
pip install redis
pip install numpy 
pip install tensorflow -->aca tarda y crece en tamaño!
pip install pymongo
pip install requests_cache

-------------------------------------------
# Para ejecutar: 
flask --app flaskr run

