# ICICLE IKLE Text-to-Query

Text-to-query component is integrated with visualization studio, but could work independently.
It is designed to convert natural language questions to formal queries (e.g., SPARQL).
The component is built on top of [Pangu](https://aclanthology.org/2023.acl-long.270/), which is a general method of grounding language models to real-world environments.
For this project, Pangu is deployed on the PPOD knowledge graph.

## PPOD Data

- KG ontology: https://github.com/ICICLE-ai/ppod/tree/master
- PPOD KG: https://github.com/ICICLE-ai/PPOD_CA/blob/main/PPOD_CA.ttl

## Preparation

- To test the text-to-query interface, the working dir is `text_to_query`:

```shell
cd backend/text_to_query
```

- See `backend/text_to_query/requirements.txt` to install required packages. Some [Sentence-Transformers](https://huggingface.co/sentence-transformers) checkpoints will be
  downloaded automatically when running this component.

```shell
pip install -r requirements.txt
```

- To run text-to-query, set the OpenAI API key in the environment variable.

```shell
export OPENAI_API_KEY=<YOUR_API_KEY>
```

- See `Virtuoso Deployment` section in this page to deploy a Virtuoso server for KG query service. If you already have an online service, you can skip this step.
- (Optional) This is required only if ColBERT is used for retrieval. ColBERT is not used by default, so this step is optional:

```shell
# download ColBERT
cd backend/text_to_query/exp
wget https://downloads.cs.stanford.edu/nlp/data/colbert/colbertv2/colbertv2.0.tar.gz
tar -zxvf colbertv2.0.tar.gz
```

## Interface

- SPARQL query interface:

```shell
python pangu/environment/examples/KB/PPODSparqlCache.py
```

- Text-to-query API demos are shown in `python pangu/ppod_api.py`

```python
if __name__ == "__main__":
    pangu = PanguForPPOD(openai_api_key=os.getenv('OPENAI_API_KEY'), llm_name='gpt-4o')

    # text-to-query API demo
    res = pangu.text_to_query('What downstream infrastructures are connected to adjacent infrastructure in Drakes Estero?')
    for item in res:
        print(item)
    print()

    question = 'Which infrastructure intersects with San Dieguito Lagoon and involves striped mullet?'  # entity: San Dieguito Lagoon, literal: striped mullet
    # entity retrieval API demo
    entities = pangu.retrieve_entity(question, top_k=10)
    for i, doc in enumerate(entities):
        print(i, doc, pangu.label_to_entity[doc])
    print()

    # literal retrieval API demo
    literals = pangu.retrieve_literal(question, top_k=10)
    for i, doc in enumerate(literals):
        print(i, doc)
    print()

    # relation retrieval API demo
    relations = pangu.retrieve_relation(question, top_k=10)
    for i, doc in enumerate(relations):
        print(i, doc, pangu.label_to_predicate[doc])
    print()

```

## Virtuoso Deployment

You may need to setup your own Virtuoso server to run a KG query service. Here are the steps:

1. Download virtuoso from [here](https://github.com/dki-lab/Freebase-Setup).
2. Loading PPOD KG ttl file to Virtuoso using `isql`:

```
ld_dir('data', 'PPOD_CA.ttl', 'sparql');
rdf_loader_run();
```

3. Set the endpoint url in `pangu/environment/examples/KB/PPODSparqlCache.py`.

## Evaluation

Using graph search and large language model (approach like [GAIN](https://aclanthology.org/2024.eacl-srw.7/)), we provide a synthesized dataset for in-context learning and
evaluation, see this dataset in `backend/text_to_query/exp`.

To create such a dataset, see the following pipeline:

- backend/text_to_query/src/enumeration/schema_generation.py: Enumerate logical forms for each question.
- backend/text_to_query/src/data_prep/lisp_to_nl.py: Create a synthesized dataset: using large language models to convert logical forms into synthesized natural language queries.
- backend/text_to_query/src/data_split.py: Split the dataset into training, validation, and test sets.

## S-expression for PPOD

[S-expression](https://arxiv.org/abs/2011.07743) is LISP like language that is used to represent logical forms. In Pangu, the pipeline
is: `natural language query -> S-expression -> SPARQL query`.

See S-expression definitions in `text_to_query/pangu/language/ppod_language.py`. For PPOD, functions in S-expression include:

- `JOIN(predicate, entity/literal) -> entities`: return an entity set that connects to the input entity/literal by the input predicate.
- `AND(entities, entities)`: return the intersection of two entity sets.
- `COUNT(entities) -> int`: return the number of entities in the input entity set.

## Guidance for Transferring to any custom KG

If you want to run this component on a new knowledge graph, things to do include:

- Check `text_to_query/src/kb_statistics.py` to create some essential files about the KG.
- (Optional) For in-context learning,
    - check `text_to_query/src/enumeration/schema_generation.py` to enumerate logical forms, and
    - check `text_to_query/src/data_prep/lisp_to_nl.py` to create a synthesized dataset using large language models.
- (Optional) Check the S-expression definition in Pangu. This is an intermediate representation that could be converted to SPARQL queries. See more explanations below.
- Check the `interface` below to run the text-to-query interface.
