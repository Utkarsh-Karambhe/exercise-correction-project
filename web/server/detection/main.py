import mediapipe as mp
import cv2
from django.conf import settings

from .plank import PlankDetection
from .bicep_curl import BicepCurlDetection
from .squat import SquatDetection
from .lunge import LungeDetection
from .utils import rescale_frame

# Drawing helpers
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

EXERCISE_DETECTIONS = {}

def get_exercise_detector(exercise_type):
    global EXERCISE_DETECTIONS
    
    if exercise_type in EXERCISE_DETECTIONS:
        return EXERCISE_DETECTIONS[exercise_type]
        
    print(f"Lazy loading ML model for: {exercise_type} ...")
    if exercise_type == 'plank':
        EXERCISE_DETECTIONS['plank'] = PlankDetection()
    elif exercise_type == 'bicep_curl':
        EXERCISE_DETECTIONS['bicep_curl'] = BicepCurlDetection()
    elif exercise_type == 'squat':
        EXERCISE_DETECTIONS['squat'] = SquatDetection()
    elif exercise_type == 'lunge':
        EXERCISE_DETECTIONS['lunge'] = LungeDetection()
    else:
        raise Exception("Not supported exercise.")
        
    return EXERCISE_DETECTIONS[exercise_type]

def load_machine_learning_models():
    """No-op for backwards compatibility, we now use true lazy loading to prevent OpenBLAS crashes."""
    pass


def pose_detection(
    video_file_path: str, video_name_to_save: str, rescale_percent: float = 40
):
    """Pose detection with MediaPipe Pose

    Args:
        video_file_path (str): path to video
        video_name_to_save (str): path to save analyzed video
        rescale_percent (float, optional): Percentage to scale back from the original video size. Defaults to 40.

    """
    cap = cv2.VideoCapture(video_file_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) * rescale_percent / 100)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * rescale_percent / 100)
    size = (width, height)
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    fourcc = cv2.VideoWriter_fourcc(*"vp80")
    save_to_path = f"{settings.MEDIA_ROOT}/{video_name_to_save}"
    out = cv2.VideoWriter(save_to_path, fourcc, fps, size)

    print("PROCESSING VIDEO ...")
    with mp_pose.Pose(
        min_detection_confidence=0.8, min_tracking_confidence=0.8
    ) as pose:
        while cap.isOpened():
            ret, image = cap.read()

            if not ret:
                break

            image = rescale_frame(image, rescale_percent)

            # Recolor image from BGR to RGB for mediapipe
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            results = pose.process(image)

            # Recolor image from BGR to RGB for mediapipe
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            mp_drawing.draw_landmarks(
                image,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(
                    color=(244, 117, 66), thickness=2, circle_radius=2
                ),
                mp_drawing.DrawingSpec(
                    color=(245, 66, 230), thickness=2, circle_radius=1
                ),
            )

            out.write(image)

    print(f"PROCESSED, save to {save_to_path}.")
    return


def exercise_detection(
    video_file_path: str,
    video_name_to_save: str,
    exercise_type: str,
    rescale_percent: float = 40,
) -> dict:
    """Analyzed Exercise Video

    Args:
        video_file_path (str): path to video
        video_name_to_save (str): path to save analyzed video
        exercise_type (str): exercise type
        rescale_percent (float, optional): Percentage to scale back from the original video size. Defaults to 40.

    Raises:
        Exception: Not supported exercise type

    Returns:
        dict: Dictionary of analyzed stats from the video
    """
    exercise_detection = get_exercise_detector(exercise_type)

    cap = cv2.VideoCapture(video_file_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) * rescale_percent / 100)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) * rescale_percent / 100)
    size = (width, height)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = 0

    fourcc = cv2.VideoWriter_fourcc(*"vp80")
    saved_path = f"{settings.MEDIA_ROOT}/{video_name_to_save}"
    out = cv2.VideoWriter(saved_path, fourcc, fps, size)

    print("PROCESSING VIDEO ...")
    prev_landmarks = None
    total_motion = 0
    with mp_pose.Pose(
        min_detection_confidence=0.8, min_tracking_confidence=0.8
    ) as pose:
        while cap.isOpened():
            ret, image = cap.read()

            if not ret:
                break

            # Calculate timestamp
            frame_count += 1
            
            # FRAME SKIPPING: Skip processing every other frame to double processing speed
            if frame_count % 2 == 0:
                out.write(image)
                continue

            timestamp = int(frame_count / fps)

            image = rescale_frame(image, rescale_percent)

            # Recolor image from BGR to RGB for mediapipe
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            results = pose.process(image)

            # Recolor image from BGR to RGB for mediapipe
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            if results.pose_landmarks:
                # STEP 7: Motion Presence Check
                if prev_landmarks:
                    for i in range(len(results.pose_landmarks.landmark)):
                        cur = results.pose_landmarks.landmark[i]
                        prev = prev_landmarks.landmark[i]
                        # Only track movement for major body parts (shoulders to ankles)
                        if 11 <= i <= 28:
                            dist = ((cur.x - prev.x)**2 + (cur.y - prev.y)**2)**0.5
                            total_motion += dist
                
                prev_landmarks = results.pose_landmarks
                
                exercise_detection.detect(
                    mp_results=results, image=image, timestamp=timestamp
                )

            out.write(image)

    # Normalize motion score by frame count
    motion_score = (total_motion * 100) / frame_count if frame_count > 0 else 0
    print(f"PROCESSED. Save path: {saved_path} | Motion Score: {motion_score:.2f}")

    processed_results = exercise_detection.handle_detected_results(
        video_name=video_name_to_save,
        motion_score=motion_score
    )
    exercise_detection.clear_results()
    return processed_results
