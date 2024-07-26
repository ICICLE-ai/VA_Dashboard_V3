# consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import logging
import asyncio
logger = logging.getLogger('django')
import pandas as pd 
import numpy as np 
from .queryHelper import queryHelper

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NumpyEncoder, self).default(obj)

class QueryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        logger.info("WebSocket connected.")

    async def disconnect(self, close_code):
        pass
        logger.info("WebSocket disconnected.")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        logger.info(text_data_json)
        question = text_data_json['question'] ## query from users 
        openai_api = text_data_json['openai_api']

        # logger.info(question, openai_api)
        ## read data 
        
        ##step1. process entity 
        # await asyncio.sleep(5)
        agent = queryHelper(openai_api)
        message = agent.getEntity(question)
        # entities = ['collaborators','water quality']      
        # message  = "Based on your question, we have identified the following entities: ['collaborators','water quality'] "
        await self.sendMessage({
            "progress": 10,
            "type": "entityExtraction",
            "text": message
        })
        # await asyncio.sleep(1)
        message = agent.analyzeEntity()
        # mappedEntities =  [{'type': 'filtering', 'entity': 'water quality', 'class': ['Dataset', 'Project', 'Program']}, {'type': 'target', 'entity': 'collaborators', 'class': ['Person', 'Organization']}]
        # message = "The entities can be mapped to our pre-defined ontology as follows: [{'type': 'filtering', 'entity': 'water quality', 'class': ['Dataset', 'Project', 'Program']}, {'type': 'target', 'entity': 'collaborators', 'class': ['Person', 'Organization']}]"
        await self.sendMessage({
            "progress": 20,
            "type": "analyzeEntity",
            "text": message
        })
        # await asyncio.sleep(1)
        
        mappedEntities = agent.retriveRelevant()
        # mappedEntities = [{"type": "filtering", "entity": "water quality", "class": ["Dataset", "Project", "Program"], "related": [{"text": "Water Quality & Watersheds Program", "entity": "https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#prg_c46c0b", "class": "http://vivoweb.org/ontology/core#Program", "idx": 5134}, {"text": "Healthy Watersheds", "entity": "https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#prg_24edc1", "class": "http://vivoweb.org/ontology/core#Program", "idx": 4982}, {"text": "Clean Lakes Estuaries And Rivers", "entity": "https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#prg_528218", "class": "http://vivoweb.org/ontology/core#Program", "idx": 5021}, {"text": "National Water Quality Initiative", "entity": "https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#prg_6b64d7", "class": "http://vivoweb.org/ontology/core#Program", "idx": 5043}, {"text": "Water for Farms, Fish and People", "entity": "https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#prj_65ae80", "class": "http://vivoweb.org/ontology/core#Project", "idx": 5648}]}, {"type": "target", "entity": "collaborators", "class": ["Person", "Organization"]}]
        await self.sendMessage({
            "progress": 40,
            "data": mappedEntities,
            "type": 'retrieveRelevant'
        })

        ## 

        await asyncio.sleep(1)
        scatterplotData = agent.getScatterData()
        # logger.info(test)
        await self.sendMessage({
            "progress": 80,
            "type": "drawScatter",
            "data": scatterplotData
        })

        networkData = agent.getNetworkData() 
        await self.sendMessage({
            "progress": 100,
            "type": "drawNetwork",
            "data": networkData
        })
        # await asyncio.sleep(3)
        # logger.info(f"sending second message from back to front")
        # await self.sendMessage(f"after sleep: {message} again!")

        
    async def sendMessage(self, data):
        await self.send(text_data=json.dumps(data))