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
            <div style="margin-bottom: 2rem;">
                <h3 style="margin-bottom: 0.5rem;">Number of Sets</h3>
                <select v-model="numberOfSets" style="padding: 10px; width: 100%; border: 3px solid var(--primary-color); border-radius: 5px; font-size: 1.1rem;">
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
    <div v-if="processedDataRawList.length > 0" style="margin-top:2rem;">
        <h2 style="text-align: center; margin-bottom: 1rem;">Session Results</h2>
        <div style="display:flex; gap:10px; justify-content:center; margin-bottom: 2rem;">
            <button 
                v-for="set in processedDataRawList" 
                :key="set.set_number"
                @click="activeTab = `set-${set.set_number}`"
                style="padding: 10px 20px; font-weight:bold; cursor:pointer"
            >
                Set {{ set.set_number }}
            </button>
            <button 
                v-if="aggregatedSessionData"
                @click="activeTab = 'final'"
                style="padding: 10px 20px; font-weight:bold; cursor:pointer; background-color: var(--primary-color); color: white; border: none; border-radius: 5px;"
            >
                Final Report
            </button>
        </div>

        <!-- Set Reports -->
        <div v-for="set in processedDataRawList" :key="`result-${set.set_number}`" v-show="activeTab === `set-${set.set_number}`">
            <Result :data="set.data" />
        </div>

        <!-- Final Aggregated Report -->
        <div v-if="aggregatedSessionData" v-show="activeTab === 'final'" style="border:3px solid var(--primary-color); padding: 2rem; border-radius: 10px; background: white;">
            
            <h2 style="margin-bottom: 1.5rem;">Session Overview — {{ aggregatedSessionData.total_sets }} Sets Analyzed</h2>

            <!-- Key Metrics Grid -->
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 2rem;">
                <!-- Over Accuracy -->
                <div style="background:#f9f9f9; padding:1.25rem; border-radius:12px; border-left: 6px solid var(--primary-color); box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <p style="font-size:0.75rem; font-weight:700; color:#666; margin-bottom:8px; text-transform: uppercase; letter-spacing: 0.5px;">Overall Accuracy</p>
                    <p style="font-size:2.5rem; font-weight:800; color: var(--primary-color); line-height: 1;">{{ Number(aggregatedSessionData.overall_score || 0).toFixed(1) }}%</p>
                    <p style="font-size:0.8rem; color:#888; margin-top: 8px;">Weighted average across all sets</p>
                </div>
                
                <!-- Fatigue Card -->
                <div style="background:#f9f9f9; padding:1.25rem; border-radius:12px; border-left: 6px solid #f59e0b; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <p style="font-size:0.75rem; font-weight:700; color:#666; margin-bottom:8px; text-transform: uppercase; letter-spacing: 0.5px;">Fatigue Index</p>
                    <p style="font-size:2rem; font-weight:800; color: #f59e0b; line-height: 1;">{{ aggregatedSessionData.fatigue_label }}</p>
                    <p style="font-size:0.8rem; color:#888; margin-top: 8px;">
                        <span v-if="aggregatedSessionData.fatigue_index > 5">⚠️ Performance declined slightly</span>
                        <span v-else-if="aggregatedSessionData.fatigue_index < -5">✅ Performance improved</span>
                        <span v-else-if="aggregatedSessionData.total_sets > 1">✅ Consistent across sets</span>
                        <span v-else>Establishing first set benchmark</span>
                    </p>
                </div>

                <!-- Total Reps Card -->
                <div style="background:#f9f9f9; padding:1.25rem; border-radius:12px; border-left: 6px solid #10b981; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <p style="font-size:0.75rem; font-weight:700; color:#666; margin-bottom:8px; text-transform: uppercase; letter-spacing: 0.5px;">Total Repetitions</p>
                    <p style="font-size:2.5rem; font-weight:800; color: #10b981; line-height: 1;">{{ aggregatedSessionData.total_reps ?? 0 }}</p>
                    <p style="font-size:0.8rem; color:#888; margin-top: 8px;">Combined volume from all sets</p>
                </div>

                <!-- Consistency Card -->
                <div style="background:#f9f9f9; padding:1.25rem; border-radius:12px; border-left: 6px solid #8b5cf6; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
                    <p style="font-size:0.75rem; font-weight:700; color:#666; margin-bottom:8px; text-transform: uppercase; letter-spacing: 0.5px;">Set Consistency</p>
                    <div style="display: flex; align-items: baseline; gap: 8px;">
                        <p style="font-size:2rem; font-weight:800; color: #8b5cf6; line-height: 1;">{{ aggregatedSessionData.consistency_label }}</p>
                    </div>
                    <p style="font-size:0.8rem; color:#888; margin-top: 8px;">Precision score (Higher is steadier)</p>
                </div>
            </div>

            <!-- Per-Set Rep Breakdown Table -->
            <div style="margin-bottom:2rem;" v-if="aggregatedSessionData.per_set_reps && aggregatedSessionData.per_set_reps.length">
                <h3 style="margin-bottom:1rem; color: #333; font-weight: 700;">Performance Breakdown</h3>
                <table style="width:100%; border-collapse:collapse; font-size:0.95rem; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <thead>
                        <tr style="background: var(--primary-color); color:white;">
                            <th style="padding:14px; text-align:left;">Set</th>
                            <th style="padding:14px; text-align:center;">Rep Count</th>
                            <th style="padding:14px; text-align:center;">Accuracy</th>
                            <th style="padding:14px; text-align:center;">Performance</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="s in aggregatedSessionData.per_set_reps" :key="s.set"
                            :style="s.set === aggregatedSessionData.best_set ? 'background:#ecfdf5;' : s.set === aggregatedSessionData.worst_set && aggregatedSessionData.total_sets > 1 ? 'background:#fff1f2;' : 'background:white; border-bottom: 1px solid #eee;'">
                            <td style="padding:14px; font-weight:700;">Set {{ s.set }}</td>
                            <td style="padding:14px; text-align:center;">{{ s.reps }}</td>
                            <td style="padding:14px; text-align:center; font-weight: 600;">{{ s.score }}%</td>
                            <td style="padding:14px; text-align:center;">
                                <span v-if="s.set === aggregatedSessionData.best_set" style="background:#10b981; color:white; padding:4px 10px; border-radius:20px; font-size:0.8rem; font-weight:bold;">🏆 Best</span>
                                <span v-else-if="s.set === aggregatedSessionData.worst_set && aggregatedSessionData.total_sets > 1" style="background:#ef4444; color:white; padding:4px 10px; border-radius:20px; font-size:0.8rem; font-weight:bold;">📉 Lowest</span>
                                <span v-else style="color:#94a3b8;">—</span>
                            </td>
                        </tr>
                        <tr style="background: #e2e8f0; font-weight:800; color: #1e293b;">
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
            <div style="background: #f8fafc; padding: 1.5rem; border-radius: 12px; border: 1px dashed #cbd5e1;">
                <h4 style="margin-bottom: 1rem; color: #475569; text-transform: uppercase; font-size: 0.8rem; letter-spacing: 1px;">Session Insights</h4>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 20px; font-size:0.95rem;">
                    <p style="color: #334155;"><strong style="color: #64748b;">Primary Error Pattern:</strong> {{ aggregatedSessionData.most_frequent_error }}</p>
                    <p style="color: #334155;"><strong style="color: #64748b;">Accuracy Trend:</strong> {{ aggregatedSessionData.accuracy_trend }}</p>
                    <p style="color: #334155;"><strong style="color: #64748b;">Best Performance:</strong> Set {{ aggregatedSessionData.best_set }}</p>
                    <p style="color: #334155;"><strong style="color: #64748b;">Consistency:</strong> {{ aggregatedSessionData.consistency_label }}</p>
                </div>
            </div>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.input-section {
    display: flex;
    gap: 1rem;

    * {
        flex: 1;
    }

    .right-container {
        display: flex;
        flex-direction: column;
        width: 100%;

        .exercises-container {
            display: flex;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 1rem;

            .exercise {
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 1rem 0;
                flex: 45%;
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
</style>
