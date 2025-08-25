import os
import pandas as pd


RESULTS_DIR = "benchmarks/edp/results"
OUTPUT_XLSX = os.path.join(RESULTS_DIR, "results.xlsx")

if __name__ == "__main__":
    # Find all .csv files in RESULTS_DIR
    csv_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith('.csv')]

    if not csv_files:
        print(f"No CSV files found in {RESULTS_DIR}.")
        exit(1)

    with pd.ExcelWriter(OUTPUT_XLSX, engine='openpyxl') as writer:
        for csv_file in csv_files:
            csv_path = os.path.join(RESULTS_DIR, csv_file)
            sheet_name = os.path.splitext(csv_file)[0][:31]  # Excel sheet name max length is 31
            df = pd.read_csv(csv_path)
            df.to_excel(writer, sheet_name=sheet_name, index=False)
