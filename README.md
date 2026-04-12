================================================================================
            EXERCISE CORRECTION — COMPREHENSIVE PROJECT README
================================================================================
                    AI-Powered Exercise Form Correction System
                    Using MediaPipe Pose Estimation + Scikit-Learn
================================================================================


TABLE OF CONTENTS
-----------------
  1.  Project Overview
  2.  High-Level Architecture
  3.  Full Technology Stack
  4.  Directory Structure Explained
  5.  Backend Deep-Dive (Django + Channels)
  6.  Frontend Deep-Dive (Vue 3 + Vite)
  7.  ML / AI Pipeline — How It All Works
  8.  Exercise-Specific Model Details
      8a.  Squat Detection
      8b.  Plank Detection
      8c.  Bicep Curl Detection
      8d.  Lunge Detection
  9.  Multi-Set Session Architecture
  10. WebSocket Real-Time Streaming Flow
  11. Video Upload Processing Flow
  12. Database Schema
  13. API Endpoints Reference
  14. GPU Acceleration (Hummingbird-ML)
  15. How to Run the Project
  16. Docker Deployment
  17. Key Configuration Files


================================================================================
1. PROJECT OVERVIEW
================================================================================

This application is an AI-powered exercise form correction system. It uses
computer vision (MediaPipe Pose) plus trained Machine Learning classifiers
(Scikit-Learn) to detect, in real-time or from uploaded videos, whether a
user is performing exercises with correct form. It identifies specific
errors, counts repetitions, and provides detailed feedback.

Supported Exercises:
  - Squat (basic squat)
  - Plank (static hold)
  - Bicep Curl (dumbbell curl)
  - Lunge (forward lunge)

Input Modes:
  - REAL-TIME: Webcam stream via WebSocket (live detection at ~7 FPS)
  - VIDEO UPLOAD: Upload pre-recorded .mp4/.webm files via REST API

Output:
  - Annotated video with skeleton overlay and error markers
  - Error summary (type, timestamp, screenshot frame)
  - Repetition counter (per exercise)
  - Multi-set session analytics (fatigue index, consistency, accuracy trend)


================================================================================
2. HIGH-LEVEL ARCHITECTURE
================================================================================

  ┌──────────────────────────────────────────────────────────────────┐
  │                         BROWSER (Vue 3)                         │
  │  ┌─────────────────────┐  ┌──────────────────────────────────┐  │
  │  │     Home.vue        │  │  VideoStreaming.vue / RealTime.vue│  │
  │  │  (Mode Selection)   │  │  (Upload / Webcam + Results)     │  │
  │  └─────────────────────┘  └──────────────────────────────────┘  │
  │         HTTP REST (Axios)          WebSocket (native WS)        │
  └──────────────┬──────────────────────────┬───────────────────────┘
                 │                          │
  ┌──────────────▼──────────────────────────▼───────────────────────┐
  │                    DJANGO SERVER (Daphne/ASGI)                  │
  │  ┌──────────────────────┐  ┌─────────────────────────────────┐  │
  │  │  stream_video/views  │  │ stream_video/consumers          │  │
  │  │  (REST API: upload,  │  │ (WebSocket: ExerciseStream      │  │
  │  │   session, aggregate)│  │  Consumer - real-time inference) │  │
  │  └──────────┬───────────┘  └──────────────┬──────────────────┘  │
  │             │                             │                     │
  │  ┌──────────▼─────────────────────────────▼──────────────────┐  │
  │  │              detection/ (ML Pipeline)                     │  │
  │  │  ┌────────────────────────────────────────────────────┐   │  │
  │  │  │  MediaPipe Pose  →  Feature Extraction  →  Model   │   │  │
  │  │  │  (33 landmarks)     (keypoint x,y,z,v)    Predict  │   │  │
  │  │  └────────────────────────────────────────────────────┘   │  │
  │  │  plank.py | squat.py | bicep_curl.py | lunge.py           │  │
  │  └──────────────────────────────────────────────────────────┘  │
  │  ┌──────────────────────────────────────────────────────────┐  │
  │  │  stream_video/services.py (Multi-Set Aggregation Layer)  │  │
  │  │  stream_video/models.py   (SQLite via Django ORM)        │  │
  │  └──────────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────────────┘


================================================================================
3. FULL TECHNOLOGY STACK
================================================================================

FRONTEND:
  - Vue.js 3 (Composition API with <script setup>)
  - Vue Router 4 (client-side routing: /, /video, /realtime)
  - Vite 3 (build tool + dev server, port 5173)
  - Axios (HTTP requests to Django REST API)
  - SCSS (scoped component styling)
  - Pinia (state management - installed but not heavily used)
  - Font Awesome (icons)
  - Native WebSocket API (for real-time camera streaming)

BACKEND:
  - Python 3.11 (virtual environment: ./venv)
  - Django 4.1.2 (web framework)
  - Django REST Framework 3.14.0 (API layer)
  - Django Channels + Daphne (ASGI server for WebSocket support)
  - Django CORS Headers 3.13.0 (cross-origin requests)
  - Django Extensions 3.2.1 (utility commands)
  - Protobuf (serialization for MediaPipe)

ML / AI:
  - MediaPipe 0.10.33 (pose estimation — 33 body landmarks)
  - Scikit-Learn (trained classification models serialized as .pkl)
  - OpenCV 4.13.0 (opencv-python + opencv-contrib-python)
  - NumPy 2.4.4 (array computation)
  - Pandas (DataFrame construction for model input)
  - Keras + Keras-Tuner (used during model training phase; not at runtime)

DATABASE:
  - SQLite 3 (db.sqlite3, managed via Django ORM)

GPU ACCELERATION (OPTIONAL):
  - PyTorch with CUDA 12.1 (tensor computation on NVIDIA GPU)
  - Hummingbird-ML (compiles sklearn models into PyTorch GPU tensors)

DEPLOYMENT:
  - Docker (Python 3.8 base image + Node.js 16)
  - Dockerfile with multi-stage build (client build → server static)


================================================================================
4. DIRECTORY STRUCTURE EXPLAINED
================================================================================

Exercise-Correction/
├── .gitignore
├── Dockerfile                     # Docker deployment config
├── README.md                      # Original project README
├── LICENSE                        # MIT License
├── package.json                   # Root NPM scripts (dev:server, dev:client)
├── requirements.txt               # Python dependencies
├── requirements-mac.txt           # macOS-specific dependencies
│
├── core/                          # ML MODEL TRAINING (Jupyter notebooks)
│   ├── README.md                  # Methodology documentation
│   ├── bicep_model/               # Bicep curl model training notebooks
│   ├── squat_model/               # Squat model training notebooks
│   ├── plank_model/               # Plank model training notebooks
│   └── lunge_model/               # Lunge model training notebooks
│       └── model/                 # Contains exported .pkl model files
│
├── venv/                          # Python 3.11 virtual environment
│
├── web/                           # Main application source
│   ├── package.json               # Web-level NPM scripts
│   ├── requirements.txt           # Additional pip dependencies
│   │
│   ├── client/                    # ===== FRONTEND (Vue 3 SPA) =====
│   │   ├── package.json           # Vue/Vite dependencies
│   │   ├── vite.config.js         # Vite build configuration
│   │   ├── index.html             # SPA entry point
│   │   ├── .env                   # VITE_BASE_URL=http://127.0.0.1:8000
│   │   └── src/
│   │       ├── main.js            # Vue app entry (createApp + router)
│   │       ├── App.vue            # Root layout (nav, footer, RouterView)
│   │       ├── router/
│   │       │   └── index.js       # Routes: /, /video, /realtime
│   │       ├── views/
│   │       │   ├── Home.vue           # Mode selector (Real-Time / Upload)
│   │       │   ├── VideoStreaming.vue  # Video upload + multi-set UI
│   │       │   └── RealTime.vue       # Webcam stream + multi-set UI
│   │       └── components/
│   │           ├── Dropzone.vue       # Drag-and-drop file upload
│   │           ├── DropzoneLoading.vue # Upload progress indicator
│   │           ├── Result.vue         # Error summary/detail/video tabs
│   │           ├── Video.vue          # Processed video player
│   │           └── Webcam.vue         # Camera capture utility
│   │
│   └── server/                    # ===== BACKEND (Django) =====
│       ├── manage.py              # Django management entry point
│       ├── db.sqlite3             # SQLite database (sessions, sets)
│       │
│       ├── exercise_correction/   # Django project settings
│       │   ├── settings.py        # Database, CORS, channels config
│       │   ├── urls.py            # Root URL routing
│       │   ├── asgi.py            # ASGI application (HTTP + WebSocket)
│       │   └── wsgi.py            # WSGI fallback
│       │
│       ├── api/                   # API app (URL namespace: /api/)
│       │   ├── urls.py            # Routes to stream_video
│       │   └── views.py           # Basic API index view
│       │
│       ├── stream_video/          # Main app (video processing + streaming)
│       │   ├── apps.py            # AppConfig (lazy ML model loading)
│       │   ├── models.py          # Session / SessionSet ORM models
│       │   ├── urls.py            # REST endpoints
│       │   ├── views.py           # upload, stream, session APIs
│       │   ├── consumers.py       # WebSocket consumer (real-time)
│       │   ├── routing.py         # WebSocket URL patterns
│       │   └── services.py        # Multi-set aggregation engine
│       │
│       ├── detection/             # ===== ML INFERENCE ENGINE =====
│       │   ├── __init__.py
│       │   ├── main.py            # Orchestrator: pose_detection(),
│       │   │                      #   exercise_detection(), lazy loader
│       │   ├── utils.py           # calculate_angle(), calculate_distance(),
│       │   │                      #   extract_important_keypoints(),
│       │   │                      #   rescale_frame(), get_static_file_url()
│       │   ├── plank.py           # PlankDetection class
│       │   ├── squat.py           # SquatDetection class
│       │   ├── bicep_curl.py      # BicepCurlDetection class
│       │   └── lunge.py           # LungeDetection class
│       │
│       ├── static/
│       │   ├── model/             # Serialized ML models (.pkl files)
│       │   │   ├── plank_model.pkl
│       │   │   ├── plank_input_scaler.pkl
│       │   │   ├── squat_model.pkl
│       │   │   ├── bicep_curl_model.pkl
│       │   │   ├── bicep_curl_input_scaler.pkl
│       │   │   ├── lunge_stage_model.pkl
│       │   │   ├── lunge_err_model.pkl
│       │   │   └── lunge_input_scaler.pkl
│       │   ├── media/             # Processed output videos
│       │   └── images/            # Error frame screenshots
│       │
│       ├── templates/
│       │   └── index.html         # SPA fallback template for Django
│       │
│       └── scripts/               # Django management scripts


================================================================================
5. BACKEND DEEP-DIVE (Django + Channels)
================================================================================

Server Entry Point: web/server/manage.py
ASGI Application:   exercise_correction/asgi.py
  - Uses ProtocolTypeRouter to handle both HTTP and WebSocket
  - HTTP → standard Django ASGI app
  - WebSocket → AuthMiddlewareStack → URLRouter
    → ws/stream/ → ExerciseStreamConsumer

CHANNEL LAYERS:
  - InMemoryChannelLayer (single-process, no Redis required)

STARTUP FLOW:
  1. StreamVideoConfig.ready() fires when Django boots
  2. Calls load_machine_learning_models() (no-op; lazy loading is used)
  3. ML models are loaded on-demand when first exercise is selected
  4. This prevents OpenBLAS memory crashes from loading all 4 models at once

OPENBLAS THREAD SAFETY:
  - Server runs with OPENBLAS_NUM_THREADS=1 (set in npm dev:server script)
  - Models use lazy instantiation via get_exercise_detector()
  - Detectors maintain independent state per WebSocket connection


================================================================================
6. FRONTEND DEEP-DIVE (Vue 3 + Vite)
================================================================================

Dev Server Port: 5173 (Vite)
Backend API URL: VITE_BASE_URL=http://127.0.0.1:8000 (from .env)

PAGES:

  / (Home.vue)
    - Two cards: "Real Time" (camera) and "Video Upload"
    - Links to /realtime and /video respectively

  /video (VideoStreaming.vue)
    - Multi-set video upload interface (1–5 sets)
    - Each set: drag-and-drop Dropzone component
    - Exercise selector: squat, plank, bicep_curl, lunge
    - Processing flow:
      1. POST /api/video/session/start → creates DB session
      2. For each set: POST /api/video/upload?type=X → ML processing
      3. POST /api/video/session/set/save → saves normalized metrics
      4. POST /api/video/session/aggregate → computes session stats
    - Results shown in tabbed UI (per-set + final report)

  /realtime (RealTime.vue)
    - WebSocket-based live camera streaming
    - Captures frames at ~7 FPS (150ms interval)
    - Compresses to JPEG at 60% quality via canvas.toDataURL
    - Sends base64 frames to ws://<host>/ws/stream/
    - Receives back: annotated frame (base64 JPEG) + counter state
    - On stop: receives "summary" message payload
    - Multi-set support: saves each set and aggregates at session end

COMPONENTS:
  - Dropzone.vue:      File drag-and-drop with click-to-browse
  - DropzoneLoading:   Animated loading indicator during processing
  - Result.vue:        Tabbed display (Summary / Detail / Full Video)
  - Video.vue:         HTML5 video player for processed output
  - Webcam.vue:        Simple camera access utility (legacy)


================================================================================
7. ML / AI PIPELINE — HOW IT ALL WORKS
================================================================================

STEP 1: FRAME CAPTURE
  - Video file is opened with cv2.VideoCapture (upload mode)
  - Or, base64 frame is decoded from WebSocket (real-time mode)
  - Frame is rescaled to 40-50% of original size (rescale_frame())

STEP 2: POSE ESTIMATION (MediaPipe)
  - Frame is converted BGR → RGB
  - image.flags.writeable = False (optimization for MediaPipe)
  - mp_pose.Pose.process(image) extracts 33 body landmarks
  - Each landmark has: x, y, z, visibility (normalized 0-1)
  - Runs entirely on CPU (MediaPipe Python on Windows)

STEP 3: FEATURE EXTRACTION
  - extract_important_keypoints() selects exercise-specific landmarks
  - Each landmark contributes 4 features: x, y, z, visibility
  - Features are flattened into a 1D array
  - Packed into a Pandas DataFrame with proper column headers
  - Input scalers (StandardScaler) normalize the features

STEP 4: MODEL PREDICTION
  - Deserialized sklearn classifiers predict exercise stage/error
  - model.predict(X) → class label (e.g., "up", "down", "C", "L")
  - model.predict_proba(X) → confidence probabilities
  - Only predictions above a threshold (0.6-0.8) are accepted

STEP 5: ERROR ANALYSIS
  - Exercise-specific geometric analysis (angles, distances, ratios)
  - Supplements ML predictions with rule-based checks
  - Error frames are captured and stored as JPEG evidence

STEP 6: VISUALIZATION
  - MediaPipe landmarks + connections drawn on frame
  - Color coding: green (correct) / red (error)
  - Counter overlay, stage indicator, error messages
  - Frame returned as annotated OpenCV image


================================================================================
8. EXERCISE-SPECIFIC MODEL DETAILS
================================================================================


--- 8a. SQUAT DETECTION (squat.py) ---

  Model File:        squat_model.pkl (~187 KB)
  Input Scaler:      None (raw features used)
  Model Type:        Scikit-Learn classifier (trained via notebooks)

  Important Landmarks (9):
    NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP,
    LEFT_KNEE, RIGHT_KNEE, LEFT_ANKLE, RIGHT_ANKLE
  
  Feature Vector Size: 9 landmarks × 4 features = 36 features

  What It Detects:
    1. STAGE PREDICTION → "up" or "down" (for rep counting)
       - Confidence threshold: 0.7
       - Counter increments when transitioning from "down" → "up"
    
    2. FEET PLACEMENT ERROR
       - Calculates foot_width / shoulder_width ratio
       - Threshold: [1.2, 2.8]
       - Too tight (<1.2) or too wide (>2.8) = error

    3. KNEE PLACEMENT ERROR  
       - Calculates knee_width / foot_width ratio
       - Stage-dependent thresholds:
         - Up:     [0.5, 1.0]
         - Middle: [0.7, 1.0]
         - Down:   [0.7, 1.1]
       - Too tight or too wide = error

  Fallback Rep Estimation:
    - If ML counter = 0 but motion_score > 5.0 → enforce 1 rep
    - Angle oscillation detection: tracks knee angle history,
      counts peaks when angle drops below 140° and rises above 160°


--- 8b. PLANK DETECTION (plank.py) ---

  Model File:        plank_model.pkl (~2.4 KB)
  Input Scaler:      plank_input_scaler.pkl (~3.2 KB)
  Model Type:        Scikit-Learn classifier

  Important Landmarks (17):
    NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_ELBOW, RIGHT_ELBOW,
    LEFT_WRIST, RIGHT_WRIST, LEFT_HIP, RIGHT_HIP, LEFT_KNEE,
    RIGHT_KNEE, LEFT_ANKLE, RIGHT_ANKLE, LEFT_HEEL, RIGHT_HEEL,
    LEFT_FOOT_INDEX, RIGHT_FOOT_INDEX

  Feature Vector Size: 17 landmarks × 4 features = 68 features

  What It Detects:
    Classifies plank posture into 3 categories:
      "C" → Correct form     (current_stage = "correct")
      "L" → Low back error   (hips sagging too low)
      "H" → High back error  (hips raised too high)
    
    Confidence threshold: 0.6
    
    No repetition counter (plank is a static hold).
    Error frames are saved when stage transitions from correct → error.


--- 8c. BICEP CURL DETECTION (bicep_curl.py) ---

  Model File:        bicep_curl_model.pkl (~3.6 MB — largest model)
  Input Scaler:      bicep_curl_input_scaler.pkl (~1.9 KB)
  Model Type:        Scikit-Learn classifier

  Important Landmarks (9):
    NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, RIGHT_ELBOW, LEFT_ELBOW,
    RIGHT_WRIST, LEFT_WRIST, LEFT_HIP, RIGHT_HIP

  Feature Vector Size: 9 landmarks × 4 features = 36 features

  What It Detects:

    1. LEAN-BACK ERROR (ML model prediction)
       - Model classifies standing posture as "C" (correct) or "L" (lean back)
       - Confidence threshold: 0.95 (very high — only confident predictions)
       
    2. LOOSE UPPER ARM ERROR (geometric analysis)
       - Calculates angle between upper arm and Y-axis
       - If shoulder-to-elbow angle > 40° → upper arm is swinging
       - Tracked independently for LEFT and RIGHT arms

    3. PEAK CONTRACTION ERROR (geometric analysis)
       - Measures minimum elbow angle achieved during "up" stage
       - If peak angle ≥ 60° → insufficient contraction (weak curl)
       
    4. REP COUNTING (geometric analysis, NOT ML)
       - Left and right arms tracked independently (BicepPoseAnalysis class)
       - elbow angle > 120° → "down" stage
       - elbow angle < 100° → "up" stage (from down → counter++)

  Architecture Note:
    - BicepPoseAnalysis is a per-arm analysis class
    - BicepCurlDetection instantiates two: left_arm_analysis + right_arm_analysis
    - Each tracks its own counter, stage, and error history independently

  Fallback Rep Estimation:
    - Tracks elbow angle oscillation history for both arms
    - Counts peaks when angle drops below 80° and rises above 110°


--- 8d. LUNGE DETECTION (lunge.py) ---

  Model Files:
    - lunge_stage_model.pkl (~2.0 KB)   — stage classifier
    - lunge_err_model.pkl (~1.1 KB)     — error classifier
    - lunge_input_scaler.pkl (~2.6 KB)  — feature normalizer
  Model Type: Scikit-Learn classifiers (2 models working together)

  Important Landmarks (13):
    NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP,
    LEFT_KNEE, RIGHT_KNEE, LEFT_ANKLE, RIGHT_ANKLE, LEFT_HEEL,
    RIGHT_HEEL, LEFT_FOOT_INDEX, RIGHT_FOOT_INDEX

  Feature Vector Size: 13 landmarks × 4 features = 52 features

  What It Detects:

    1. STAGE PREDICTION (lunge_stage_model)
       - Classifies: "I" (init), "M" (mid), "D" (down)
       - Confidence threshold: 0.8
       - Counter increments on transition to "D" from "I" or "M"

    2. KNEE-OVER-TOE ERROR (lunge_err_model, only in "down" stage)
       - Classifies: "C" (correct) or "L" (error / knee past toes)
       - Confidence threshold: 0.8

    3. KNEE ANGLE ERROR (geometric analysis, only in "down" stage)
       - Calculates both left and right knee angles
       - Threshold: [60°, 125°]
       - Outside range = error (too deep or not deep enough)
       - Skipped if knee-over-toe error already detected

  Fallback Rep Estimation:
    - Tracks knee angle oscillation: below 140° → "down", above 160° → "up"


================================================================================
9. MULTI-SET SESSION ARCHITECTURE
================================================================================

The system supports 1–5 exercise sets per session with full analytics.

DATABASE FLOW:
  1. Client calls POST /api/video/session/start
     → Creates a Session record (UUID, exercise_type)
  
  2. For each set, client uploads video or streams webcam:
     → ML pipeline processes the video
     → Client calls POST /api/video/session/set/save
     → NormalizedMetricExtractor computes universal metrics:
        - normalized_accuracy:      100 - (10 × total_errors)
        - normalized_deviation:     total_errors × 0.5
        - normalized_stability:     100 - (5 × total_errors)
        - normalized_range_of_motion: 100 if 0 errors, else 85
        - normalized_rep_validity:  100 if reps>0 and 0 errors
        - set_score:                = normalized_accuracy
     → SessionSet row created in database

  3. After all sets, client calls POST /api/video/session/aggregate
     → ReportAggregator computes session-level metrics:
        - overall_score:     Weighted average of set_scores by rep count
        - consistency_score: 100 - variance(scores) across sets
        - fatigue_index:     set_1_score - last_set_score
        - accuracy_trend:    "Improving" / "Declining" / "Stable"
        - most_frequent_error: Error type that appeared most across sets
        - best_set / worst_set: Set numbers with highest/lowest scores
        - total_reps:        Sum of all sets' rep counts

SERVICE CLASSES:
  - NormalizedMetricExtractor: Per-set metric normalization
  - ReportAggregator:          Cross-set session analysis
  - DatabaseService:           ORM abstraction layer
  - MultiSetSessionManager:    Orchestrates save + aggregate


================================================================================
10. WEBSOCKET REAL-TIME STREAMING FLOW
================================================================================

Client (RealTime.vue) → WebSocket → ExerciseStreamConsumer (consumers.py)

CONNECTION:
  1. Client connects to ws://<host>/ws/stream/
  2. Consumer.connect() fires:
     - Initializes empty detector dictionary (lazy loading)
     - Creates MediaPipe Pose estimator (confidence: 0.8)
     - Starts frame counter and timer

FRAME PROCESSING LOOP:
  3. Client sends JSON: { type: "squat", image: "data:image/jpeg;base64,..." }
  4. Consumer.receive() processes:
     a. Lazy-loads the appropriate detector (first frame only)
     b. Decodes base64 → numpy array → OpenCV image
     c. Rescales frame to 50%
     d. Runs MediaPipe Pose on the frame
     e. If landmarks detected → detector.detect(results, image, timestamp)
     f. Encodes annotated frame as JPEG (quality: 70%)
     g. Sends back JSON: { image: "data:image/jpeg;base64,...", counter: N }

STOP:
  5. Client sends JSON: { action: "stop" }
  6. Consumer builds summary:
     - Calls detector.handle_detected_results()
     - Collects error results and counter state
     - Converts frame filenames to absolute URLs
     - Sends back JSON: { msg_type: "summary", type: X, details: [...], counter: N }
  7. Consumer resets detectors and counters for next session


================================================================================
11. VIDEO UPLOAD PROCESSING FLOW
================================================================================

Client (VideoStreaming.vue) → REST API → upload_video() → exercise_detection()

  1. Client POSTs multipart file to /api/video/upload?type=squat
  2. views.py receives file, writes to temp path
  3. Calls exercise_detection() in detection/main.py:
     a. Opens video with cv2.VideoCapture
     b. Creates cv2.VideoWriter for output (H.264/avc1 codec)
     c. Opens MediaPipe Pose context manager
     d. Frame-by-frame loop:
        - Read frame → rescale → BGR→RGB → pose.process()
        - RGB→BGR → detector.detect() → draw landmarks → write output
        - Track per-frame motion score (landmark displacement)
     e. After all frames: handle_detected_results() with motion_score
     f. Returns (results_list, metadata_dict)
  4. Django serializes results as JSON response
  5. Error frames saved as JPEG in static/images/
  6. Processed video saved in static/media/


================================================================================
12. DATABASE SCHEMA
================================================================================

Session (stream_video/models.py):
  ┌─────────────────────┬──────────────────────────────────────────┐
  │ Field               │ Description                              │
  ├─────────────────────┼──────────────────────────────────────────┤
  │ session_id (PK)     │ UUID, auto-generated                     │
  │ exercise_type       │ CharField (squat/plank/bicep_curl/lunge) │
  │ overall_score       │ Float (weighted accuracy, 0-100)         │
  │ consistency_score   │ Float (100 - variance, 0-100)            │
  │ fatigue_index       │ Float (set1_score - last_set_score)      │
  │ most_frequent_error │ CharField (most common error type)       │
  │ accuracy_trend      │ CharField (Improving/Declining/Stable)   │
  │ best_set            │ Integer (set number with highest score)   │
  │ worst_set           │ Integer (set number with lowest score)    │
  │ total_reps          │ Integer (sum across all sets)             │
  │ session_deviation   │ Float (average deviation across sets)     │
  │ total_sets          │ Integer (number of sets analyzed)         │
  │ timestamp           │ DateTime (session creation time)          │
  └─────────────────────┴──────────────────────────────────────────┘

SessionSet (stream_video/models.py):
  ┌──────────────────────────┬──────────────────────────────────────┐
  │ Field                    │ Description                          │
  ├──────────────────────────┼──────────────────────────────────────┤
  │ id (PK)                  │ Auto integer                         │
  │ session (FK → Session)   │ Foreign key to parent session        │
  │ exercise_type            │ CharField                            │
  │ set_number               │ Integer (1-5)                        │
  │ raw_report_json          │ TextField (full JSON of ML results)  │
  │ normalized_accuracy      │ Float (0-100)                        │
  │ normalized_deviation     │ Float                                │
  │ normalized_stability     │ Float (0-100)                        │
  │ normalized_range_of_motion│ Float (85 or 100)                   │
  │ normalized_rep_validity  │ Float (0 or 100)                     │
  │ set_score                │ Float (0-100)                        │
  │ total_errors             │ Integer                              │
  │ rep_count                │ Integer                              │
  │ timestamp                │ DateTime                             │
  └──────────────────────────┴──────────────────────────────────────┘

  Meta: unique_together = (session, set_number)
        ordering = ['set_number']


================================================================================
13. API ENDPOINTS REFERENCE
================================================================================

Base URL: http://127.0.0.1:8000

  GET  /api/                           → API index (health check)
  
  POST /api/video/upload?type={type}   → Upload video for ML processing
       Body: multipart/form-data { file: <video> }
       Returns: { type, processed, file_name, details, counter, metadata }

  GET  /api/video/stream?video_name=X  → Stream processed video (chunked)
       Returns: StreamingHttpResponse (video/mp4)

  POST /api/video/session/start        → Create new multi-set session
       Body: { exercise_type: "squat" }
       Returns: { status, session_id }

  POST /api/video/session/set/save     → Save single set results
       Body: { session_id, exercise_type, set_number, raw_report }
       Returns: { status, set_number, rep_count, norms }

  POST /api/video/session/aggregate    → Aggregate session analytics
       Body: { session_id }
       Returns: { status, overall_score, consistency_score,
                  fatigue_index, accuracy_trend, per_set_reps, ... }

WEBSOCKET:
  ws://127.0.0.1:8000/ws/stream/
    Send: { type: "squat", image: "data:image/jpeg;base64,..." }
    Recv: { image: "data:image/jpeg;base64,...", counter: N }
    Send: { action: "stop" }
    Recv: { msg_type: "summary", type: "squat", details: [...], counter: N }


================================================================================
14. GPU ACCELERATION (Hummingbird-ML)
================================================================================

STATUS: Optional — fails gracefully to CPU if unavailable.

The scikit-learn models (.pkl files) normally run on CPU. For GPU acceleration:

  1. PyTorch with CUDA 12.1 is installed into the venv
  2. Hummingbird-ML converts sklearn models to PyTorch tensor operations
  3. Converted models are moved to cuda:0 (RTX 3050)

Code changes are in the load_machine_learning_model() method of each detector:

    import torch
    from hummingbird.ml import convert
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    self.model = convert(self.model, "pytorch")
    self.model.to(device)

Wrapped in try/except — if PyTorch or Hummingbird aren't installed,
the app seamlessly continues using the original sklearn models on CPU.

Note: MediaPipe Pose estimation always runs on CPU on Windows.
      The GPU accelerates only the sklearn model inference step.


================================================================================
15. HOW TO RUN THE PROJECT
================================================================================

PREREQUISITES:
  - Python 3.11 (with venv already set up)
  - Node.js 16+ and npm
  - NVIDIA GPU + drivers (optional, for GPU acceleration)

STEP 1: Install Python dependencies
  > cd Exercise-Correction
  > venv\Scripts\python -m pip install -r requirements.txt

STEP 2: Install client dependencies
  > npm run install:client

STEP 3: Start the backend server (terminal 1)
  > npm run dev:server
  This runs: cd ./web/server && SET OPENBLAS_NUM_THREADS=1 &&
             ..\..\venv\Scripts\python manage.py runserver --noreload
  Server starts at: http://127.0.0.1:8000

STEP 4: Start the frontend dev server (terminal 2)
  > npm run dev:client
  This runs: cd ./web/client && npm run dev (Vite)
  Client starts at: http://localhost:5173

STEP 5: Open browser
  Navigate to http://localhost:5173
  - Click "Real Time" for webcam-based detection
  - Click "Video Upload" for file-based detection


================================================================================
16. DOCKER DEPLOYMENT
================================================================================

  Build:  docker build -t ec .
  Run:    docker run -e VITE_BASE_URL=http://127.0.0.1 -p 80:8000 ec
  Access: http://127.0.0.1

The Dockerfile:
  1. Uses Python 3.8 base image
  2. Installs Node.js 16 + npm + rsync + ffmpeg + OpenCV dependencies
  3. Installs Python requirements
  4. Copies web/ folder and installs client dependencies
  5. Builds Vue client and deploys to Django static/templates
  6. Exposes port 8000 and starts Django runserver


================================================================================
17. KEY CONFIGURATION FILES
================================================================================

  VITE_BASE_URL:
    - Location: web/client/.env
    - Purpose: Tells frontend where the Django API lives
    - Default: http://127.0.0.1:8000

  OPENBLAS_NUM_THREADS=1:
    - Set in the npm dev:server script
    - Prevents OpenBLAS from crashing when multiple sklearn models
      try to use all CPU threads simultaneously

  --noreload flag:
    - Django's auto-reloader is disabled to prevent double-loading
      heavy ML models into memory

  MediaPipe Pose Confidence:
    - min_detection_confidence=0.8
    - min_tracking_confidence=0.8
    - Set in both main.py and consumers.py

  Video Rescale:
    - Upload mode: 40% of original resolution
    - WebSocket mode: 50% of original resolution

  WebSocket Frame Rate:
    - Client sends frames every 150ms (~6.7 FPS)
    - JPEG quality: 60% compression for WebSocket, 70% for response

  Channel Layer:
    - InMemoryChannelLayer (no external Redis required)
    - Suitable for single-server deployment


================================================================================
                         END OF PROJECT README
================================================================================
