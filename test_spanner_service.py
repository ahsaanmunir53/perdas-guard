from google.cloud import spanner

from app.schemas import NetworkSignals
from app.services.network_spanner import SpannerGraphStore
from app.services.privacy import Hasher

hasher = Hasher("local-emulator-test-salt-only")

store = SpannerGraphStore(
    project="pardes-guard-local",
    instance="pardes-local-instance",
    database="pardes-local-db",
    hasher=hasher,
)

suffix = "spanner-integration-test-001"

first = NetworkSignals(
    case_id=f"case-a-{suffix}",
    recruiter_license_no="TEST-LIC-A-001",
    recruiter_name="Synthetic Recruiter Alpha",
    phones=["+923001234567"],
    fee_accounts=[],
)

second = NetworkSignals(
    case_id=f"case-b-{suffix}",
    recruiter_license_no="TEST-LIC-B-002",
    recruiter_name="Synthetic Recruiter Beta",
    phones=["+923001234567"],
    fee_accounts=[],
)

store.ingest(first, fraud_case=True)
store.ingest(second)

print("Write test: both synthetic recruiters ingested.")

partners = store.shared_phone_partners("lic_TESTLICA001")
print("Shared-phone partners:", partners)

risk, reasons = store.recruiter_risk(
    "TEST-LIC-A-001",
    "Synthetic Recruiter Alpha",
)
print("Recruiter risk:", risk)
print("Risk reasons:", reasons)

print("Employer wage cases:", store.employer_wage_cases(None))
print("Fake layouts:", store.known_fake_layouts())
print("Rings found:", len(store.rings()))
print("Alerts found:", len(store.alerts()))
