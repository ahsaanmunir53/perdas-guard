from pathlib import Path
import sqlparse
from google.cloud import spanner

schema_path = Path("infra/spanner/schema.sql")
ddl = schema_path.read_text(encoding="utf-8")

statements = [
    s.strip().rstrip(";").strip()
    for s in sqlparse.split(ddl)
    if s.strip()
]

client = spanner.Client(project="pardes-guard-local")
instance = client.instance("pardes-local-instance")
database = instance.database("pardes-local-db")

for i, statement in enumerate(statements, start=1):
    first_line = next(
        (
            line.strip()
            for line in statement.splitlines()
            if line.strip() and not line.strip().startswith("--")
        ),
        "(empty)",
    )
    print(f"[{i}/{len(statements)}] Applying: {first_line[:90]}", flush=True)

    try:
        database.update_ddl([statement]).result(timeout=120)
        print("  OK", flush=True)
    except Exception as exc:
        print(f"  FAILED: {type(exc).__name__}: {exc}", flush=True)
        raise

print("All schema statements accepted by the local emulator.")
