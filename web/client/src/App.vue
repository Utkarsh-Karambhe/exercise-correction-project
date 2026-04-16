<script setup></script>

<template>
    <div class="site-container">
        <nav>
            <RouterLink 
                :to="{ name: 'Home' }" 
                class="nav__header"
                aria-label="Go to homepage"
            >
                Exercise Correction
            </RouterLink>
        </nav>

        <main>
            <RouterView />
        </main>

        <footer>
            <a href="#">© 2026 Exercise Correction</a>
        </footer>
    </div>
</template>

<style lang="scss">
.site-container {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    background: radial-gradient(circle at top, #1e293b 0%, #0f172a 100%);
}

nav {
    margin: 4rem 0 3rem;
    text-align: center;

    .nav__header {
        font-size: 2.5rem;
        font-family: var(--font-heading);
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: transparent;
        background: linear-gradient(90deg, var(--primary-color), var(--primary-hover));
        -webkit-background-clip: text;
        background-clip: text;
        transition: 0.3s ease;
        filter: drop-shadow(var(--shadow-glow));

        &:hover {
            opacity: 0.9;
            letter-spacing: 4px;
        }
    }
}

main {
    margin-inline: auto;
    width: 90vw;
    max-width: 1200px;
    flex-grow: 1;
}

footer {
    margin-top: auto;
    width: 100%;
    padding: 2rem 0;
    text-align: center;
    border-top: var(--border-subtle);
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(10px);

    a {
        font-family: var(--font-body);
        color: var(--text-muted);
        font-size: 0.9rem;
        font-weight: 500;
        letter-spacing: 1px;
        
        &:hover {
            color: var(--primary-color);
        }
    }
}
</style>