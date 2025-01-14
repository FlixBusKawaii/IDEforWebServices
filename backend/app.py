from flask import Flask, render_template, request, jsonify, redirect, url_for, make_response, json
from flask_socketio import SocketIO, emit
import socket
from config import Config
from services.cursor_service import CursorService
from services.user_service import UserService

app = Flask(__name__)
socketio = SocketIO(app, ping_timeout=10)
cursor_service = CursorService()
user_service = UserService()

Config.init_app()

# Route pour la page d'accueil
@app.route('/')
def index():
    return render_template('index.html')

# Route pour la page de formulaire d'inscription
@app.route('/register')
def register_page():
    return render_template('register.html')

# Route pour gérer l'inscription
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
        return redirect(url_for('login_page'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route pour la page de connexion
@app.route('/login')
def login_page():
    return render_template('login.html')

# Route pour gérer la connexion
@app.route('/login', methods=['POST'])
def login():
    # Essayez de récupérer les données JSON
    data = request.get_json(silent=True)  # `silent=True` empêche Flask de lever une exception si ce n'est pas JSON
    
    # Si les données JSON sont absentes, essayez de lire les données du formulaire
    if not data:
        data = request.form
    
    # Vérifiez si les données sont disponibles
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
            "user_id": str(user["_id"])
        }), max_age=30 * 24 * 60 * 60, httponly=True)
        return response
    else:
        return jsonify({"error": "Invalid email or password"}), 401



# Route pour récupérer l'adresse IP
@app.route('/get-ip', methods=['GET'])
def get_ip():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return jsonify(ip=ip_address)

# Socket event handlers
from handlers.project_handler import register_project_handlers
from handlers.file_handler import register_file_handlers
from handlers.execution_handler import register_execution_handlers
from handlers.cursor_handler import register_cursor_handlers
from handlers.folder_handler import register_folder_handlers
from handlers.connected_users_handler import register_connected_users_handlers

def register_handlers(socketio):
    register_project_handlers(socketio)
    register_file_handlers(socketio)
    register_execution_handlers(socketio)
    register_cursor_handlers(socketio)
    register_folder_handlers(socketio)
    register_connected_users_handlers(socketio)

register_handlers(socketio)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)
