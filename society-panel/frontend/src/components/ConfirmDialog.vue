<!-- Reusable confirmation dialog component with promise-based API. -->
<script setup>
import { ref } from 'vue';

const isVisible = ref(false);
const title = ref('');
const message = ref('');
const confirmText = ref('Confirm');
const cancelText = ref('Cancel');
const isDanger = ref(false);

let resolvePromise = null;

const show = (options) => {
  title.value = options.title || 'Confirm';
  message.value = options.message || 'Are you sure?';
  confirmText.value = options.confirmText || 'Confirm';
  cancelText.value = options.cancelText || 'Cancel';
  isDanger.value = options.isDanger !== undefined ? options.isDanger : true;
  isVisible.value = true;

  return new Promise((resolve) => {
    resolvePromise = resolve;
  });
};

const handleConfirm = () => {
  isVisible.value = false;
  if (resolvePromise) {
    resolvePromise(true);
    resolvePromise = null;
  }
};

const handleCancel = () => {
  isVisible.value = false;
  if (resolvePromise) {
    resolvePromise(false);
    resolvePromise = null;
  }
};

defineExpose({ show });
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog-fade">
      <div v-if="isVisible" class="dialog-overlay" @click.self="handleCancel">
        <div class="dialog-container">
          <div class="dialog-header">
            <div class="dialog-icon" :class="{ 'danger': isDanger }">
              <svg v-if="isDanger" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 9v4M12 17h.01"/>
                <circle cx="12" cy="12" r="10"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 8v4M12 16h.01"/>
                <circle cx="12" cy="12" r="10"/>
              </svg>
            </div>
            <h3 class="dialog-title">{{ title }}</h3>
          </div>
          <p class="dialog-message">{{ message }}</p>
          <div class="dialog-actions">
            <button @click="handleCancel" class="btn-cancel">{{ cancelText }}</button>
            <button @click="handleConfirm" class="btn-confirm" :class="{ 'danger': isDanger }">{{ confirmText }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.dialog-container {
  background: var(--card-bg);
  border-radius: 16px;
  padding: 24px;
  min-width: 320px;
  max-width: 420px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-soft);
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.dialog-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--nav-link-hover-bg);
  color: var(--accent);
  flex-shrink: 0;
}

.dialog-icon.danger {
  background: var(--error-bg);
  color: var(--accent-strong);
}

[data-theme="dark"] .dialog-icon.danger {
  color: #f85149;
}

.dialog-icon svg {
  width: 22px;
  height: 22px;
}

.dialog-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-primary);
}

.dialog-message {
  margin: 0 0 24px 0;
  color: var(--text-secondary);
  font-size: 0.95rem;
  line-height: 1.6;
  padding-left: 52px;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn-cancel,
.btn-confirm {
  padding: 10px 20px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 200ms ease;
  min-width: 90px;
}

.btn-cancel {
  background: var(--surface);
  color: var(--text-secondary);
  border: 1px solid var(--border-soft);
}

.btn-cancel:hover {
  background: var(--bg-inset-soft);
  color: var(--text-primary);
  border-color: var(--text-muted);
}

.btn-confirm {
  background: var(--accent);
  color: #FDF8E8;
  border: none;
}

.btn-confirm.danger {
  background: var(--accent-strong);
}

[data-theme="dark"] .btn-confirm {
  color: #0a0f1e;
}

[data-theme="dark"] .btn-confirm.danger {
  background: #f85149;
}

.btn-confirm:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px var(--accent-shadow);
}

.btn-confirm.danger:hover {
  box-shadow: 0 4px 12px rgba(200, 80, 50, 0.4);
}

.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: all 200ms ease;
}

.dialog-fade-enter-active .dialog-container,
.dialog-fade-leave-active .dialog-container {
  transition: all 200ms ease;
}

.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}

.dialog-fade-enter-from .dialog-container,
.dialog-fade-leave-to .dialog-container {
  transform: scale(0.95) translateY(-10px);
  opacity: 0;
}
</style>
