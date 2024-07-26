
import pandas as pd 
import plotly.express as px 
import plotly.offline as pyo
import plotly.graph_objs as go
from langchain_core.output_parsers import JsonOutputParser,StrOutputParser,CommaSeparatedListOutputParser
from langchain_openai import ChatOpenAI 
from colorama import Fore, Back, Style
from langchain_core.prompts import PromptTemplate
import font 
from sentence_transformers import SentenceTransformer
import numpy as np 
from itertools import product

# Set notebook mode to work in offline
pyo.init_notebook_mode()
class vizData():
    def __init__(self, query):
        self.query = query 
        font.showMessage('title', 3, '<Reading Node Info>')
        self.data = pd.read_csv('nodes_info.csv')
        self.phraseEmbs = np.load('node_phrasebert_embeddings.npy')
        font.showMessage('title', 3, '<Reading Embedding Info>')
        # self.llm = ChatOpenAI(openai_api_key="", temperature=0, model_name = "gpt-4-0125-preview") 

        # self.llm = ChatOpenAI(openai_api_key="", temperature=0, model_name = "gpt-4-0125-preview")


        self.entities = self.getEntity(query)
        # self.entities = ['collaborators', 'water quality'] 
        self.entities = ['Monique Fountain', 'water quality'] 

        # print(self.entities)
        self.mappedEntities = self.analyzeEntity()
        # self.mappedEntities = [{'type': 'filtering', 'entity': 'water quality', 'class': ['Dataset', 'Project', 'Program']}, {'type': 'target', 'entity': 'collaborators', 'class': ['Person', 'Organization']}]
        
        self.mappedEntities = [{'type': 'filtering', 'entity': 'water quality', 'class': ['Dataset', 'Project', 'Program']}, {'type': 'target', 'entity': 'Monique Fountain', 'class': ['Person', 'Organization']}]

        self.retrieRelevant()
        # print(self.mappedEntities)
        # self.mappedEntities = [{'type': 'filtering', 'entity': 'water quality', 'class': ['Dataset', 'Project', 'Program'], 'related': [{'text': 'Water Quality & Watersheds Program', 'entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#prg_c46c0b', 'class': 'http://vivoweb.org/ontology/core#Program', 'idx': 5134}, {'text': 'Healthy Watersheds', 'entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#prg_24edc1', 'class': 'http://vivoweb.org/ontology/core#Program', 'idx': 4982}, {'text': 'Clean Lakes Estuaries And Rivers', 'entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#prg_528218', 'class': 'http://vivoweb.org/ontology/core#Program', 'idx': 5021}, {'text': 'National Water Quality Initiative', 'entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#prg_6b64d7', 'class': 'http://vivoweb.org/ontology/core#Program', 'idx': 5043}, {'text': 'Water for Farms, Fish and People', 'entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#prj_65ae80', 'class': 'http://vivoweb.org/ontology/core#Project', 'idx': 5648}]}, {'type': 'target', 'entity': 'collaborators', 'class': ['Person', 'Organization']}]
        self.prepareDraw()

    def getEntity(self, input):
        parser = CommaSeparatedListOutputParser()
        prompt  = PromptTemplate.from_template("""
        Goal: 
        Understand the users' input questions and identify possible entities. 
        Return a list of entities or keywords, seperated by comma, without output in the front. 
        
        Example:
        input: find author who works at Ohio State University 
        output: author, Ohio State University

        Input:
        {input}
        """)
        # font.showMessage('title', 3, '<Entity Extraction>')
        # chain = prompt | self.llm | parser 
        # result = chain.invoke({
        #     'input': input
        # })
        # font.showMessage('content', 6, f'Extracted entities are: {result}')
        # return result

    def analyzeEntity(self):
        example = """
        Example:
        <input query>: find authors who works at Ohio State University 
        <input entities>: author, Ohio State University
        
        [
            {
            "type": "filtering",
            "entity": "Ohio State University",
            "class": ["Organization"]
            },
            {
            "type": "target",
            "entity": "author",
            "class": ["Person"]
            }
        ]
        """
        entityClass = {
            'Dataset': "http://vivoweb.org/ontology/core#Dataset",
            'Best Practices And Mandates': 'http://www.sdsconsortium.org/schemas/sds-okn.owl#BestPracticesAndMandates',
            'Infrastructure': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/sustsource.owl#Infrastructure',
            'Organization': 'http://xmlns.com/foaf/0.1/Organization',
            'Person': 'http://xmlns.com/foaf/0.1/Person',
            'Program': 'http://vivoweb.org/ontology/core#Program',
            'Project': 'http://vivoweb.org/ontology/core#Project',
            'Issue': 'http://purl.obolibrary.org/obo/BFO_0000023',
            'Tool': 'http://www.sdsconsortium.org/schemas/sds-okn.owl#Tool'
        }
        parser = JsonOutputParser()
        prompt  = PromptTemplate.from_template(f"""
        Goal:  Read (1) users' input query (2)extracted entities from the query (3) defined entity classes of a knowledge graph. 
        mapping each entity to the possible entity classes, and classify them into target entity and filtering entity.
        Target entity type is the entity that users are interested to explore while filtering entity are entities which was used as filtering conditions in the query.                                     
        Output should be a valid json format without other information. 
        <Entity Classes>
        {{entityClass}}
        </Entity Classes>                                       
        
        <Example>
        {{example}}
        </Example>

        <Inputs>:
        {{input}} {{entity}}
        </Inputs>
        """)
        # font.showMessage('title', 3, '<Entity Mapping>')
        # chain = prompt | self.llm | parser 
        # # print(list(entityClass.values()))
        # result = chain.invoke({
        #     'entityClass': list(entityClass.values()),
        #     'example': example,
        #     'input': self.query,
        #     'entity': self.entities
        # })
        # font.showMessage('content', 6, f'Mapped entities are: {result}')
        # return result

    def retrieRelevant(self, k=5):
        font.showMessage('title', 3, '<Entity Retrieval>')
        
        for ent in self.mappedEntities:
            entities = []
            if ent['type']=="filtering" and ent['entity']!="": ## remove empty entities 
                to_find = ent['entity']
                font.showMessage('title', 4, f'Processing {to_find}')
                model = SentenceTransformer('whaleloops/phrase-bert')
                embed = model.encode(ent['entity'])
                embed = np.array(embed)
                distances = np.linalg.norm(self.phraseEmbs - embed, axis=1)
                best_k_ind = np.argpartition(distances, range(0,50))[:50]
                

                for ele in best_k_ind:
                    curr = self.data.iloc[ele]
                    curr_type = curr['type']
                    if curr_type.split('#')[-1] in ent['class'] or curr_type.split('/')[-1] in ent['class']: 
                        entities.append({
                            'text': curr['text'],
                            'entity': curr['entity'],
                            'class': curr['type'],
                            'idx': ele 
                        })
                        font.showMessage('explain', 5, f"The {len(entities)}-th related entities of {to_find} is {curr['text']}, its class is {curr['type']}")
                        if len(entities)==k:
                            break 
                ent['related'] = entities

                

    def prepareDraw(self):
        entityClass = []
        entityHighlight = {}
        entityMapping = {
            'Dataset': "http://vivoweb.org/ontology/core#Dataset",
            'Best Practices And Mandates': 'http://www.sdsconsortium.org/schemas/sds-okn.owl#BestPracticesAndMandates',
            'Infrastructure': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/sustsource.owl#Infrastructure',
            'Organization': 'http://xmlns.com/foaf/0.1/Organization',
            'Person': 'http://xmlns.com/foaf/0.1/Person',
            'Program': 'http://vivoweb.org/ontology/core#Program',
            'Project': 'http://vivoweb.org/ontology/core#Project',
            'Issue': 'http://purl.obolibrary.org/obo/BFO_0000023',
            'Tool': 'http://www.sdsconsortium.org/schemas/sds-okn.owl#Tool'
        }
        for ele in self.mappedEntities:
            if ele['type'] == 'filtering':
                for one_entity in ele['related']:
                    entityHighlight[one_entity['entity']] = "related_entity"
                    entityClass.append(one_entity['class'])
            else:
                for one_class in ele['class']:
                    entityClass.append(entityMapping[one_class])
        print(entityClass, entityHighlight)

        entityClass = [
        'http://vivoweb.org/ontology/core#Program',  # Assuming water quality-related programs have this class
        'http://xmlns.com/foaf/0.1/Person',  # Assuming Monique Fountain has this class
        ]
        
        for ele in self.mappedEntities:
            if ele['type'] == 'filtering':
                for one_entity in ele['related']:
                    entityHighlight[one_entity['entity']] = "related_entity"
                    entityClass.append(one_entity['class'])
            else:
                for one_class in ele['class']:
                    entityClass.append(entityMapping[one_class])

        # Call create_edges method to generate edges
        edges = self.create_edges()

        # Call drawScatterWithEdges method with entityClass, entityHighlight, and edges
        self.drawScatterWithEdges(entityClass=entityClass, entityHighlight=entityHighlight, edges=edges)


    

    def drawScatter(self, entityClass=None, entityHighlight = None): 
      """
      entityClass: List of str
      entityHighlight: Dict, {entity: highlight_type,}
      """
      if entityClass:
        drawData = self.data[self.data['type'].isin(entityClass)]
        if entityHighlight == None:
           fig = px.scatter(drawData, x='tsne_x', y='tsne_y', hover_data=['text'], color='type')
           fig.update_layout(title="Node projects of specific entity class", hovermode='closest')
           fig.show()
        else:
            new_color = []
            for index, row in drawData.iterrows():
                if row['entity'] in entityHighlight:
                    new_color.append(entityHighlight[row['entity']])
                else:
                    new_color.append(row['type'])
            drawData['new_color']  = new_color
            fig = px.scatter(drawData, x='tsne_x', y='tsne_y', hover_data=['text'], color='new_color')
            fig.update_layout(title="Node projects of specific entity class", hovermode='closest')
            fig.show()
      else:
            fig = px.scatter(self.data, x='tsne_x', y='tsne_y', hover_data=['text'], color='type')
            # Update layout if necessary
            fig.update_layout(title='Scatter Plot with Text on Hover',
                            xaxis_title='X Axis',
                            yaxis_title='Y Axis',
                            hovermode='closest')
            fig.show()
    

        
    def create_edges(self):
        edges = []
        # Find rows containing "water quality" and "Monique Fountain"
        water_quality_rows = self.data[self.data['text'].str.contains('water quality', case=False)]
        monique_fountain_rows = self.data[self.data['text'].str.contains('Monique Fountain', case=False)]
        
        # Iterate over the matched rows
        for _, water_quality_row in water_quality_rows.iterrows():
            for _, monique_fountain_row in monique_fountain_rows.iterrows():
                edges.append((water_quality_row['text'], monique_fountain_row['text']))
        
        return edges







    def drawScatterWithEdges(self, entityClass=None, entityHighlight=None, edges=None):
        print("Starting drawScatterWithEdges...")
        print(f"entityClass: {entityClass}")
        print(f"entityHighlight: {entityHighlight}")
        print(f"edges: {edges}")

        if entityClass:
            drawData = self.data[self.data['type'].isin(entityClass)]
            print(f"Number of rows in drawData: {len(drawData)}")

            fig = px.scatter(drawData, x='tsne_x', y='tsne_y', hover_data=['text'], color='type')
            
            # Add edges to the scatter plot
            if edges:
                for edge in edges:
                    entity1 = edge[0]
                    entity2 = edge[1]
                    if entity1 in drawData['text'].values and entity2 in drawData['text'].values:
                        x_values = [
                            drawData.loc[drawData['text'] == entity1, 'tsne_x'].values[0],
                            drawData.loc[drawData['text'] == entity2, 'tsne_x'].values[0]
                        ]
                        y_values = [
                            drawData.loc[drawData['text'] == entity1, 'tsne_y'].values[0],
                            drawData.loc[drawData['text'] == entity2, 'tsne_y'].values[0]
                        ]
                        fig.add_trace(
                            go.Scatter(
                                x=x_values,
                                y=y_values,
                                mode='lines',
                                line=dict(color='rgba(50, 50, 50, 0.5)', width=1),
                                showlegend=False
                            )
                        )

            fig.update_traces(marker=dict(size=5), selector=dict(mode='markers'))
            fig.update_layout(title="Node projects of specific entity class", hovermode='closest')
            fig.show()








            
        
