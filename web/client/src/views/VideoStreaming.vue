<script setup>
import { ref } from "vue";
import axios from "axios";

import Dropzone from "../components/Dropzone.vue";
import DropzoneLoading from "../components/DropzoneLoading.vue";
import Result from "../components/Result.vue";

const apiUrl = import.meta.env.VITE_BASE_URL || "http://127.0.0.1:8000";

const EXERCISES = ["squat", "plank", "bicep_curl", "lunge"];

const submitData = ref({
    videoFiles: {}, // { 1: File, 2: File, ... }
    exerciseType: null,
});
const numberOfSets = ref(1);
const processedDataRawList = ref([]); // raw JSONs
const aggregatedSessionData = ref(null);

const activeTab = ref("set-1");
const isProcessing = ref(false);
const processingStatus = ref("");

const uploadToServer = async () => {
    for (let i = 1; i <= numberOfSets.value; i++) {
        if (!submitData.value.videoFiles[i]) {
            alert(`No video selected for Set ${i}`);
            return;
        }
    }

    if (!submitData.value.exerciseType) {
        alert("No exercise type selected");
        return;
    }

    // Hard Reactivity Reset
    processedDataRawList.value = [];
    aggregatedSessionData.value = null;
    
    try {
        isProcessing.value = true;
        processingStatus.value = `Initializing Session...`;

        // Create DB Session Handshake First
        const sessionResp = await axios.post(`${apiUrl}/api/video/session/start`, {
            exercise_type: submitData.value.exerciseType
        });
        
        if (sessionResp.data.error) throw new Error(sessionResp.data.error);
        const sessionId = sessionResp.data.session_id;

        for (let i = 1; i <= numberOfSets.value; i++) {
            processingStatus.value = `Processing Set ${i} of ${numberOfSets.value}...`;
            
            // 1. Process Video via Legacy Endpoint
            let uploadRes;
            try {
                uploadRes = await axios.post(
                    `${apiUrl}/api/video/upload?type=${submitData.value.exerciseType}`,
                    { file: submitData.value.videoFiles[i] },
                    { headers: { "Content-Type": "multipart/form-data" } }
                );
            } catch (err) {
                console.error(`Error uploading video set ${i}: `, err);
                throw new Error(`Upload Failed for Set ${i}`);
            }
            
            const rawReport = uploadRes.data;

            // 2. Save Set using new endpoint
            await axios.post(`${apiUrl}/api/video/session/set/save`, {
                session_id: sessionId,
                exercise_type: submitData.value.exerciseType,
                set_number: i,
                raw_report: rawReport
            });
            
            // Add raw result mapped cleanly for Reactivity
            processedDataRawList.value.push({
                set_number: i,
                data: JSON.parse(JSON.stringify(rawReport)) // avoid stale references
            });
        }
        
        processingStatus.value = `Aggregating Results...`;
        
        // 3. Aggregate Session if multi-set
        if (numberOfSets.value > 1) {
            const aggregateResp = await axios.post(`${apiUrl}/api/video/session/aggregate`, {
                session_id: sessionId
            });
            const aggData = aggregateResp.data;
            // Only set if it's a valid success response (not an error object)
            if (aggData && aggData.status === 'success') {
                aggregatedSessionData.value = aggData;
                activeTab.value = 'final'; // Auto-switch to Final Report
            } else {
                console.error('Aggregation error from server:', aggData);
            }
        }
    } catch (e) {
        console.error("Error: ", e);
        alert("An error occurred during processing. Check console for details.");
    } finally {
        isProcessing.value = false;
        processingStatus.value = "";
    }
};
</script>

<template>
    <!-- Input section -->
    <section class="input-section">
        <div class="uploads-col">
            <!-- Display N dropzones based on numberOfSets -->
            <div v-for="i in numberOfSets" :key="i" style="margin-bottom: 2rem;">
                <h3>Set {{ i }} Video</h3>
                <Dropzone
                    v-show="!isProcessing"
                    @file-uploaded="(file) => (submitData.videoFiles[i] = file)"
                />
                <p v-if="submitData.videoFiles[i] && !isProcessing">Selected: {{ submitData.videoFiles[i].name }}</p>
            </div>
            <div v-show="isProcessing">
                 <DropzoneLoading />
                 <p style="text-align:center; font-weight:bold; margin-top:1rem;">{{ processingStatus }}</p>
            </div>
        </div>

        <div class="right-container">
            <!-- Number of sets selector -->
            <div class="settings-group">
                <h3>Number of Sets</h3>
                <select v-model="numberOfSets" class="fancy-select">
                    <option :value="1">1 Set (Single Video)</option>
                    <option :value="2">2 Sets</option>
                    <option :value="3">3 Sets</option>
                    <option :value="4">4 Sets</option>
                    <option :value="5">5 Sets</option>
                </select>
            </div>

            <!-- exercises selection -->
            <div class="exercises-container">
                <p
                    class="exercise"
                    v-for="exercise in EXERCISES"
                    :class="{ active: submitData.exerciseType == exercise }"
                    @click="submitData.exerciseType = exercise"
                >
                    {{ exercise }}
                </p>
            </div>

            <button class="process-btn" @click="uploadToServer">
                <span>Process!</span>
            </button>
        </div>
    </section>

    <!-- Results section -->
    <div v-if="processedDataRawList.length > 0" class="results-dashboard">
        <h2 class="dashboard-title">Session Results</h2>
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

        <!-- Set Reports -->
        <div v-for="set in processedDataRawList" :key="`result-${set.set_number}`" v-show="activeTab === `set-${set.set_number}`">
            <Result :data="set.data" />
        </div>

        <!-- Final Aggregated Report -->
        <div v-if="aggregatedSessionData" v-show="activeTab === 'final'" class="final-report-card">
            
            <h2 style="margin-bottom: 1.5rem;">Session Overview — {{ aggregatedSessionData.total_sets }} Sets Analyzed</h2>

            <!-- Key Metrics Grid -->
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 2rem;">
                <!-- Over Accuracy -->
                <div style="background: rgba(0,0,0,0.2); padding:1.25rem; border-radius:16px; border-left: 6px solid var(--primary-color); border-top: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <p style="font-size:0.75rem; font-weight:700; color: var(--text-muted); margin-bottom:8px; text-transform: uppercase;">Overall Accuracy</p>
                    <p style="font-size:2.5rem; font-weight:800; color: var(--primary-color); line-height: 1; font-family: var(--font-heading);">{{ Number(aggregatedSessionData.overall_score || 0).toFixed(1) }}%</p>
                    <p style="font-size:0.8rem; color: var(--text-muted); margin-top: 8px;">Weighted average across all sets</p>
                </div>
                
                <!-- Fatigue Card -->
                <div style="background: rgba(0,0,0,0.2); padding:1.25rem; border-radius:16px; border-left: 6px solid #f59e0b; border-top: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <p style="font-size:0.75rem; font-weight:700; color: var(--text-muted); margin-bottom:8px; text-transform: uppercase;">Fatigue Index</p>
                    <p style="font-size:2rem; font-weight:800; color: #f59e0b; line-height: 1; font-family: var(--font-heading);">{{ aggregatedSessionData.fatigue_label }}</p>
                    <p style="font-size:0.8rem; color: var(--text-muted); margin-top: 8px;">
                        <span v-if="aggregatedSessionData.fatigue_index > 5">⚠️ Performance declined slightly</span>
                        <span v-else-if="aggregatedSessionData.fatigue_index < -5">✅ Performance improved</span>
                        <span v-else-if="aggregatedSessionData.total_sets > 1">✅ Consistent across sets</span>
                        <span v-else>Establishing first set benchmark</span>
                    </p>
                </div>

                <!-- Total Reps Card -->
                <div style="background: rgba(0,0,0,0.2); padding:1.25rem; border-radius:16px; border-left: 6px solid #10b981; border-top: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <p style="font-size:0.75rem; font-weight:700; color: var(--text-muted); margin-bottom:8px; text-transform: uppercase;">Total Repetitions</p>
                    <p style="font-size:2.5rem; font-weight:800; color: #10b981; line-height: 1; font-family: var(--font-heading);">{{ aggregatedSessionData.total_reps ?? 0 }}</p>
                    <p style="font-size:0.8rem; color: var(--text-muted); margin-top: 8px;">Combined volume from all sets</p>
                </div>

                <!-- Consistency Card -->
                <div style="background: rgba(0,0,0,0.2); padding:1.25rem; border-radius:16px; border-left: 6px solid #8b5cf6; border-top: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05); border-bottom: 1px solid rgba(255,255,255,0.05);">
                    <p style="font-size:0.75rem; font-weight:700; color: var(--text-muted); margin-bottom:8px; text-transform: uppercase;">Set Consistency</p>
                    <div style="display: flex; align-items: baseline; gap: 8px;">
                        <p style="font-size:2rem; font-weight:800; color: #8b5cf6; line-height: 1; font-family: var(--font-heading);">{{ aggregatedSessionData.consistency_label }}</p>
                    </div>
                    <p style="font-size:0.8rem; color: var(--text-muted); margin-top: 8px;">Precision score (Higher is steadier)</p>
                </div>
            </div>

            <!-- Per-Set Rep Breakdown Table -->
            <div style="margin-bottom:2rem;" v-if="aggregatedSessionData.per_set_reps && aggregatedSessionData.per_set_reps.length">
                <h3 style="margin-bottom:1rem; color: var(--text-main); font-weight: 700;">Performance Breakdown</h3>
                <table style="width:100%; border-collapse:collapse; font-size:0.95rem; border-radius: 12px; overflow: hidden; background: rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.05);">
                    <thead>
                        <tr style="background: rgba(16, 185, 129, 0.1); color: var(--primary-color);">
                            <th style="padding:14px; text-align:left;">Set</th>
                            <th style="padding:14px; text-align:center;">Rep Count</th>
                            <th style="padding:14px; text-align:center;">Accuracy</th>
                            <th style="padding:14px; text-align:center;">Performance</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="s in aggregatedSessionData.per_set_reps" :key="s.set"
                            :style="s.set === aggregatedSessionData.best_set ? 'background: rgba(16, 185, 129, 0.05);' : s.set === aggregatedSessionData.worst_set && aggregatedSessionData.total_sets > 1 ? 'background: rgba(239, 68, 68, 0.05);' : 'border-bottom: 1px solid rgba(255,255,255,0.05);'">
                            <td style="padding:14px; font-weight:700; color: var(--text-main);">Set {{ s.set }}</td>
                            <td style="padding:14px; text-align:center; color: var(--text-muted);">{{ s.reps }}</td>
                            <td style="padding:14px; text-align:center; font-weight: 600; color: var(--text-main);">{{ s.score }}%</td>
                            <td style="padding:14px; text-align:center;">
                                <span v-if="s.set === aggregatedSessionData.best_set" style="background:rgba(16, 185, 129, 0.2); color: var(--primary-color); padding:4px 10px; border-radius:20px; font-size:0.8rem; font-weight:bold;">🏆 Best</span>
                                <span v-else-if="s.set === aggregatedSessionData.worst_set && aggregatedSessionData.total_sets > 1" style="background:rgba(239, 68, 68, 0.2); color:#ef4444; padding:4px 10px; border-radius:20px; font-size:0.8rem; font-weight:bold;">📉 Lowest</span>
                                <span v-else style="color:var(--text-muted);">—</span>
                            </td>
                        </tr>
                        <tr style="background: rgba(255,255,255,0.03); font-weight:800; color: var(--text-main);">
                            <td style="padding:14px;">SESSION TOTAL</td>
                            <td style="padding:14px; text-align:center;">{{ aggregatedSessionData.total_reps }}</td>
                            <td style="padding:14px; text-align:center;">{{ Number(aggregatedSessionData.overall_score || 0).toFixed(1) }}%</td>
                            <td style="padding:14px; text-align:center; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px;">
                                {{ aggregatedSessionData.accuracy_trend }}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Summary Insights -->
            <div style="background: rgba(0,0,0,0.2); padding: 1.5rem; border-radius: 12px; border: 1px dashed rgba(255,255,255,0.1);">
                <h4 style="margin-bottom: 1rem; color: var(--text-muted); text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px;">Session Insights</h4>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; font-size:0.95rem;">
                    <p style="color: var(--text-main);"><strong style="color: var(--text-muted);">Primary Error Pattern:</strong> {{ aggregatedSessionData.most_frequent_error }}</p>
                    <p style="color: var(--text-main);"><strong style="color: var(--text-muted);">Accuracy Trend:</strong> {{ aggregatedSessionData.accuracy_trend }}</p>
                    <p style="color: var(--text-main);"><strong style="color: var(--text-muted);">Best Performance:</strong> Set {{ aggregatedSessionData.best_set }}</p>
                    <p style="color: var(--text-main);"><strong style="color: var(--text-muted);">Consistency:</strong> {{ aggregatedSessionData.consistency_label }}</p>
                </div>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.input-section {
    display: flex;
    gap: 2rem;
    margin-bottom: 4rem;

    * {
        flex: 1;
    }
    
    // Minimal Dropzone Styling Fixes
    .uploads-col {
        background: var(--surface-light);
        padding: 2.5rem;
        border-radius: 24px;
        border: var(--border-subtle);
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        
        h3 {
            color: var(--text-main);
            margin-bottom: 1rem;
        }
        
        p {
            color: var(--text-muted);
            margin-top: 1rem;
        }
    }

    .right-container {
        display: flex;
        flex-direction: column;
        width: 100%;
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

                &:focus { border-color: var(--primary-color); }
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

/* Results Dashboard Styling */
.results-dashboard {
    margin-top: 3rem;
    width: 100%;
    margin-inline: auto;
    
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
}
</style>
