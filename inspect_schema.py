from pathlib import Path
import sqlparse

path = Path("infra/spanner/schema.sql")
ddl = path.read_text(encoding="utf-8")

statements = [
    statement.strip()
    for statement in sqlparse.split(ddl)
    if statement.strip()
]

print(f"Found {len(statements)} statements:")
for index, statement in enumerate(statements, start=1):
    first_line = next(
        (line.strip() for line in statement.splitlines()
         if line.strip() and not line.strip().startswith("--")),
        "(empty)"
    )
    print(f"{index}. {first_line[:100]}")
