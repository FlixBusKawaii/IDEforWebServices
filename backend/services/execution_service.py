import os
import subprocess
from config import Config

class ExecutionService:
    @staticmethod
    def preprocess_c_code(code):
        """this function adds the missing features in the C code ( main ...)"""
        if "#include <stdio.h>" not in code:
            code = "#include <stdio.h>\n" + code

        if "main" not in code:
            code = code.rstrip('; \n')
            code = f"""#include <stdio.h>
                    int main() {{
                        {code};
                        return 0;
                    }}"""
        return code
    
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
        
    @staticmethod
    def execute_c_file(project_name, filename, code):
        if not project_name or not filename:
            raise ValueError("Project or filename not specified")

        processed_code = ExecutionService.preprocess_c_code(code)

        escaped_code = processed_code.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')

        dockerfile_path = "../compilers/c"
        
        image_name = "custom_c_compiler_image"

        bin_path = os.path.join("..","ide_projects", project_name, "bin")
        os.makedirs(bin_path, exist_ok=True)

        executable_name = os.path.splitext(filename)[0]

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
            volume_path = os.path.abspath(bin_path)
            
            run_process = subprocess.Popen(
                [
                    "docker", "run", "--rm",
                    "-v", f"{volume_path}:/workspace/bin",
                    "-w", "/workspace",
                    "--memory", "512m",
                    "--cpus", "0.5",
                    image_name,
                    "bash", "-c",
                    f'touch {filename} && echo "{escaped_code}" > {filename} && '
                    f'gcc {filename} -o bin/{executable_name} && ./bin/{executable_name}',
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = run_process.communicate()
            
            if run_process.returncode != 0:
                error_message = f"Erreur lors de la compilation/exécution du fichier C : {stderr}"
                print(error_message)
                return {'success': False, 'output': error_message}
            
            print(f"Résultat de l'exécution : {stdout}")
            return {'success': True, 'output': stdout}

        except Exception as e:
            error_message = f"Erreur lors de l'exécution : {str(e)}"
            print(error_message)
            return {'success': False, 'output': error_message}
    