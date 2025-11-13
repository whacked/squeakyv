;;; squeakyv-test.el --- Tests for squeakyv -*- lexical-binding: t -*-

;;; Commentary:
;; ERT tests for squeakyv SQLite cache library

;;; Code:

(require 'ert)
(require 'sqlite)
(require 'squeakyv)

(ert-deftest squeakyv-test-init-db ()
  "Test database initialization."
  (let ((db (sqlite-open)))
    (should-not (squeakyv-init-db db))
    (sqlite-close db)))

(ert-deftest squeakyv-test-set-and-get ()
  "Test setting and getting a value."
  (let ((db (sqlite-open)))
    (squeakyv-init-db db)

    ;; Set a value
    (squeakyv-set-value db "testkey" "testvalue")

    ;; Get the value
    (let ((result (squeakyv-get-current-value db "testkey")))
      (should (equal result "testvalue")))

    (sqlite-close db)))

(ert-deftest squeakyv-test-get-nonexistent ()
  "Test getting a nonexistent key returns nil."
  (let ((db (sqlite-open)))
    (squeakyv-init-db db)

    (let ((result (squeakyv-get-current-value db "nonexistent")))
      (should (null result)))

    (sqlite-close db)))

(ert-deftest squeakyv-test-update ()
  "Test updating a value creates new version."
  (let ((db (sqlite-open)))
    (squeakyv-init-db db)

    ;; Set initial value
    (squeakyv-set-value db "key" "value1")

    ;; Update value
    (squeakyv-set-value db "key" "value2")

    ;; Verify updated value
    (let ((result (squeakyv-get-current-value db "key")))
      (should (equal result "value2")))

    (sqlite-close db)))

(ert-deftest squeakyv-test-delete ()
  "Test deleting a key."
  (let ((db (sqlite-open)))
    (squeakyv-init-db db)

    ;; Set a value
    (squeakyv-set-value db "key" "value")

    ;; Delete it
    (squeakyv-delete-key db "key")

    ;; Verify it's gone
    (let ((result (squeakyv-get-current-value db "key")))
      (should (null result)))

    (sqlite-close db)))

(ert-deftest squeakyv-test-list-keys ()
  "Test listing active keys."
  (let ((db (sqlite-open)))
    (squeakyv-init-db db)

    ;; Set multiple values
    (squeakyv-set-value db "key1" "value1")
    (squeakyv-set-value db "key2" "value2")
    (squeakyv-set-value db "key3" "value3")

    ;; List keys
    (let ((keys (squeakyv-list-active-keys db)))
      (should (= (length keys) 3))
      (should (member "key1" keys))
      (should (member "key2" keys))
      (should (member "key3" keys)))

    (sqlite-close db)))

(ert-deftest squeakyv-test-list-after-delete ()
  "Test listing keys after deletion."
  (let ((db (sqlite-open)))
    (squeakyv-init-db db)

    ;; Set multiple values
    (squeakyv-set-value db "key1" "value1")
    (squeakyv-set-value db "key2" "value2")
    (squeakyv-set-value db "key3" "value3")

    ;; Delete one
    (squeakyv-delete-key db "key2")

    ;; List keys
    (let ((keys (squeakyv-list-active-keys db)))
      (should (= (length keys) 2))
      (should (member "key1" keys))
      (should-not (member "key2" keys))
      (should (member "key3" keys)))

    (sqlite-close db)))

(ert-deftest squeakyv-test-persistence ()
  "Test persistent database file."
  (let* ((temp-file (make-temp-file "squeakyv-test" nil ".db"))
         (db1 (sqlite-open temp-file)))
    (unwind-protect
        (progn
          ;; Create and populate database
          (squeakyv-init-db db1)
          (squeakyv-set-value db1 "persist-key" "persist-value")
          (sqlite-close db1)

          ;; Reopen and verify
          (let ((db2 (sqlite-open temp-file)))
            (let ((result (squeakyv-get-current-value db2 "persist-key")))
              (should (equal result "persist-value")))
            (sqlite-close db2)))

      ;; Cleanup
      (when (file-exists-p temp-file)
        (delete-file temp-file)))))

(ert-deftest squeakyv-test-empty-value ()
  "Test storing empty string."
  (let ((db (sqlite-open)))
    (squeakyv-init-db db)

    (squeakyv-set-value db "empty" "")

    (let ((result (squeakyv-get-current-value db "empty")))
      (should (equal result "")))

    (sqlite-close db)))

(ert-deftest squeakyv-test-unicode ()
  "Test storing unicode strings."
  (let ((db (sqlite-open)))
    (squeakyv-init-db db)

    (squeakyv-set-value db "unicode" "Hello 世界 🎉")

    (let ((result (squeakyv-get-current-value db "unicode")))
      (should (equal result "Hello 世界 🎉")))

    (sqlite-close db)))

;;; squeakyv-test.el ends here
