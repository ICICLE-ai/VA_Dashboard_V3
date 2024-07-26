<script setup>
import { NodeResizer } from '@vue-flow/node-resizer'
import { Handle, Position} from '@vue-flow/core'
import {initialize} from '../../js/initialize.js'
import { excelParser } from "../../js/excel-parser.js";
import { VDataTable } from 'vuetify/labs/components'
import Highcharts from 'highcharts'
import { Chart } from "highcharts-vue";
import exportInit from 'highcharts/modules/exporting'
// import organization from 'highcharts/modules/organization'
import networkgraph from 'highcharts/modules/networkgraph'
import wordcloud from 'highcharts/modules/wordcloud'
import { ref,reactive, onMounted, defineComponent} from 'vue';

exportInit(Highcharts);
networkgraph(Highcharts);
wordcloud(Highcharts);
// organization(Highcharts);


import Toolbar from './Toolbar.vue'
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

const chartOptionsNetwork = reactive({
    credits: false, // removes watermark,
    credits: false, // removes watermark,
    chart: {
      type: 'networkgraph',
      height: props.data['height'],
      width: props.data['width']
    },
    title: {
      text: props.data['input']['title']
    },
    // subtitle: {
    //   text: 'A Force-Directed Network Graph in Highcharts'
    // },
    plotOptions: {
      networkgraph: {
        keys: ['from', 'to'],
        layoutAlgorithm: {
          enableSimulation: false,
          friction: -0.9
        }
      }
    },
    series: [{
      accessibility: {
        enabled: false
      },

      dataLabels: {
        enabled: true,
        linkFormat: '',
        style: {
              fontWeight: 'bold',
              fontSize: '14px',
              color: 'black'
            }
      },
      id: 'lang-tree',
      data: props.data['input']['edges'],
      nodes: props.data['input']['nodes']
  }]
});

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
        <Chart :options = "chartOptionsNetwork"></Chart>
      </div>
      </v-card>
      
    </div>
</template>
<style>

</style>