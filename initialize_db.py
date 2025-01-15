from pymongo import MongoClient

# Configurer l'URI MongoDB
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "my_database"
COLLECTION_NAME = "users"

def initialize_db():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    
    # Crée une collection "users" si elle n'existe pas déjà
    if COLLECTION_NAME not in db.list_collection_names():
        db.create_collection(COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' créée dans la base '{DB_NAME}'")
    else:
        print(f"La collection '{COLLECTION_NAME}' existe déjà")

    # Ajouter un index sur l'email pour éviter les doublons
    db[COLLECTION_NAME].create_index("email", unique=True)
    print("Index unique sur 'email' créé.")

    client.close()

if __name__ == "__main__":
    initialize_db()
