<script setup>
import { NodeResizer } from '@vue-flow/node-resizer'
import { Handle, Position } from '@vue-flow/core'
import { initialize } from '../../js/initialize.js'
import Toolbar from './Toolbar.vue'
import { ref, onMounted, defineEmits } from 'vue'
import axios from 'axios'
import { client } from '../../stores/client.js'

const props = defineProps({
  data: {
    type: Object,
    required: true
  },
  id: {
    type: String,
    required: true
  },
  type: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['update-query'])

const { cardWidth, cardHeight, resizeEndFunc } = initialize(props.data['width'], props.data['height'])

const question = ref('Enter your question here...')
const openai_api = ref('')
const loading_text2query = ref(false)

const text2query = () => {
  const queryText = question.value
  if (queryText && openai_api.value) {
    const passed_data = { question: queryText, openai_api: openai_api.value }
    
    loading_text2query.value = true
    client.post('/api/text2query/', passed_data)
      .then(response => {
        if (response.data.result && response.data.result.length > 0) {
          const query = response.data.result[0].sparql
          console.log("Generated SPARQL query:", query)
          props.data.output = query  // Update props.data.output with the generated query
          emit('update-query', query)  // Emit the updated query if needed
        } else {
          console.log("No query generated from the response")
        }
        loading_text2query.value = false
      })
      .catch(error => {
        console.error('Error in text2query:', error)
        loading_text2query.value = false
      })
  } else {
    alert('Please provide both OpenAI API and a question!')
  }
}

onMounted(() => {
  if (typeof props.data.input === 'string') {
    question.value = props.data.input
  } else {
    question.value = 'Enter your question here...'
  }
})
</script>

<template>
  <div>
    <NodeResizer @resize="resizeEndFunc" min-width="100" min-height="30" color="white" />
    <Toolbar :data="data" :id="id" :type="type"></Toolbar>
    <Handle type="target" :position="Position.Left" />
    <Handle type="source" :position="Position.Right" />
    <v-card
      class="node-card"
      :width="cardWidth"
      :height="cardHeight"
      variant="outlined"
      :title="type"
      :style="{
        backgroundColor: data.style['background'],
        borderColor: data.style['background'],
        borderRadius: data.style['borderRadius'],
        color: data.style['textColor']
      }"
    >
      <div>
        <v-textarea
          v-model="question"
          :rows="5"
          auto-grow
          filled
          label="Enter question"
          class="mt-2"
        ></v-textarea>
        <v-form>
          <v-text-field
            v-model="openai_api"
            label="OpenAI API"
            required
          ></v-text-field>
        </v-form>
        <v-btn @click="text2query()">Question Generator
          <v-progress-circular v-if="loading_text2query" :model-value="loading_text2query" :rotate="360" :size="30" :width="5" color="teal">
          </v-progress-circular>
        </v-btn>
      </div>
    </v-card>
  </div>
</template>

<style scoped>
.node-card {
  overflow: hidden;
}
</style>
