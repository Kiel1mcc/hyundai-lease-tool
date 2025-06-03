
import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    dealer_stock = pd.read_csv("Drivepath_Dealer_Inventory.csv")
    table_17 = pd.read_csv("Table_17.csv")
    return dealer_stock, table_17

dealer_stock, df_table = load_data()
dealer_stock.set_index("VIN", inplace=True)

def extract_lease_data(df, model_number, term_label):
    section_idx = df[df.iloc[:, 4] == f"{term_label} Month Lease"].index
    if section_idx.empty:
        return None
    start = section_idx[0] + 2
    matches = df[(df.index >= start) & (df.iloc[:, 1] == model_number)]
    if matches.empty:
        return None
    row = matches.iloc[0]
    try:
        residual = float(row[12])
    except:
        residual = None
    return {
        "Lease Cash": row[3],
        "MF": row[4],
        "Residual": residual
    }

def adjust_residual(base, months, mileage):
    try:
        if mileage == 10000 and 33 <= months <= 48:
            return round(base + 0.01, 4)
        elif mileage == 15000:
            return round(base - 0.02, 4)
        return base
    except:
        return None

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
                    # Format Lease Cash safely
                    try:
                        lease_cash_value = float(str(data["Lease Cash"]).replace("$", "").replace(",", ""))
                        lease_cash_display = f"${lease_cash_value:,.0f}"
                    except:
                        lease_cash_display = "—"

                    # Format residual
                    adj_resid = adjust_residual(data["Residual"], term, miles)
                    residual_display = f"{int(adj_resid * 100)}%" if isinstance(adj_resid, (int, float)) else "—"

                    results.append({
                        "Term": f"{term} mo",
                        "Miles/Yr": f"{miles:,}",
                        "Lease Cash": lease_cash_display,
                        "Tier 1 MF": data["MF"] if pd.notna(data["MF"]) else "—",
                        "Residual": residual_display
                    })

        if results:
            df_out = pd.DataFrame(results)
            st.dataframe(df_out, use_container_width=True)
        else:
            st.warning("No lease data found for this model number.")
    else:
        st.error("VIN not found in dealer stock.")
