# The lakehouse: DuckLake with its catalog in Postgres and its data files in the bucket
from pathlib import Path

import duckdb

from . import config
from .schema import create_table_sql


def connect():
    # Open DuckDB with the bucket credentials and attach the lakehouse
    con = duckdb.connect()
    for extension in ("ducklake", "postgres", "httpfs"):
        con.execute(f"install {extension}")
        con.execute(f"load {extension}")
    con.execute(f"""
        create or replace secret hf (
            type s3, key_id '{config.HF_S3_KEY_ID}', secret '{config.HF_S3_SECRET}',
            endpoint 's3.hf.co/{config.HF_NAMESPACE}', region 'us-east-1', url_style 'path'
        )
    """)
    # own folder in the bucket and own catalog schema; limit 0 = always write parquet files
    con.execute(f"""
        attach 'ducklake:postgres:{config.PG_CATALOG}' as lake (
            data_path 's3://{config.HF_BUCKET}/lake/gdelt/',
            metadata_schema 'gdelt',
            data_inlining_row_limit 0
        )
    """)
    con.execute(create_table_sql())
    return con


def loaded_files(names):
    # Which of these raw file names are already in the table?
    con = connect()
    marks = ", ".join("?" for _ in names)
    rows = con.execute(
        f"select distinct source_file from lake.gdelt_events where source_file in ({marks})",
        list(names),
    ).fetchall()
    con.execute("detach lake")
    con.close()
    return {r[0] for r in rows}


def insert_files(con, paths):
    # One insert for all files, so a run adds one snapshot and one data file.
    # The file name tells every row which slot it came from.
    files = ", ".join("'" + Path(p).as_posix() + "'" for p in paths)
    return con.execute(f"""
        insert into lake.gdelt_events by name
        select * exclude (filename), regexp_extract(filename, '[^/]+$') as source_file
        from read_parquet([{files}], filename = true)
    """).fetchone()[0]


def load(paths):
    con = connect()
    rows = insert_files(con, paths)
    print(f"loaded {len(paths)} files, {rows} rows into the lakehouse")
    con.execute("detach lake")
    con.close()