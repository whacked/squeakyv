{
  '$schema': 'http://json-schema.org/draft-07/schema#',
  title: 'Database Schema',
  type: 'object',
  properties: {
    kv: {
      description: 'Single key-value table storing arbitrary values',
      type: 'array',
      items: {
        '$ref': '#/$defs/KVEntry',
      },
    },
    __metadata__: {
      description: 'Database internal metadata table',
      type: 'array',
      items: {
        '$ref': '#/$defs/MetadataEntry',
      },
    },
  },
  '$defs': {
    KVEntry: {
      type: 'object',
      description: 'Key-value entry',
      properties: {
        key: {
          type: 'string',
          description: 'Logical key identifier',
          maxLength: 255,
        },
        value: {
          description: 'Arbitrary payload stored as BLOB for maximum compatibility',
          'sqlite:type': 'BLOB',
        },
        inserted_at: {
          type: 'integer',
          description: 'UNIX insertion time (milliseconds)',
          'sqlite:default': "CAST(unixepoch('subsec') * 1000 AS INTEGER)",
        },
        is_active: {
          type: 'integer',
          description: 'Logical active flag (0 or 1)',
          'sqlite:default': '1',
          'sqlite:check': 'is_active IN (0,1)',
        },
      },
      required: ['key', 'value', 'inserted_at', 'is_active'],
    },
    MetadataEntry: {
      type: 'object',
      description: 'Stores internal library metadata (e.g., schema version)',
      properties: {
        key: {
          type: 'string',
          description: "Metadata key (e.g., 'schema_version', 'creation_date')",
          maxLength: 64,
          'sqlite:primaryKey': true,
        },
        value: {
          type: 'string',
          description: 'Associated value for the metadata key',
          maxLength: 255,
        },
      },
      required: ['key', 'value'],
    },
  },
}
