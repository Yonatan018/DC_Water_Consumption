import pandas as pd

# 1. Load OpenDC 3 outputs
base = "output/water-sim-smoke-test/raw-output/0/seed=0"
dc_df = pd.read_parquet(f"{base}/dataCenter.parquet").sort_values("timestamp")
svc_df = pd.read_parquet(f"{base}/service.parquet").sort_values("timestamp")

# 2. Convert cumulative Joules -> per-interval IT Energy E_IT(t) in kWh
dc_df["energy_delta_j"] = dc_df["energy_usage"].diff().fillna(dc_df["energy_usage"])
dc_df["E_IT_kwh"] = dc_df["energy_delta_j"] / 3_600_000.0
dc_df["P_IT_kw"] = dc_df["power_draw"] / 1_000.0

# 3. ThirstyFLOPS dynamic WUE_on (T_wb in Celsius -> converted to Fahrenheit)
def calc_wue_on(t_wb_c: float, cycles_s: float = 3.0) -> float:
    t_f = (t_wb_c * 9.0 / 5.0) + 32.0
    evap = 6e-5 * (t_f ** 3) - 0.01 * (t_f ** 2) + 0.61 * t_f - 10.4
    return max(0.0, (cycles_s / (cycles_s - 1.0)) * evap)

# 4. Run a quick regional comparison using static placeholder conditions
#    (Next step: replace these scalars with hourly CSVs joined on timestamp)
regions = {
    "France (Nuclear-heavy)": {"t_wb_c": 14.0, "ewf": 2.60, "pue": 1.25, "wsi": 1.2},
    "California (Hot/Scarce)": {"t_wb_c": 22.0, "ewf": 1.10, "pue": 1.25, "wsi": 4.2},
    "Netherlands (Wind/Gas)":  {"t_wb_c": 12.0, "ewf": 0.85, "pue": 1.25, "wsi": 1.0},
}

completed_tasks = int(svc_df["tasks_completed"].iloc[-1])
total_kwh = dc_df["E_IT_kwh"].sum()
print(f"Total IT Energy: {total_kwh:.4f} kWh | Completed Tasks: {completed_tasks}\n")

for name, cfg in regions.items():
    wue_on = calc_wue_on(cfg["t_wb_c"])
    w_direct = (dc_df["E_IT_kwh"] * wue_on).sum()
    w_indirect = (dc_df["E_IT_kwh"] * cfg["pue"] * cfg["ewf"]).sum()
    w_total = w_direct + w_indirect
    w_scarcity = w_total * cfg["wsi"]
    l_per_task = w_total / completed_tasks if completed_tasks > 0 else float("nan")

    print(
        f"{name:24s} | WUE_on={wue_on:.2f} L/kWh | "
        f"Direct={w_direct:.2f} L | Indirect={w_indirect:.2f} L | "
        f"Total={w_total:.2f} L ({l_per_task:.2f} L/task) | "
        f"Scarcity-Weighted={w_scarcity:.2f}"
    )
