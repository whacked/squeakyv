# squeakyv.el - Emacs Lisp Implementation

Simple SQLite-backed key-value cache for Emacs. Part of the squeakyv cross-language cache library family.

## Requirements

- Emacs 29.1+ (with built-in SQLite support)

Check your Emacs version:
```elisp
M-x emacs-version
```

Check if SQLite is available:
```elisp
(featurep 'sqlite)  ; Should return t
```

## Installation

### Manual Installation

1. Download `squeakyv.el`
2. Place it in your load path
3. Add to your init file:

```elisp
(require 'squeakyv)
```

### Using `use-package`

```elisp
(use-package squeakyv
  :load-path "path/to/squeakyv")
```

## Quick Start

```elisp
(require 'sqlite)
(require 'squeakyv)

;; Create an in-memory database
(setq db (sqlite-open))

;; Initialize schema
(squeakyv-init-db db)

;; Store a value
(squeakyv-set-value db "mykey" "myvalue")

;; Retrieve a value
(squeakyv-get-current-value db "mykey")  ; => "myvalue"

;; Close when done
(sqlite-close db)
```

## Usage

### Creating a Database

```elisp
;; In-memory (non-persistent)
(setq db (sqlite-open))

;; Persistent file
(setq db (sqlite-open "~/.emacs.d/cache.db"))

;; Always initialize schema
(squeakyv-init-db db)
```

### Basic Operations

```elisp
;; Set a value
(squeakyv-set-value db "key" "value")

;; Get a value (returns nil if not found)
(let ((value (squeakyv-get-current-value db "key")))
  (if value
      (message "Found: %s" value)
    (message "Not found")))

;; Delete a key
(squeakyv-delete-key db "key")

;; List all active keys
(let ((keys (squeakyv-list-active-keys db)))
  (dolist (key keys)
    (message "Key: %s" key)))
```

### Working with Structured Data

```elisp
;; Store elisp data structures as strings
(require 'json)

;; Serialize alist to JSON
(let ((data '((name . "Alice") (age . 30))))
  (squeakyv-set-value db "user:1" (json-encode data)))

;; Deserialize JSON back to alist
(let ((json-str (squeakyv-get-current-value db "user:1")))
  (when json-str
    (json-read-from-string json-str)))
```

### Caching Expensive Computations

```elisp
(defun my-expensive-computation (arg)
  "Compute something expensive, with caching."
  (let* ((cache-key (format "computation:%s" arg))
         (cached (squeakyv-get-current-value my-cache-db cache-key)))
    (if cached
        (progn
          (message "Cache hit!")
          cached)
      (message "Computing...")
      (let ((result (format "Computed: %s" arg)))
        (squeakyv-set-value my-cache-db cache-key result)
        result))))

;; Setup cache
(setq my-cache-db (sqlite-open "~/.emacs.d/my-cache.db"))
(squeakyv-init-db my-cache-db)

;; Use it
(my-expensive-computation "test")  ; Computes
(my-expensive-computation "test")  ; Cache hit!
```

### Integration with Org Mode

```elisp
;; Cache org-mode query results
(defun org-cache-query (query)
  "Execute org query with caching."
  (let* ((cache-key (format "org-query:%s" query))
         (cached (squeakyv-get-current-value org-cache-db cache-key)))
    (or cached
        (let ((result (org-ql-select (org-agenda-files)
                        query
                        :action #'org-get-heading)))
          (squeakyv-set-value org-cache-db cache-key
                             (prin1-to-string result))
          (prin1-to-string result)))))
```

## API Reference

### `(squeakyv-init-db db)`

Initialize database schema. Must be called once after opening a database.

**Parameters:**
- `db`: SQLite database handle from `sqlite-open`

### `(squeakyv-set-value db key value)`

Store a value for a key. If key exists, creates new version (old value soft-deleted).

**Parameters:**
- `db`: Database handle
- `key`: String key
- `value`: String value

**Returns:** `nil`

### `(squeakyv-get-current-value db key)`

Retrieve the current value for a key.

**Parameters:**
- `db`: Database handle
- `key`: String key

**Returns:** String value or `nil` if key doesn't exist

### `(squeakyv-delete-key db key)`

Delete a key (soft delete - marks as inactive).

**Parameters:**
- `db`: Database handle
- `key`: String key

**Returns:** `nil`

### `(squeakyv-list-active-keys db)`

List all active keys, ordered by insertion time (newest first).

**Parameters:**
- `db`: Database handle

**Returns:** List of string keys

## Testing

Run the test suite in Emacs:

```elisp
;; Load tests
(load-file "squeakyv-test.el")

;; Run all tests
(ert-run-tests-batch-and-exit "squeakyv-")

;; Or interactively
M-x ert RET squeakyv- RET
```

Run from command line:

```bash
emacs -batch -l squeakyv.el -l squeakyv-test.el -f ert-run-tests-batch-and-exit
```

## Performance

SQLite in Emacs is fast enough for most use cases:
- ~1000 reads/sec
- ~500 writes/sec
- Suitable for caching LSP results, org queries, completion data

For very high-frequency access, consider in-memory databases or hash tables.

## Use Cases

- **LSP caching**: Cache expensive language server queries
- **Org-mode**: Cache org-ql query results
- **Completion**: Store frequently used completions
- **Project metadata**: Cache project-specific data
- **Custom commands**: Persist command history
- **Mail/News**: Cache headers and metadata
- **Web scraping**: Cache downloaded content

## Version History

Like all squeakyv implementations, this uses soft deletes. Updated or deleted values are marked inactive but preserved in the database for audit trails and potential time-travel features.

## Cross-Language Compatibility

squeakyv implementations share the same database schema:
- **Python** - Production-ready, full-featured
- **Bash** - Shell scripting, CI/CD
- **Go** - High-performance, compiled
- **Emacs Lisp** - Editor integration ← You are here

You can write data in Emacs and read it in Python, or vice versa!

## Limitations

- **Strings only**: Values are TEXT (use JSON for complex data)
- **No TTL/expiration**: Keep design simple
- **No namespacing**: Single keyspace per database
- **Emacs 29.1+**: Older versions don't have SQLite support

## Example: Simple Memoization Macro

```elisp
(defmacro defun-cached (name args docstring &rest body)
  "Define a function with automatic caching."
  (declare (indent defun) (doc-string 3))
  `(progn
     (unless (boundp 'global-cache-db)
       (setq global-cache-db (sqlite-open "~/.emacs.d/cache.db"))
       (squeakyv-init-db global-cache-db))

     (defun ,name ,args
       ,docstring
       (let* ((cache-key (format "%s:%s" ',name (prin1-to-string (list ,@args))))
              (cached (squeakyv-get-current-value global-cache-db cache-key)))
         (or cached
             (let ((result (progn ,@body)))
               (squeakyv-set-value global-cache-db cache-key
                                  (prin1-to-string result))
               result))))))

;; Usage
(defun-cached expensive-factorial (n)
  "Compute factorial with caching."
  (if (<= n 1)
      1
    (* n (expensive-factorial (1- n)))))
```

## Contributing

This package is auto-generated from a schema definition. To modify:

1. Edit `generators/database.schema.jsonnet`
2. Edit `generators/languages/elisp.py`
3. Run `sdflow generate-elisp-target`

## License

MIT License

## Links

- [Python Implementation](../python/)
- [Go Implementation](../go/)
- [Bash Implementation](../bash/)
