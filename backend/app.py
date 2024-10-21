import os
import json
import subprocess
import sys
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import shutil

app = Flask(__name__, template_folder=os.path.abspath("../frontend/templates"))
socketio = SocketIO(app, ping_timeout=10)

PROJECTS_DIR = os.path.join('/app', 'ide_projects')

if not os.path.exists(PROJECTS_DIR):
    os.makedirs(PROJECTS_DIR)
    print(f"Created projects directory at: {PROJECTS_DIR}")

print(f"Using projects directory: {PROJECTS_DIR}")
print(f"Projects directory: {os.path.abspath(PROJECTS_DIR)}")

user_cursors = {}

current_project = None

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    session_id = request.sid
    user_cursors[session_id] = {
        'position': {'row': 0, 'column': 0},
        'color': f'#{hash(session_id) % 0xFFFFFF:06x}'
    }
    emit('user_connected', {'user_id': session_id, 'color': user_cursors[session_id]['color']}, broadcast=True)
    emit('project_list', {'projects': get_projects()})

def get_projects():
    return [d for d in os.listdir(PROJECTS_DIR) if os.path.isdir(os.path.join(PROJECTS_DIR, d))]

def get_project_files(project_name):
    if not project_name:
        return []
    project_path = os.path.join(PROJECTS_DIR, project_name)
    files = []
    for root, dirs, filenames in os.walk(project_path):
        for filename in filenames:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, project_path)
            files.append(rel_path)
    return files

@socketio.on('execute_code')
def handle_execute_code(data):
    project_name = data.get('project')
    filename = data.get('filename')

    if not project_name or not filename:
        emit('code_output', {
            'error': f"Erreur : Projet ({project_name}) ou fichier ({filename}) non spécifié",
            'success': False
        })
        return

    try:
        file_path = os.path.join(PROJECTS_DIR, project_name, filename)

        if not os.path.exists(file_path):
            emit('code_output', {
                'error': f"Erreur : Le fichier {filename} n'existe pas dans le projet {project_name}",
                'success': False
            })
            return

        # Exécuter le code et capturer stdout et stderr
        result = subprocess.run(
            [sys.executable, file_path],
            capture_output=True,
            text=True,
            timeout=5
        )

        emit('code_output', {
            'output': result.stdout,
            'error': result.stderr,
            'success': result.returncode == 0
        })
    except subprocess.TimeoutExpired:
        emit('code_output', {
            'error': "Erreur : L'exécution du code a dépassé le délai imparti",
            'success': False
        })
    except Exception as e:
        emit('code_output', {
            'error': f"Erreur : {str(e)}",
            'success': False
        })

@socketio.on('create_project')
def handle_create_project(data):
    project_name = data['name']
    project_path = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.exists(project_path):
        os.makedirs(project_path)
        emit('project_created', {'name': project_name}, broadcast=True)
        emit('project_list', {'projects': get_projects()}, broadcast=True)
    else:
        emit('project_error', {'error': 'Project already exists'})

@socketio.on('delete_project')
def handle_delete_project(data):
    project_name = data['name']
    project_path = os.path.join(PROJECTS_DIR, project_name)
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
        emit('project_deleted', {'name': project_name}, broadcast=True)
        emit('project_list', {'projects': get_projects()}, broadcast=True)

@socketio.on('select_project')
def handle_select_project(data):
    project_name = data['name']
    files = get_project_files(project_name)
    emit('project_selected', {'name': project_name, 'files': files})

@socketio.on('create_file')
def handle_create_file(data):
    project_name = data.get('project')
    filename = data.get('name')
    
    print(f"Creating file: {filename} in project: {project_name}")
    print(f"Full path will be: {os.path.join(PROJECTS_DIR, project_name, filename)}")
    
    if not project_name:
        emit('file_error', {'error': 'No project selected'})
        return

    try:
        file_path = os.path.join(PROJECTS_DIR, project_name, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write('')
            
        print(f"File successfully created at: {file_path}")
        
        emit('file_created', {
            'name': filename,
            'project': project_name,
            'files': get_project_files(project_name)
        }, broadcast=True)
    except Exception as e:
        print(f"Error creating file: {str(e)}")
        emit('file_error', {'error': str(e)})

@socketio.on('rename_file')
def handle_rename_file(data):
    project_name = data['project']
    if not project_name:
        emit('file_error', {'error': 'No project selected'})
        return

    old_name = data['old_name']
    new_name = data['new_name']
    old_path = os.path.join(PROJECTS_DIR, project_name, old_name)
    new_path = os.path.join(PROJECTS_DIR, project_name, new_name)

    if os.path.exists(old_path) and not os.path.exists(new_path):
        os.rename(old_path, new_path)
        emit('file_renamed', {
            'old_name': old_name,
            'new_name': new_name,
            'project': project_name,
            'files': get_project_files(project_name)
        }, broadcast=True)

@socketio.on('delete_file')
def handle_delete_file(data):
    project_name = data['project']
    if not project_name:
        emit('file_error', {'error': 'No project selected'})
        return

    filename = data['name']
    file_path = os.path.join(PROJECTS_DIR, project_name, filename)

    if os.path.exists(file_path):
        os.remove(file_path)
        emit('file_deleted', {
            'name': filename,
            'project': project_name,
            'files': get_project_files(project_name)
        }, broadcast=True)

@socketio.on('save_file')
def handle_save_file(data):
    project_name = data['project']
    if not project_name:
        emit('file_error', {'error': 'No project selected'})
        return

    filename = data['filename']
    content = data['content']

    try:
        file_path = os.path.join(PROJECTS_DIR, project_name, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        emit('file_saved', {'filename': filename, 'project': project_name}, broadcast=True)
    except Exception as e:
        emit('save_error', {'error': str(e)})

@socketio.on('load_file')
def handle_load_file(data):
    project_name = data['project']
    if not project_name:
        emit('file_error', {'error': 'No project selected'})
        return

    filename = data['filename']

    try:
        file_path = os.path.join(PROJECTS_DIR, project_name, filename)
        with open(file_path, 'r') as f:
            content = f.read()
        emit('file_content', {'content': content, 'filename': filename})
    except Exception as e:
        emit('load_error', {'error': str(e)})

@socketio.on('cursor_move')
def handle_cursor_move(data):
    session_id = request.sid
    user_cursors[session_id]['position'] = data['position']
    emit('cursor_update', {
        'user_id': session_id,
        'position': data['position']
    }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    if session_id in user_cursors:
        del user_cursors[session_id]
        emit('user_disconnected', {'user_id': session_id}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0",debug=True)
