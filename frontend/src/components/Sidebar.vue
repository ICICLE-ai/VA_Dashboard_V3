<script setup>

// Add Table Viewer on clicking the button function
import { Panel, useVueFlow } from '@vue-flow/core'
import { ref,reactive, onMounted} from 'vue';
import axios from 'axios';
const { nodes, edges, addNodes, addEdges, dimensions,onPaneReady } = useVueFlow();
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome';
import { faTable, faComment, faChartArea, faDiagramProject, faCircleDot, faPenToSquare} from '@fortawesome/free-solid-svg-icons';
import { library } from '@fortawesome/fontawesome-svg-core';
library.add(faTable, faComment, faChartArea, faDiagramProject, faCircleDot, faPenToSquare);
import {useCardManage} from '@/stores/helper.js'
import { storeToRefs } from 'pinia'
import * as d3 from 'd3';
import { client } from '../stores/client.js'

function onDragStart(event, nodeInfo) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vueflow', JSON.stringify(nodeInfo))
    event.dataTransfer.effectAllowed = 'move'
  }
}
const cardManage = useCardManage()
const cardManageStore = storeToRefs(cardManage)

const ws = ref(null);
const loading = ref(false);
// const question = ref('What downstream infrastructures are connected to adjacent infrastructure in Drakes Estero?')
const question = ref('');
const asrAndWakeword = ref('')

const openai_api = ref('');
const receivedMessage = ref('');
const progress = ref(0);
const loading_text2query = ref(false);

const x_space = ref(320)
const y_space = ref(220)
const card_width = ref(200)
const card_height = ref(150)

const entity_retrieve_node_id = ref(0)
const current_x = ref(20)
const current_y = ref(20)


//Speech 2 text
  const wakeWord = ref('Testing');
  const audioFile = ref(null);
  const csrfToken = ref('{{ csrf_token }}'); 
  // const response = ref(null);
  const transcription = ref('');
  const relEntityCardId = reactive([]);

  
  // const submitForm = () => {
  //   axios.post('http://127.0.0.1:8000/api/page_method/', {})
  //   .then(response => {
  //       // console.log(response)
  //       // Extract the words from each object in the result array
  //     const words = response.data.result.map(obj => obj.word);

  //     // Join the words into a single string with space separator
  //     transcription.value = words.join(' ');
  //   })
  //   .catch(error => {
  //     console.error('Error processing audio:', error);
  //   });

  // };



  // const wakeWordDetection = () => {
  //   axios.post('http://127.0.0.1:8000/api/audio_main/', {})
  //   .then(response => {
  //       // console.log(response)
  //       // Extract the words from each object in the result array
  //     const words = response.data.result.map(obj => obj.word);

  //     // Join the words into a single string with space separator
  //     transcription.value = words.join(' ');
  //   })
  //   .catch(error => {
  //     console.error('Error processing audio:', error);
  //   });

  // };


//   const wakeWordDetection = () => {
//   axios.post('http://127.0.0.1:8000/api/audio_main/', {
//     kwd: wakeWord.value  // Send wakeWord value as kwd in the request body
//   }, {
//     headers: {
//       'X-CSRFToken': csrfToken
//     }
//   })
//   .then(response => {
//     // Extract the words from each object in the result array
//     const words = response.data.result.map(obj => obj.word);

//     // Join the words into a single string with space separator
//     transcription.value = words.join(' ');
//   })
//   .catch(error => {
//     console.error('Error processing audio:', error);
//   });
// };


const wakeWordDetection = () => {
 // axios.post('http://127.0.0.1:8000/api/wake_and_asr/', {
  axios.post('/api/wake_and_asr/', {
    kwd: wakeWord.value
  }, {
    headers: {
      'X-CSRFToken': csrfToken.value
    }
  })
  .then(response => {
    console.log('Response:', response);
    const words = Array.isArray(response.data.transcription) ? response.data.transcription.map(obj => obj.word) : [];
    console.log('Transcription Words:', words);
    transcription.value = words.join(' ');
    console.log('Transcription Display:', transcription.value);
    
    // Update asrAndWakeword with the transcription
    asrAndWakeword.value = transcription.value;
  })
  .catch(error => {
    console.error('Error processing audio:', error);
  });
};






const convertClass=(d)=>{
  let delimiter = d.includes('#') ? "#" : "/";
  let parts = d.split(delimiter);
  return parts[parts.length - 1]; // Directly return the last part
}

const connect = () => {
      // Assuming the Django development server is running on localhost:8000
      ws.value = new WebSocket(`${import.meta.env.VITE_APP_BACKEND_BASE_URL}/ws/query/`);

      ws.value.onopen = () => {
        console.log('WebSocket connection established');
      };

      ws.value.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // updating the progress bar 
        progress.value = data['progress']
        // 
        // console.log(data);
        // useCardManage
        if(data['type'] == "entityExtraction"){
          const node_id = cardManage.getId();
          current_x.value += x_space.value;
          
          const node = cardManage.initialize(node_id, 
            'textViewer', 
            'title:textViewer', 
            current_x.value, current_y.value, 
            "Entity Extraction", data['text'],data['text'], 
            card_width, card_height, 
            cardManage.setStyle('#1a9850', 'white','white', '10px')
            )
          const params = reactive({
            "source": (node_id-1).toString(),
            "sourceHandle": (node_id-1).toString()+"__handle-right",
            "target": node_id.toString(),
            "targetHandle": node_id.toString() +"__handle-left"
          });
          addNodes([node]);
          cardManage.addId();
          addEdges(params);
          // console.log(edges.value, nodes.value);
        }
      if(data['type']=="analyzeEntity"){
          const node_id = cardManage.getId();
          current_x.value += x_space.value; 
          const node = cardManage.initialize(node_id, 
            'textViewer', 
            'title:textViewer', 
            current_x.value, current_y.value, 
            "Entity Analysis", data['text'],data['text'], 
            card_width, card_height, 
            cardManage.setStyle('#1a9850', 'white','white', '10px')
            )
          const params = reactive({
            "source": (node_id-1).toString(),
            "sourceHandle": (node_id-1).toString()+"__handle-right",
            "target": node_id.toString(),
            "targetHandle": node_id.toString() +"__handle-left"
          });
          addNodes([node]);
          cardManage.addId();
          addEdges(params);
      }
      if(data['type']=="retrieveRelevant"){
        // console.log(data['data'])
        const previous_node = cardManage.getId()-1;
      
          for(let i=0; i<data['data'].length; i++){
            // filtering entities 
            if(data['data'][i]['type']=='filtering'){
              const node_id = cardManage.getId();
              entity_retrieve_node_id.value = node_id
              const show_text = "Retrieving relevant entities to: "+ data['data'][i]['entity']
              current_x.value += x_space.value;
              const node = cardManage.initialize(node_id, 
                'textViewer', 
                'title:textViewer', 
                current_x.value, current_y.value, 
                "Entity Retrieval", show_text,show_text, 
                card_width, card_height, 
                cardManage.setStyle('#1a9850', 'white','white', '10px')
                )
              const params = reactive({
                "source": previous_node.toString(),
                "sourceHandle": previous_node.toString()+"__handle-right",
                "target": node_id.toString(),
                "targetHandle": node_id.toString() +"__handle-left"
              });
              addNodes([node]);
              cardManage.addId();
              addEdges(params);
              current_x.value += x_space.value;
              for(let j=0; j<data['data'][i]['related'].length; j++){
                relEntityCardId.push(node_id);
                const sub_node_id = cardManage.getId();
                const show_text =  "label: "+data['data'][i]['related'][j]['text']+", type:" + convertClass(data['data'][i]['related'][j]['class'])
                current_y.value += y_space.value 
                const node = cardManage.initialize(sub_node_id, 
                  'textViewer', 
                  'title:textViewer', 
                  current_x.value, current_y.value, 
                  "Entity Retrieval",show_text, show_text, 
                  card_width, card_height, 
                  cardManage.setStyle( data['data'][i]['related'][j]['color'], 'white','white', '10px')
                  )
                const params = reactive({
                  "source": node_id.toString(),
                  "sourceHandle": node_id.toString()+"__handle-right",
                  "target": sub_node_id.toString(),
                  "targetHandle": sub_node_id.toString() +"__handle-left"
                });
                addNodes([node]);
                cardManage.addId();
                addEdges(params);
              }
          }
          
        }
      }
      if(data['type']=="drawScatter"){
        const node_id = cardManage.getId();
        // current_x.value += x_space.value; 
        current_y.value -= y_space.value*7.5;
        const node = cardManage.initialize(node_id, 
          'scatterplot', 
          'title:scatterplot', 
          current_x.value, current_y.value, 
          "Scatterplot", data['data'],data['data'], 
          card_width.value*3, card_height.value*3, 
          cardManage.setStyle('#f7f7f7', '#252525','#252525', '10px')
          )
        const params = reactive({
          "source": (entity_retrieve_node_id.value).toString(),
          "sourceHandle": (entity_retrieve_node_id.value).toString()+"__handle-right",
          "target": node_id.toString(),
          "targetHandle": node_id.toString() +"__handle-left"
        });
        addNodes([node]);
        cardManage.addId();
        addEdges(params);
      }
      if(data['type']=="drawNetwork"){
        console.log('dddd:',relEntityCardId);
        current_x.value += x_space.value;
        current_y.value += y_space.value/2;
         // Create a color scale using the Highcharts color palette
         const highchartsColors = [
            "#7cb5ec", "#434348", "#90ed7d", "#f7a35c", "#8085e9",
            "#f15c80", "#e4d354", "#2b908f", "#f45b5b", "#91e8e1"
        ];
         const colorScale = d3.scaleOrdinal()
            .domain(data['data']['unique_class'])
            .range(highchartsColors);
        data['data']['graph'].forEach(sourceEnt=>{
          const drawData = reactive({'edges': [], 'nodes': []})
          drawData['nodes'].push({
              'id': sourceEnt['source_label'],
              'name': sourceEnt['source_label'],
              'color': colorScale(sourceEnt['source_class']),
              'type': sourceEnt['source_class']
            })
          sourceEnt['target_nodes'].forEach(t=>{
            drawData['edges'].push([sourceEnt['source_label'], t['target_label']])
            drawData['nodes'].push({
              'id': t['target_label'],
              'name': t['target_label'],
              'color': colorScale(t['target_class']),
              'type': t['target_class']
            })
          })
          const node_id = cardManage.getId();
            current_y.value += y_space.value + card_height.value*1;
            drawData['title'] = "Related to entity: " + sourceEnt['source_label'];
            const node = cardManage.initialize(node_id, 
              'networkplot', 
              'title:drawNetwork', 
              current_x.value, current_y.value, 
              "Network", drawData, drawData, 
              card_width.value*3, card_height.value*2, 
              cardManage.setStyle('#1a9850', 'white','white', '10px')
              )
            addNodes([node]);
            cardManage.addId();
        })
        
        // const params = reactive({
        //   "source": previous_node.toString(),
        //   "sourceHandle": previous_node.toString()+"__handle-right",
        //   "target": node_id.toString(),
        //   "targetHandle": node_id.toString() +"__handle-left"
        // });
        
        // addEdges(params);
      }
      };

      ws.value.onclose = () => {
        console.error('Chat socket closed unexpectedly');
      };
};

// Function to send a message/question to the WebSocket server
const sendMessage = () => {
  const queryText = question.value || asrAndWakeword.value;
  if (queryText && openai_api.value) {
    loading.value = true;
    const passed_data = { "question": queryText, "openai_api": openai_api.value };
    ws.value.send(JSON.stringify(passed_data));

    // Add initial query node
    const newNode = cardManage.initialize(
      cardManage.getId(), 
      'textViewer', 
      'title:textViewer', 
      current_x.value, current_y.value,
      "User Query", queryText, queryText, 
      card_width, card_height, 
      cardManage.setStyle('#1a9850', 'white', 'white', '10px')
    )
    addNodes([newNode]);
    cardManage.addId();
  } else {
    alert('Please provide both OpenAI API and a question (either typed or spoken)!');
  }
};




const text2query = () => {
  const queryText = question.value || asrAndWakeword.value;
  if (queryText && openai_api.value) {
    const passed_data = { "question": queryText, "openai_api": openai_api.value };
    //A new node is created to display the user's query.
    const question_node_id = cardManage.getId()
    const newNode = cardManage.initialize(
      question_node_id, 
      'textViewer', 
      'title:textViewer', 
      current_x.value, current_y.value,
      "User Query", queryText, queryText, //This is for the 1st displayed node "User Query"
      card_width, card_height, 
      cardManage.setStyle('#66c2a5', 'black', 'black', '10px')
    );

    addNodes([newNode]);
    cardManage.addId();

    //Setting Up Color Mapping
    const colormapping = reactive({
      'score': "#fc8d62",
      's-expression': '#8da0cb',
      's-expression_repr': '#e78ac3',
      'sparql':'#a6d854',
      'results':'#ffd92f',
      'labels':'#e5c494',
      'kg_api_s_expr': '#699eb3',
      'kg_api_call': '#71b369'
    })

    loading_text2query.value = true;
    // axios.post('http://127.0.0.1:8000/api/text2query/', passed_data)
    client.post('/api/text2query/', passed_data)
      .then(response => {
        // console.log( response['data']['result'])

        // The response data is a list of results which is iterated over. For each result (ele), a temporary x-coordinate (temp_x) is calculated.
        for(let i = 0; i < response['data']['result'].length; i++) {
          const ele = response['data']['result'][i]
          const temp_x = ref(current_x.value + x_space.value)

          //creating Nodes for Each Key in the Response:
          Object.keys(ele).forEach(key => {
            if(key !== "input") {
              const node_id = cardManage.getId()
              const newNode = cardManage.initialize(
                node_id, 
                'textViewer', 
                'title:textViewer', 
                temp_x.value, current_y.value,
                key, ele[key], ele[key], 
                card_width, card_height, 
                cardManage.setStyle(colormapping[key], 'black', 'black', '10px')
              );
              addNodes([newNode]);
              cardManage.addId();

              //Creating Edges Between Nodes
              const params = reactive({});
              if(key === "s-expression") {
                params.source = question_node_id.toString();
                params.sourceHandle = question_node_id.toString() + "__handle-right";
                params.target = node_id.toString();
                params.targetHandle = node_id.toString() + "__handle-left";
              } else {
                params.source = (node_id - 1).toString();
                params.sourceHandle = (node_id - 1).toString() + "__handle-right";
                params.target = node_id.toString();
                params.targetHandle = node_id.toString() + "__handle-left";
              }
              temp_x.value += x_space.value; 
              addEdges(params);
            }
          })
          current_y.value += y_space.value;
        }
        loading_text2query.value = false;
      })
      .catch(error => { //Error Handling
        console.error('Error in text2query:', error);
        loading_text2query.value = false;
      });
  } else {
    alert('Please provide both OpenAI API and a question (either typed or spoken)!');
  }

}




onMounted(connect);
</script>

<template>
  <aside class="sidebar-container">
    <div class="scrollable-content">
    <div class="description">You can drag these nodes to the pane.</div>
    <div >
      <!-- https://fontawesome.com/icons/categories/design -->
      <v-row>
        <div class="drag-node" :draggable="true" @dragstart="onDragStart($event, {type:'tableViewer', title:'Table Viewer'})">
          <font-awesome-icon :icon="['fas','table']" class="drag-icon"/> Table Viewer
        </div>
      </v-row>
      <v-row>
        <div class="drag-node" :draggable="true" @dragstart="onDragStart($event, {type:'graphViewer', title:'Graph Viewer'})">
          <font-awesome-icon :icon="['fas','diagram-project']" class="drag-icon"/>Graph Viewer
        </div>
      </v-row>
      <v-row>
        <div class="drag-node" :draggable="true" @dragstart="onDragStart($event, {type:'sparqlEditor', title:'SPARQL Editor'})">
          <font-awesome-icon :icon="['fas','pen-to-square']" class="drag-icon"/>SPARQL Editor</div>
      </v-row>
      <v-row>
        <div class="drag-node" :draggable="true" @dragstart="onDragStart($event, {type:'sparqlExecutor', title:'SPARQL Executor'})">
          <font-awesome-icon :icon="['fas','pen-to-square']" class="drag-icon"/>SPARQL Executor</div>
      </v-row>
      <v-row>
        <div class="drag-node" :draggable="true" @dragstart="onDragStart($event, {type:'textArea', title:'Question Generator'})">
          <font-awesome-icon :icon="['fas','pen-to-square']" class="drag-icon"/>Question Generator</div>
      </v-row>

      <!-- <v-row>
        <div class="drag-node" :draggable="true" @dragstart="onDragStart($event, {type:'textViewer', title:'Text Viewer'})">
          <font-awesome-icon :icon="['fas','comment']" class="drag-icon"/>Text Viewer</div>
      </v-row>  -->
      <!-- <v-row>
        <div class="drag-node" :draggable="true" @dragstart="onDragStart($event, {type:'scatterplot', title:'Scatterplot'})">
          <font-awesome-icon :icon="['fas','circle-dot']" class="drag-icon"/>Scatterplot</div>
      </v-row>  -->
      <v-row>
        <div class="drag-node" :draggable="true" @dragstart="onDragStart($event, {type:'vegaLite', title:'VegaLite'})">
          <font-awesome-icon :icon="['fas','circle-dot']" class="drag-icon"/>VegaLite</div>
      </v-row> 
      <!-- <v-row>
        <div class="drag-node" :draggable="true" @dragstart="onDragStart($event, {type:'networkplot', title:'Networkplot'})">
          <font-awesome-icon :icon="['fas','circle-dot']" class="drag-icon"/>Networkplot</div>
      </v-row>  -->
      <v-row>
        <v-form ref="form">
          <v-text-field
            v-model="openai_api"
            label="OpenAI API"
            required
          ></v-text-field>

          <v-card class="mb-4">
            <v-card-title class="text-h5 font-weight-bold">
              Speech Recognition
            </v-card-title>
            <v-card-text>
              <v-text-field 
                v-model="wakeWord" 
                label="Wakeword"
                class="mb-4"
              ></v-text-field>
              
              <v-text-field
                v-model="asrAndWakeword"
                label="Detected Question"
                style="width: 100%;"
                required
              ></v-text-field>
            </v-card-text>
          </v-card>

          <!-- <v-btn @click="submitForm">Listen</v-btn> -->
          <v-btn @click="wakeWordDetection">Start Recording</v-btn>

          <!-- Text area to display the result -->
          <!-- <textarea v-model="transcription" rows="10" cols="50" placeholder="Transcription"></textarea> -->

          <v-card class="mb-4 mt-4">
            <v-card-title class="text-h5 font-weight-bold">
              Type your question here
            </v-card-title>
          
          <v-text-field
            v-model="question"
            label="Question"
            style="width: 100%;"
            required
          ></v-text-field>
        </v-card>
          <!-- Instead of the question we give the transcription that is taken from the speech to text -->
          <!-- <v-text-field
            v-model="transcription"
            label="Question"
            style="width: 100%;"
            required
          ></v-text-field> -->

          <v-btn
            @click="sendMessage"
          >
            Explore
          <v-progress-circular v-if="loading" :model-value="progress" :rotate="360" :size="30" :width="5" color="teal">
          </v-progress-circular>
          </v-btn>
          <v-btn @click="text2query()">Text2Query
            <v-progress-circular v-if="loading_text2query" :model-value="progress" :rotate="360" :size="30" :width="5" color="teal">
          </v-progress-circular>
          </v-btn>
          
          
          
          
        </v-form>
        
        {{ receivedMessage }}
        
      </v-row>

      
    </div>
    </div>
  </aside>
</template>


<style scoped>
@import '../css/main.css';
.sidebar-container {
  height: 100vh; /* Full viewport height */
  display: flex;
  flex-direction: column;
}

.scrollable-content {
  flex-grow: 1;
  overflow-y: auto;
  padding: 16px;
}

/* Additional styles to ensure proper spacing */
.v-row {
  margin-bottom: 16px;
}

.drag-node {
  margin-bottom: 8px;
}
</style>
