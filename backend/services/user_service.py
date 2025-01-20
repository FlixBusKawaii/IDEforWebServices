from pymongo import MongoClient
from datetime import datetime, timezone
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from config import MONGO_URI, DB_NAME

class UserService:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.users = self.db["users"]
        self.exercises = self.db["user_exercises"]
        self.stats = self.db["user_stats"]
        
        # Création des index nécessaires
        self.users.create_index("email", unique=True)
        self.exercises.create_index([("user_id", 1), ("date", -1)])
        self.stats.create_index("user_id", unique=True)

    def create_user(self, username, email, password):
        current_time = datetime.now(timezone.utc)
        hashed_password = generate_password_hash(password)
        user = {
            "username": username,
            "email": email,
            "password": hashed_password,
            "created_at": current_time,
            "last_login": current_time
        }
        result = self.users.insert_one(user)
        
        # Initialiser les stats de l'utilisateur
        self._initialize_user_stats(result.inserted_id)
        return user

    def find_user_by_email(self, email):
        return self.users.find_one({"email": email})

    def verify_password(self, email, password):
        user = self.find_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            # Mettre à jour la date de dernière connexion
            self.users.update_one(
                {"_id": user["_id"]},
                {"$set": {"last_login": datetime.now(timezone.utc)}}
            )
            return user
        return None
    
    def get_user_data(self, email):
        user = self.find_user_by_email(email)
        if user:
            return {
                "username": user.get("username"),
                "email": user.get("email")
            }
        return None

    def add_exercise(self, email, exercise_name, score, completed=True, time_spent=0):
        """Ajoute un exercice à l'historique de l'utilisateur"""
        user = self.find_user_by_email(email)
        if not user:
            raise ValueError("Utilisateur non trouvé")

        exercise_data = {
            "user_id": user["_id"],
            "exercise_name": exercise_name,
            "score": score,
            "completed": completed,
            "time_spent": time_spent,
            "date": datetime.now(timezone.utc),
            "subject": exercise_name.split(" - ")[0] if " - " in exercise_name else "General"
        }

        result = self.exercises.insert_one(exercise_data)
        self._update_user_stats(user["_id"])
        return exercise_data

    def get_user_exercises(self, email, limit=10, subject=None):
        """Récupère l'historique des exercices d'un utilisateur"""
        user = self.find_user_by_email(email)
        if not user:
            raise ValueError("Utilisateur non trouvé")

        filter_query = {"user_id": user["_id"]}
        if subject:
            filter_query["subject"] = subject

        return list(self.exercises
                   .find(filter_query)
                   .sort("date", -1)
                   .limit(limit))

    def get_user_stats(self, email):
        """Récupère les statistiques de l'utilisateur"""
        user = self.find_user_by_email(email)
        if not user:
            raise ValueError("Utilisateur non trouvé")

        return self.stats.find_one({"user_id": user["_id"]})

    def _initialize_user_stats(self, user_id):
        """Initialise les statistiques pour un nouvel utilisateur"""
        current_time = datetime.now(timezone.utc)
        initial_stats = {
            "user_id": user_id,
            "created_at": current_time,
            "last_updated": current_time,
            "general_stats": {
                "total_exercises": 0,
                "completed_exercises": 0,
                "total_time_spent": 0,
                "average_score": 0
            },
            "subject_stats": {},
            "recent_activity": {
                "last_week_exercises": 0,
                "last_month_exercises": 0
            }
        }
        self.stats.insert_one(initial_stats)

    def _update_user_stats(self, user_id):
        """Met à jour les statistiques de l'utilisateur"""
        exercises = list(self.exercises.find({"user_id": user_id}))
        
        if not exercises:
            return

        # Calcul des statistiques générales
        total_exercises = len(exercises)
        completed_exercises = sum(1 for e in exercises if e["completed"])
        total_time_spent = sum(e.get("time_spent", 0) for e in exercises)
        average_score = sum(e["score"] for e in exercises) / total_exercises

        # Calcul des statistiques par matière
        subject_stats = {}
        for exercise in exercises:
            subject = exercise["subject"]
            if subject not in subject_stats:
                subject_stats[subject] = {
                    "total_exercises": 0,
                    "average_score": 0,
                    "total_time": 0
                }
            stats = subject_stats[subject]
            stats["total_exercises"] += 1
            stats["total_time"] += exercise.get("time_spent", 0)
            stats["average_score"] = (
                (stats["average_score"] * (stats["total_exercises"] - 1) + exercise["score"])
                / stats["total_exercises"]
            )

        # Mise à jour des statistiques
        self.stats.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "last_updated": datetime.now(timezone.utc),
                    "general_stats": {
                        "total_exercises": total_exercises,
                        "completed_exercises": completed_exercises,
                        "total_time_spent": total_time_spent,
                        "average_score": average_score
                    },
                    "subject_stats": subject_stats
                }
            }
        )
    def get_all_users(self):
        """Récupère tous les utilisateurs avec leurs statistiques complètes"""
        users = self.db.user_data.find({}, {
            "password": 0  # Exclure le mot de passe des résultats
        })
        user_list = []

        for user in users:
            user_data = {
                "id": str(user["_id"]),
                "username": user.get("username"),
                "email": user.get("email"),
                "created_at": user.get("creation_date"),
                "last_login": user.get("last_login"),
                "experience_level": user.get("experience_level"),
                "years_experience": user.get("years_experience"),
                "current_role": user.get("current_role"),
                "availability_for_collaboration": user.get("availability_for_collaboration"),
                "preferred_working_hours": user.get("preferred_working_hours"),
                "skills": user.get("skills", {}),
                "stats": user.get("stats", {
                    "speed": 0,
                    "best_practices": 0,
                    "skill_levels": {}
                })
            }
            user_list.append(user_data)

        return user_list


    def get_detailed_user_stats(self, user_id):
        """Récupère les statistiques détaillées d'un utilisateur spécifique avec ses compétences"""
        from bson.objectid import ObjectId
        
        # Récupération de l'utilisateur sans le mot de passe
        user = self.users.find_one({"_id": ObjectId(user_id)}, {"password": 0})
        if not user:
            raise ValueError("Utilisateur non trouvé")
        
        # Récupération des statistiques
        stats = self.stats.find_one({"user_id": ObjectId(user_id)})
        
        # Récupération des compétences
        skills = self.skills.find_one({"user_id": ObjectId(user_id)})
        
        # Récupération des 10 derniers exercices
        recent_exercises = list(self.exercises
                            .find({"user_id": ObjectId(user_id)})
                            .sort("date", -1)
                            .limit(10))
        
        # Stats par défaut si aucune n'existe
        default_stats = {
            "general_stats": {
                "total_exercises": 0,
                "completed_exercises": 0,
                "average_score": 0,
                "best_score": 0,
                "total_time_spent": 0
            },
            "subject_stats": {},
            "recent_activity": {
                "last_week_exercises": 0,
                "last_month_exercises": 0
            },
            "learning_patterns": {
                "preferred_subjects": [],
                "struggling_subjects": [],
                "best_performance_time": None
            },
            "recommendations": {
                "suggested_difficulty": "easy",
                "suggested_subjects": [],
                "practice_needed": []
            }
        }
        
        # Compétences par défaut si aucune n'existe
        default_skills = {
            "skills": {
                "frontend": {"skills": []},
                "backend": {"skills": []},
                "database": {"skills": []},
                "devops": {"skills": []},
                "mobile": {"skills": []},
                "other": {"skills": []}
            },
            "last_updated": datetime.utcnow()
        }
        
        # Ajout des champs par défaut pour l'utilisateur si ils n'existent pas
        if "experience_level" not in user:
            user.update({
                "experience_level": "Junior",
                "years_experience": 0,
                "current_role": "Developer",
                "availability_for_collaboration": "Available",
                "preferred_working_hours": "Flexible"
            })
        
        return {
            "user": user,
            "stats": stats if stats else default_stats,
            "skills": skills if skills else default_skills,
            "recent_exercises": recent_exercises,
            "created_at": ObjectId(user_id).generation_time
        }
    