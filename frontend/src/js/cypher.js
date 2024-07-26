export const node_properties_query = `
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "node"
WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
RETURN {labels: nodeLabels, properties: properties} AS output
`

export const rel_properties_query = `
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE NOT type = "RELATIONSHIP" AND elementType = "relationship"
WITH label AS nodeLabels, collect({property:property, type:type}) AS properties
RETURN {type: nodeLabels, properties: properties} AS output
`


export const rel_query = `
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE type = "RELATIONSHIP" AND elementType = "node"
RETURN "(:" + label + ")-[:" + property + "]->(:" + toString(other[0]) + ")" AS output
`

export function search_by_keyword(keyword){
    return `
    match (n)
    where apoc.text.fuzzyMatch(toLower(n.name), toLower('${keyword.value}'))
    return ID(n) as id, labels(n) as label, properties(n) as property
    `
} 

export const query_ontology_rel = `
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE type="RELATIONSHIP" and elementType="relationship"
RETURN label as label, property as source, other[0] as target
`

export const query_ontology_node = `
CALL apoc.meta.data()
YIELD label, other, elementType, type, property
WHERE elementType = "node" and type="STRING" and label<>"_GraphConfig"
RETURN label as entity,  property as properties
`

export function filter_by_edge(n_type){
    return `
    match (n)-[p: ${n_type}]->(m)
    return ID(n) as source_id, labels(n) as source_label, properties(n) as source_property, 
    ID(p) as edge_id, ID(m) as target_id, labels(m) as target_label, properties(m) as target_property
    `
}

export function filter_by_node(n_type){
    return `
    match (n: ${n_type})
    return ID(n) as id, labels(n) as label, properties(n) as property
    `
}