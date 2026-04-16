<script setup></script>

<template>
    <div class="container">
        <RouterLink :to="{ name: 'RealTime' }" class="box">
            <i class="fa-solid fa-video"></i>
            <p class="box__description">Real Time</p>
        </RouterLink>

        <RouterLink :to="{ name: 'VideoStreaming' }" class="box">
            <i class="fa-solid fa-upload"></i>
            <p class="box__description">Video Upload</p>
        </RouterLink>
    </div>
</template>

<style lang="scss" scoped>
.container {
    margin-top: 8rem;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4rem;
    flex-wrap: wrap;

    .box {
        width: 100%;
        max-width: 260px;
        aspect-ratio: 1 / 1;
        display: flex;
        justify-content: center;
        align-items: center;
        flex-direction: column;
        gap: 1.5rem;
        cursor: pointer;
        
        background: var(--surface-light);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: var(--border-subtle);
        border-radius: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        transition: all 0.4s cubic-bezier(0.2, 0.8, 0.2, 1);

        i {
            font-size: 4.5rem;
            color: var(--primary-color);
            transition: all 0.4s ease;
            filter: drop-shadow(0 0 15px rgba(16, 185, 129, 0.2));
        }

        &__description {
            font-size: 1.25rem;
            font-family: var(--font-heading);
            font-weight: 700;
            text-transform: uppercase;
            color: var(--text-main);
            letter-spacing: 1.5px;
            transition: color 0.3s ease;
        }

        &:hover {
            transform: translateY(-12px);
            border-color: var(--primary-color);
            background: var(--surface-solid);
            box-shadow: 0 20px 40px rgba(0,0,0,0.5), var(--shadow-glow);

            i {
                transform: scale(1.1);
                color: var(--text-main);
                filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.4));
            }
            
            &__description {
                color: var(--primary-color);
            }
        }
    }
}
</style>
