import os

class Config:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
    PROJECTS_DIR = os.path.join('..', 'ide_projects')

    @classmethod
    def init_app(cls):
        if not os.path.exists(cls.PROJECTS_DIR):
            os.makedirs(cls.PROJECTS_DIR)
            print(f"Created projects directory at: {cls.PROJECTS_DIR}")