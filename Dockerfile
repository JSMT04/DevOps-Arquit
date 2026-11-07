# Dockerfile para ejecutar el pipeline de datos
FROM python:3.12-slim

# Evitar escritura de archivos .pyc y buffer de salida para logs en tiempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código y los datos
COPY . .

# Comando por defecto: ejecutar el pipeline ETL
CMD ["python", "etl.py"]
