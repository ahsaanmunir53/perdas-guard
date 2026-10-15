from google.cloud import spanner

client = spanner.Client(project="pardes-guard-local")
database = client.instance(
    "pardes-local-instance"
).database("pardes-local-db")

test_key = "local-test-recruiter-001"

def write_test_data(transaction):
    transaction.insert_or_update(
        "Recruiters",
        columns=("rkey", "label"),
        values=[(test_key, "Synthetic Test Recruiter")],
    )

database.run_in_transaction(write_test_data)
print("Synthetic recruiter inserted.")

with database.snapshot() as snapshot:
    rows = list(snapshot.execute_sql(
        "GRAPH IntegrityGraph "
        "MATCH (r:Recruiters) "
        "WHERE r.rkey = @key "
        "RETURN r.rkey, r.label",
        params={"key": test_key},
        param_types={"key": spanner.param_types.STRING},
    ))

print("Graph read result:", rows)
assert rows, "Test recruiter was not found."
assert rows[0][0] == test_key
print("PASS: Spanner Graph write/read test.")
