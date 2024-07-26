<script setup lang="ts">
import { NodeToolbar } from '@vue-flow/node-toolbar'
import {Position,applyNodeChanges,useVueFlow} from '@vue-flow/core'
import {ref, reactive} from 'vue'
import type { NodeRemoveChange, GraphNode,ElementData,CustomEvent, Node} from "@vue-flow/core";
const {onPaneReady, getNodes, removeNodes, findNode}  = useVueFlow({})
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

function deleteModule(){
    removeNodes([props.id], false)
}

</script>

<template>
    <NodeToolbar
        style="display: flex; gap: 0.5rem; align-items: center"
        :is-visible="undefined"
        :position="Position.Top"
      >
        <v-btn size="x-small" variant="outlined" @click="deleteModule()">Delete</v-btn>
        <!-- <v-btn size="x-small" variant="outlined" @click="miniModule()">Minimize</v-btn>
        <v-btn size="x-small" variant="outlined">Maximize</v-btn> -->
    </NodeToolbar>
</template>