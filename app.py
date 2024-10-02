import subprocess
import sys
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('text_update')
def handle_text_update(data):
    emit('update_text', data, broadcast=True)

@socketio.on('execute_code')
def handle_execute_code(data):
    code = data['code']

    try:
        # Exécuter le code et capturer stdout et stderr
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, check=True
        )
        output = result.stdout  # La sortie standard (stdout)
    except subprocess.CalledProcessError as e:
        # Capture l'erreur si la commande échoue
        output = e.stdout + e.stderr  # Combine stdout et stderr pour afficher l'erreur
    except Exception as e:
        # Capture les erreurs Python plus génériques (ex : erreurs de syntaxe)
        output = str(e)

    # Renvoie la sortie ou l'erreur au client
    emit('code_output', {'output': output})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True)
