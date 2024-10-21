# Utiliser l'image officielle GCC comme base
FROM gcc:latest

# Installer des dépendances supplémentaires si nécessaire
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /usr/src/app

# Copier les fichiers source dans le conteneur (si nécessaire)
# COPY . .

# Compiler et exécuter le code
# RUN gcc -o output main.c
# CMD ["./output"]
