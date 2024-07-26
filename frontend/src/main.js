import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import VNetworkGraph from "v-network-graph"
import '@mdi/font/css/materialdesignicons.min.css';

const vuetify = createVuetify({
    components,
    directives,
  })

const app = createApp(App)


app.use(createPinia())
app.use(VNetworkGraph)

// app.mount('#app')
app.use(vuetify).mount('#app')
