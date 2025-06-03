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

    # Select and rename columns to match Drivepath_Dealer_Inventory.csv
    df = df[["AON or VIN", "Model", "Description", "MSRP", "Model Number", "MY"]]
    df = df.rename(columns={
        "AON or VIN": "VIN",
        "Model": "MODEL",
        "Description": "TRIM",
        "MSRP": "MSRP",
        "Model Number": "MODEL NUMBER",
        "MY": "YEAR"
    })

    # Clean MSRP: Remove commas, ensure it starts with $
    df["MSRP"] = df["MSRP"].apply(lambda x: f"${x.replace(',', '').split('.')[0]}" if pd.notnull(x) else "$0")

    # Save to CSV
    df.to_csv(output_csv_path, index=False)
    print(f"Updated inventory and saved as {output_csv_path}")

if __name__ == "__main__":
    update_inventory("Inventory_Detail_20250527.xlsx", "Drivepath_Dealer_Inventory.csv")
