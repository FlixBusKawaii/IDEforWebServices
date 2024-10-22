import os
import json
import subprocess
import sys
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import shutil

# Configuration des chemins avec la nouvelle structure
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR , 'templates')
PROJECTS_DIR = os.path.join('/app', 'ide_projects')

print(f"Base directory: {BASE_DIR}")
print(f"Template directory: {TEMPLATE_DIR}")
print(f"Projects directory: {PROJECTS_DIR}")

# Créer l'application Flask avec le nouveau chemin des templates
app = Flask(__name__)  # Plus besoin de spécifier template_folder car il suivra la convention
socketio = SocketIO(app, ping_timeout=10)

if not os.path.exists(PROJECTS_DIR):
    os.makedirs(PROJECTS_DIR)
    print(f"Created projects directory at: {PROJECTS_DIR}")

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
        # Chemin complet dans le conteneur Flask
        host_file_path = os.path.join('/app/ide_projects', project_name, filename)
        
        if not os.path.exists(host_file_path):
            emit('code_output', {
                'error': f"Erreur : Le fichier {filename} n'existe pas dans le projet {project_name}",
                'success': False
            })
            return

        # Chemin pour le montage Docker
        container_project_path = f"/app/ide_projects/{project_name}"
        
        if filename.endswith(".py"):
            try:
                print(f"Executing Python file: {host_file_path}")
                
                run_process = subprocess.Popen(
                    [
                        "docker", "run", "--rm",
                        "--network", "none",
                        "-v", f"{container_project_path}:/workspace",  # Monte le dossier du projet
                        "-w", "/workspace",  # Définit le dossier de travail
                        "--memory", "512m",
                        "--cpus", "0.5",
                        "python:3.9-slim",
                        "python", filename  # Utilise directement le nom du fichier
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = run_process.communicate(timeout=10)
                
                if run_process.returncode == 0:
                    emit('code_output', {
                        'output': stdout,
                        'success': True
                    })
                else:
                    emit('code_output', {
                        'error': f"Erreur d'exécution Python:\n{stderr}",
                        'success': False
                    })

            except subprocess.TimeoutExpired:
                run_process.kill()
                emit('code_output', {
                    'error': "Timeout après 10 secondes",
                    'success': False
                })

        elif filename.endswith(".c"):
            output_name = f"output_{os.path.splitext(filename)[0]}"
            
            try:
                # Compilation
                compile_process = subprocess.Popen(
                    [
                        "docker", "run", "--rm",
                        "-v", f"{container_project_path}:/workspace",
                        "-w", "/workspace",
                        "gcc:latest",
                        "gcc", "-o", output_name, filename
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                compile_stdout, compile_stderr = compile_process.communicate(timeout=5)
                
                if compile_process.returncode != 0:
                    emit('code_output', {
                        'error': f"Erreur de compilation:\n{compile_stderr}",
                        'success': False
                    })
                    return

                # Exécution
                run_process = subprocess.Popen(
                    [
                        "docker", "run", "--rm",
                        "-v", f"{container_project_path}:/workspace",
                        "-w", "/workspace",
                        "gcc:latest",
                        f"./{output_name}"
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                run_stdout, run_stderr = run_process.communicate(timeout=5)

                # Nettoyage
                output_path = os.path.join(container_project_path, output_name)
                if os.path.exists(output_path):
                    os.remove(output_path)

                if run_process.returncode == 0:
                    emit('code_output', {
                        'output': run_stdout,
                        'success': True
                    })
                else:
                    emit('code_output', {
                        'error': f"Erreur d'exécution:\n{run_stderr}",
                        'success': False
                    })

            except subprocess.TimeoutExpired:
                emit('code_output', {
                    'error': "Timeout",
                    'success': False
                })

    except Exception as e:
        emit('code_output', {
            'error': f"Erreur système: {str(e)}",
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
    filetype = data.get('type')
    
    filename = filename + "." + filetype
    
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
