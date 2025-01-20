from flask_socketio import emit
from config import Config
import os
from services.exercise_service import ExerciseService
from services.file_service import FileService
from services.execution_service import ExecutionService

def register_exercise_handlers(socketio):
    exercise_service = ExerciseService(ExecutionService,  os.path.join(Config.EXERCISES_DIR,  "exercice1_file.json") )
    @socketio.on('get_exercises')
    def handle_get_exercises():
        """Récupère la liste de tous les exercices"""
        try:
            print("envoi des exercices")
            exercises = exercise_service.get_all_exercises()
            emit('exercises_list', exercises)
        except Exception as e:
            emit('error', {'message': str(e)})

    @socketio.on('get_exercise')
    def handle_get_exercise(data):
        """Récupère un exercice spécifique"""
        try:
            exercise_id = data.get('exercise_id')
            if not exercise_id:
                raise ValueError('Exercise ID is required')
            
            exercise = exercise_service.load_exercise(exercise_id)
            emit('exercise_data', exercise)
        except Exception as e:
            emit('error', {'message': str(e)})

    @socketio.on('submit_exercise')
    def handle_submit_exercise(data):
        """Gère la soumission d'un exercice"""
        try:
            exercise_id = data.get('exercise_id')
            code = data.get('code')
            filename = data.get('filename')
            project_name = "exercices_python"  # Nom du projet pour les exercices
            
            if not all([exercise_id, code, filename]):
                raise ValueError('Exercise ID, code, and filename are required')
            
            result = exercise_service.evaluate_submission(
                project_name=project_name,
                filename=filename,
                code=code,
                exercise_id=exercise_id
            )
            
            emit('submission_result', result)
            
        except Exception as e:
            emit('error', {
                'message': str(e),
                'success': False
            })