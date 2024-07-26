<script setup lang="ts">
import { NodeResizer } from '@vue-flow/node-resizer'
import { Handle, Position,useVueFlow,useNode} from '@vue-flow/core'
import {initialize} from '../../js/initialize.js'
const {cardWidth, cardHeight, resizeEndFunc} = initialize(700, 300)
import Toolbar from './Toolbar.vue'
import {ref, reactive, toRaw} from 'vue'
import {neoInit, neoQuery} from '../../js/neo4j.js'
import {query_ontology_rel, query_ontology_node, filter_by_edge, filter_by_node, search_by_keyword} from '../../js/cypher.js'
import { Chart } from "highcharts-vue";
import Highcharts from "highcharts";
// import Sankey from "highcharts/modules/sankey";
import exporting from 'highcharts/modules/exporting';
import exportData from 'highcharts/modules/export-data'
import accessibility from 'highcharts/modules/accessibility'
import networkgraph from 'highcharts/modules/networkgraph'
import exportInit from 'highcharts/modules/exporting'
const { findNode} = useVueFlow()


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

const tab = ref(null)
const session = neoInit()
const relation_obj_list = ref([] as any) // {source, target, label}
const relation_types = ref([] as any)
const entity_types = ref([] as any)
const entity_obj_list = ref([] as any) // entity, properties
const loading_window_one = ref(false) //


getOnt()
async function getOnt(){
  loading_window_one.value=true
  const retrieved_rels = await neoQuery(session, query_ontology_rel)
  relation_obj_list.value = []// array of triplets 
  retrieved_rels['records'].forEach(item => {
    const temp = {}
    temp['source'] =item['_fields'][item['_fieldLookup']['source']]
    temp['target'] = item['_fields'][item['_fieldLookup']['target']]
    temp['label'] = item['_fields'][item['_fieldLookup']['label']]
    relation_obj_list.value.push(temp)
    relation_types.value.push(item['_fields'][item['_fieldLookup']['label']])
  });
  
  const retrieved_nodes = await neoQuery(session, query_ontology_node)
  retrieved_nodes['records'].forEach(item=>{
    var temp = {}
    temp['entity'] = item['_fields'][item['_fieldLookup']['entity']]
    temp['properties'] = item['_fields'][item['_fieldLookup']['properties']]
    entity_obj_list.value.push(temp)

    if(entity_types.value.includes(item['_fields'][item['_fieldLookup']['entity']])==false){
      entity_types.value.push(item['_fields'][item['_fieldLookup']['entity']])
    }
  })
  loading_window_one.value=false
}

// searching function from tab 2 
const keyword = ref('')
const btn_loading_search = ref(false)
const retrieved_data_num = ref('0')
const retrieved_data_status = ref('error')

function updateOutput(data){
  // props.data['output'] = data
  const output: object[] = [];
  data.slice(0,3).forEach(item=>{
    const keys = item['keys']
    const keys_index = item['_fieldLookup']
    const temp = {}
    keys.forEach(k=>{
      const value = item['_fields'][keys_index[k]]
      console.log(typeof(value))
      if(typeof(value)=="object"){
        temp[k] = JSON.stringify(value)
      }else{
        temp[k] = value
      }
    })
    output.push(temp)
  })
  console.log(output)
  props.data['output'] = output
  console.log(useNode(props.id))
}
async function search(){
  btn_loading_search.value = true 
  const result = await neoQuery(session, search_by_keyword(keyword))
  // retrieved_data_num = result['']
  retrieved_data_num.value = result['records'].length.toString()
  retrieved_data_status.value = 'success'
  btn_loading_search.value = false 
  updateOutput(result['records'])
}

async function retrieveByNode(chip, type){
  const result = ref({})
  if(type=='node'){
    result.value = await neoQuery(session, filter_by_node(chip))
  }else{
    result.value = await neoQuery(session, filter_by_edge(chip))
  }
  retrieved_data_status.value='success'
  retrieved_data_num.value = result.value['records'].length.toString()
  updateOutput(result.value['records'])
}
</script>

<template>
    <div>
      <NodeResizer @resize="resizeEndFunc" min-width="100" min-height="30" color="white"/>
      <Toolbar :data="data" :id="id" :type="type"></Toolbar>
      <!-- <Toolbar :data="data" :id="id" :type="type" @remove-node-event="afterDelete"></Toolbar> -->
      <Handle type="target" :position="Position.Left" />
      <Handle type="source" :position="Position.Right" />
      <v-card
      :width=cardWidth
      :height=cardHeight
      variant = "outlined">
        <v-card-text>
        <div style="font-weight: bold; font-family: 'Gill Sans', 'Gill Sans MT', Calibri, 'Trebuchet MS', sans-serif;">
          {{data.nodeTitle}}
        </div>
        <!-- <p>adjective</p> -->
        <div class="text--primary" style="font-style:italic;">
          Data retrieving status from knowledge graph:
          <v-badge :content="retrieved_data_num" :color="retrieved_data_status" inline>
          </v-badge>
        </div>
       </v-card-text>
      <v-divider></v-divider>
        <v-tabs
          v-model="tab"
          color="rgb(98, 0, 234)"
          align-tabs="center"
        >
          <v-tab value="one">Filter-by-Ontology</v-tab>
          <v-tab value="two">Search-by-Semantics</v-tab>
          <v-tab value="three">Query-by-Cypher</v-tab>
        </v-tabs>
        <v-card-text :height="cardHeight">
          <v-window v-model="tab">
            <v-window-item value="one" :loading="loading_window_one">
              <!-- <v-btn @click="getOnt">Retrieve Ontology</v-btn> -->
              <!-- <chart :options="chartOptionsNetwork"></chart> -->
              <!-- {{toRaw(networkData.value)}} -->
              <div class="text-overline mb-1">
                Entity Types:
              </div>
                <v-chip
                  v-for="chip in entity_types"
                  :key="chip"
                  size="x-small"
                  color="indigo"
                  @click="retrieveByNode(chip, 'node')"
                  text-color="white"
                >
                {{chip}}
                </v-chip>
              <div class="text-overline mb-1">
                Relation Types:
              </div>
              <v-chip
                  v-for="chip in relation_types"
                  :key="chip"
                  size="x-small"
                  @click="retrieveByNode(chip, 'relationship')"
                  color="indigo"
                  text-color="white"
                >
                {{chip}}
              </v-chip>
            </v-window-item>

            <v-window-item value="two">
              <v-text-field
              v-model="keyword"
              label="Input your keyword"
              required
              ></v-text-field>
              <v-btn @click="search" :loading="btn_loading_search">Search</v-btn>
            </v-window-item>

            <v-window-item value="three">
              {{data}}
            </v-window-item>
          </v-window>
        </v-card-text>
      </v-card>
      
    </div>
</template>
<style>

</style>