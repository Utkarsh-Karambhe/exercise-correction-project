<div align="center">

```
███████╗██╗  ██╗███████╗██████╗  ██████╗██╗███████╗███████╗
██╔════╝╚██╗██╔╝██╔════╝██╔══██╗██╔════╝██║██╔════╝██╔════╝
█████╗   ╚███╔╝ █████╗  ██████╔╝██║     ██║███████╗█████╗  
██╔══╝   ██╔██╗ ██╔══╝  ██╔══██╗██║     ██║╚════██║██╔══╝  
███████╗██╔╝ ██╗███████╗██║  ██║╚██████╗██║███████║███████╗
╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝╚══════╝╚══════╝
        ██████╗ ██████╗ ██████╗ ██████╗ ███████╗ ██████╗████████╗██╗ ██████╗ ███╗   ██╗
       ██╔════╝██╔═══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝╚══██╔══╝██║██╔═══██╗████╗  ██║
       ██║     ██║   ██║██████╔╝██████╔╝█████╗  ██║        ██║   ██║██║   ██║██╔██╗ ██║
       ██║     ██║   ██║██╔══██╗██╔══██╗██╔══╝  ██║        ██║   ██║██║   ██║██║╚██╗██║
       ╚██████╗╚██████╔╝██║  ██║██║  ██║███████╗╚██████╗   ██║   ██║╚██████╔╝██║ ╚████║
        ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝   ╚═╝   ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
```

### AI-Powered Exercise Form Analysis · Real-Time Pose Estimation · Multi-Set Analytics









</div>

***

## 🧠 What Is This?

**Exercise Correction** is a full-stack computer vision application that watches you work out and tells you when your form breaks down — in real time.

It combines **MediaPipe's 33-point body pose estimation** with **trained Scikit-Learn classifiers** to detect exercise stages, count reps, identify specific form errors, and generate per-session analytics — all without sending data to any third-party service.

```
Webcam / Video  →  MediaPipe Pose  →  ML Classifier  →  Error Detection  →  Annotated Output
    📷                 🦴                  🤖                  ⚠️                   📊
```

> Supports **Squat**, **Plank**, **Bicep Curl**, and **Lunge** — with live webcam streaming or pre-recorded video upload.

***

## ✨ Key Features

| Feature | Description |
|---|---|
| 🎥 **Real-Time Detection** | Webcam stream at ~7 FPS via WebSocket |
| 📁 **Video Upload** | Process pre-recorded `.mp4`/`.webm` files |
| 🦴 **Pose Estimation** | MediaPipe 33-landmark body skeleton |
| 🤖 **ML Form Analysis** | Trained Scikit-Learn classifiers per exercise |
| 🔢 **Rep Counting** | Automatic stage-based repetition tracking |
| ⚠️ **Error Detection** | Geometric + ML-based error identification |
| 📸 **Error Screenshots** | JPEG snapshots captured at error frames |
| 📦 **Multi-Set Sessions** | 1–5 sets with fatigue index & trend analysis |
| ⚡ **GPU Acceleration** | Optional Hummingbird-ML + CUDA 12.1 support |

***

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        BROWSER  (Vue 3)                         │
│                                                                 │
│   Home.vue           VideoStreaming.vue        RealTime.vue     │
│   (Mode Select)      (Upload + Multi-Set)    (Webcam + WS)      │
└────────────┬──────────────────────────────────────┬────────────┘
             │  HTTP/REST  (Axios)                  │  WebSocket
             ▼                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DJANGO  (Daphne / ASGI)                       │
│                                                                 │
│   stream_video/views.py          stream_video/consumers.py      │
│   (upload, session, aggregate)   (ExerciseStreamConsumer)       │
└────────────────────────┬────────────────────────────────────────┘
                         │
             ┌───────────▼────────────┐
             │   detection/  (ML)     │
             │                        │
             │  MediaPipe Pose        │
             │       ↓                │
             │  Feature Extraction   │
             │       ↓                │
             │  sklearn .predict()   │
             │       ↓                │
             │  Geometric Analysis   │
             └───────────┬────────────┘
                         │
             ┌───────────▼────────────┐
             │  services.py           │
             │  Multi-Set Analytics   │
             │  SQLite via Django ORM │
             └────────────────────────┘
```

***

## 🏋️ Supported Exercises

<details>
<summary><strong>🦵 Squat</strong> — Stage + Foot/Knee Placement Analysis</summary>

```
Model:      squat_model.pkl  (~187 KB)
Landmarks:  9  (nose, shoulders, hips, knees, ankles)
Features:   36  (9 × x, y, z, visibility)
```

**Detects:**
- ✅ Stage: `up` / `down` (rep counting at confidence ≥ 0.7)
- ⚠️ Feet too narrow (`ratio < 1.2`) or too wide (`ratio > 2.8`)
- ⚠️ Knee collapse or bow-out (stage-dependent thresholds)

**Fallback Counting:** Knee angle oscillation — peaks below 140° / above 160°

**📊 Model Evaluation**



</details>

<details>
<summary><strong>🧘 Plank</strong> — Static Posture Classification</summary>

```
Model:      plank_model.pkl  (~2.4 KB)
Scaler:     plank_input_scaler.pkl  (~3.2 KB)
Landmarks:  17  (full upper + lower body)
Features:   68  (17 × x, y, z, visibility)
```

**Detects:**
- ✅ `C` → Correct form
- ⚠️ `L` → Hips sagging too low
- ⚠️ `H` → Hips raised too high

> No rep counter — plank is a static hold. Error frames are saved on form breaks.

**📊 Model Evaluation**



</details>

<details>
<summary><strong>💪 Bicep Curl</strong> — Per-Arm Independent Tracking</summary>

```
Model:      bicep_curl_model.pkl  (~3.6 MB — largest model)
Scaler:     bicep_curl_input_scaler.pkl  (~1.9 KB)
Landmarks:  9  (nose, shoulders, elbows, wrists, hips)
Features:   36  (9 × x, y, z, visibility)
```

**Detects:**
- ⚠️ **Lean-back error** (ML model, threshold ≥ 0.95)
- ⚠️ **Loose upper arm** (elbow swing > 40° from Y-axis)
- ⚠️ **Weak peak contraction** (elbow angle ≥ 60° at top)
- 🔢 Left & right arms tracked **independently** via `BicepPoseAnalysis`

> Rep counted when elbow goes from > 120° (down) to < 100° (up).

**📊 Model Evaluation**



</details>

<details>
<summary><strong>🚶 Lunge</strong> — Dual-Model Stage + Error Pipeline</summary>

```
Stage Model:  lunge_stage_model.pkl  (~2.0 KB)
Error Model:  lunge_err_model.pkl    (~1.1 KB)
Scaler:       lunge_input_scaler.pkl (~2.6 KB)
Landmarks:    13  (torso, hips, legs, feet)
Features:     52  (13 × x, y, z, visibility)
```

**Detects:**
- Stage: `I` (init) → `M` (mid) → `D` (down) at confidence ≥ 0.8
- ⚠️ **Knee-over-toe** error (ML model, down stage only)
- ⚠️ **Knee angle out of range** [60°–125°] (geometric, down stage only)

**📊 Model Evaluation**



</details>

***

## 📊 Multi-Set Session Analytics

After completing 1–5 sets, the system computes:

| Metric | How It's Calculated |
|---|---|
| `overall_score` | Weighted average of set scores by rep count |
| `consistency_score` | `100 - variance(scores)` across all sets |
| `fatigue_index` | `set_1_score - last_set_score` |
| `accuracy_trend` | `Improving` / `Declining` / `Stable` |
| `most_frequent_error` | Error type with highest cross-set frequency |
| `best_set` / `worst_set` | Set numbers with highest / lowest scores |
| `total_reps` | Sum of all sets |

Per-set normalization via `NormalizedMetricExtractor`:

```python
normalized_accuracy  = 100 - (10 × total_errors)
normalized_stability = 100 - ( 5 × total_errors)
normalized_range_of_motion = 100 if errors == 0 else 85
set_score            = normalized_accuracy
```

***

## ⚡ WebSocket Real-Time Flow

```
Client (150ms interval)              Server (consumers.py)
─────────────────────────────────────────────────────────────
connect() ──────────────────────────→ Initialize MediaPipe Pose
                                      Create detector registry

{ type: "squat",          ────────→  1. Lazy-load detector
  image: "data:image/..." }           2. Decode base64 → OpenCV
                                      3. Rescale to 50%
                                      4. Run MediaPipe Pose
                                      5. detector.detect()
                                      6. Draw landmarks + errors
{ image: "data:...",      ←────────  7. Encode JPEG (quality 70)
  counter: 5 }

{ action: "stop" }        ────────→  Build summary from history

{ msg_type: "summary",    ←────────  Serialize errors, frames,
  details: [...],                     counter state
  counter: 12 }
```

***

## 🗄️ Database Schema

### `Session`
| Field | Type | Description |
|---|---|---|
| `session_id` | UUID (PK) | Auto-generated identifier |
| `exercise_type` | CharField | `squat` / `plank` / `bicep_curl` / `lunge` |
| `overall_score` | Float | Weighted accuracy (0–100) |
| `consistency_score` | Float | Score variance metric (0–100) |
| `fatigue_index` | Float | First set vs last set delta |
| `accuracy_trend` | CharField | `Improving` / `Declining` / `Stable` |
| `total_reps` | Integer | Sum across all sets |
| `total_sets` | Integer | Number of sets analyzed |
| `timestamp` | DateTime | Session creation time |

### `SessionSet`
| Field | Type | Description |
|---|---|---|
| `session` | FK → Session | Parent session reference |
| `set_number` | Integer | 1–5 |
| `raw_report_json` | TextField | Full ML results payload |
| `set_score` | Float | Normalized accuracy (0–100) |
| `total_errors` | Integer | Error count for this set |
| `rep_count` | Integer | Reps detected in this set |

***

## 🌐 API Reference

```
BASE URL: http://127.0.0.1:8000
```

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/` | Health check |
| `POST` | `/api/video/upload?type={exercise}` | Upload video for ML processing |
| `GET` | `/api/video/stream?video_name={name}` | Stream processed video (chunked) |
| `POST` | `/api/video/session/start` | Create new multi-set session |
| `POST` | `/api/video/session/set/save` | Save individual set results |
| `POST` | `/api/video/session/aggregate` | Compute session analytics |

**WebSocket:**
```
ws://127.0.0.1:8000/ws/stream/

→ Send:   { "type": "squat",  "image": "data:image/jpeg;base64,..." }
← Recv:   { "image": "data:image/jpeg;base64,...", "counter": 5 }

→ Send:   { "action": "stop" }
← Recv:   { "msg_type": "summary", "type": "squat", "details": [...], "counter": 12 }
```

***

## 🚀 Getting Started

### Prerequisites
- Python **3.11** with `venv`
- Node.js **16+** and npm
- *(Optional)* NVIDIA GPU with CUDA 12.1 for hardware acceleration

### 1 — Clone & Install

```bash
git clone https://github.com/your-username/Exercise-Correction.git
cd Exercise-Correction

# Python dependencies
venv\Scripts\python -m pip install -r requirements.txt

# Frontend dependencies
npm run install:client
```

### 2 — Run Development Servers

```bash
# Terminal 1 — Django backend (port 8000)
npm run dev:server

# Terminal 2 — Vite frontend (port 5173)
npm run dev:client
```

### 3 — Open in Browser

```
http://localhost:5173
```

- 📷 **Real Time** → Webcam-based live detection
- 📁 **Video Upload** → File-based detection + multi-set analysis

***

## 🐳 Docker Deployment

```bash
# Build
docker build -t exercise-correction .

# Run
docker run -e VITE_BASE_URL=http://127.0.0.1 -p 80:8000 exercise-correction

# Access
open http://127.0.0.1
```

***

## ⚙️ Configuration Reference

| Setting | Location | Default | Purpose |
|---|---|---|---|
| `VITE_BASE_URL` | `web/client/.env` | `http://127.0.0.1:8000` | Django API URL for frontend |
| `OPENBLAS_NUM_THREADS` | npm `dev:server` script | `1` | Prevents multi-model thread crashes |
| `--noreload` | Django runserver flag | — | Stops double-loading ML models |
| Pose confidence | `main.py`, `consumers.py` | `0.8` | MediaPipe detection threshold |
| Video rescale | upload / websocket | `40%` / `50%` | Frame resolution reduction |
| WS frame rate | `RealTime.vue` | `150ms` (~6.7 FPS) | WebSocket send interval |
| WS JPEG quality | client / server | `60%` / `70%` | Compression settings |

***

## 🛠️ Technology Stack

<table>
<tr>
<td valign="top" width="33%">

**Frontend**
- Vue.js 3 (Composition API)
- Vue Router 4
- Vite 3
- Axios
- Pinia
- SCSS
- Native WebSocket API

</td>
<td valign="top" width="33%">

**Backend**
- Python 3.11
- Django 4.1.2
- Django REST Framework 3.14
- Django Channels + Daphne
- Django CORS Headers
- SQLite 3

</td>
<td valign="top" width="33%">

**ML / AI**
- MediaPipe 0.10.33
- Scikit-Learn (.pkl models)
- OpenCV 4.13
- NumPy 2.4.4
- Pandas
- PyTorch + CUDA *(optional)*
- Hummingbird-ML *(optional)*

</td>
</tr>
</table>

***

## 📁 Project Structure

```
Exercise-Correction/
├── core/                        # 📓 Model training notebooks
│   ├── squat_model/
│   ├── plank_model/
│   ├── bicep_model/
│   └── lunge_model/
│
├── images/                      # 📊 Model evaluation matrices
│   ├── squat_eval_3.png
│   ├── plank_eval_3.png
│   ├── bicep_curl_eval_3.png
│   └── lunge_eval_3.png
│
├── web/
│   ├── client/                  # 🖥️  Vue 3 SPA
│   │   └── src/
│   │       ├── views/
│   │       │   ├── Home.vue
│   │       │   ├── VideoStreaming.vue
│   │       │   └── RealTime.vue
│   │       └── components/
│   │           ├── Dropzone.vue
│   │           ├── Result.vue
│   │           └── Video.vue
│   │
│   └── server/                  # ⚙️  Django backend
│       ├── detection/           # 🤖 ML inference engine
│       │   ├── main.py          #    Orchestrator + lazy loader
│       │   ├── utils.py         #    Angle/distance helpers
│       │   ├── squat.py
│       │   ├── plank.py
│       │   ├── bicep_curl.py
│       │   └── lunge.py
│       ├── stream_video/        # 📡 API + WebSocket + DB
│       │   ├── views.py
│       │   ├── consumers.py
│       │   ├── models.py
│       │   └── services.py
│       └── static/
│           └── model/           # 📦 Serialized .pkl models
```

***

<div align="center">

Built with 🏋️ for better workouts · Powered by MediaPipe + Scikit-Learn

</div>