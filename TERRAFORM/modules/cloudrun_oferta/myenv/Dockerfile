# Usamos una imagen base con Python
FROM python:3.9

# Establecemos el directorio de trabajo
WORKDIR /app

# Copiamos los archivos del script al contenedor desde la carpeta generador_solicitantes
COPY generador_ayudantes/ayudantes.py /app/
COPY generador_ayudantes/requirements.txt /app/

# Instalamos las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Definimos el comando que ejecutará el script cuando se lance el contenedor
CMD ["python", "ayudantes.py"]