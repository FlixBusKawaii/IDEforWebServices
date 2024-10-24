from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from config import Config
from services.project_service import ProjectService
from services.file_service import FileService
from services.execution_service import ExecutionService
from services.cursor_service import CursorService

app = Flask(__name__)
socketio = SocketIO(app, ping_timeout=10)
cursor_service = CursorService()

Config.init_app()

@app.route('/')
def index():
    return render_template('index.html')

# Socket event handlers
from handlers.project_handler import register_project_handlers
from handlers.file_handler import register_file_handlers
from handlers.execution_handler import register_execution_handlers
from handlers.cursor_handler import register_cursor_handlers

def register_handlers(socketio):
    register_project_handlers(socketio)
    register_file_handlers(socketio)
    register_execution_handlers(socketio)
    register_cursor_handlers(socketio)

register_handlers(socketio)

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)