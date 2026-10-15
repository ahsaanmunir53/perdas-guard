from google.cloud import spanner

client = spanner.Client(project="pardes-guard-local")
instance = client.instance("pardes-local-instance")
database_id = "pardes-local-db"

database = instance.database(database_id)

if not database.exists():
    operation = instance.database(
        database_id,
        ddl_statements=[],
    ).create()
    operation.result(timeout=120)

print("Local Spanner database ready:", database_id)
