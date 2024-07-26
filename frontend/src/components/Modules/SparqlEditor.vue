<script setup>
import { NodeResizer } from '@vue-flow/node-resizer'
import { Handle, Position} from '@vue-flow/core'
import {initialize} from '../../js/initialize.js'
import { excelParser } from "../../js/excel-parser.js";
import { VDataTable } from 'vuetify/labs/components'
import { PrismEditor } from 'vue-prism-editor';
import 'vue-prism-editor/dist/prismeditor.min.css'; // import the styles somewhere
// import highlighting library (you can use any library you want just return html string)
import { highlight, languages } from 'prismjs/components/prism-core';
import 'prismjs/components/prism-clike';
import 'prismjs/components/prism-markup';
import 'prismjs/components/prism-javascript';
import "prismjs/themes/prism-tomorrow.css";

// Polyfill for the global object
if (typeof global === 'undefined') {
  window.global = window;
}
import Toolbar from './Toolbar.vue'
import {ref, watch,onMounted} from 'vue'
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

const highlighter = (code) =>{
        return highlight(
        code,
        {
          ...languages['markup'],
          ...languages['js'],
          ...languages['css'],
        },
        'markup'
      )}

const code = ref('');
onMounted(() => {
  console.log(typeof(props.data.input))
  if (typeof(props.data.input)=='object') {
    console.log('ddd')
      code.value = ref(`
      select distinct ?Concept where {[] a ?Concept} LIMIT 100
        `)
    }else{
      code.value = ref(props.data.input)
    }
});
watch(code, (newCode) => {
  props['data']['output'] = newCode
  console.log(props.data)
}, {deep: true});

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
      :title=props.data.nodeTitle
      :style="{ backgroundColor: data.style['background'],
          borderColor: data.style['background'],
          borderRadius: data.style['borderRadius'], // Assuming the value is in pixels
          color: data.style['textColor']}">
      <div>
        <prism-editor
            class="my-editor"
            language="html"
            v-model="code"
            :highlight="highlighter"
            line-numbers
        ></prism-editor>
      </div>
      </v-card>
      
    </div>
</template>
<style>

</style>