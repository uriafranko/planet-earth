from pathlib import Path
from app.tasks.ingest_worker import process_schema


if __name__ == "__main__":
    scheme_id = "b0c901fb-ac5a-4cc9-9cea-8b10a8d6f422"
    file_content = Path("./openapis/slack.yaml").read_bytes()
    print("Starting schema processing...")
    res = process_schema(scheme_id, file_content, "slack.yaml")
    print(res)
