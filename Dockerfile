# 1. Usar una imagen ligera de Python
FROM python:3.10-slim

# 2. Definir el directorio de trabajo dentro del contenedor
WORKDIR /app

# 3. Copiar el archivo de requerimientos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar el resto del código de la aplicación
COPY . .

# 5. Exponer el puerto en el que corre Dash
EXPOSE 8050

# 6. Comando para arrancar la aplicación
CMD ["python", "app.py"]