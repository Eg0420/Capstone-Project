import csv
from pathlib import Path
from datetime import datetime

LOG_FILE = Path(__file__).parent / "events.csv"

def log_event(event_type, metadata=None):
    file_exists = LOG_FILE.exists()

    with open(LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Write header once
        if not file_exists:
            writer.writerow(["event_type", "timestamp", "metadata"])

        writer.writerow([
            datetime.now().isoformat(),
            event_type,
            str(metadata) if metadata else ""
        ])