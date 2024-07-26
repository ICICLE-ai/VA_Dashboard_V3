<script setup>
import { NodeResizer } from '@vue-flow/node-resizer'
import { Handle, Position} from '@vue-flow/core'
import {initialize} from '../../js/initialize.js'
import { excelParser } from "../../js/excel-parser.js";
import { VDataTable } from 'vuetify/labs/components'
// import {VegaLite} from 'vue-vega'
import vegaEmbed from 'vega-embed'
import Toolbar from './Toolbar.vue'
import {ref, onMounted, watch, reactive, toRaw} from 'vue'
import axios from 'axios';

// import Vue from 'vue'
import * as d3 from 'd3';
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

const vegaLite = ref()
// onMounted(() => {
  
    // const spec = {
    // "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    // "description": "A simple bar chart with embedded data.",
    // "data": {
    //     "values": [
    //         {"a": "A", "b": 28}, {"a": "B", "b": 55}, {"a": "C", "b": 43},
    //         {"a": "D", "b": 91}, {"a": "E", "b": 81}, {"a": "F", "b": 53},
    //         {"a": "G", "b": 19}, {"a": "H", "b": 87}, {"a": "I", "b": 52}
    //     ]
    // },
    // "mark": "bar",
    // "encoding": {
    //     "x": {"field": "a", "type": "nominal", "axis": {"labelAngle": 0}},
    //     "y": {"field": "b", "type": "quantitative"}
    // }
    // }
    // vegaEmbed("#vega_div", spec)
  
// })
const replace = (data, column_name)=>{
  if(column_name in data['data']['values'][0]){
        // we need to replace the date with Date type
        var temp = {
          'color': data['color'],
          'mark': data['mark'],
          'encoding': data['encoding'],
          'data': {
            'values': []
          }
        }
        for(let i=0; i<data['data']['values'].length; i++){
          let current_ = data['data']['values'][i]
          // current_['year'] = new Date(current_['year'])
          current_[column_name]  = new Date(current_[column_name])
          temp['data']['values'].push(current_)
        }
        return temp 

      }else{
        return data 
      }
}
watch(()=> props['data']['input'], (newData)=>{
  // alert('data updated!')
  // console.log(props['data']['input'], props.data, 'test')
  axios.post('http://127.0.0.1:8000/api/generate_vega/', {'data': newData})
  .then(response=>{
    console.log(response)
    const cleaned_data = []
    var response = response.data
    for(let j=0; j<response.data.length; j++){
        var one_data = response.data[j]
        for(let i=0; i<response.info['date_column'].length; i++){
          var date_column_name = response.info['date_column'][i]
            one_data = replace(one_data, date_column_name)
        }
        one_data['ID'] = "chart"+ props.id.toString()+j.toString()
        cleaned_data.push(one_data)
    }
    
    vegaLite.value = cleaned_data
    console.log(cleaned_data, vegaLite.value)
    for(let j=0; j<vegaLite.value.length;j++){
      console.log('rendering...',toRaw(vegaLite.value[j]))
      vegaEmbed("#"+'chart'+props.id.toString()+j.toString(), toRaw(vegaLite.value[j]))
    }
  })

}, {deep: true})
</script>

<template>
    <div>
      <NodeResizer @resize="resizeEndFunc" min-width="100" min-height="30"  color="white"/>
      <Toolbar :data="data" :id="id" :type="type"></Toolbar>
      <!-- <tool-bar ></tool-bar> -->
      <Handle type="target" :position="Position.Left" />
      <Handle type="source" :position="Position.Right" />
      <v-card
      :width=cardWidth
      :height=cardHeight
      variant = "outlined"
      :title="type"
      :style="{ backgroundColor: data.style['background'],
          borderColor: data.style['background'],
          borderRadius: data.style['borderRadius'], // Assuming the value is in pixels
          color: data.style['textColor']}"
      >
      <!-- <div id="vega"></div> -->
      <!-- <div id="vega_div"></div> -->
      <div v-for="(item, index) in vegaLite" :key="index">
          <div v-bind:id=item.ID></div>
        <!-- <vega-lite :data="item.data.values" :mark="item.mark" :encoding="item.encoding" :color="item.color" :shape="item.shape"/> -->
      </div>
     <!-- <vega-lite :data="spec.data" :mark="spec.mark" :encoding="spec.encoding" :color="spec.color" :shape="spec.shape"></vega-lite> -->
    </v-card>  
    </div>
</template>
<style>

</style>