import pandas as pd

base = "output/water-sim-smoke-test/raw-output/0/seed=0"

for name in ["dataCenter", "powerSource", "host", "service"]:
    df = pd.read_parquet(f"{base}/{name}.parquet")
    print(f"\n=== {name.upper()} ({len(df)} rows) ===")
    print("Columns:", df.columns.tolist())
    print(df.head(5))
