/*
 * Table: __metadata__
 * Description: Database internal metadata table
 */
CREATE TABLE IF NOT EXISTS __metadata__ (
  -- Metadata key (e.g., 'schema_version', 'creation_date')
  key TEXT NOT NULL PRIMARY KEY,
  -- Associated value for the metadata key
  value TEXT NOT NULL
);

/*
 * Table: kv
 * Description: Single key-value table storing arbitrary values
 */
CREATE TABLE IF NOT EXISTS kv (
  -- UNIX insertion time (milliseconds)
  inserted_at INTEGER NOT NULL DEFAULT (CAST(unixepoch('subsec') * 1000 AS INTEGER)),
  -- Logical active flag (0 or 1)
  is_active INTEGER NOT NULL DEFAULT (1) CHECK (is_active IN (0,1)),
  -- Logical key identifier
  key TEXT NOT NULL,
  -- Arbitrary payload stored as BLOB for maximum compatibility
  value BLOB NOT NULL
);


/*
 * Initialization Data: Schema Version and Creation Date (Idempotent)
 * These records are only inserted if they do not already exist.
 */
INSERT OR IGNORE INTO __metadata__ (key, value) VALUES ('schema_version', '1.0.0');
INSERT OR IGNORE INTO __metadata__ (key, value) VALUES ('schema_tree_ish', 'git-hash-abc123');
INSERT OR IGNORE INTO __metadata__ (key, value) VALUES ('creation_date', strftime('%Y-%m-%dT%H:%M:%f', 'now'));

-- Only one active row per key
CREATE UNIQUE INDEX IF NOT EXISTS kv_active_key ON kv(key) WHERE is_active = 1;

-- Time-travel and scans
CREATE INDEX IF NOT EXISTS kv_key_time ON kv(key, inserted_at);

-- Swap-out on overwrite: retire old active row just before insert
CREATE TRIGGER IF NOT EXISTS kv_swap_active
BEFORE INSERT ON kv
FOR EACH ROW
BEGIN
  UPDATE kv SET is_active = 0
  WHERE key = NEW.key AND is_active = 1;
END;

-- Convenience view
CREATE VIEW IF NOT EXISTS kv_current AS
  SELECT key, value, inserted_at
  FROM kv
  WHERE is_active = 1;

