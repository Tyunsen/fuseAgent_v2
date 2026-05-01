MIROFISH_CREATION_MODE = "mirofish_simple"
LEGACY_CREATION_MODE = "aperag_advanced"

MIROFISH_GRAPH_ENGINE = "mirofish"
LEGACY_GRAPH_ENGINE = "lightrag"

GRAPH_STATUS_WAITING_FOR_DOCUMENTS = "waiting_for_documents"
GRAPH_STATUS_BUILDING = "building"
GRAPH_STATUS_UPDATING = "updating"
GRAPH_STATUS_READY = "ready"
GRAPH_STATUS_FAILED = "failed"

MIROFISH_ONTOLOGY_ENTITY_CAP = 16
MIROFISH_ONTOLOGY_EDGE_CAP = 16

TRACE_ATTRIBUTE_FIELDS = (
    {"name": "time", "type": "text", "description": "Exact time or period when explicitly stated"},
    {"name": "time_start", "type": "text", "description": "Normalized start time when a range is stated"},
    {"name": "time_end", "type": "text", "description": "Normalized end time when a range is stated"},
    {"name": "time_label", "type": "text", "description": "Human-readable time label from the source"},
    {"name": "place", "type": "text", "description": "Original place wording from the source"},
    {"name": "place_normalized", "type": "text", "description": "Normalized place name when available"},
    {"name": "place_aliases", "type": "list[text]", "description": "Alternative place names from the source"},
)

BASE_ENTITY_TYPES = [
    {
        "name": "Person",
        "display_name": "Person",
        "description": "An individual person, leader, expert, or named actor.",
        "attributes": [
            {"name": "role", "type": "text", "description": "Primary role or title"},
            *TRACE_ATTRIBUTE_FIELDS,
        ],
        "examples": ["Commander", "Analyst"],
    },
    {
        "name": "Organization",
        "display_name": "Organization",
        "description": "A formal group, unit, institution, company, or agency.",
        "attributes": [
            {"name": "org_type", "type": "text", "description": "Organization category"},
            *TRACE_ATTRIBUTE_FIELDS,
        ],
        "examples": ["Agency", "Task Force"],
    },
    {
        "name": "Location",
        "display_name": "Location",
        "description": "A named place, region, site, or geographic area.",
        "attributes": [
            {"name": "location_type", "type": "text", "description": "Location category"},
            *TRACE_ATTRIBUTE_FIELDS,
        ],
        "examples": ["Abu Dhabi", "Port", "Airbase"],
    },
    {
        "name": "Facility",
        "display_name": "Facility",
        "description": "A named installation, base, building, or infrastructure site.",
        "attributes": [
            {"name": "facility_type", "type": "text", "description": "Facility category"},
            *TRACE_ATTRIBUTE_FIELDS,
        ],
        "examples": ["Command Center", "Airport"],
    },
    {
        "name": "Asset",
        "display_name": "Asset",
        "description": "A named platform, equipment item, system, or tangible resource.",
        "attributes": [
            {"name": "asset_type", "type": "text", "description": "Asset category"},
            *TRACE_ATTRIBUTE_FIELDS,
        ],
        "examples": ["Drone", "Radar", "Vessel"],
    },
    {
        "name": "Activity",
        "display_name": "Activity",
        "description": "A named operation, action, mission, exercise, or other meaningful activity.",
        "attributes": [
            {"name": "activity_type", "type": "text", "description": "Activity category"},
            *TRACE_ATTRIBUTE_FIELDS,
        ],
        "examples": ["Exercise", "Deployment", "Inspection"],
    },
    {
        "name": "Document",
        "display_name": "Document",
        "description": "A named report, directive, agreement, or publication.",
        "attributes": [
            {"name": "document_type", "type": "text", "description": "Document category"},
            *TRACE_ATTRIBUTE_FIELDS,
        ],
        "examples": ["Report", "Directive"],
    },
    {
        "name": "Topic",
        "display_name": "Topic",
        "description": "A named concept, issue, theme, or subject discussed in the source.",
        "attributes": [
            {"name": "topic_scope", "type": "text", "description": "Topic scope or area"},
            *TRACE_ATTRIBUTE_FIELDS,
        ],
        "examples": ["Energy Security", "Air Defense"],
    },
]

BASE_EDGE_TYPES = [
    {
        "name": "RELATED_TO",
        "display_name": "Related To",
        "description": "A broad factual association between two entities.",
        "source_targets": [],
        "attributes": list(TRACE_ATTRIBUTE_FIELDS),
    },
    {
        "name": "LOCATED_IN",
        "display_name": "Located In",
        "description": "An entity is based in, present in, or associated with a place.",
        "source_targets": [],
        "attributes": list(TRACE_ATTRIBUTE_FIELDS),
    },
    {
        "name": "PART_OF",
        "display_name": "Part Of",
        "description": "An entity belongs to or forms part of a larger entity.",
        "source_targets": [],
        "attributes": list(TRACE_ATTRIBUTE_FIELDS),
    },
    {
        "name": "PARTICIPATES_IN",
        "display_name": "Participates In",
        "description": "A person, organization, or asset takes part in an activity.",
        "source_targets": [],
        "attributes": list(TRACE_ATTRIBUTE_FIELDS),
    },
    {
        "name": "OCCURS_IN",
        "display_name": "Occurs In",
        "description": "An activity or topic takes place in a time period or location context.",
        "source_targets": [],
        "attributes": list(TRACE_ATTRIBUTE_FIELDS),
    },
    {
        "name": "SUPPORTS",
        "display_name": "Supports",
        "description": "An entity provides support, enablement, or backing to another entity.",
        "source_targets": [],
        "attributes": list(TRACE_ATTRIBUTE_FIELDS),
    },
    {
        "name": "USES",
        "display_name": "Uses",
        "description": "An entity uses, employs, or relies on another entity.",
        "source_targets": [],
        "attributes": list(TRACE_ATTRIBUTE_FIELDS),
    },
    {
        "name": "BELONGS_TO",
        "display_name": "Belongs To",
        "description": "An asset, facility, or document belongs to an owning entity.",
        "source_targets": [],
        "attributes": list(TRACE_ATTRIBUTE_FIELDS),
    },
]
