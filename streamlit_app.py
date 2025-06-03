import streamlit as st
import pandas as pd

# Load your prepared inventory and lease program data
@st.cache_data
def load_data():
    inventory = pd.read_excel("Inventory_Detail_20250527.xlsx")
    lease_programs = pd.read_excel("H202_BulletinCE.xlsx", sheet_name=None)
    return inventory, lease_programs

inventory_df, lease_sheets = load_data()

# Utility to find the sheet containing the model number
def find_lease_terms_by_model(model_number):
    for sheet in lease_sheets.values():
        match = sheet[sheet.iloc[:, 1].astype(str).str.strip() == model_number]
        if not match.empty:
            return match
    return pd.DataFrame()

# UI layout
st.title("Hyundai Lease Quote Tool")

# VIN input
vin_input = st.text_input("Enter VIN to get lease options")

if vin_input:
    vehicle_row = inventory_df[inventory_df["VIN"] == vin_input]

    if not vehicle_row.empty:
        # Extract vehicle info
        msrp = float(vehicle_row["MSRP"].values[0])
        model = vehicle_row["Model"].values[0]
        trim = vehicle_row["Trim"].values[0]
        model_number = vehicle_row["Model Number"].values[0]
        year = vehicle_row["Year"].values[0]

        st.subheader(f"{year} {model} {trim}")
        selling_price = st.number_input("Selling Price", value=msrp, step=100.0)
        credit_score = st.selectbox("Estimated Credit Score", ["720+", "680–719", "640–679", "600–639", "<600"])
        county = st.selectbox("Customer County", ["Franklin", "Cuyahoga", "Delaware", "Hamilton", "Montgomery", "Lucas", "Other"])

        lease_data = find_lease_terms_by_model(model_number)

        if not lease_data.empty:
            st.markdown("### Lease Options")
            for _, row in lease_data.iterrows():
                term = int(row["Term"])
                mileage = int(row["Mileage"])
                residual_pct = float(row["Residual"])
                money_factor = float(row["MF"])
                lease_cash = float(row["Lease Cash"])

                # Apply mileage adjustment
                if mileage == 10000 and 33 <= term <= 48:
                    residual_pct += 1
                elif mileage == 15000:
                    residual_pct -= 2

                # Checkboxes for toggles
                include_rebate = st.checkbox(f"Include Lease Cash for {term}mo/{mileage:,}mi", value=False, key=f"rebate_{term}_{mileage}")
                markup_toggle = st.checkbox(f"Include MF Markup for {term}mo/{mileage:,}mi", value=True, key=f"mf_{term}_{mileage}")

                if markup_toggle:
                    money_factor += 0.0004

                cap_cost = selling_price - (lease_cash if include_rebate else 0)
                residual_value = msrp * (residual_pct / 100)
                depreciation = (cap_cost - residual_value) / term
                finance_charge = (cap_cost + residual_value) * money_factor
                base_payment = depreciation + finance_charge

                # Sample tax calculation (use correct county logic later)
                tax_rate = 0.0725
                monthly_tax = base_payment * tax_rate
                total_payment = base_payment + monthly_tax

                st.markdown(f"**{term} months / {mileage:,} miles:** ${total_payment:,.2f}")
        else:
            st.warning("No lease program found for this vehicle.")
    else:
        st.error("VIN not found in dealer stock.")
