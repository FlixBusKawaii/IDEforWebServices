import os
import subprocess
from config import Config

class ExecutionService:
    @staticmethod
    def execute_python_file(project_name, filename, code):
        if not project_name or not filename:
            raise ValueError("Project or filename not specified")

        # Échapper les caractères spéciaux dans le code
        escaped_code = code.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')

        # Le chemin du Dockerfile depuis le docker
        dockerfile_path = "../compilers/python"
        
        # Nom de l'image personnalisée
        image_name = "custom_python_compiler_image"

        # Étape 1 : Construire l'image Docker
        print(f"Construction de l'image Docker à partir du Dockerfile {dockerfile_path}...")
        build_process = subprocess.Popen(
            ["docker", "build", "-t", image_name, dockerfile_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout, stderr = build_process.communicate()
        if build_process.returncode != 0:
            error_message = f"Erreur lors de la construction de l'image Docker : {stderr}"
            print(error_message)
            return {'success': False, 'output': error_message}

        try:
            run_process = subprocess.Popen(
                [
                    "docker", "run", "--rm",
                    "-w", "/workspace",
                    "--memory", "512m",
                    "--cpus", "0.5",
                    image_name,
                    "bash", "-c",
                    f'touch {filename} && echo "{escaped_code}" > {filename} && python3 {filename}',
                    
                    
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = run_process.communicate()
            
            if run_process.returncode != 0:
                error_message = f"Erreur lors de l'exécution du fichier Python : {stderr}"
                print(error_message)
                return {'success': False, 'output': error_message}
            
            print(f"Résultat de l'exécution : {stdout}")
            return {'success': True, 'output': stdout}

        except Exception as e:
            error_message = f"Erreur lors de l'exécution : {str(e)}"
            print(error_message)
            return {'success': False, 'output': error_message}