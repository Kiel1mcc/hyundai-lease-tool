
import streamlit as st
import pandas as pd

# Load reference files
@st.cache_data
def load_data():
    dealer_stock = pd.read_csv("Dealer_Stock_Summary_Clean.csv")
    table_17 = pd.read_csv("Table_17.csv")
    return dealer_stock, table_17

dealer_stock, df_table = load_data()
dealer_stock.set_index("VIN", inplace=True)

# Helper function to find lease data for a model number and term
def extract_lease_data(df, model_number, term_label):
    section_idx = df[df.iloc[:, 4] == f"{term_label} Month Lease"].index
    if section_idx.empty:
        return None
    start = section_idx[0] + 2
    matches = df[(df.index >= start) & (df.iloc[:, 1] == model_number)]
    if matches.empty:
        return None
    row = matches.iloc[0]
    return {
        "Lease Cash": row[3],
        "MF": row[4],
        "Residual": row[12]
    }

# Residual adjustment logic
def adjust_residual(base, months, mileage):
    if mileage == 10000 and 33 <= months <= 48:
        return round(base + 0.01, 4)
    elif mileage == 15000:
        return round(base - 0.02, 4)
    return base

# UI
st.title("Hyundai Lease Program Lookup")

vin_input = st.text_input("Enter VIN")
if vin_input:
    vin_input = vin_input.strip().upper()
    if vin_input in dealer_stock.index:
        model_number = dealer_stock.loc[vin_input, "Model Number"]
        st.success(f"Model Number: {model_number}")

        all_terms = [24, 36, 39, 48]
        all_miles = [10000, 12000, 15000]
        results = []

        for term in all_terms:
            data = extract_lease_data(df_table, model_number, term)
            for miles in all_miles:
                if data:
                    adj_resid = adjust_residual(data["Residual"], term, miles)
                    results.append({
                        "Term": f"{term} mo",
                        "Miles/Yr": miles,
                        "Lease Cash": f"${data['Lease Cash']}",
                        "Tier 1 MF": data["MF"],
                        "Residual": f"{int(adj_resid * 100)}%"
                    })

        if results:
            st.dataframe(pd.DataFrame(results))
        else:
            st.warning("No lease data found for this model number.")
    else:
        st.error("VIN not found in dealer stock.")
