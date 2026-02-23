import csv
from pathlib import Path
from datetime import datetime

LOG_FILE = Path(__file__).parent / "events.csv"

def log_event(event_type):
    file_exists = LOG_FILE.exists()

    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)

        # Write header once
        if not file_exists:
            writer.writerow(["event_type", "timestamp"])

        writer.writerow([event_type, datetime.now().isoformat()])