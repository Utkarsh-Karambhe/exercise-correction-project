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
        
        // Compression is crucial for live WebSocket streams to prevent clogging
        const base64Frame = canvas.toDataURL("image/jpeg", 0.6);
        
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
            <div style="margin-bottom: 2rem;">
                <h3 style="margin-bottom: 0.5rem; color: var(--secondary-color);">Number of Sets</h3>
                <select v-model="numberOfSets" style="padding: 10px; width: 100%; border: 3px solid var(--primary-color); border-radius: 5px; font-size: 1.1rem;">
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
    <div v-if="processedDataRawList.length > 0 && !isStreaming" style="margin-top:2rem; width: 100%; max-width: 900px; padding: 0 1rem;">
        <h2 style="text-align: center; margin-bottom: 1rem;">Live Session Results</h2>
        <div style="display:flex; flex-wrap:wrap; gap:10px; justify-content:center; margin-bottom: 2rem;">
            <button 
                v-for="set in processedDataRawList" 
                :key="set.set_number"
                @click="activeTab = `set-${set.set_number}`"
                style="padding: 10px 20px; font-weight:bold; cursor:pointer;"
                :style="activeTab === `set-${set.set_number}` ? 'background-color: var(--primary-color); color: white; border: none; border-radius: 5px;' : ''"
            >
                Set {{ set.set_number }}
            </button>
            <button 
                v-if="aggregatedSessionData"
                @click="activeTab = 'final'"
                style="padding: 10px 20px; font-weight:bold; cursor:pointer;"
                :style="activeTab === 'final' ? 'background-color: var(--primary-color); color: white; border: none; border-radius: 5px;' : ''"
            >
                Final Report
            </button>
        </div>

        <!-- Render active tab content properly -->
        <div v-for="set in processedDataRawList" :key="`result-${set.set_number}`" v-show="activeTab === `set-${set.set_number}`">
            <Result :data="set.data" />
        </div>

        <div v-if="aggregatedSessionData" v-show="activeTab === 'final'" style="border:3px solid var(--primary-color); padding: 2rem; border-radius: 10px; background: white;">
            <h2>Session Overview ({{ numberOfSets }} Sets)</h2>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top:2rem;">
                <div>
                    <p><strong>Overall Score:</strong> {{ aggregatedSessionData.overall_score.toFixed(2) }}%</p>
                    <p><strong>Consistency Score:</strong> {{ aggregatedSessionData.consistency_score.toFixed(2) }}</p>
                    <p><strong>Total Reps:</strong> {{ aggregatedSessionData.total_reps }}</p>
                    <p><strong>Fatigue Index:</strong> {{ aggregatedSessionData.fatigue_index.toFixed(2) }}</p>
                </div>
                <div>
                    <p><strong>Accuracy Trend:</strong> {{ aggregatedSessionData.accuracy_trend }}</p>
                    <p><strong>Most Frequent Error:</strong> {{ aggregatedSessionData.most_frequent_error }}</p>
                    <p><strong>Best Set:</strong> Set {{ aggregatedSessionData.best_set }}</p>
                    <p><strong>Worst Set:</strong> Set {{ aggregatedSessionData.worst_set }}</p>
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

    .intro {
        text-align: center;
        h2 { color: var(--secondary-color); margin-bottom: 0.5rem; }
    }

    .right-container {
        display: flex;
        flex-direction: column;
        width: 100%;
        max-width: 600px;
        
        .exercises-container {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 2rem;

            .exercise {
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 1rem 0;
                flex: calc(50% - 0.5rem);
                color: var(--secondary-color);
                text-transform: uppercase;
                border: 3px solid var(--primary-color);
                border-radius: 0.3rem;
                cursor: pointer;
                transition: all 0.25s ease;

                &:hover {
                    box-shadow: 0 6px 18px 0 rgba(#000, 0.1);
                    transform: translateY(-6px);
                }

                &.active {
                    background-color: var(--primary-color);
                    color: white;
                    font-weight: 700;
                }
            }
        }

        .process-btn {
            border: none;
            background-color: var(--primary-color);
            padding: 1.25rem 0;
            color: whitesmoke;
            font-size: 1.25rem;
            font-weight: 700;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.25s ease;

            &:hover {
                box-shadow: 0 6px 18px 0 rgba(#000, 0.1);
                color: var(--primary-color);
                border-color: transparent;
                background-color: transparent;
            }
        }
    }
}

.streaming-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
    
    .feed-container {
        position: relative;
        width: 100%;
        max-width: 800px;
        background: #000;
        border-radius: 12px;
        overflow: hidden;
        min-height: 480px;
        display: flex;
        justify-content: center;
        align-items: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);

        .live-feed {
            width: 100%;
            height: auto;
            display: block;
        }

        .loading {
            color: white;
            font-size: 1.2rem;
            animation: pulse 1.5s infinite;
        }
        
        .server-error {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(220, 38, 38, 0.9);
            color: white;
            padding: 1rem 2rem;
            border-radius: 8px;
            font-weight: bold;
            text-align: center;
            z-index: 10;
        }

        .counter-overlay {
            position: absolute;
            top: 20px;
            left: 20px;
            
            .counter-box {
               background: rgba(0, 0, 0, 0.7);
               color: #fff;
               padding: 10px 15px;
               border-radius: 8px;
               font-family: monospace;
               font-size: 1.1rem;
               border: 2px solid var(--primary-color);
               
               .label { font-weight: bold; color: var(--primary-color); display: block; margin-bottom: 5px; }
               pre { margin: 0; }
            }
        }
    }

    .stop-btn {
        background: #ef4444;
        color: white;
        border: none;
        padding: 1rem 3rem;
        font-size: 1.2rem;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        transition: transform 0.2s;
        
        &:hover {
            transform: scale(1.05);
            background: #dc2626;
        }
    }
}

@keyframes pulse {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}
</style>
