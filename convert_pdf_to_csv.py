import tabula
import pandas as pd
import os

def convert_pdf_to_csv(pdf_path, output_csv_path):
    # Extract all tables from the PDF
    tables = tabula.read_pdf(pdf_path, pages="all", multiple_tables=True, lattice=True)

    if not tables:
        print("No tables found in the PDF.")
        return

    # Combine all tables into a single DataFrame
    combined_df = pd.DataFrame()
    for i, table in enumerate(tables):
        print(f"Processing table {i+1} with columns: {table.columns.tolist()}")
        df = table.copy()

        # Clean column names: strip whitespace, replace spaces with underscores, lowercase
        df.columns = df.columns.str.strip().str.replace(" ", "_").str.lower()

        # Possible variations of column names in the PDF
        column_mapping = {
            "model_year": "Model_Year",
            "model_#": "Model_Number",
            "model_no": "Model_Number",
            "model_number": "Model_Number",
            "trim_level": "Trim",
            "trim": "Trim",
            "description": "Trim",
            "term": "Lease_Term",
            "lease_term": "Lease_Term",
            "credit_tier": "Tier",
            "tier": "Tier",
            "cash_incentive": "Lease_Cash",
            "lease_cash": "Lease_Cash",
            "residual": "Residual_Value",
            "residual_value": "Residual_Value",
            "money_factor": "Residual_Value"
        }

        # Rename columns if they exist
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

        # Ensure all required columns are present
        required_cols = ["Model_Year", "Model_Number", "Trim", "Lease_Term", "Tier", "Lease_Cash", "Residual_Value"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = ""  # Default empty string

        # Clean Lease_Cash: Ensure it starts with $ and has no decimals
        if "Lease_Cash" in df.columns:
            df["Lease_Cash"] = df["Lease_Cash"].astype(str).apply(
                lambda x: f"${int(float(x.replace('$', '').replace(',', '')))}" if x and x != "nan" and x.strip() else "$0"
            )

        # Clean Model_Year: Ensure it’s an integer
        if "Model_Year" in df.columns:
            df["Model_Year"] = df["Model_Year"].astype(str).apply(
                lambda x: x.split(".")[0] if x and x != "nan" else "2025"
            )

        # Clean Lease_Term: Ensure it’s an integer
        if "Lease_Term" in df.columns:
            df["Lease_Term"] = df["Lease_Term"].astype(str).apply(
                lambda x: x.split(" ")[0] if x and x != "nan" else "36"
            )

        # Append to combined DataFrame
        combined_df = pd.concat([combined_df, df], ignore_index=True)

    # Remove duplicates
    combined_df = combined_df.drop_duplicates()

    # Save to CSV
    combined_df.to_csv(output_csv_path, index=False)
    print(f"Converted PDF to CSV and saved as {output_csv_path}")

if __name__ == "__main__":
    pdf_path = "new_lease_programs.pdf"
    output_csv_path = "Combined_Lease_Programs.csv"
    convert_pdf_to_csv(pdf_path, output_csv_path)
