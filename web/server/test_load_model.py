import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exercise_correction.settings')
django.setup()
from detection.main import load_machine_learning_models
print('Starting to load...')
load_machine_learning_models()
print('Finished loading.')
