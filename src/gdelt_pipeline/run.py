# The pipeline: find the slots we do not have yet, download them, save the raw files,
# then add them all to the lakehouse in one go
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from . import config, lake, storage
from .fetch import get_slot, raw_key, raw_name, recent_slots


def main():
    run_time = datetime.now(timezone.utc)
    slots = recent_slots(run_time, config.LOOKBACK_HOURS)

    # what the lake already has, so a missed run is caught up on the next one
    done = lake.loaded_files([raw_name(s) for s in slots])
    todo = [s for s in slots if raw_name(s) not in done]
    print(f"{len(slots)} slots in the last {config.LOOKBACK_HOURS}h, {len(todo)} to fetch")
    if not todo:
        return

    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for slot in todo:
            df = get_slot(slot, run_time)
            time.sleep(config.PAUSE)
            if df is None or df.empty:
                print(f"{slot:%Y-%m-%d %H:%M}: not available yet")
                continue

            path = Path(tmp) / raw_name(slot)
            df.to_parquet(path, index=False)
            storage.upload(path, raw_key(slot))      # raw layer, one file per slot
            paths.append(path)
            print(f"{slot:%Y-%m-%d %H:%M}: {len(df)} events, uploaded {raw_key(slot)}")

        if not paths:
            print("nothing new this run")
            return
        lake.load(paths)                              # lakehouse layer, one insert


if __name__ == "__main__":
    main()