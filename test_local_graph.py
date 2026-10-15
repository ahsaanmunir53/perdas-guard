from google.cloud import spanner

client = spanner.Client(project="pardes-guard-local")
database = client.instance(
    "pardes-local-instance"
).database("pardes-local-db")

with database.snapshot() as snapshot:
    rows = list(snapshot.execute_sql(
        "GRAPH IntegrityGraph "
        "MATCH (r:Recruiters) "
        "RETURN COUNT(r.rkey) AS recruiter_count"
    ))

print("Graph query result:", rows)
print("Local Spanner Graph query test passed.")
