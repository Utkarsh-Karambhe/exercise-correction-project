import json
import base64
import numpy as np
import cv2
import traceback
import time
from channels.generic.websocket import WebsocketConsumer
import mediapipe as mp

from detection.main import load_machine_learning_models
from detection.plank import PlankDetection
from detection.bicep_curl import BicepCurlDetection
from detection.squat import SquatDetection
from detection.lunge import LungeDetection
from detection.utils import rescale_frame

mp_pose = mp.solutions.pose

class ExerciseStreamConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        
        # Detectors will be instantiated lazily into this dictionary to prevent OpenBLAS memory crash
        self.detectors = {}
        
        # Maintain independent pose estimator block.
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.8, 
            min_tracking_confidence=0.8
        )
        self.frame_count = 0
        # Track stream start time for accurate timestamps
        self.start_time = time.time()

    def disconnect(self, close_code):
        if hasattr(self, 'pose'):
            self.pose.close()

    def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            exercise_type = data.get('type')
            action = data.get('action')

            # Lazy load the detector to avoid loading all 4 scikit-learn models simultaneously
            if exercise_type and exercise_type not in self.detectors:
                if exercise_type == 'plank':
                    self.detectors['plank'] = PlankDetection()
                elif exercise_type == 'bicep_curl':
                    self.detectors['bicep_curl'] = BicepCurlDetection()
                elif exercise_type == 'squat':
                    self.detectors['squat'] = SquatDetection()
                elif exercise_type == 'lunge':
                    self.detectors['lunge'] = LungeDetection()

            detector = self.detectors.get(exercise_type)
            if not detector:
                return

            if action == 'stop':
                # Build the absolute URL prefix from generic channels scope
                headers = dict(self.scope['headers'])
                host = "http://" if headers.get(b'x-forwarded-proto', b'http') == b'http' else "https://"
                if b'host' in headers:
                    host += headers[b'host'].decode('utf-8') + "/"
                else:
                    host = "http://127.0.0.1:8000/" # Fallback baseline

                # Ask detector to persist its in-memory frames using a generated stream name
                stream_name = f"stream_{int(self.start_time)}.mp4"

                try:
                    handled = detector.handle_detected_results(stream_name)
                except Exception:
                    # If detector.handle_detected_results fails, fall back to raw results
                    handled = None

                # Normalize results and metadata from handler return
                if isinstance(handled, tuple) and len(handled) >= 1:
                    results = handled[0]
                    metadata = handled[1] if len(handled) > 1 else {}
                    counter_from_handler = metadata.get('counter') if isinstance(metadata, dict) else metadata
                else:
                    results = getattr(detector, 'results', [])
                    metadata = {}
                    counter_from_handler = None

                # Convert frame filenames to absolute URLs when applicable
                for index, error in enumerate(results):
                    frame_val = error.get("frame")
                    if frame_val and isinstance(frame_val, str) and not frame_val.startswith("http"):
                        results[index]["frame"] = host + f"static/images/{frame_val}"

                # Determine counter value (only use numeric or dict results)
                counter = None
                if counter_from_handler is not None and isinstance(counter_from_handler, (int, dict)):
                    counter = counter_from_handler
                elif hasattr(detector, 'counter'):
                    counter = detector.counter
                if exercise_type == 'bicep_curl' and counter is None:
                    counter = {
                        "left_counter": detector.left_arm_analysis.get_counter(),
                        "right_counter": detector.right_arm_analysis.get_counter()
                    }

                # Construct identical payload shape to standard /upload/ API endpoint
                response_data = {
                    "msg_type": "summary",
                    "type": exercise_type,
                    "processed": True,
                    "file_name": None, # live streams do not save generic mp4 outputs
                    "details": results,
                    "metadata": metadata,
                    "counter": counter,
                }

                self.send(text_data=json.dumps(response_data))

                # Reset detectors cleanly without re-loading ML models into memory
                if hasattr(detector, 'clear_results'):
                    try:
                        detector.clear_results()
                    except Exception:
                        detector.results = []
                        if hasattr(detector, 'counter'):
                            detector.counter = 0

                # Reset internal time counters
                self.frame_count = 0
                self.start_time = time.time()
                return

            image_b64 = data.get('image')
            if not image_b64:
                return

            # Extract base64 header (e.g. "data:image/jpeg;base64,")
            if "," in image_b64:
                encoded_data = image_b64.split(',')[1]
            else:
                encoded_data = image_b64

            # Decode to numpy array, then OpenCV matrix
            nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            self.frame_count += 1
            # Use elapsed real time for accurate timestamps (seconds)
            timestamp = int(time.time() - self.start_time)

            # Mirror the scaling behavior but keep high resolution for modern computers
            image = rescale_frame(image, 80) 
            
            # Predict
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = self.pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            if results.pose_landmarks:
                detector.detect(
                    mp_results=results, image=image, timestamp=timestamp
                )

            # Map the counter state tracking
            counter = None
            if hasattr(detector, 'counter'):
                counter = detector.counter
            
            if exercise_type == 'bicep_curl':
                counter = {
                    "left_counter": detector.left_arm_analysis.get_counter(),
                    "right_counter": detector.right_arm_analysis.get_counter()
                }

            # Ship it back to the client!
            _, buffer = cv2.imencode('.jpg', image, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
            b64_output = base64.b64encode(buffer).decode('utf-8')
            resp_image = f"data:image/jpeg;base64,{b64_output}"

            self.send(text_data=json.dumps({
                'image': resp_image,
                'counter': counter
            }))

        except Exception as e:
            traceback.print_exc()
            self.send(text_data=json.dumps({
                'error': str(e)
            }))
