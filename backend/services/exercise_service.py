import json
import os
from typing import Dict, Any, List

class ExerciseService:
    def __init__(self, execution_service, exercises_file_path: str):
        
        self.execution_service = execution_service
        self.exercises_file_path = exercises_file_path
        self.exercises_data = self._load_exercises_data()

    def _load_exercises_data(self) -> Dict:
        """Charge les données des exercices depuis le fichier JSON"""
        try:
            if not os.path.exists(self.exercises_file_path):
                raise FileNotFoundError(f"Exercises file not found at: {self.exercises_file_path}")
                
            with open(self.exercises_file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in exercises file: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading exercises data: {str(e)}")

    def get_all_exercises(self) -> List[Dict]:
        """Récupère la liste de tous les exercices disponibles"""
        return [{
            'id': exercise['id'],
            'name': exercise['name'],
            'description': exercise['description'],
            'template': exercise['template']
        } for exercise in self.exercises_data['exercises']]

    def load_exercise(self, exercise_id: str) -> Dict:
        """Charge les détails d'un exercice spécifique"""
        exercise = next(
            (ex for ex in self.exercises_data['exercises'] if ex['id'] == exercise_id),
            None
        )
        if not exercise:
            raise ValueError(f"Exercise {exercise_id} not found")
        # print("exercices : ", exercise)
        
        # Create a copy without tests for client
        exercise_data = {
            'id': exercise['id'],
            'name': exercise['name'],
            'description': exercise['description'],
            'template': exercise['template'] or ""  
        }
        return exercise_data

    def evaluate_submission(self, project_name: str, filename: str, code: str, exercise_id: str) -> Dict[str, Any]:
        """Évalue la soumission d'un exercice"""
        try:
            # Find the exercise
            exercise = next(
                (ex for ex in self.exercises_data['exercises'] if ex['id'] == exercise_id),
                None
            )
            
            if not exercise:
                return {
                    'success': False,
                    'message': f'Exercise {exercise_id} not found'
                }

            tests = exercise.get('tests', [])
            if not tests:
                return {
                    'success': False,
                    'message': 'No tests found for this exercise'
                }
            
            results = []
            passed_tests = 0
            
            for test in tests:
                test_code = self._prepare_test_code(code, test, filename)
                result = self._execute_test(project_name, filename, test_code)
                
                test_passed = self._verify_test_result(result, test)
                if test_passed:
                    passed_tests += 1
                    
                results.append({
                    'test_name': test['name'],
                    'passed': test_passed,
                    'output': result['output'],
                    'expected': test['expected_output']
                })

            return {
                'success': True,
                'note': round((passed_tests / len(tests)) * 20, 2),
                'details': results,
                'feedback': self._generate_feedback(passed_tests, len(tests), results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"Error evaluating submission: {str(e)}"
            }

    def _prepare_test_code(self, original_code: str, test: Dict, filename: str) -> str:
        """Prépare le code pour le test en fonction du type de fichier"""
        if filename.endswith('.py'):
            return f"""
{original_code}

def test_function():
    {test['test_code']}

if __name__ == '__main__':
    test_function()
"""
        elif filename.endswith('.c'):
            return f"""
{original_code}

int main() {{
    {test['test_code']}
    return 0;
}}
"""
        else:
            raise ValueError(f"Unsupported file type: {filename}")

    def _execute_test(self, project_name: str, filename: str, test_code: str) -> Dict[str, Any]:
        """Exécute le test en fonction du type de fichier"""
        if filename.endswith('.py'):
            return self.execution_service.execute_python_file(
                project_name, filename, test_code
            )
        elif filename.endswith('.c'):
            return self.execution_service.execute_c_file(
                project_name, filename, test_code
            )
        else:
            raise ValueError(f"Unsupported file type: {filename}")

    def _verify_test_result(self, result: Dict, test: Dict) -> bool:
        """Vérifie si le résultat du test correspond au résultat attendu"""
        if not result['success']:
            return False
            
        expected_output = test['expected_output'].strip()
        actual_output = result['output'].strip()
        return expected_output == actual_output

    def _generate_feedback(self, passed_tests: int, total_tests: int, results: List[Dict]) -> str:
        """Génère un feedback détaillé sur les résultats des tests"""
        feedback = [f"Tests réussis: {passed_tests}/{total_tests}"]
        
        if passed_tests < total_tests:
            feedback.extend([
                f"- {result['test_name']}: "
                f"Attendu: {result['expected']}, "
                f"Obtenu: {result['output']}"
                for result in results if not result['passed']
            ])
            
        return "\n".join(feedback)