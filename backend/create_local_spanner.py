from google.cloud import spanner

client = spanner.Client(project="pardes-guard-local")

instance = client.instance(
    "pardes-local-instance",
    configuration_name="emulator-config",
    display_name="Pardes Guard Local Test",
    node_count=1,
)

if not instance.exists():
    instance.create().result(timeout=60)

print("Local Spanner instance ready:", instance.instance_id)
