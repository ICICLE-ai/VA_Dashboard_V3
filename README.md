# About The Project

Visualization Studio Version 3 is a cutting-edge visual analytics system designed for interactive exploration of knowledge graphs (KG). This system offers a variety of features to enhance user interaction and understanding of KGs through natural language and speech inputs. Visualization Studio Version 3 not only enhances user engagement with knowledge graphs but also ensures the clarity and transparency of the information retrieval process, making it a powerful tool for visual analytics.

## Key Features
1. **Natural Language Queries**: Users can ask questions in natural language, and the system provides answers by referencing the KG. This facilitates a more intuitive interaction with complex data.

2. **Explorative Answers**: By leveraging large language models (LLMs), the system delivers comprehensive answers and visually displays the reasoning process. This enhances explainability and transparency of the provided answers.

3. **Direct Answer Retrieval**: For users preferring direct responses, a text-to-query module transforms natural language questions into precise queries to fetch the answers directly from the KG.

4. **Speech-to-Text Module**: The system includes a robust speech-to-text functionality, allowing users to input queries via speech. A wake word activates the system to start recording, making it seamless to switch between speech and text inputs.

5. **Multiple Types of Viewers**: The system fascilitates viewers to use table viewers and graph viewers which flows data between them to visualize user uploaded csv tables of KGs and display them upon being connected to graph viewers. Users can upload CSV files related to the KG in the table viewer. The system processes these files and visualizes the associated nodes and edges as an interactive network graph, facilitating data exploration and analysis.


# Built With
- django
- Vue 3



# Getting Started
To clone this repository and run the application, use the following instructions.

1. Clone this repository <br/>
git clone https://github.com/ICICLE-ai/VA_Dashboard_V3.git

2. Install the redis server

3. Install dependencies  <br/>
npm install

4. From the project root folder run the redis server  <br/>
redis-server

5. To run the backend go into the djangoBackend folder within the backend folder  <br/>
uvicorn djangoBackend.asgi:application --port 8000 --reload

6. To run the frontend go into the frontend folder  <br/>
npm run dev

7. Get an OpenAI API key to use the Knowledge Graph exploring features


# Docker Development and Deployment
This repo features a Makefile to enable easy containerized deployments. Running `make up` and `make down` is the expected developer routine. Or a convenient `make down up`.  The Makefile makes use of `docker compose` to deploy `docker-compose.yml`, which in turn runs the frontend Django and backend Vite of VA3 in Docker containers defined by `frontend/Dockerfile` and `backend/Dockerfile`. Both of these images are built in the Makefile.
```
$ make <arg>
  build      Build front and backend images
  up         Deploy service
  down       Burndown service
  vars       Lists vars
```
When deployed, with `make up`, there will be three docker containers, va3-backend:dev, va3-frontend:dev, redis.


# Roadmap
Side panel
![Sidepanel Screenshot](https://github.com/user-attachments/assets/be7d018d-b95d-4d6a-b300-5980f40fa295)

1. Exploratory question answering

Users will be displayed with a side panel which includes an area for providng the OpenAI API key where users should provide their OpenAI API key. 
Users can ask their questions in two ways.
 1. Type in the question
 2. Provide the question as a speech input by giving a wakeword
    - The wake word will be used as the word to signal the system to start recoding. Once the wake word is given to the system and the user clicks the **START RECORDING** button, the automatic speech recognition will start and upon identifying the wake word, the system starts recording the speech. After te user has given the speech input there will be a 80 millisecond wait by the system which is used to identify the end of speech by the user. When the recording is detected, it will appear in the **Detected Question** text area.
   
Once the question is given as input the user can click the **Explore** button. This will result in displaying how the LLM retrieves answers for the user's question providing explainability.
The example shown below depicts the visualization pipeline displayed by the system for the question **Find possible collaborators that work on water quality**.

![Exploratory question answering](https://github.com/user-attachments/assets/65769b57-2bf6-4471-91cd-a2c0a4a4b595)


2. Text 2 query
The system integrates a text 2 query module to allow users to get the direct answers to their questions. The OpneAI APIK key would be necessary for this component as well.



3. Table viewer and Graph viewer components
The Table Viewer component enables users to upload a CSV file containing data related to the Knowledge Graph (KG), where each row represents a node within the KG. This component offers several powerful features to enhance data interaction and visualization:

- **CSV File Upload**: Users can upload CSV files that contain node data for the KG, making it easy to integrate and visualize new datasets.

- **Data Flow Connection**: By linking the Table Viewer with a selected number of rows with another table, users can observe the flow of data between these modules..

- **Selective Display**: Users can select a subset of rows to be displayed according to their specific needs, allowing for focused analysis and exploration of particular nodes.

- **Graph Viewer Integration**: When connected to a Graph Viewer, the Table Viewer allows users to explore the attached nodes and edges. By clicking on the pie sections around the nodes, users can see detailed connections and relationships, providing a comprehensive view of the KG's structure.



4. SPARQL Editor and Executor
This component allows users to create SPARQL queries in the SPARQL Editor and connect that to a SPARQL Executor where users can click the “Query” Button. Next a table viewer needs to be connected to see the outputs of the query. The example shows a query executed to retrieve distinct concepts used in the dbpedia dataset. 
![SPARQL EDITOR](https://github.com/user-attachments/assets/3420a447-38ea-4f17-bad2-fb9ca3d83de8)

6. VegaLite Visualizer
This component automatically generates visualization charts for input data. When a CSV file is uploaded, the corresponding chart for that table will be displayed for which an example is shown below.
<img width="1001" alt="vegalite" src="https://github.com/user-attachments/assets/3e924617-bb46-4ea5-af16-dec08617bf3d">

