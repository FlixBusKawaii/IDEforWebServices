from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response, json, g
from flask_socketio import SocketIO, emit
import socket
import json
from config import Config
from services.cursor_service import CursorService
from services.user_service import UserService
from pymongo import MongoClient
from collections import defaultdict
import math

MONGO_URI = "mongodb://mongodb:27017"
DB_NAME = "Userdatabase"
COLLECTIONS = {
    "users": "users",
    "exercises": "user_exercises",
    "stats": "user_stats",
    "skills": "user_skills" 
}
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

app = Flask(__name__)
socketio = SocketIO(app, ping_timeout=10)
cursor_service = CursorService()
user_service = UserService()

Config.init_app()

def is_authenticated():
    user_data = request.cookies.get('user_data')
    if not user_data:
        return False
    try:
        user_info = json.loads(user_data)
        g.username = user_info.get("username") 
        return True
    except json.JSONDecodeError:
        return False

@app.route('/')
def index():
    if not is_authenticated():
        return redirect(url_for('leaderboard'))
    return render_template('index.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.form
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    if password != confirm_password:
        return jsonify({"error": "Passwords do not match"}), 400

    try:
        user_service.create_user(username, email, password)
        return redirect(url_for('leaderboard'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not data:
        data = request.form
    if not data:
        return jsonify({"error": "No data provided"}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = user_service.verify_password(email, password)
    if user:
        response = make_response(redirect(url_for('index')))
        response.set_cookie('user_data', json.dumps({
            "username": user["username"],
            "user_id": str(user["_id"]),
            "email" : user["email"]
        }), max_age=30 * 24 * 60 * 60, httponly=True)
        return response
    else:
        return jsonify({"error": "Invalid email or password"}), 401

@app.route('/get-ip', methods=['GET'])
def get_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return jsonify(ip=ip_address)

@app.route("/api/users/<user_id>/stats")
def get_user_stats(user_id):
    try:
        stats = user_service.get_detailed_user_stats(user_id)
        return jsonify(stats)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    

@app.route('/leaderboard')
def leaderboard():
    users = user_service.get_all_users()

    return render_template('leaderboard.html', users=users)

@app.route('/api/user/profile')
def get_user_profile():
    user_data= request.cookies.get('user_data')
    current_user = json.loads(user_data)
    # Utiliser votre UserService pour récupérer les données
    return jsonify(user_service.get_user_data(current_user["email"]))

@app.route('/api/user/stats')
def get_profile_stats():
    user_data= request.cookies.get('user_data')
    current_user = json.loads(user_data)
    return jsonify(user_service.get_user_stats(current_user["email"]))

@app.route('/api/user/exercises')
def get_user_exercises():
    user_data= request.cookies.get('user_data')
    current_user = json.loads(user_data)
    limit = request.args.get('limit', 5, type=int)
    return jsonify(user_service.get_user_exercises(current_user["email"], limit=limit))

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login_page')))
    response.delete_cookie('user_data')  
    return response

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = db.user_data.find_one({"_id": user_id})
    if user:
        return jsonify(user)
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/api/users/<int:user_id>/collaborators', methods=['GET'])
def get_collaborators(user_id):
    algorithm = request.args.get('algorithm', 'skills')
    user = db.user_data.find_one({"_id": user_id})

    if not user:
        return jsonify({"error": "User not found"}), 404

    collaborators = []

    if algorithm == 'skills':
        collaborators = recommend_by_experience(user)
    # elif algorithm == 'experience':
    #     collaborators = recommend_by_experience(user)
    # elif algorithm == 'availability':
    #     collaborators = recommend_by_availability(user)
    else:
        return jsonify({"error": "Invalid algorithm"}), 400

    return jsonify(collaborators)

def calculate_rmse_score(user1_skills, user2_skills):
    """
    Calcule le score RMSE entre les compétences de deux utilisateurs.
    Plus le score est bas, plus les utilisateurs sont compatibles.
    """
    squared_diff_sum = 0
    total_comparisons = 0
    
    for domain, skills1 in user1_skills.items():
        if domain in user2_skills:
            skills2 = user2_skills[domain]
            
            # Créer des dictionnaires pour un accès facile
            skills2_dict = {skill["name"]: skill for skill in skills2["skills"]}
            
            for skill1 in skills1["skills"]:
                if skill1["name"] in skills2_dict:
                    skill2 = skills2_dict[skill1["name"]]
                    
                    # Calculer la différence au carré pour le niveau
                    level_diff = (skill1["level"] - skill2["level"]) ** 2
                    
                    # Calculer la différence au carré pour les années d'expérience (normalisé sur 5)
                    exp1 = min(skill1["years_experience"] / 2, 5)  # Cap à 10 ans -> 5 points
                    exp2 = min(skill2["years_experience"] / 2, 5)
                    exp_diff = (exp1 - exp2) ** 2
                    
                    # Ajouter les différences au total
                    squared_diff_sum += level_diff + exp_diff
                    total_comparisons += 2  # Car on compte niveau et expérience
    
    if total_comparisons == 0:
        return 100  # Score maximum si aucune compétence en commun
        
    rmse = math.sqrt(squared_diff_sum / total_comparisons)
    
    # Convertir le RMSE en score de compatibilité (0-100)
    # Plus le RMSE est bas, plus le score est élevé
    max_rmse = math.sqrt(25)  # Différence maximale possible (5^2)
    compatibility_score = 100 * (1 - (rmse / max_rmse))
    
    return max(0, compatibility_score)  # Garantir un score positif

def calculate_experience_rmse(user1, user2):
    """
    Calcule un score de compatibilité basé sur l'expérience globale
    """
    experience_levels = {
        "Junior": 1,
        "Intermediate": 2,
        "Senior": 3,
        "Expert": 4
    }
    
    level1 = experience_levels.get(user1["experience_level"], 2)
    level2 = experience_levels.get(user2["experience_level"], 2)
    
    years1 = min(user1["years_experience"] / 2, 5)  # Cap à 10 ans -> 5 points
    years2 = min(user2["years_experience"] / 2, 5)
    
    squared_diff_sum = (level1 - level2) ** 2 + (years1 - years2) ** 2
    rmse = math.sqrt(squared_diff_sum / 2)
    
    max_rmse = math.sqrt(25)  # Différence maximale possible
    experience_score = 100 * (1 - (rmse / max_rmse))
    
    return max(0, experience_score)

def recommend_by_experience(user):
    """
    Recommande des collaborateurs basés sur le RMSE des niveaux d'expérience
    et des compétences
    """
    # Trouver tous les utilisateurs potentiels
    potential_collaborators = db.user_data.find({
        "_id": {"$ne": user["_id"]},
        "availability_for_collaboration": "Available"
    }, {"password": 0})
    
    recommendations = []
    for collaborator in potential_collaborators:
        # Calculer le score RMSE pour les compétences
        skills_score = calculate_rmse_score(user["skills"], collaborator["skills"])
        
        # Calculer le score RMSE pour l'expérience globale
        experience_score = calculate_experience_rmse(user, collaborator)
        
        # Calculer le score de disponibilité
        availability_score = 100 if (
            collaborator["preferred_working_hours"] == user["preferred_working_hours"]
        ) else 50
        
        # Calculer le score final pondéré
        final_score = (
            skills_score * 0.5 +          # Les compétences comptent pour 50%
            experience_score * 0.3 +       # L'expérience compte pour 30%
            availability_score * 0.2       # La disponibilité compte pour 20%
        )
        
        recommendations.append({
            "user": collaborator,
            "compatibility_score": round(final_score, 2),
            "skill_score": round(skills_score, 2),
            "experience_score": round(experience_score, 2),
            "availability_score": round(availability_score, 2)
        })
    
    recommendations.sort(key=lambda x: x["compatibility_score"], reverse=True)
    return list(recommendations)


from handlers.project_handler import register_project_handlers
from handlers.file_handler import register_file_handlers
from handlers.execution_handler import register_execution_handlers
from handlers.cursor_handler import register_cursor_handlers
from handlers.folder_handler import register_folder_handlers
from handlers.connected_users_handler import register_connected_users_handlers
from handlers.exercise_handler import register_exercise_handlers

def register_handlers(socketio):
    register_project_handlers(socketio)
    register_file_handlers(socketio)
    register_execution_handlers(socketio)
    register_cursor_handlers(socketio)
    register_folder_handlers(socketio)
    register_connected_users_handlers(socketio)
    register_exercise_handlers(socketio)

register_handlers(socketio)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)
