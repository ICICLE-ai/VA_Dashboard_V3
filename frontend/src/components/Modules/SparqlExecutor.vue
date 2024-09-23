<script setup>
import { NodeResizer } from '@vue-flow/node-resizer'
import { Handle, Position} from '@vue-flow/core'
import {initialize} from '../../js/initialize.js'
import { excelParser } from "../../js/excel-parser.js";
import { VDataTable } from 'vuetify/labs/components'
import axios from 'axios';

import Toolbar from './Toolbar.vue'
import {ref} from 'vue'
const props = defineProps({
  data: {
    type:Object,
    required: true
  },
  id: {
    type:String, 
    required: true
  },
  type: {
    type: String, 
    required: true
  }
})
const {cardWidth, cardHeight, resizeEndFunc} = initialize(props.data['width'], props.data['height'])
const endpoint = ref('http://dbpedia.org/sparql')
const loading_sparql_query_result = ref(false);
const sparql_query = () => {
    // console.log(endpoint, props.data.input)
    const passed_data = {
        'endpoint': endpoint.value, 
        'sparql': props.data.input
    }
    console.log('dddd', passed_data)
    loading_sparql_query_result.value = true
    axios.post('http://127.0.0.1:8000/api/sparql_execute/', passed_data)
      .then(response => {
        console.log(response)
        loading_sparql_query_result.value = false
        props.data.output = response.data
      })
}
</script>

<template>
    <div>
      <NodeResizer @resize="resizeEndFunc" min-width="100" min-height="30"  color="white"/>
      <Toolbar :data="data" :id="id" :type="type"></Toolbar>
      <!-- <tool-bar ></tool-bar> -->
      <Handle type="target" :position="Position.Left" />
      <Handle type="source" :position="Position.Right" />
      <v-card
      class="node-card"
      :width=cardWidth
      :height=cardHeight
      variant = "outlined"
      :title=type
      :style="{ backgroundColor: data.style['background'],
          borderColor: data.style['background'],
          borderRadius: data.style['borderRadius'], // Assuming the value is in pixels
          color: data.style['textColor']}">
      <div>
        <v-text-field
        v-model="endpoint"
        label="KG Endpoint"
        required
        ></v-text-field>
        <v-btn
        @click="sparql_query()">Query
            <v-progress-circular v-if="loading_sparql_query_result" :model-value="progress" :rotate="360" :size="30" :width="5" color="teal">
            </v-progress-circular>
        </v-btn>
      </div>
      </v-card>
      
    </div>
</template>
<style>

</style>