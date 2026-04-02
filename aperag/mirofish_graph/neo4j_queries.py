SCHEMA_QUERIES = [
    "CREATE CONSTRAINT graph_graph_id_unique IF NOT EXISTS FOR (g:Graph) REQUIRE g.graph_id IS UNIQUE",
    "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
    "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT related_to_id_unique IF NOT EXISTS FOR ()-[r:RELATED_TO]-() REQUIRE r.id IS UNIQUE",
    "CREATE INDEX entity_lookup_idx IF NOT EXISTS FOR (e:Entity) ON (e.graph_id, e.entity_type, e.normalized_name)",
    "CREATE INDEX chunk_lookup_idx IF NOT EXISTS FOR (c:Chunk) ON (c.graph_id, c.document_id, c.chunk_index)",
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
