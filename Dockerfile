# Utiliser une image de base officielle Python 3.11.7
FROM python:3.11.7

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier requirements.txt et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# Copier le reste des fichiers de l'application
COPY . .

# Exposer le port sur lequel l'application fonctionne
EXPOSE 5001

# Définir la commande de démarrage
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "student_app.server_run:app", "--bind", "0.0.0.0:5001"]
