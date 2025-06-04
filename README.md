# Hyundai Lease Tool

This repository contains utilities for updating dealer inventory data and a Streamlit app for viewing lease options.

## Prerequisites

- **Python**: version 3.10 or later is recommended.
- **Dependencies**: install Python packages listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

## Setup and Usage

1. **Prepare Data Files**
   - `Inventory_Detail_20250527.xlsx` – source spreadsheet with dealer inventory.
   - `Combined_Lease_Programs.csv` – current lease program data.
   - `ohio_county_tax.csv` – Ohio tax rates by county.

   Place these files in the project root directory. The `update_inventory.py` script outputs `Drivepath_Dealer_Inventory.csv` in the same directory.

2. **Update Inventory CSV**

   Run the inventory update script to convert the Excel file to the CSV used by the Streamlit app:

   ```bash
   python update_inventory.py
   ```

   By default the script reads `Inventory_Detail_20250527.xlsx` and writes `Drivepath_Dealer_Inventory.csv`.

3. **Launch the Streamlit App**

   Start the application with:

   ```bash
   streamlit run streamlit_app.py
   ```

   Ensure that `Drivepath_Dealer_Inventory.csv`, `Combined_Lease_Programs.csv`, and `ohio_county_tax.csv` are present in the project directory so the app can load inventory, lease programs, and tax data.

## Files

- `update_inventory.py` – converts the inventory spreadsheet to CSV for use in the app.
- `streamlit_app.py` – main Streamlit application for exploring inventory and lease options.
- `requirements.txt` – list of Python dependencies.

