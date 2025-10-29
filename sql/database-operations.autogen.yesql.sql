

-- ====================================================================
-- Auto-generated Key-Value Access Queries (Single Table with Active Flag)
-- Table: kv
-- ====================================================================

-- name: get-current-value(key)^
-- Retrieves the current active value for a key
SELECT value -- , inserted_at
FROM kv
WHERE key = :key AND is_active = 1;

-- name: set-value(key, value)!
-- Sets a new value for a key (trigger handles deactivating old values)
INSERT INTO kv (key, value)
VALUES (:key, :value);

-- name: delete-key(key)!
-- Soft deletes a key by setting is_active = 0
UPDATE kv
SET is_active = 0
WHERE key = :key AND is_active = 1;

-- name: list-active-keys()
-- Lists all currently active keys
SELECT key -- , inserted_at
FROM kv
WHERE is_active = 1
ORDER BY inserted_at DESC;
