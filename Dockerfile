# Usar una imagen base de python
FROM python:3.13.2-alpine3.21

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requerimientos al contenedor
COPY . /app

# Instalar las dependencias necesarias
RUN pip install -r requirements.txt

# Exponer el puerto en el que la aplicación se ejecutará
EXPOSE 5000

# Comando para ejecutar la aplicación
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]