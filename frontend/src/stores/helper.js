import { ref, computed ,nextTick, watch,reactive} from 'vue'
import { defineStore } from 'pinia'
import {useVueFlow} from "@vue-flow/core"
export const useCardManage = defineStore('cardManage', {
  state: () => ({
    nodes: [],
    id: 0,
    defaultCardStyle : {
      background: '#f0f0f0',
      // textColor: '#bdbdbd',
      textColor: 'black',
      borderColor: '#bdbdbd',
      borderRadius: '10px',
    }
  }),
  actions: {
    getId() {
      // const nextId = `node_${this.id++}`;
      return this.id;
    },
    addId() {
      this.id++;
    },
    setStyle(background, textColor, borderColor, borderRadius){
      return {
        "background": background,
        "textColor": textColor,
        'borderColor': borderColor,
        'borderRadius': borderRadius
      }
    },
    initialize(id, type, label, x,y,title, input,output, width, height, defaultStyle){
      const template = reactive({
          id: '123',
          type: 'ddddd',
          label: "label", 
          position: {
              x: 0,
              y: 0
          },
          data: {
              nodeTitle: "title",
              input: null,
              output: null,
              width: 350,
              height: 400,
              style: {}
          },
          
      })
      template['id'] = id 
      template['type'] = type 
      template['label'] = label
      template['position']['x'] = x
      template['position']['y'] = y 
      template['data']['nodeTitle'] = title 
      template['data']['input'] = input
      template['data']['output'] = output  
      template['data']['width'] = width 
      template['data']['height'] = height 
      template['data']['style'] = defaultStyle
      // template['draggable'] = false
      return template
    }
  },
})
