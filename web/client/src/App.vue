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
}

nav {
    margin: 3rem 0;
    text-align: center;

    .nav__header {
        font-size: 2rem;
        font-family: var(--font-family);
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--primary-color);
        transition: 0.3s ease;

        &:hover {
            opacity: 0.7;
        }
    }
}

main {
    margin-inline: auto;
    width: 90vw;
    max-width: 1200px;
}

footer {
    margin-top: auto;
    margin-inline: auto;
    width: 90vw;
    max-width: 1200px;
    border-top: 1px solid var(--primary-color);
    padding: 0.3rem 0;
    text-align: center;

    a {
        font-family: var(--font-family);
        color: var(--primary-color);
    }
}
</style>