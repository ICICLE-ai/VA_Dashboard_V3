# ICICLE IKLE Text-to-Query

Text-to-query component is integrated with visualization studio, but could work independently.
It is designed to convert natural language questions to formal queries (e.g., SPARQL).
The component is built on top of [Pangu](https://aclanthology.org/2023.acl-long.270/), which is a general method of grounding language models to real-world environments.
For this project, Pangu is deployed on the PPOD knowledge graph.

## PPOD Data

- KG ontology: https://github.com/ICICLE-ai/ppod/tree/master
- PPOD KG: https://github.com/ICICLE-ai/PPOD_CA/blob/main/PPOD_CA.ttl

## Preparation

- See `backend/requirements.txt` to install required packages. Some [Sentence-Transformers](https://huggingface.co/sentence-transformers) checkpoints will be
  downloaded automatically when running this component.

```shell
cd backend
pip install -r requirements.txt
```

- See `Virtuoso Deployment` section in this page to deploy a Virtuoso server for KG query service. If you already have an online query service, you can skip this step.
- See `Language Model Deployment` section in this page to deploy a local LLM service. If you already have an online LLM service, you can skip this step.
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
python pangu/environment/examples/KB/PPODSparqlService.py
```

- To test the text-to-query interface, the working dir is `text_to_query`. API demos are shown in `test/test_ppod_sparql.py`:

```shell
cd backend/text_to_query
python test/test_ppod_sparql.py
```

## Virtuoso Deployment

You can use a public service to visit the KG, otherwise you may need to setup your own Virtuoso server to run a KG query service. Here are the steps:

The default **working dir** for this section is your Virtuoso root path.

1. Download [virtuoso](https://github.com/dki-lab/Freebase-Setup).
2. Create a dir under virtuoso root path for a KG, and put `backend/text_to_query/config/virtuoso.ini` under this dir:

```shell
cd <your_virtuoso_path>
mkdir ppod_kg
cp /this_project/backend/text_to_query/config/virtuoso.ini your_virtuoso_path/ppod_kg
```

Modify the `virtuoso.ini` file if you need to set a different port or path.

3. Put PPOD KG ttl file under `your_data_path`, which is specified in `virtuoso.ini`.

4. Start the Virtuoso server:

```shell
python3 virtuoso.py start 3002 -d ppod_kg
```

5. Load ttl file to Virtuoso using `isql`:

```
/your_virtuoso_path/bin/isql 13002 dba dba
ld_dir('your_virtuoso_path/ppod_kg', 'PPOD_CA.ttl', '');
rdf_loader_run();
```

Where `13002` is the `isql` port in `virtuoso.ini` file.

6. (Optional) Set the endpoint url in `pangu/environment/examples/KB/PPODSparqlService.py` if you want to change the default port `3002` or use a public service.

7. Stop the Virtuoso server when you finish:

```shell
python3 virtuoso.py stop 3002
```

## Language Model Deployment

This component supports [llama.cpp](https://github.com/ggerganov/llama.cpp) to run local LLM service. Its repository provides a detailed guide on how to build and run the LLM
service. Here are the steps:

1. [Download and build llama.cpp](https://github.com/ggerganov/llama.cpp?tab=readme-ov-file#basic-usage). Note that when building, you may need to check
   the [CUDA version](https://github.com/ggerganov/llama.cpp/blob/master/docs/build.md) rather
   than [the default version without CUDA](https://github.com/ggerganov/llama.cpp/blob/master/docs/build.md#build-llamacpp-locally).
2. Download [Llama model](https://huggingface.co/meta-llama) or any other LLM that [llama.cpp supports](https://github.com/ggerganov/llama.cpp?tab=readme-ov-file#description). One
   way to download large models from HuggingFace is to use `huggingface-cli`:

```shell
pip install huggingface-hub
huggingface-cli download meta-llama/Meta-Llama-3.1-8B-Instruct
```

3. [Convert the LLM into gguf format](https://github.com/ggerganov/llama.cpp?tab=readme-ov-file#prepare-and-quantize), e.g.,

```shell
cd <your_llama_cpp_path>
python convert_hf_to_gguf.py <your_hf_model_path> --outtype <q8_0, fp16 or other type> --outfile <gguf_output_path>
```

If you use `huggingface-cli` to download the model, <your_hf_model_path> looks
like `$HF_HOME//hub/models--meta-llama--Meta-Llama-3.1-70B-Instruct/snapshots/1d54af340dc8906a2d21146191a9c184c35e47bd`.

4. Run llama.cpp server:

```shell
your_llama_cpp_path/llama-server -m <gguf_output_path> --port 8080 --n_gpu_layers 100 --thread 1 --all-logits
```

Approximation of GPU memory consumption:

- Llama 3.1 8B FP16: single GPU, 40GB
- Llama 3.1 70B Q8: at least 2x A100 / 4x A6000

## Interface

To test the text-to-query component, run the following command:

```shell
cd backend/text_to_query
python test/test_ppod_sparql.py
```

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
