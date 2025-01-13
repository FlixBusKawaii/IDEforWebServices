import sys
import os
from .project_handler import register_project_handlers
from .file_handler import register_file_handlers
from .execution_handler import register_execution_handlers
from .cursor_handler import register_cursor_handlers
from .connected_users_handler import register_connected_users_handlers
from .exercise_handler import register_exercise_handlers

service_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services'))
if service_path not in sys.path:
    sys.path.append(service_path)

from services import ProjectService, FileService, ExecutionService, CursorService, ExerciseService

__all__ = [
    'register_project_handlers',
    'register_file_handlers',
    'register_execution_handlers',
    'register_cursor_handlers'
    'register_connected_users_handlers'
    'register_exercise_handlers'
]