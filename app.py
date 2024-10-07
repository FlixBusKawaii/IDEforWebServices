import os
import json
import subprocess
import sys
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, ping_timeout=10)

STORAGE_DIR = 'ide_files'
if not os.path.exists(STORAGE_DIR):
    os.makedirs(STORAGE_DIR)

# Dictionnaire pour suivre les curseurs des utilisateurs
user_cursors = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    session_id = request.sid
    user_cursors[session_id] = {
        'position': {'row': 0, 'column': 0},
        'color': f'#{hash(session_id) % 0xFFFFFF:06x}'  # Couleur unique par utilisateur
    }
    emit('user_connected', {'user_id': session_id, 'color': user_cursors[session_id]['color']}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    if session_id in user_cursors:
        del user_cursors[session_id]
    emit('user_disconnected', {'user_id': session_id}, broadcast=True)

@socketio.on('cursor_move')
def handle_cursor_move(data):
    session_id = request.sid
    if session_id in user_cursors:
        user_cursors[session_id]['position'] = data['position']
        emit('cursor_update', {
            'user_id': session_id,
            'position': data['position'],
            'color': user_cursors[session_id]['color']
        }, broadcast=True)

@socketio.on('text_update')
def handle_text_update(data):
    emit('update_text', data, broadcast=True)

@socketio.on('save_file')
def handle_save_file(data):
    filename = data['filename']
    content = data['content']
    
    try:
        file_path = os.path.join(STORAGE_DIR, f"{filename}.py")
        with open(file_path, 'w') as f:
            f.write(content)
        emit('file_saved', {'filename': filename}, broadcast=True)
    except Exception as e:
        emit('save_error', {'error': str(e)})

@socketio.on('load_file')
def handle_load_file(data):
    filename = data['filename']
    
    try:
        file_path = os.path.join(STORAGE_DIR, f"{filename}.py")
        with open(file_path, 'r') as f:
            content = f.read()
        emit('file_content', {'content': content, 'filename': filename})
    except Exception as e:
        emit('load_error', {'error': str(e)})

@socketio.on('get_file_list')
def handle_get_file_list():
    files = [f[:-3] for f in os.listdir(STORAGE_DIR) if f.endswith('.py')]
    emit('file_list', {'files': files})

@socketio.on('execute_code')
def handle_execute_code(data):
    code = data['code']
    
    try:
        # Exécuter le code et capturer stdout et stderr
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout
        error = result.stderr
        
        emit('code_output', {
            'output': output,
            'error': error,
            'success': result.returncode == 0
        })
    except subprocess.TimeoutExpired:
        emit('code_output', {
            'error': "Error: Code execution timed out",
            'success': False
        })
    except Exception as e:
        emit('code_output', {
            'error': f"Error: {str(e)}",
            'success': False
        })

if __name__ == '__main__':
    socketio.run(app, debug=True)