# sqeakyv

super simple kv store for caching

# why?

- sqlite is the obvious choice for small-scale disk-based caching
- you want it to be _extremely_ simple, i.e. we can work directly with the db from the sqlite repl
- if it's so simple, we can easily make clients for multiple different languages and keep the same semantics

so we define the database, and codegen the clients

# development

the clients are mostly AI-generated, but are yoked to a curated core interaction definition.

the build flow is defined in [[./Sdflow.yaml]] and generally follows the steps of:
- update json schema template (jsonnet)
- generate json schemas
- generate DDL and YesQL, which is the interaction core
- generate clients from YesQL

the ground truth of squeakyv's specification is the YesQL and basically only defines CRUD.

all extended operations are left to individual languages and downstream clients; if they are repeatable, we may add them to codegen scripts, but there are no guarantees outside of the YesQL.
