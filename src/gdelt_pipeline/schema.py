# The 61 columns of a GDELT 2.0 events file, in file order, with their types
import pandas as pd


def _actor(n):
    base = [("code", "VARCHAR"), ("name", "VARCHAR"), ("country_code", "VARCHAR"),
            ("known_group_code", "VARCHAR"), ("ethnic_code", "VARCHAR"),
            ("religion1_code", "VARCHAR"), ("religion2_code", "VARCHAR"),
            ("type1_code", "VARCHAR"), ("type2_code", "VARCHAR"), ("type3_code", "VARCHAR")]
    return [(f"actor{n}_{name}", kind) for name, kind in base]


def _geo(prefix):
    base = [("type", "BIGINT"), ("full_name", "VARCHAR"), ("country_code", "VARCHAR"),
            ("adm1_code", "VARCHAR"), ("adm2_code", "VARCHAR"), ("lat", "DOUBLE"),
            ("long", "DOUBLE"), ("feature_id", "VARCHAR")]
    return [(f"{prefix}_{name}", kind) for name, kind in base]


SCHEMA = (
    [("global_event_id", "BIGINT"), ("sql_date", "BIGINT"), ("month_year", "BIGINT"),
     ("year", "BIGINT"), ("fraction_date", "DOUBLE")]
    + _actor(1) + _actor(2)
    + [("is_root_event", "BIGINT"), ("event_code", "VARCHAR"), ("event_base_code", "VARCHAR"),
       ("event_root_code", "VARCHAR"), ("quad_class", "BIGINT"), ("goldstein_scale", "DOUBLE"),
       ("num_mentions", "BIGINT"), ("num_sources", "BIGINT"), ("num_articles", "BIGINT"),
       ("avg_tone", "DOUBLE")]
    + _geo("actor1_geo") + _geo("actor2_geo") + _geo("action_geo")
    + [("date_added", "BIGINT"), ("source_url", "VARCHAR")]
)
COLUMNS = [name for name, _ in SCHEMA]

# columns we add ourselves
EXTRA = [("event_date", "DATE"), ("added_at", "TIMESTAMPTZ"), ("ingested_at", "TIMESTAMPTZ")]


def create_table_sql():
    cols = [f"{n} {t}" for n, t in SCHEMA + EXTRA] + ["source_file VARCHAR"]
    return "CREATE TABLE IF NOT EXISTS lake.gdelt_events (\n    " + ",\n    ".join(cols) + "\n)"


def clean(df, run_time):
    # Force every file to the same column types, so all parquet files match
    for name, kind in SCHEMA:
        if kind == "BIGINT":
            df[name] = pd.to_numeric(df[name], errors="coerce").astype("Int64")
        elif kind == "DOUBLE":
            df[name] = pd.to_numeric(df[name], errors="coerce").astype("float64")
        else:
            df[name] = df[name].astype("string")
    df["event_date"] = pd.to_datetime(
        df["sql_date"].astype("string"), format="%Y%m%d", errors="coerce"
    ).dt.date
    df["added_at"] = pd.to_datetime(
        df["date_added"].astype("string"), format="%Y%m%d%H%M%S", errors="coerce", utc=True
    )
    df["ingested_at"] = run_time
    return df