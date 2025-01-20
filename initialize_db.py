from pymongo import MongoClient
from faker import Faker
import random
from datetime import datetime, timedelta
import time
from pymongo.errors import ServerSelectionTimeoutError

fake = Faker()
MONGO_URI = "mongodb://mongodb:27017"
DB_NAME = "Userdatabase"
COLLECTIONS = {
    "user_data": "user_data",
    "exercises": "user_exercises"
}

SKILLS = {
    "frontend": ["React", "Vue", "Angular", "HTML", "CSS", "JavaScript", "TypeScript", "Redux", "Tailwind"],
    "backend": ["Python", "Java", "Node.js", "PHP", "Go", "Ruby", "C#", "Spring", "Django", "Express"],
    "database": ["MongoDB", "PostgreSQL", "MySQL", "Redis", "Elasticsearch", "Oracle", "SQLite"],
    "devops": ["Docker", "Kubernetes", "AWS", "GCP", "Azure", "Jenkins", "GitLab CI", "Terraform"],
    "mobile": ["React Native", "Flutter", "iOS", "Android", "Kotlin", "Swift"],
    "other": ["Git", "Agile", "Scrum", "GraphQL", "REST API", "WebSockets", "Testing", "CI/CD"]
}

EXPERIENCE_LEVELS = ["Junior", "Intermediate", "Senior", "Lead"]

def wait_for_mongo():
    while True:
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            client.server_info()  # Tentative de connexion
            print("MongoDB est prêt.")
            break
        except ServerSelectionTimeoutError:
            print("En attente de MongoDB...")
            time.sleep(5)

def get_first_name():
    return fake.first_name() + fake.last_name()

def initialize_db():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    for collection_name in COLLECTIONS.values():
        if collection_name not in db.list_collection_names():
            db.create_collection(collection_name)
            print(f"Collection '{collection_name}' créée dans la base '{DB_NAME}'")
        else:
            print(f"La collection '{collection_name}' existe déjà")

    client.close()

def generate_random_skills():
    """Génère un ensemble aléatoire de compétences pour un utilisateur."""
    skills = {}

    # Pour chaque domaine, on choisit un nombre aléatoire de compétences
    for domain, domain_skills in SKILLS.items():
        num_skills = random.randint(1, min(5, len(domain_skills)))
        selected_skills = random.sample(domain_skills, num_skills)

        skills[domain] = {
            "skills": [
                {
                    "name": skill,
                    "level": random.randint(1, 5),  # Niveau de compétence de 1 à 5
                    "years_experience": random.randint(1, 8)  # Années d'expérience
                }
                for skill in selected_skills
            ]
        }

    return skills

def generate_random_stats():
    """Génère des statistiques aléatoires pour un utilisateur."""
    stats = {
        "speed": random.randint(1, 5),
        "best_practices": random.randint(1, 5),
        "skill_levels": {
            domain: {
                skill["name"]: random.randint(1, 5)
                for skill in skills["skills"]
            }
            for domain, skills in generate_random_skills().items()
        }
    }
    return stats

def create_random_user(user_id):
    """Crée un utilisateur aléatoire avec des exercices, des statistiques et des compétences."""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Générer l'expérience professionnelle
    experience_level = random.choice(EXPERIENCE_LEVELS)
    years_experience = {
        "Junior": random.randint(0, 2),
        "Intermediate": random.randint(3, 5),
        "Senior": random.randint(6, 10),
        "Lead": random.randint(8, 15)
    }[experience_level]

    username = str(get_first_name())

    # Mise à jour du modèle utilisateur
    user = {
        "_id": user_id,
        "email": f"user{user_id}@gmail.com",
        "password": "password",
        "username": username,
        "creation_date": datetime.utcnow(),
        "last_login": datetime.utcnow(),
        "experience_level": experience_level,
        "years_experience": years_experience,
        "current_role": fake.job(),
        "availability_for_collaboration": random.choice(["Available", "Busy", "Open to discussions"]),
        "preferred_working_hours": random.choice(["Morning", "Afternoon", "Evening", "Flexible"]),
        "skills": generate_random_skills(),
        "stats": generate_random_stats()
    }

    db[COLLECTIONS["user_data"]].insert_one(user)

    # Création des exercices (comme avant)
    num_exercises = random.randint(5, 20)
    exercises = []
    subjects = ["Math", "Science", "History", "Literature", "Coding"]
    for i in range(num_exercises):
        subject = random.choice(subjects)
        score = random.randint(0, 100)
        completed = random.choice([True, False])
        time_spent = random.randint(10, 60)
        date = datetime.utcnow() - timedelta(days=random.randint(0, 60))
        exercises.append({
            "user_id": user_id,
            "exercise_name": f"{subject} - Exercise {i+1}",
            "score": score,
            "completed": completed,
            "time_spent": time_spent,
            "date": date
        })
    db[COLLECTIONS["exercises"]].insert_many(exercises)

    client.close()
    return user

def populate_database(num_users):
    """Peuple la base de données avec un nombre donné d'utilisateurs aléatoires."""
    initialize_db()
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    last_user = db[COLLECTIONS["user_data"]].find_one({}, sort=[("_id", -1)])
    next_user_id = last_user["_id"] + 1 if last_user else 1

    for i in range(num_users):
        create_random_user(next_user_id + i)
        print(f"User {next_user_id + i} created with skills and experience.")

    client.close()

def clear_database():
    """Vide toutes les collections de la base de données sans les supprimer."""
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    # Parcourt toutes les collections existantes et supprime leur contenu
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        result = collection.delete_many({})
        print(f"Collection '{collection_name}' vidée ({result.deleted_count} documents supprimés).")

    client.close()

if __name__ == "__main__":
    wait_for_mongo()
    clear_database()
    initialize_db()
    populate_database(30)

