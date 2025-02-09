FROM python:3.10-slim

# Crear directorio de trabajo
WORKDIR /app

# Copiar e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto 8080 (Cloud Run por defecto)
EXPOSE 8080

# Usamos gunicorn para iniciar la app Flask
CMD ["gunicorn", "--bind=0.0.0.0:8080", "main:app"]