# Download one 15-minute GDELT events file
import io
import time
import zipfile
from datetime import timedelta

import pandas as pd
import requests

from . import config
from .schema import COLUMNS, clean


def recent_slots(now, hours):
    # the 15-minute slots of the last `hours` hours, oldest first
    newest = now.replace(minute=now.minute - now.minute % 15, second=0, microsecond=0)
    return [newest - timedelta(minutes=15 * i) for i in range(hours * 4 - 1, -1, -1)]


def raw_name(slot):
    return f"gdelt_events_{slot:%Y%m%d%H%M%S}.parquet"


def raw_key(slot):
    return (f"raw/gdelt/events/year={slot:%Y}/month={slot:%m}/day={slot:%d}/"
            f"{raw_name(slot)}")


def parse(content, run_time):
    # the zip holds one tab-separated file with no header row
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        with z.open(z.namelist()[0]) as f:
            df = pd.read_csv(f, sep="\t", header=None, names=COLUMNS, dtype=str,
                             quoting=3, index_col=False, encoding_errors="replace")
    return clean(df, run_time)


def get_slot(slot, run_time):
    # Returns a DataFrame, or None if the slot is not published (yet) or keeps failing
    url = f"{config.GDELT_BASE_URL}{slot:%Y%m%d%H%M%S}.export.CSV.zip"
    for attempt in range(config.MAX_TRIES):
        try:
            response = requests.get(url, timeout=60)
        except requests.RequestException as e:
            print(f"{slot:%H:%M}: {type(e).__name__}")
        else:
            if response.status_code == 404:
                return None                      # not published yet, or a gap in GDELT
            if response.status_code == 200:
                return parse(response.content, run_time)
            if response.status_code not in (429, 500, 502, 503, 504):
                print(f"{slot:%H:%M}: HTTP {response.status_code}")
                return None
        time.sleep(2 ** (attempt + 1))
    print(f"{slot:%H:%M}: gave up after {config.MAX_TRIES} tries")
    return None