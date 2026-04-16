<script setup>
import { ref, onUnmounted } from "vue";
import Result from "../components/Result.vue";

const EXERCISES = ["squat", "plank", "bicep_curl", "lunge"];
const selectedExercise = ref(null);
const isStreaming = ref(false);

const videoElement = ref(null);
const canvasElement = ref(null);

const currentFrame = ref(null);
const currentCounter = ref(null);
const serverError = ref(null);

const numberOfSets = ref(1);
const currentSetIndex = ref(1);
const sessionId = ref(null);
const activeTab = ref("set-1");
const isAggregating = ref(false);

const processedDataRawList = ref([]); // array of single-set parsed data
const aggregatedSessionData = ref(null);

let ws = null;
let streamInterval = null;
let mediaStream = null;

const baseUrl = import.meta.env.VITE_BASE_URL || "http://127.0.0.1:8000";

const initializeSession = async () => {
    try {
        const res = await fetch(`${baseUrl}/api/video/session/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ exercise_type: selectedExercise.value })
        });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        
        sessionId.value = data.session_id;
        currentSetIndex.value = 1;
        processedDataRawList.value = [];
        aggregatedSessionData.value = null;
        activeTab.value = "set-1";
    } catch (err) {
        console.error("Error creating session: ", err);
        alert("Failed to initialize session");
        throw err;
    }
};

const startCamera = async () => {
    if (!selectedExercise.value) {
        alert("Please select an exercise type first.");
        return;
    }
    
    // First run initialization
    if (currentSetIndex.value === 1 && !sessionId.value) {
        await initializeSession();
    }
    
    isStreaming.value = true;
    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } });
        videoElement.value.srcObject = mediaStream;
        await videoElement.value.play();
        
        // Connect WebSocket
        const baseUrl = import.meta.env.VITE_BASE_URL || "http://127.0.0.1:8000";
        const wsUrl = baseUrl.replace(/^http/, "ws");
        ws = new WebSocket(`${wsUrl}/ws/stream/`);
        
        ws.onopen = () => {
            console.log("WebSocket connected!");
            serverError.value = null;
            captureAndSendFrames();
        };

        ws.onmessage = async (event) => {
            const data = JSON.parse(event.data);
            
            // Core flow check: When stopped, grab the summary and trigger SAVE hook
            if (data.msg_type === "summary") {
                finalizeStop();
                await handleSaveSet(data);
                return;
            }
            if (data.error) {
                console.error("Server error:", data.error);
                serverError.value = data.error;
                return;
            }
            if (data.image) {
                currentFrame.value = data.image;
                serverError.value = null;
            }
            if (data.counter !== undefined) {
                currentCounter.value = data.counter;
            }
        };

        ws.onclose = () => {
            console.log("WebSocket disconnected.");
            stopCamera();
        };
        
    } catch (err) {
        console.error("Camera access failed:", err);
        alert("Could not access camera. Please allow permissions.");
        isStreaming.value = false;
    }
};

const captureAndSendFrames = () => {
    streamInterval = setInterval(() => {
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        if (!videoElement.value || videoElement.value.readyState < 2) return;
        
        const canvas = canvasElement.value;
        const ctx = canvas.getContext('2d');
        canvas.width = videoElement.value.videoWidth || 640;
        canvas.height = videoElement.value.videoHeight || 480;
        
        ctx.drawImage(videoElement.value, 0, 0, canvas.width, canvas.height);
        
        // Balanced compression for local streams (higher quality)
        const base64Frame = canvas.toDataURL("image/jpeg", 0.85);
        
        ws.send(JSON.stringify({
            type: selectedExercise.value,
            image: base64Frame
        }));
    }, 150); // ~7 FPS provides a good balance for tracking
};

const stopCamera = () => {
    if (streamInterval) clearInterval(streamInterval);
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: "stop" }));
    } else {
        finalizeStop();
    }
};

const finalizeStop = () => {
    if (ws) ws.close();
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
    }
    isStreaming.value = false;
    currentFrame.value = null;
    currentCounter.value = null;
};

const handleSaveSet = async (rawReport) => {
    try {
        await fetch(`${baseUrl}/api/video/session/set/save`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                session_id: sessionId.value,
                exercise_type: selectedExercise.value,
                set_number: currentSetIndex.value,
                raw_report: rawReport
            })
        });
        
        // Ensure robust array updates
        processedDataRawList.value.push({
            set_number: currentSetIndex.value,
            data: JSON.parse(JSON.stringify(rawReport))
        });
        
        activeTab.value = `set-${currentSetIndex.value}`;
        
        // Progress Set
        if (currentSetIndex.value < numberOfSets.value) {
            currentSetIndex.value++;
        } else {
            // Aggregate if end.
            if (numberOfSets.value > 1) {
                await aggregateSessionData();
            }
            // Mark complete by unsetting current session state hooks (optional, allow review)
            sessionId.value = null;
            currentSetIndex.value = 1;
        }
    } catch (err) {
        console.error("Error saving set: ", err);
        alert("Failed to save set details.");
    }
};

const aggregateSessionData = async () => {
    try {
        isAggregating.value = true;
        const res = await fetch(`${baseUrl}/api/video/session/aggregate`, {
             method: 'POST',
             headers: {'Content-Type': 'application/json'},
             body: JSON.stringify({
                 session_id: sessionId.value
             })
        });
        aggregatedSessionData.value = await res.json();
        activeTab.value = 'final';
    } catch (e) {
        console.err("Error aggregating: ", e);
    } finally {
        isAggregating.value = false;
    }
};

// Cleanup securely if user navigates away
onUnmounted(() => {
    finalizeStop();
});

</script>

<template>
    <section class="input-section" v-if="!isStreaming">
        <div class="intro">
            <h2>Live Exercise Tracking</h2>
            <p>Select an exercise and allow camera access to begin real-time pose evaluation.</p>
        </div>
        
        <div class="right-container">
            <div class="settings-group">
                <h3>Number of Sets</h3>
                <select v-model="numberOfSets" class="fancy-select">
                    <option :value="1">1 Set</option>
                    <option :value="2">2 Sets</option>
                    <option :value="3">3 Sets</option>
                    <option :value="4">4 Sets</option>
                    <option :value="5">5 Sets</option>
                </select>
            </div>

            <div class="exercises-container">
                <p
                    class="exercise"
                    v-for="exercise in EXERCISES"
                    :key="exercise"
                    :class="{ active: selectedExercise == exercise }"
                    @click="selectedExercise = exercise"
                >
                    {{ exercise }}
                </p>
            </div>

            <button class="process-btn" @click="startCamera">
                <span v-if="sessionId">Start Set {{ currentSetIndex }}!</span>
                <span v-else>Start Workout!</span>
            </button>
        </div>
    </section>

    <section class="streaming-section" v-show="isStreaming">
        <video ref="videoElement" autoplay playsinline muted style="display: none;"></video>
        <canvas ref="canvasElement" style="display: none;"></canvas>
        
        <div class="feed-container">
               <img v-if="currentFrame" :src="currentFrame" alt="Live Feed" class="live-feed" />
               <div v-else class="loading">Loading stream mapping...</div>
               
               <div class="server-error" v-if="serverError">
                  <p>Error: {{ serverError }}</p>
               </div>

               <div class="counter-overlay" v-if="currentCounter !== null">
                  <div class="counter-box">
                      <span class="label">STATUS:</span>
                      <pre>{{ currentCounter }}</pre>
                  </div>
               </div>
        </div>

        <button class="stop-btn" @click="stopCamera">
            <span>Stop Workout</span>
        </button>
    </section>

    <!-- Results Summary & Multi-Set Tabs -->
    <div v-if="processedDataRawList.length > 0 && !isStreaming" class="results-dashboard">
        <h2 class="dashboard-title">Live Session Results</h2>
        <div class="tabs-wrapper">
            <button 
                v-for="set in processedDataRawList" 
                :key="set.set_number"
                @click="activeTab = `set-${set.set_number}`"
                class="tab-btn"
                :class="{ 'active-tab': activeTab === `set-${set.set_number}` }"
            >
                Set {{ set.set_number }}
            </button>
            <button 
                v-if="aggregatedSessionData"
                @click="activeTab = 'final'"
                class="tab-btn"
                :class="{ 'active-tab': activeTab === 'final' }"
            >
                Final Report
            </button>
        </div>

        <!-- Render active tab content properly -->
        <div v-for="set in processedDataRawList" :key="`result-${set.set_number}`" v-show="activeTab === `set-${set.set_number}`">
            <Result :data="set.data" />
        </div>

        <div v-if="aggregatedSessionData" v-show="activeTab === 'final'" class="final-report-card">
            <h2>Session Overview <span class="badge">{{ numberOfSets }} Sets</span></h2>
            <div class="metrics-grid">
                <div class="metric-box">
                    <p><span>Overall Score</span> <strong>{{ aggregatedSessionData.overall_score.toFixed(2) }}%</strong></p>
                    <p><span>Consistency</span> <strong>{{ aggregatedSessionData.consistency_score.toFixed(2) }}</strong></p>
                    <p><span>Total Reps</span> <strong>{{ aggregatedSessionData.total_reps }}</strong></p>
                    <p><span>Fatigue Index</span> <strong>{{ aggregatedSessionData.fatigue_index.toFixed(2) }}</strong></p>
                </div>
                <div class="metric-box">
                    <p><span>Accuracy Trend</span> <strong>{{ aggregatedSessionData.accuracy_trend }}</strong></p>
                    <p><span>Freq. Error</span> <strong>{{ aggregatedSessionData.most_frequent_error }}</strong></p>
                    <p><span>Best Set</span> <strong>Set {{ aggregatedSessionData.best_set }}</strong></p>
                    <p><span>Worst Set</span> <strong>Set {{ aggregatedSessionData.worst_set }}</strong></p>
                </div>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.input-section {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    align-items: center;
    margin-bottom: 3rem;

    .intro {
        text-align: center;
        h2 { 
            font-size: 2.5rem;
            color: var(--text-main); 
            margin-bottom: 0.5rem; 
        }
        p {
            color: var(--text-muted);
            font-size: 1.1rem;
        }
    }

    .right-container {
        display: flex;
        flex-direction: column;
        width: 100%;
        max-width: 600px;
        background: var(--surface-light);
        padding: 2.5rem;
        border-radius: 24px;
        border: var(--border-subtle);
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        
        .settings-group {
            margin-bottom: 2rem;
            h3 {
                margin-bottom: 0.8rem;
                color: var(--text-muted);
                font-size: 1rem;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .fancy-select {
                width: 100%;
                padding: 1rem 1.2rem;
                background: var(--bg-base);
                color: var(--text-main);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                font-size: 1.1rem;
                outline: none;
                transition: border-color 0.3s;
                font-family: var(--font-body);

                &:focus {
                    border-color: var(--primary-color);
                }
            }
        }

        .exercises-container {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 2.5rem;

            .exercise {
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 1rem 0;
                flex: calc(50% - 0.5rem);
                color: var(--text-muted);
                background: rgba(255, 255, 255, 0.03);
                font-family: var(--font-heading);
                text-transform: uppercase;
                letter-spacing: 1px;
                border: 2px solid rgba(255,255,255,0.05);
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s ease;

                &:hover {
                    background: rgba(255, 255, 255, 0.08);
                    border-color: rgba(255,255,255,0.2);
                    transform: translateY(-4px);
                }

                &.active {
                    background: rgba(16, 185, 129, 0.1);
                    color: var(--primary-color);
                    border-color: var(--primary-color);
                    box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
                }
            }
        }

        .process-btn {
            border: none;
            background: linear-gradient(135deg, var(--primary-hover), var(--primary-color));
            padding: 1.25rem 0;
            color: #0f172a;
            font-size: 1.25rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            cursor: pointer;
            border-radius: 12px;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-glow);

            &:hover {
                transform: translateY(-2px);
                box-shadow: 0 0 25px rgba(16, 185, 129, 0.4);
                filter: brightness(1.1);
            }
        }
    }
}

.streaming-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2rem;
    
    .feed-container {
        position: relative;
        width: 100%;
        max-width: 800px;
        background: #000;
        border-radius: 24px;
        overflow: hidden;
        min-height: 480px;
        display: flex;
        justify-content: center;
        align-items: center;
        border: 2px solid rgba(255,255,255,0.1);
        box-shadow: 0 20px 40px rgba(0,0,0,0.5);

        .live-feed {
            width: 100%;
            height: auto;
            display: block;
        }

        .loading {
            color: var(--primary-color);
            font-size: 1.2rem;
            font-weight: bold;
            animation: pulse 1.5s infinite;
        }
        
        .server-error {
            position: absolute;
            background: rgba(220, 38, 38, 0.9);
            color: white;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-weight: bold;
        }

        .counter-overlay {
            position: absolute;
            top: 20px;
            left: 20px;
            
            .counter-box {
               background: rgba(15, 23, 42, 0.85);
               backdrop-filter: blur(8px);
               color: var(--text-main);
               padding: 15px 20px;
               border-radius: 16px;
               font-family: var(--font-heading);
               font-size: 1.2rem;
               border: 1px solid rgba(255,255,255,0.1);
               box-shadow: 0 10px 20px rgba(0,0,0,0.5);
               
               .label { 
                   font-size: 0.8rem;
                   text-transform: uppercase;
                   letter-spacing: 2px;
                   color: var(--primary-color); 
                   display: block; 
                   margin-bottom: 8px; 
               }
               pre { margin: 0; font-family: monospace; font-size: 1.3rem; }
            }
        }
    }

    .stop-btn {
        background: rgba(239, 68, 68, 0.1);
        color: #ef4444;
        border: 2px solid #ef4444;
        padding: 1rem 3rem;
        font-size: 1.2rem;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-radius: 12px;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        
        &:hover {
            transform: translateY(-4px);
            background: #ef4444;
            color: #fff;
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.4);
        }
    }
}

/* Results Dashboard Styling */
.results-dashboard {
    margin-top: 3rem;
    width: 100%;
    max-width: 900px;
    padding: 0 1rem;
    
    .dashboard-title {
        text-align: center;
        margin-bottom: 2rem;
        font-size: 2rem;
        color: var(--text-main);
    }
    
    .tabs-wrapper {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        justify-content: center;
        margin-bottom: 3rem;
        
        .tab-btn {
            background: var(--surface-light);
            color: var(--text-muted);
            border: 1px solid rgba(255,255,255,0.1);
            padding: 12px 24px;
            font-size: 1rem;
            font-weight: 600;
            border-radius: 30px;
            cursor: pointer;
            transition: all 0.3s ease;
            
            &:hover {
                background: rgba(255,255,255,0.05);
                color: var(--text-main);
            }
            
            &.active-tab {
                background: var(--primary-color);
                color: #0f172a;
                border-color: var(--primary-color);
                box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
            }
        }
    }
    
    .final-report-card {
        background: var(--surface-light);
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(12px);
        padding: 3rem;
        border-radius: 24px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        
        h2 {
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            
            .badge {
                font-size: 0.9rem;
                background: rgba(16, 185, 129, 0.2);
                color: var(--primary-color);
                padding: 4px 12px;
                border-radius: 20px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            
            .metric-box {
                background: rgba(0,0,0,0.2);
                padding: 2rem;
                border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.05);
                
                p {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px 0;
                    border-bottom: 1px solid rgba(255,255,255,0.05);
                    
                    &:last-child {
                        border-bottom: none;
                        padding-bottom: 0;
                    }
                    
                    span {
                        color: var(--text-muted);
                        font-size: 0.95rem;
                    }
                    
                    strong {
                        font-size: 1.1rem;
                        color: var(--text-main);
                        font-family: var(--font-heading);
                    }
                }
            }
        }
    }
}

@keyframes pulse {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}
</style>
