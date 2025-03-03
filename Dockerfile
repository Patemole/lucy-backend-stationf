# Utiliser une image de base plus légère et sécurisée
FROM python:3.11.11-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Mettre à jour les paquets système et nettoyer après installation
RUN apt-get update && apt-get upgrade -y --no-install-recommends \
    && apt-get dist-upgrade -y --no-install-recommends \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installer les mises à jour critiques de pip et des dépendances
RUN pip install --upgrade --no-cache-dir pip setuptools cryptography

# Copier uniquement requirements.txt pour optimiser le cache Docker
COPY requirements.txt .

# Installer les dépendances Python et supprimer le fichier pour économiser de l'espace
RUN pip install --no-cache-dir -r requirements.txt && rm -f requirements.txt

# Copier le reste des fichiers de l'application après l'installation des dépendances
COPY . .

# Exposer le port sur lequel l'application fonctionne
EXPOSE 5001

# Définir la commande de démarrage avec Gunicorn et Uvicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "student_app.server_run:app", "--bind", "0.0.0.0:5001"]