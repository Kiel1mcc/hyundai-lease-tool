import pandas as pd
import os


def update_inventory(excel_path, output_csv_path):
    # Check if the Excel file exists
    if not os.path.exists(excel_path):
        print(f"Excel file {excel_path} not found. Skipping inventory update.")
        return

    # Read the Excel file
    df = pd.read_excel(excel_path, engine="openpyxl", dtype=str)

    # Filter for "DS - Dealer Stock"
    df = df[df["Vehicle Status"] == "DS - Dealer Stock"]

    # Select and rename columns to match the CSV structure
    df = df[["VIN", "MY", "Model", "Description", "MSRP"]]
    df = df.rename(columns={
        "VIN": "VIN",
        "MY": "YEAR",
        "Model": "MODEL",
        "Description": "TRIM",
        "MSRP": "MSRP"
    })

    # Clean MSRP formatting
    df["MSRP"] = df["MSRP"].apply(lambda x: f"${x.replace(',', '')}" if pd.notna(x) else "$0")

    # Save to CSV
    df.to_csv(output_csv_path, index=False)
    print(f"✅ Inventory updated and saved as {output_csv_path}")


if __name__ == "__main__":
    update_inventory(
        "Inventory_Detail_20250527.xlsx",
        "Drivepath_Dealer_Inventory.csv",
    )
