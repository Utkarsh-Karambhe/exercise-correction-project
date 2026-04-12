import os
import sys
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'exercise_correction.settings')
sys.path.append('d:/Exercise-Correction/Exercise-Correction/web/server')

import django
django.setup()

from detection.main import load_machine_learning_models, exercise_detection

try:
    load_machine_learning_models()
    res, *other = exercise_detection('d:/Exercise-Correction/Exercise-Correction/test_out.mp4', 'test2.mp4', 'bicep_curl', 40)
    print('Success:', res, other)
except Exception as e:
    print('Caught exception:')
    traceback.print_exc()
