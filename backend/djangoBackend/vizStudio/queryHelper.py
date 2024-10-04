
from langchain_openai import ChatOpenAI 
from langchain_core.output_parsers import JsonOutputParser,StrOutputParser,CommaSeparatedListOutputParser
from langchain_core.prompts import PromptTemplate
from sentence_transformers import SentenceTransformer
import numpy as np 
import pandas as pd 
import yaml 
import rdflib
from rdflib import Graph, Namespace
import networkx as nx
class queryHelper():
    def __init__(self, api_key):
        self.llm = ChatOpenAI(openai_api_key=api_key, temperature=0, model_name = "gpt-4-0125-preview") 
        self.data = pd.read_csv('../data/nodes_info.csv')
        self.phraseEmbs = np.load('../data/node_phrasebert_embeddings.npy')
        self.linkml, self.g  = self.readKG("../data/PPOD.yaml", "../data/PPOD_CA.ttl")
        self.ont = nx.read_graphml('../data/ontology_ppod.graphml')
        self.relevantEntId = []
        self.relevantEntClass = []
        self.drawEntId = []
        self.mode = "test"
    def readKG(self, file1, file2):
        g = rdflib.Graph()
        g.parse(file2, format="turtle")
        with open(file1, 'r') as file:
            linkml = yaml.safe_load(file)
            prefix = linkml['prefixes']
            for ele in prefix:
                g.bind(ele, Namespace(prefix[ele]))
            return linkml, g 
    def getEntity(self, input):
        self.query = input 
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
        if self.mode == "dev":
            result = ['collaborators','water quality']
            self.entities = result
        else:
            chain = prompt | self.llm | parser 
            result = chain.invoke({
                'input': input
            })
            self.entities = result
        message = f"Based on your question, we have identified the following entities: {result}"
        return message

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
        if self.mode == "dev":
            result = [{'type': 'filtering', 'entity': 'water quality', 'class': ['Dataset', 'Project', 'Program']}, {'type': 'target', 'entity': 'collaborators', 'class': ['Person', 'Organization']}]
        else:
            chain = prompt | self.llm | parser 
            result = chain.invoke({
                'entityClass': list(entityClass.values()),
                'example': example,
                'input': self.query,
                'entity': self.entities
            })
        message = f"The entities can be mapped to our pre-defined ontology as follows: {result}"
        self.mappedEntities = result
        return  message


    def retriveRelevant(self, k=5, n=200):
        for ent in self.mappedEntities:
            # to_find = ent['entity']
            entities = []
            if ent['type']=="filtering" and ent['entity']!="": ## remove empty entities 
                model = SentenceTransformer('whaleloops/phrase-bert')
                embed = model.encode(ent['entity'])
                embed = np.array(embed)
                distances = np.linalg.norm(self.phraseEmbs - embed, axis=1)
                best_k_ind = np.argpartition(distances, range(0,n))[:n]
                for ele in best_k_ind:
                    curr = self.data.iloc[ele]
                    curr_type = curr['type']
                    ## the similar entity is in the inferred entity class
                    if curr_type.split('#')[-1] in ent['class'] or curr_type.split('/')[-1] in ent['class']: 
                        color = "#1a9850"
                    else: ## false negative 
                        color = "#d73027"
                    
                    if curr['type'] not in self.relevantEntClass:
                        self.relevantEntClass.append(curr['type'])
                    if len(entities)<=k: 
                        entities.append({
                        'text': curr['text'],
                        'entity': curr['entity'],
                        'class': curr['type'],
                        'idx': int(ele),
                        'color': color
                    })
                        self.relevantEntId.append(ele)
                    self.drawEntId.append(ele)
                    if len(entities)==n:
                        break
                ent['related'] = entities
            # message += f"We find related entity to {ent['entity']} are {entities}"
        return self.mappedEntities

    def getScatterData(self):
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
        highlightData = self.data.iloc[self.relevantEntId]
        # highlightData = highlightData[highlightData['type'].isin(self.relevantEntClass)]
        highlightData['opacity'] = [1]*len(highlightData)
        highlightData['r'] = [10]*len(highlightData)

        notHighlightData = self.data.loc[self.drawEntId]
        # notHighlightData = notHighlightData[notHighlightData['type'].isin(self.relevantEntClass)]
        notHighlightData['opacity'] = [0.4]*len(notHighlightData)
        notHighlightData['r'] = [5]* len(notHighlightData)
        
        return highlightData.to_dict('records') + notHighlightData.to_dict('records')
        # print(entityClass, entityHighlight)
        # self.drawScatter(entityClass, entityHighlight)

    def getTargetEntities(self, target_uris, target_classes, node_class, node_id):
        graph = []
        for i in range(len(target_uris)):
            uri = target_uris[i]
            query = f"""
            SELECT ?target ?label 
                WHERE {{
                    BIND(<{node_id}> AS ?startNode)
                    ?startNode (<>|!<>)* ?target .
                    ?target rdf:type <{uri}> .
                    ?target rdfs:label ?label . 
                }}
            """
#             print(query)
            results = self.g.query(query)
        
            for row in results:
#                 print(str(row['target'].toPython()))
                graph.append({
                    "target_entity": str(row['target'].toPython()),
                    "target_label": str(row['label'].toPython()),
                    "target_uri": uri,
                    "targte_class": target_classes[i],
                })
        return graph 
        
    def getNetworkData(self):
        if self.mode=="dev":
            graph_data = {'graph': [{'source_label': 'Water Quality & Watersheds Program', 'source_class': 'Program', 'source_uri': 'http://vivoweb.org/ontology/core#Program', 'source_id': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#prg_c46c0b', 'source_color': '#1a9850', 'target_nodes': [{'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_902d0e', 'target_label': "Governor's Office of Planning and Research", 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_114dfb', 'target_label': 'Bay Planning Coalition', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_7bd98c', 'target_label': 'Invasive Species Council of California', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_e82d9f', 'target_label': 'Lake Tahoe West Restoration Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_d3e5d0', 'target_label': 'San Francisco Estuary Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_fb6e58', 'target_label': 'Trinity Management Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_170f6c', 'target_label': 'California Tahoe Conservancy', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_b0d31f', 'target_label': 'Tahoe Fire & Fuels Team', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_5dccc2', 'target_label': 'Tahoe Science Advisory Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a281e8', 'target_label': 'Tahoe-Sierra Integrated Regional Water Management Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_aa9bcc', 'target_label': 'Yolo Bypass Cache Slough Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a39c14', 'target_label': 'California Strategic Growth Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_8130b6', 'target_label': 'Fire Adapted Communities Learning Network', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_acb46a', 'target_label': 'Central Valley Salmon Habitat Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_915458', 'target_label': 'California Central Coast Joint Venture', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a6a937', 'target_label': 'California Wildfire & Forest Resilience Task Force', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_c413bb', 'target_label': 'Sierra Meadows Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_726fc4', 'target_label': 'California Forest Management Task Force', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_6e065b', 'target_label': 'Central Valley Joint Venture', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_e57cc7', 'target_label': 'Network For Landscape Conservation', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_2cffad', 'target_label': 'Tulare Basin Wildlife Partners', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_4a4073', 'target_label': 'California Biodiversity Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_546245', 'target_label': 'San Francisco Bay Joint Venture', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_b186fd', 'target_label': 'California Natural Resources Agency', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a435a7', 'target_label': 'California Biodiversity Network', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}]}, {'source_label': 'Nitrate Groundwater Pollution Hazard Index', 'source_class': 'Tool', 'source_uri': 'http://www.sdsconsortium.org/schemas/sds-okn.owl#Tool', 'source_id': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#tol_b14e38', 'source_color': '#d73027', 'target_nodes': [{'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_fad586', 'target_label': 'California Institute for Water Resources', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_902d0e', 'target_label': "Governor's Office of Planning and Research", 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_114dfb', 'target_label': 'Bay Planning Coalition', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_7bd98c', 'target_label': 'Invasive Species Council of California', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_d3e5d0', 'target_label': 'San Francisco Estuary Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_fb6e58', 'target_label': 'Trinity Management Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_5dccc2', 'target_label': 'Tahoe Science Advisory Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_24fd4f', 'target_label': 'University of California Office of the President', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_aa9bcc', 'target_label': 'Yolo Bypass Cache Slough Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a39c14', 'target_label': 'California Strategic Growth Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_f623c2', 'target_label': 'University of California Agriculture and Natural Resources', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_4df9bf', 'target_label': 'California Pollinator Coalition', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_acb46a', 'target_label': 'Central Valley Salmon Habitat Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_915458', 'target_label': 'California Central Coast Joint Venture', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a6a937', 'target_label': 'California Wildfire & Forest Resilience Task Force', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_726fc4', 'target_label': 'California Forest Management Task Force', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_6e065b', 'target_label': 'Central Valley Joint Venture', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_e57cc7', 'target_label': 'Network For Landscape Conservation', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_2cffad', 'target_label': 'Tulare Basin Wildlife Partners', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_4a4073', 'target_label': 'California Biodiversity Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_546245', 'target_label': 'San Francisco Bay Joint Venture', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_b186fd', 'target_label': 'California Natural Resources Agency', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a435a7', 'target_label': 'California Biodiversity Network', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}]}, {'source_label': 'Safe Drinking Water, Water Quality and Supply, Flood Control, River and Coastal Protection Bond Act of 2006', 'source_class': 'Best Practices And Mandates', 'source_uri': 'http://www.sdsconsortium.org/schemas/sds-okn.owl#BestPracticesAndMandates', 'source_id': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#gmt_3b0a8a', 'source_color': '#d73027', 'target_nodes': []}, {'source_label': 'Water Resources Specialist', 'source_class': 'Issue', 'source_uri': 'http://purl.obolibrary.org/obo/BFO_0000023', 'source_id': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#rol_9b72be', 'source_color': '#d73027', 'target_nodes': [{'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#per_dd9363', 'target_label': 'Jeanne Brantigan', 'target_uri': 'http://xmlns.com/foaf/0.1/Person', 'targte_class': 'Person'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_397086', 'target_label': 'Loma Prieta Resource Conservation District', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_772d10', 'target_label': 'Wildland Fire Leadership Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_d552da', 'target_label': 'Pinnacles National Park', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_ec15eb', 'target_label': 'Federal Emergency Management Agency', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_1c99d5', 'target_label': 'Alhambra Watershed Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_770035', 'target_label': 'Wildland Fire Mitigation and Management Commission', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_968bba', 'target_label': 'Sierra Valley Conservation Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_e8b142', 'target_label': 'Migratory Bird Conservation Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_baf212', 'target_label': 'California Salmon and Steelhead Coalition', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_c0cf9e', 'target_label': 'Middle Truckee River Watershed Forest Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_902d0e', 'target_label': "Governor's Office of Planning and Research", 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a848cb', 'target_label': 'Southern Sierra Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_c86122', 'target_label': 'One Tam', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_114dfb', 'target_label': 'Bay Planning Coalition', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_7bd98c', 'target_label': 'Invasive Species Council of California', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_68a0cb', 'target_label': 'National Drought Resilience Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_68d673', 'target_label': 'Cosumnes River Preserve Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_f5233a', 'target_label': 'Northern Sierra Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_282a05', 'target_label': 'U.S. Department of the Interior', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_29d5eb', 'target_label': 'Food and Agriculture Climate Alliance', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_fc414b', 'target_label': 'North Yuba Forest Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a8b1b2', 'target_label': 'Eastern Sierra Sustainable Recreation Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_d3e5d0', 'target_label': 'San Francisco Estuary Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_fb6e58', 'target_label': 'Trinity Management Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_5dccc2', 'target_label': 'Tahoe Science Advisory Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_f1c090', 'target_label': 'Western Klamath Restoration Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_e8e1e7', 'target_label': 'Watersheds Coalition of Ventura County', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_5648d0', 'target_label': 'San Benito Working Landscapes Group', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_6d29d0', 'target_label': 'West Coast Regional Carbon Sequestration Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_98aaad', 'target_label': 'San Joaquin River Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_aa9bcc', 'target_label': 'Yolo Bypass Cache Slough Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a39c14', 'target_label': 'California Strategic Growth Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_9c0712', 'target_label': 'Monarch Joint Venture', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_41ac24', 'target_label': 'Golden Gate Biosphere Network', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_4df9bf', 'target_label': 'California Pollinator Coalition', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_4b157a', 'target_label': 'Klamath Meadows Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_fbb43b', 'target_label': 'Sierra Cascade Land Trust Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_87d72f', 'target_label': 'U.S. Department of Agriculture', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_acb46a', 'target_label': 'Central Valley Salmon Habitat Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_915458', 'target_label': 'California Central Coast Joint Venture', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a6a937', 'target_label': 'California Wildfire & Forest Resilience Task Force', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_c413bb', 'target_label': 'Sierra Meadows Partnership', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_726fc4', 'target_label': 'California Forest Management Task Force', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_2f833e', 'target_label': 'Ventura River Watershed Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_ab496a', 'target_label': 'Reimagining San Francisco', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_f736e5', 'target_label': 'U.S. National Park Service', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_6e065b', 'target_label': 'Central Valley Joint Venture', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_e57cc7', 'target_label': 'Network For Landscape Conservation', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_2e9a1c', 'target_label': 'Green Vision Coalition', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_b6d1a5', 'target_label': 'Cosumnes American Bear Yuba Integrated Regional Water Management Group', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_2cffad', 'target_label': 'Tulare Basin Wildlife Partners', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_c776d6', 'target_label': 'The Nature Conservancy', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_4a4073', 'target_label': 'California Biodiversity Council', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_546245', 'target_label': 'San Francisco Bay Joint Venture', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_5ea017', 'target_label': 'TOGETHER Bay Area', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_b186fd', 'target_label': 'California Natural Resources Agency', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_22f94e', 'target_label': 'California Council of Land Trusts', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_e68031', 'target_label': 'Wildlife Corridor Working Group', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a435a7', 'target_label': 'California Biodiversity Network', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}, {'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_a54512', 'target_label': 'California Association of Resource Conservation Districts', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}]}, {'source_label': 'Advanced Water Purification Facility', 'source_class': 'Infrastructure', 'source_uri': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/sustsource.owl#Infrastructure', 'source_id': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#inf_1640d2', 'source_color': '#d73027', 'target_nodes': [{'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_200efc', 'target_label': 'City of Oxnard', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}]}, {'source_label': 'Healthy Watersheds', 'source_class': 'Program', 'source_uri': 'http://vivoweb.org/ontology/core#Program', 'source_id': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#prg_24edc1', 'source_color': '#1a9850', 'target_nodes': [{'target_entity': 'https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#org_7f685e', 'target_label': 'Water Foundation', 'target_uri': 'http://xmlns.com/foaf/0.1/Organization', 'targte_class': 'Organization'}]}], 'unique_class': ['Infrastructure', 'Program', 'Organization', 'Issue', 'Person', 'Best Practices And Mandates', 'Tool']}
            return graph_data
        else:
            class2URI = {
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
            URI2class = {value: key for key, value in class2URI.items()}
            target_class = []
            for ele in self.mappedEntities:
                if ele['type']=='target':
                    target_class += ele['class']
            target_class = list(set(target_class))
            target_uris = [class2URI[ele] for ele in target_class]
            
            graph_data = []
            unique_class = target_class 
            for ele in self.mappedEntities:
                if ele['type']=='filtering':
                    for ent in ele['related']:
                        idx = ent['idx']
                        print(idx)
                        node_id = self.data.iloc[idx]['entity'] ## current enitty id
                        node_class_uri = self.data.iloc[idx]['type']
                        node_class = URI2class[node_class_uri]
                        small_graph = self.getTargetEntities( target_uris, target_class, node_class, node_id)
                        unique_class.append(node_class)
                
                        graph_data.append({
                            'source_label': ent['text'],
                            'source_class': node_class, 
                            'source_uri': node_class_uri,
                            'source_id': node_id,
                            'source_color': ent['color'],
                            'target_nodes': small_graph
                        })
            unique_class = list(set(unique_class))
            result = {
                'graph': graph_data,
                'unique_class': unique_class
            }
            # print(result)
            return result
