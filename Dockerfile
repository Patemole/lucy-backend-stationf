# Utiliser une image de base plus légère et sécurisée
FROM python:3.11.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Mettre à jour les paquets système pour corriger les vulnérabilités
RUN apt-get update && apt-get upgrade -y && apt-get dist-upgrade -y && \
    apt-get autoremove -y && apt-get clean

# Installer les mises à jour critiques de pip et des dépendances
RUN pip install --upgrade --no-cache-dir pip setuptools cryptography

# Copier le fichier requirements.txt et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && rm requirements.txt

# Copier le reste des fichiers de l'application
COPY . .

# Exposer le port sur lequel l'application fonctionne
EXPOSE 5001

# Définir la commande de démarrage
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "student_app.server_run:app", "--bind", "0.0.0.0:5001"]
