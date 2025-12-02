// Application entry point that initializes Vue app with Pinia and Vue Router.

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

import './styles/variables.css'
import './styles/config-editor.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
