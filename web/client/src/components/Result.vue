<script setup>
import { ref, computed } from "vue";

import Video from "./Video.vue";

const { data } = defineProps(["data"]);
const summaryData = computed(() => {
    let results = {
        total: 0,
        totalInString: "",
        details: {},
    };

    let totalErrors = data.details.length;
    results.total = totalErrors;
    if (totalErrors == 0 || totalErrors == 1)
        results.totalInString = `${totalErrors} error`;
    else results.totalInString = `${totalErrors} errors`;

    data.details.forEach((error) => {
        let stage = error.stage;
        results.details[stage] = results.details[stage]
            ? results.details[stage] + 1
            : 1;
    });

    return results;
});
const selectedDisplay = ref("summary");
const videoStart = ref(0);

const jumpToVideoLocation = (second) => {
    selectedDisplay.value = "video";
    videoStart.value = second;
};
</script>

<template>
    <section class="result-section">
        <!-- Navigators -->
        <ul class="tab-links">
            <li
                :class="{ active: selectedDisplay == 'summary' }"
                @click="() => (selectedDisplay = 'summary')"
            >
                Summary
            </li>
            <li
                :class="{ active: selectedDisplay == 'detail' }"
                @click="() => (selectedDisplay = 'detail')"
            >
                Detail
            </li>
            <li
                v-if="data.file_name"
                :class="{ active: selectedDisplay == 'video' }"
                @click="() => (selectedDisplay = 'video')"
            >
                Full Video
            </li>
        </ul>

        <!-- Contents -->
        <div class="tab-container">
            <!-- Summary content -->
            <template v-if="selectedDisplay == 'summary'">
                <!-- Display Counter or other information -->
                <p class="main" v-if="data.counter">
                    <span class="info-color" v-if="data.type != 'bicep_curl'">
                        Counter: {{ data.counter }}
                    </span>

                    <span class="info-color" v-else>
                        Left arm counter: {{ data.counter.left_counter }} -
                        Right arm counter: {{ data.counter.right_counter }}
                    </span>
                </p>

                <!-- Display error -->
                <p class="main">
                    There are
                    <span class="error-color">
                        {{ summaryData.totalInString }}
                    </span>
                    found.

                    <!-- Icon -->
                    <i
                        class="fa-solid fa-circle-exclamation error-color"
                        v-if="summaryData.total > 0"
                    ></i>
                    <i class="fa-solid fa-circle-check" v-else></i>
                </p>

                <ul class="errors" v-if="summaryData.total > 0">
                    <li v-for="(total, error) in summaryData.details">
                        <i class="fa-solid fa-caret-right"></i>

                        {{ error }}: {{ total }}
                    </li>
                </ul>
            </template>

            <!-- Detail Content -->
            <KeepAlive>
                <template v-if="selectedDisplay == 'detail'">
                    <div
                        class="box-error"
                        v-for="(error, index) in data.details"
                    >
                        <p>
                            {{ index + 1 }}. {{ error.stage }} at
                            <span
                                class="error-time"
                                @click="jumpToVideoLocation(error.timestamp)"
                            >
                                {{ error.timestamp }} second
                            </span>
                        </p>
                        <img :src="`${error.frame}`" />
                        <hr />
                    </div>
                </template>
            </KeepAlive>

            <!-- Full Video content -->
            <KeepAlive>
                <template v-if="selectedDisplay == 'video'">
                    <div class="video-container">
                        <Video
                            :video-name="data.file_name"
                            :start-at="videoStart"
                        ></Video>
                    </div>
                </template>
            </KeepAlive>
        </div>
    </section>
</template>

<style lang="scss" scoped>
.result-section {
    margin-top: 2rem;
    margin-bottom: 5rem;

    .tab-links {
        display: flex;
        gap: 8px;
        margin-bottom: 1.5rem;

        li {
            padding: 0.75rem 1.5rem;
            background-color: var(--surface-light);
            color: var(--text-muted);
            border-radius: 30px;
            font-size: 0.95rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.1);

            &.active {
                background-color: var(--primary-color);
                color: #0f172a;
                border-color: var(--primary-color);
                box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
            }

            &:hover:not(.active) {
                background-color: rgba(255, 255, 255, 0.05);
                color: var(--text-main);
            }
        }
    }

    .tab-container {
        padding: 2.5rem;
        background: var(--surface-light);
        backdrop-filter: blur(12px);
        border: var(--border-subtle);
        border-radius: 24px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.3);

        p.main {
            font-size: 1.35rem;
            margin: 1rem 0 2rem;
            font-family: var(--font-heading);
            color: var(--text-main);

            i {
                font-size: 1.5rem;
                margin-left: 10px;
            }
        }

        ul.errors {
            list-style: none;
            padding: 0;
            li {
                margin: 1rem 0;
                font-size: 1.15rem;
                text-transform: capitalize;
                color: var(--text-main);
                background: rgba(0,0,0,0.2);
                padding: 1rem 1.5rem;
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.05);

                i {
                    margin-right: 1rem;
                    color: var(--primary-color);
                }
            }
        }

        .box-error {
            margin-bottom: 2.5rem;
            background: rgba(0,0,0,0.2);
            padding: 1.5rem;
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.05);

            p {
                font-size: 1.2rem;
                text-transform: capitalize;
                margin-bottom: 1rem;
                color: var(--text-main);
                font-family: var(--font-heading);
            }

            img {
                width: 100%;
                max-width: 500px;
                border-radius: 12px;
                border: 2px solid rgba(255,255,255,0.1);
            }

            span.error-time {
                color: var(--primary-color);
                cursor: pointer;
                text-decoration: underline;
                text-underline-offset: 4px;
            }

            hr {
                display: none;
            }
        }

        .video-container {
            width: 100%;
            margin-inline: auto;
            display: flex;
            justify-content: center;
            align-items: center;
            border-radius: 16px;
            overflow: hidden;
            border: 2px solid rgba(255,255,255,0.1);
        }
    }

    .error-color {
        color: #ef4444; /* red-500 */
    }

    .info-color {
        color: var(--primary-color);
    }
}
</style>
