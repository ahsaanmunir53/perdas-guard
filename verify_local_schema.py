from google.cloud import spanner

client = spanner.Client(project="pardes-guard-local")
database = client.instance(
    "pardes-local-instance"
).database("pardes-local-db")

with database.snapshot() as snapshot:
    rows = snapshot.execute_sql(
        "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES "
        "WHERE TABLE_SCHEMA = '' ORDER BY TABLE_NAME"
    )
    tables = [row[0] for row in rows]

print("Tables found:", len(tables))
for table in tables:
    print(" -", table)
