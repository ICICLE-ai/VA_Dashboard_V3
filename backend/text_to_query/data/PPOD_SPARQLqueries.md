1. Which non-profit organizations work on water quality in Yolo or Solano counties?

```
SELECT DISTINCT ?node_variable_1 where
{VALUES ?county { <http://www.wikidata.org/entity/Q109709> <http://www.wikidata.org/entity/Q108083> }
?node_variable_1 rdf:type foaf:Organization ;
                   <http://www.w3.org/ns/org#classification> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#oty_cf5070> ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#inCounty> ?county  ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#FSI_000239> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/sustsourceindiv.rdf#CI0303> . }
```
===> Returns 8 results.

2. Who are the directors of organizations that work on fragmentation in the Great Valley ecoregion?

```
select ?node_variable_1 ?node_variable_2 ?node_variable_3 where
{ ?node_variable_1 rdf:type foaf:Organization ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#inEcoregion> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#eco_7dfa16> ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#FSI_000239> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/sustsourceindiv.rdf#CI0167> .
  ?node_variable_2 rdf:type foaf:Person .
  ?node_variable_3 rdf:type <http://purl.obolibrary.org/obo/BFO_0000023> ;
                   <http://purl.obolibrary.org/obo/RO_0000057> ?node_variable_2 ;
                   <http://purl.obolibrary.org/obo/RO_0000081> ?node_variable_1 ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#positionType> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#positiontypedict_e7e6b1> . }
```

===> No Results.

Let's take out the is a Director clause. I.e. "Who are people in organizations that work on fragmentation in the Great Valley ecoregion?"

```
select ?node_variable_1 ?node_variable_2 ?node_variable_3 where
{ ?node_variable_1 rdf:type foaf:Organization ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#inEcoregion> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#eco_7dfa16> ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#FSI_000239> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/sustsourceindiv.rdf#CI0167> .
  ?node_variable_2 rdf:type foaf:Person .
  ?node_variable_3 rdf:type <http://purl.obolibrary.org/obo/BFO_0000023> ;
                   <http://purl.obolibrary.org/obo/RO_0000057> ?node_variable_2 ;
                   <http://purl.obolibrary.org/obo/RO_0000081> ?node_variable_1 . }
```
===> Lots of people returned.

or we could ask: Who are the owners of organizations that work on fragmentation in the Great Valley ecoregion?

```
select ?node_variable_1 ?node_variable_2 ?node_variable_3 where
{ ?node_variable_1 rdf:type foaf:Organization ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#inEcoregion> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#eco_7dfa16> ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#FSI_000239> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/sustsourceindiv.rdf#CI0167> .
  ?node_variable_2 rdf:type foaf:Person .
  ?node_variable_3 rdf:type <http://purl.obolibrary.org/obo/BFO_0000023> ;
                   <http://purl.obolibrary.org/obo/RO_0000057> ?node_variable_2 ;
                   <http://purl.obolibrary.org/obo/RO_0000081> ?node_variable_1 ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#positionType> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#positiontypedict_ea1c97> . }

limit 32
```
===> one result: Lobata Group with owner Patrick Huber


3. What programs provide funding for dealing with wildfire issues?

```
select ?node_variable_1 ?node_variable_2 where
{ ?node_variable_2 rdf:type <http://vivoweb.org/ontology/core#Project> ;
                   <http://vivoweb.org/ontology/core#hasFundingVehicle> ?node_variable_1 ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#FSI_000239> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/sustsourceindiv.rdf#CI0320> .
  ?node_variable_1 rdf:type <http://vivoweb.org/ontology/core#Program> . }
```

==> returns 14 combinations of programs and projects. There is no direct information about the characteristics of the funding provided by programs, so we're looking at the projects for information.


4. What wetlands-focused projects are there in the Central Coast or Southern Coast ecoregions?

```
select ?node_variable_1 where
{ 
VALUES ?ecoregion {<https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#eco_ac7474> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/CA_PPODterms.ttl#eco_824b01> }
?node_variable_1 rdf:type <http://vivoweb.org/ontology/core#Project> ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#inEcoregion> ?ecoregion ;
                   <https://raw.githubusercontent.com/adhollander/FSLschemas/main/fsisupp.owl#FSI_000239> <https://raw.githubusercontent.com/adhollander/FSLschemas/main/sustsourceindiv.rdf#CI0309> . }
```

===> returns 16 results.
