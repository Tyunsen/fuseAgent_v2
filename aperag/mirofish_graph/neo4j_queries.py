SCHEMA_QUERIES = [
    "CREATE CONSTRAINT graph_graph_id_unique IF NOT EXISTS FOR (g:Graph) REQUIRE g.graph_id IS UNIQUE",
    "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
    "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT related_to_id_unique IF NOT EXISTS FOR ()-[r:RELATED_TO]-() REQUIRE r.id IS UNIQUE",
    "CREATE INDEX entity_lookup_idx IF NOT EXISTS FOR (e:Entity) ON (e.graph_id, e.entity_type, e.normalized_name)",
    "CREATE INDEX chunk_lookup_idx IF NOT EXISTS FOR (c:Chunk) ON (c.graph_id, c.document_id, c.chunk_index)",
    "CREATE INDEX entity_graph_id_idx IF NOT EXISTS FOR (e:Entity) ON (e.graph_id)",
]

UPSERT_GRAPH_QUERY = """
MERGE (g:Graph {graph_id: $graph_id})
ON CREATE SET g.created_at = $now
SET
    g.project_id = $project_id,
    g.name = $name,
    g.description = $description,
    g.ontology_json = $ontology_json,
    g.updated_at = $now
RETURN g.graph_id AS graph_id
"""

UPSERT_DOCUMENT_QUERY = """
MATCH (g:Graph {graph_id: $graph_id})
MERGE (d:Document {id: $id})
ON CREATE SET d.created_at = $now
SET
    d.graph_id = $graph_id,
    d.project_id = $project_id,
    d.filename = $filename,
    d.display_name = $display_name,
    d.content_checksum = $content_checksum,
    d.updated_at = $now
MERGE (g)-[:HAS_DOCUMENT]->(d)
RETURN d.id AS id
"""

UPSERT_CHUNK_QUERY = """
MATCH (g:Graph {graph_id: $graph_id})
MATCH (d:Document {id: $document_id})
MERGE (c:Chunk {id: $id})
ON CREATE SET c.created_at = $now
SET
    c.graph_id = $graph_id,
    c.project_id = $project_id,
    c.document_id = $document_id,
    c.chunk_index = $chunk_index,
    c.content = $content,
    c.content_checksum = $content_checksum,
    c.updated_at = $now
MERGE (g)-[:HAS_CHUNK]->(c)
MERGE (d)-[:HAS_CHUNK]->(c)
RETURN c.id AS id
"""

UPSERT_ENTITY_QUERY = """
MATCH (g:Graph {graph_id: $graph_id})
MATCH (c:Chunk {id: $chunk_id})
MERGE (e:Entity {id: $id})
ON CREATE SET e.created_at = $now
SET
    e.graph_id = $graph_id,
    e.project_id = $project_id,
    e.name = $name,
    e.entity_type = $entity_type,
    e.normalized_name = $normalized_name,
    e.aliases = CASE
        WHEN e.aliases IS NULL THEN $aliases
        ELSE reduce(acc = e.aliases, alias IN $aliases |
            CASE WHEN alias IN acc THEN acc ELSE acc + [alias] END
        )
    END,
    e.normalized_aliases = CASE
        WHEN e.normalized_aliases IS NULL THEN $normalized_aliases
        ELSE reduce(acc = e.normalized_aliases, alias IN $normalized_aliases |
            CASE WHEN alias IN acc THEN acc ELSE acc + [alias] END
        )
    END,
    e.summary = CASE
        WHEN coalesce(e.summary, '') = '' THEN $summary
        WHEN $summary IS NULL OR trim($summary) = '' THEN e.summary
        ELSE e.summary
    END,
    e.attributes_json = $attributes_json,
    e.updated_at = $now
MERGE (g)-[:HAS_ENTITY]->(e)
MERGE (c)-[:MENTIONS]->(e)
RETURN e.id AS id
"""

FIND_ENTITY_BY_ALIASES_QUERY = """
MATCH (e:Entity {graph_id: $graph_id, entity_type: $entity_type})
WHERE e.normalized_name IN $normalized_aliases
   OR any(alias IN coalesce(e.normalized_aliases, []) WHERE alias IN $normalized_aliases)
RETURN
    e.id AS id,
    e.name AS name,
    coalesce(e.aliases, []) AS aliases
LIMIT 1
"""

UPSERT_RELATION_QUERY = """
MATCH (source:Entity {id: $source_id})
MATCH (target:Entity {id: $target_id})
MERGE (source)-[r:RELATED_TO {id: $id}]->(target)
ON CREATE SET r.created_at = $now
SET
    r.graph_id = $graph_id,
    r.project_id = $project_id,
    r.name = $name,
    r.fact_type = $fact_type,
    r.fact = $fact,
    r.evidence = $evidence,
    r.confidence = $confidence,
    r.attributes_json = $attributes_json,
    r.source_chunk_id = $source_chunk_id,
    r.updated_at = $now
RETURN r.id AS id
"""

DELETE_GRAPH_QUERY = """
MATCH (n {graph_id: $graph_id})
DETACH DELETE n
"""

GRAPH_NODES_QUERY = """
MATCH (c:Chunk {graph_id: $graph_id})-[:MENTIONS]->(e:Entity {graph_id: $graph_id})
RETURN e, collect(DISTINCT c.id) AS chunk_ids
ORDER BY e.name ASC
"""

GRAPH_RELATIONS_QUERY = """
MATCH (source:Entity {graph_id: $graph_id})-[r:RELATED_TO {graph_id: $graph_id}]->(target:Entity {graph_id: $graph_id})
RETURN source, target, r
ORDER BY source.name ASC, target.name ASC, r.name ASC
"""

GRAPH_CHUNKS_QUERY = """
MATCH (d:Document {graph_id: $graph_id})-[:HAS_CHUNK]->(c:Chunk {graph_id: $graph_id})
RETURN d, c
ORDER BY d.display_name ASC, c.chunk_index ASC
"""

GRAPH_METADATA_QUERY = """
MATCH (g:Graph {graph_id: $graph_id})
RETURN
    g.graph_id AS graph_id,
    g.project_id AS project_id,
    g.name AS name,
    g.description AS description,
    g.ontology_json AS ontology_json
LIMIT 1
"""

GRAPH_DOCUMENTS_QUERY = """
MATCH (d:Document {graph_id: $graph_id})
RETURN
    d.id AS id,
    d.filename AS filename,
    d.display_name AS display_name,
    d.content_checksum AS content_checksum,
    d.updated_at AS updated_at
ORDER BY coalesce(d.display_name, d.filename, '') ASC
"""

GRAPH_COUNTS_QUERY = """
OPTIONAL MATCH (e:Entity {graph_id: $graph_id})
WITH count(e) AS node_count
OPTIONAL MATCH ()-[r:RELATED_TO {graph_id: $graph_id}]->()
WITH node_count, count(r) AS edge_count
OPTIONAL MATCH (c:Chunk {graph_id: $graph_id})
RETURN node_count, edge_count, count(c) AS chunk_count
"""

BULK_LOAD_ENTITIES_QUERY = """
MATCH (e:Entity {graph_id: $graph_id})
RETURN
    e.id AS id,
    e.name AS name,
    e.entity_type AS entity_type,
    e.normalized_name AS normalized_name,
    coalesce(e.aliases, []) AS aliases,
    coalesce(e.normalized_aliases, []) AS normalized_aliases
"""

BATCH_UPSERT_CHUNKS_QUERY = """
UNWIND $batch AS item
MATCH (g:Graph {graph_id: item.graph_id})
MATCH (d:Document {id: item.document_id})
MERGE (c:Chunk {id: item.id})
ON CREATE SET c.created_at = item.now
SET
    c.graph_id = item.graph_id,
    c.project_id = item.project_id,
    c.document_id = item.document_id,
    c.chunk_index = item.chunk_index,
    c.content = item.content,
    c.content_checksum = item.content_checksum,
    c.updated_at = item.now
MERGE (g)-[:HAS_CHUNK]->(c)
MERGE (d)-[:HAS_CHUNK]->(c)
RETURN c.id AS id
"""

BATCH_UPSERT_ENTITIES_QUERY = """
UNWIND $batch AS item
MATCH (g:Graph {graph_id: item.graph_id})
MATCH (c:Chunk {id: item.chunk_id})
MERGE (e:Entity {id: item.id})
ON CREATE SET e.created_at = item.now
SET
    e.graph_id = item.graph_id,
    e.project_id = item.project_id,
    e.name = item.name,
    e.entity_type = item.entity_type,
    e.normalized_name = item.normalized_name,
    e.aliases = CASE
        WHEN e.aliases IS NULL THEN item.aliases
        ELSE reduce(acc = e.aliases, alias IN item.aliases |
            CASE WHEN alias IN acc THEN acc ELSE acc + [alias] END
        )
    END,
    e.normalized_aliases = CASE
        WHEN e.normalized_aliases IS NULL THEN item.normalized_aliases
        ELSE reduce(acc = e.normalized_aliases, alias IN item.normalized_aliases |
            CASE WHEN alias IN acc THEN acc ELSE acc + [alias] END
        )
    END,
    e.summary = CASE
        WHEN coalesce(e.summary, '') = '' THEN item.summary
        WHEN item.summary IS NULL OR trim(item.summary) = '' THEN e.summary
        ELSE e.summary
    END,
    e.attributes_json = item.attributes_json,
    e.updated_at = item.now
MERGE (g)-[:HAS_ENTITY]->(e)
MERGE (c)-[:MENTIONS]->(e)
RETURN e.id AS id
"""

BATCH_UPSERT_RELATIONS_QUERY = """
UNWIND $batch AS item
MATCH (source:Entity {id: item.source_id})
MATCH (target:Entity {id: item.target_id})
MERGE (source)-[r:RELATED_TO {id: item.id}]->(target)
ON CREATE SET r.created_at = item.now
SET
    r.graph_id = item.graph_id,
    r.project_id = item.project_id,
    r.name = item.name,
    r.fact_type = item.fact_type,
    r.fact = item.fact,
    r.evidence = item.evidence,
    r.confidence = item.confidence,
    r.attributes_json = item.attributes_json,
    r.source_chunk_id = item.source_chunk_id,
    r.updated_at = item.now
RETURN r.id AS id
"""
