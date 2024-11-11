# How to add new template? 
1. template vue in Modules  e.g. TableViewer.vue
2. main.vue add import e.g. import TableViewerNode from './TableViewer.vue'
3. main.vue add template. 
 <template #node-tableViewer="{data,id,type}">
                <TableViewerNode :data="data" :id="id" :type="type"></TableViewerNode>
              </template>

4. SideBar.vue
5. NewNode.vue is made for testing purposes of creating a new node

## Run the redis server
From any location in the device
redis-server


## To run backend
Go to backend > djangoBackend
### Give path to your project folder
set PYTHONPATH=C:\OSU\ResearchProject\ICICLE FINAL GUI_\VA_Dashboard_V3;%PYTHONPATH% 

uvicorn djangoBackend.asgi:application --port 8000 --reload





## To run the frontend
Go to frontend
npm run dev
   

## If it's the first time running the frontend
Might need to do "npm install" if you get the error  'vite' is not recognized as an internal or external command

## SPARQL endpoint to run questions like "Find possible collaborators that work on water quality." on PPOD
https://jupyter002-second.pods.tacc.develop.tapis.io/sparql



## To run test_kg_api.py for debugging
Go to backend\text_to_query
python -m test.test_kg_api

## If you need to set OPENAI api 
set OPENAI_API_KEY=your_api_key_here
