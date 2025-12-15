<!-- Main application layout component with navigation and theme switching. -->
<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { useThemeStore } from './stores/theme'

const themeStore = useThemeStore()
</script>

<template>
  <div class="society-panel-page">
    <div class="ak-backdrop ak-backdrop--one"></div>
    <div class="ak-backdrop ak-backdrop--two"></div>
    <div class="ak-backdrop ak-backdrop--grid"></div>

    <header class="ak-nav">
      <div class="ak-nav__brand">
        <img src="/logo.png" alt="Society Panel" class="ak-logo-icon" />
        <div class="ak-brand-copy">
          <span class="ak-brand-title">Society-Panel</span>
        </div>
      </div>
      <nav class="ak-nav__links">
        <RouterLink class="ak-link" to="/">Dashboard</RouterLink>
        <RouterLink class="ak-link" to="/files">File Management</RouterLink>
        <RouterLink class="ak-link" to="/configs">Configuration</RouterLink>
        <RouterLink class="ak-link" to="/editor">Node Editor</RouterLink>
      </nav>
      <div class="ak-nav__actions">
        <button
          type="button"
          class="theme-toggle"
          :class="{ 'theme-toggle--dark': themeStore.isDark }"
          @click="themeStore.toggleTheme"
          :title="themeStore.isDark ? 'Switch to light theme' : 'Switch to dark theme'"
        >
          <svg v-if="!themeStore.isDark" class="theme-toggle__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
          </svg>
          <svg v-else class="theme-toggle__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="5"></circle>
            <line x1="12" y1="1" x2="12" y2="3"></line>
            <line x1="12" y1="21" x2="12" y2="23"></line>
            <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
            <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
            <line x1="1" y1="12" x2="3" y2="12"></line>
            <line x1="21" y1="12" x2="23" y2="12"></line>
            <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
            <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
          </svg>
        </button>
      </div>
    </header>

    <main class="ak-main">
      <RouterView />
    </main>
  </div>
</template>

<style>
.society-panel-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: clamp(2rem, 6vw, 3rem) 0 clamp(3rem, 7vw, 5rem);
  color: var(--ak-text-primary);
  background: var(--ak-bg);
  transition: background 280ms ease, color 280ms ease;
  --ak-container-width: min(var(--content-width), calc(100% - 2rem));

  --ak-bg: var(--bg-gradient);
  --ak-surface: var(--card-bg);
  --ak-surface-strong: var(--bg-inset-lightest);
  --ak-surface-highlight: var(--nav-link-hover-bg);
  --ak-text-primary: var(--text-primary);
  --ak-text-secondary: var(--text-secondary);
  --ak-text-muted: var(--text-muted);
  --ak-border-soft: var(--border-soft);
  --ak-border-strong: color-mix(in srgb, var(--border-soft) 45%, var(--accent) 55%);
  --ak-shadow-soft: var(--accent-shadow);
}

[data-theme='dark'] .society-panel-page {
  --ak-bg: var(--bg-gradient);
  --ak-surface: var(--card-bg);
  --ak-surface-strong: var(--surface);
  --ak-surface-highlight: var(--accent-soft);
  --ak-text-primary: var(--text-primary);
  --ak-text-secondary: var(--text-secondary);
  --ak-text-muted: var(--text-muted);
  --ak-border-soft: var(--border-soft);
  --ak-border-strong: color-mix(in srgb, var(--accent) 60%, var(--border-soft) 40%);
  --ak-shadow-soft: rgba(0, 0, 0, 0.45);
}

.society-panel-page::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(circle at 12% 8%, color-mix(in srgb, var(--accent-soft) 70%, transparent), transparent 60%),
    radial-gradient(circle at 84% 14%, color-mix(in srgb, var(--accent) 22%, transparent), transparent 52%);
  opacity: 0.8;
  mix-blend-mode: screen;
}

[data-theme='dark'] .society-panel-page::before {
  background: radial-gradient(circle at 12% 8%, color-mix(in srgb, var(--accent) 18%, transparent), transparent 60%),
    radial-gradient(circle at 85% 12%, color-mix(in srgb, var(--accent-strong) 20%, transparent), transparent 55%);
  mix-blend-mode: screen;
  opacity: 0.55;
}

.ak-backdrop {
  position: absolute;
  border-radius: 999px;
  filter: blur(60px);
  opacity: 0.55;
  pointer-events: none;
  transition: opacity 280ms ease;
}

.ak-backdrop--one {
  top: -10rem;
  left: -6rem;
  width: 320px;
  height: 320px;
  background: color-mix(in srgb, var(--accent) 36%, transparent);
}

.ak-backdrop--two {
  bottom: -8rem;
  right: -4rem;
  width: 360px;
  height: 360px;
  background: color-mix(in srgb, var(--accent-strong) 32%, transparent);
}

.ak-backdrop--grid {
  top: 10%;
  bottom: 12%;
  left: 50%;
  width: var(--ak-container-width);
  transform: translateX(-50%);
  border-radius: 32px;
  background-image: linear-gradient(color-mix(in srgb, var(--accent) 12%, rgba(255, 255, 255, 0.85)) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--accent) 12%, rgba(255, 255, 255, 0.85)) 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.22;
  filter: blur(0);
}

[data-theme='dark'] .ak-backdrop--grid {
  opacity: 0.18;
  background-image: linear-gradient(color-mix(in srgb, var(--accent) 18%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--accent) 18%, transparent) 1px, transparent 1px);
}

.ak-nav,
.ak-main {
  width: var(--ak-container-width);
  margin: 0 auto;
}

.ak-nav {
  position: relative;
  z-index: 100;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: clamp(1rem, 4vw, 2.5rem);
  padding: 1rem clamp(1.25rem, 3vw, 2rem);
  border-radius: 24px;
  background: var(--ak-surface);
  border: 1px solid var(--ak-border-soft);
  box-shadow: 0 22px 40px var(--ak-shadow-soft);
  backdrop-filter: blur(16px);
}

.ak-nav__brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.ak-logo-icon {
  width: 2.75rem;
  height: 2.75rem;
  object-fit: contain;
}

.ak-brand-copy {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.ak-brand-title {
  font-size: 1.2rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--ak-text-primary);
}

.ak-nav__links {
  display: flex;
  align-items: center;
  gap: clamp(0.8rem, 2.6vw, 1.8rem);
}

.ak-link {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-secondary);
  padding: 0.5rem 0.85rem;
  border-radius: 999px;
  text-decoration: none;
  transition: background 200ms ease, color 200ms ease, transform 200ms ease;
}

.ak-link:hover,
.ak-link.router-link-active {
  color: var(--text-primary);
  background: var(--nav-link-hover-bg);
  transform: translateY(-2px);
}

.ak-nav__actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.theme-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  min-width: 40px;
  min-height: 40px;
  flex-shrink: 0;
  border: 1px solid var(--border-soft);
  border-radius: 50%;
  background: var(--bg-inset-light);
  color: var(--text-primary);
  cursor: pointer;
  transition: all 200ms ease;
  position: relative;
  overflow: hidden;
  padding: 0;
}

.theme-toggle:hover {
  transform: translateY(-1px);
  background: var(--accent-soft);
  box-shadow: 0 8px 20px var(--accent-shadow);
}

.theme-toggle__icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  stroke: var(--text-primary);
  transition: transform 300ms ease;
}

.theme-toggle--dark .theme-toggle__icon {
  transform: rotate(180deg);
}

.theme-toggle:active {
  transform: scale(0.95);
}

.ak-main {
  position: relative;
  z-index: 1;
  margin-top: clamp(2.3rem, 4.8vw, 3.3rem);
  padding: 0 0 48px;
}

h1 {
  font-size: 2.5rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin-top: 0;
  margin-bottom: 1rem;
  color: var(--accent);
}

h2 {
  font-size: 1.75rem;
  font-weight: 600;
  border-bottom: 1px solid var(--border-soft);
  padding-bottom: 0.75rem;
  margin-top: 3rem;
  margin-bottom: 1.5rem;
  color: var(--text-primary);
}

h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 2rem;
  margin-bottom: 1rem;
  color: var(--text-secondary);
}

h4 {
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: var(--text-secondary);
}

p {
  color: var(--text-secondary);
  line-height: 1.7;
  font-size: 1rem;
  max-width: 75ch;
}

code {
  background-color: var(--chip-bg);
  padding: 0.2em 0.4em;
  border-radius: var(--border-radius-sm);
  font-family: var(--font-family-mono);
  font-size: 0.9em;
  border: 1px solid var(--border-soft);
  color: var(--accent-strong);
}

[data-theme="dark"] code {
  color: var(--accent);
}

.panel-container {
  border: 1px solid var(--border-soft);
  padding: 28px;
  border-radius: var(--border-radius-lg);
  background: var(--card-bg);
  backdrop-filter: blur(12px);
  box-shadow: var(--shadow-md);
  transition: var(--transition-fast);
}

.panel-container:hover {
  border-color: var(--accent);
  box-shadow: var(--shadow-glow);
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--surface-muted);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: var(--accent-soft);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--accent);
}

[data-theme="dark"]::-webkit-scrollbar-thumb {
  background: var(--surface-muted);
}

[data-theme="dark"]::-webkit-scrollbar-thumb:hover {
  background: var(--accent);
}

@media (max-width: 960px) {
  .ak-nav {
    grid-template-columns: 1fr;
    justify-items: stretch;
    text-align: center;
  }

  .ak-nav__brand {
    justify-content: center;
  }

  .ak-nav__links {
    justify-content: center;
  }

  .ak-nav__actions {
    justify-content: center;
  }
}

@media (max-width: 640px) {
  .society-panel-page {
    padding: 1.5rem 1rem;
  }
}
</style>
