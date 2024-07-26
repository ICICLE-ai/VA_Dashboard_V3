<script setup>
import { NodeResizer } from '@vue-flow/node-resizer'
import { Handle, Position } from '@vue-flow/core'
import {initialize} from '../../js/initialize.js'
const {cardWidth, cardHeight, resizeEndFunc} = initialize(400, 300)
import {TabulatorFull as Tabulator} from 'tabulator-tables'; //import Tabulator library
import {ref, reactive, onMounted, watch} from 'vue'



import { Chart } from "highcharts-vue";
import Highcharts from "highcharts";
// import Sankey from "highcharts/modules/sankey";
import exporting from 'highcharts/modules/exporting';
import exportData from 'highcharts/modules/export-data'
import accessibility from 'highcharts/modules/accessibility'
import networkgraph from 'highcharts/modules/networkgraph'
import exportInit from 'highcharts/modules/exporting'
import  "tabulator-tables/dist/css/tabulator_modern.min.css"
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

exportInit(Highcharts);
exporting(Highcharts);
exportData(Highcharts);
accessibility(Highcharts);
networkgraph(Highcharts);


const chartOptionsNetwork = {
  chart: {
        type: 'networkgraph',
        height: '100%'
    },
    // title: {
    //     text: 'The Indo-European Language Tree',
    //     align: 'left'
    // },
    // subtitle: {
    //     text: 'A Force-Directed Network Graph in Highcharts',
    //     align: 'left'
    // },
    plotOptions: {
        networkgraph: {
            keys: ['from', 'to', 'link'],
            layoutAlgorithm: {
                enableSimulation: true,
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
            linkFormat: '{point.link}',
            style: {
                fontSize: '0.8em',
                fontWeight: 'normal'
            }
        },
        id: 'lang-tree',
        data: [[
          'a','b','c'
        ]]
    }]
}

const tab = ref('one')

// const table = ref(null); //reference to your table element
// const tabulator = ref(null); //variable to hold your table
const tableData = ref([]); //data for table to display
const tableCol = ref([])
watch(() => props.data.input, (newInput, oldInput) => { 
   /* ... */ 
  alert('rew')
  console.log(newInput)
  if(newInput.length>0){
    const keys = Object.keys(newInput[0])
    keys.forEach(k=>{
      tableCol.value.push({
        title: k,
        field: k,
      })
    })
  }
  tableData.value = newInput
  new Tabulator('#table', {
      data: tableData.value,
      reactiveData:true, //enable data reactivity
      columns: tableCol.value, //define table columns
      resizableColumnFit: true, //
      movableRows: true, // 行のドラッグ&ドロップを可能にする
      movableColumns: true, 
      layout:"fitColumns",
      pagination:"local",
      paginationSize:6,
      paginationSizeSelector:[3, 6, 8, 10],
      paginationCounter:"rows",
  });
})


</script>

<template>
    <div>
      <NodeResizer @resize="resizeEndFunc" min-width="100" min-height="30"  color="white"/>
      <Toolbar :data="data" :id="id" :type="type"></Toolbar>
      <Handle type="target" :position="Position.Left" />
      <Handle type="source" :position="Position.Right" />
      <v-card
      :width=cardWidth
      :height=cardHeight
      variant = "outlined"
      :title=type>
      <div>
        <v-tabs
        v-model="tab"
        color="rgb(98,0,234)"
        align-tabs="center">
        <v-tab value="one">Tables</v-tab>
        <v-tab value="two">Network</v-tab>
        </v-tabs>
        <v-card-text>
          <v-window v-model="tab">
            <v-window-item value="one">
              <div id="table"></div>
            </v-window-item>
            <v-window-item value="two">
              <chart :options="chartOptionsNetwork"></chart>
            </v-window-item>
          </v-window>
        </v-card-text>
        
      </div>
      </v-card>
      
    </div>
</template>
<style>

</style>