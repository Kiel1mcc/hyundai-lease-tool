import streamlit as st
import pandas as pd

# Load inventory and lease data
@st.cache_data
def load_data():
    inventory = pd.read_csv("Drivepath_Dealer_Inventory.csv", dtype=str)
    lease_programs = pd.read_csv("Combined_Lease_Programs.csv")
    return inventory, lease_programs

inventory_df, lease_df = load_data()

# Streamlit UI
st.title("Hyundai Lease Quote Tool")

vin_input = st.text_input("Enter VIN to get lease options")

if vin_input:
    vehicle = inventory_df[inventory_df["VIN"] == vin_input.upper()]

    if vehicle.empty:
        st.error("VIN not found in inventory.")
    else:
        vehicle = vehicle.iloc[0]
        st.subheader(f"{vehicle['Year']} {vehicle['Model']} {vehicle['Trim']}")
        
        msrp = float(vehicle['MSRP'])
        model_number = vehicle['Model Number']

        # User Inputs
        selling_price = st.number_input("Selling Price", value=msrp, step=100.0)
        credit_score = st.selectbox("Estimated Credit Score", ["720+", "680–719", "640–679", "600–639", "<600"])
        county = st.selectbox("Customer County", ["Franklin", "Cuyahoga", "Delaware", "Hamilton", "Montgomery", "Lucas", "Other"])

        # Credit Tier Mapping (example)
        credit_tier_map = {
            "720+": 1,
            "680–719": 2,
            "640–679": 3,
            "600–639": 4,
            "<600": 5
        }
        tier = credit_tier_map[credit_score]

        # Filter lease data
        lease_matches = lease_df[lease_df["Model Number"] == model_number]

        if lease_matches.empty:
            st.warning("No lease data available for this vehicle.")
        else:
            st.markdown("## Lease Options")

            for _, row in lease_matches.iterrows():
                term = int(row["Term"])
                mileage = int(row["Mileage"])
                residual_pct = float(row["Residual"])
                base_mf = float(row[f"MF_Tier{tier}"])
                lease_cash = float(row["Lease Cash"])

                # Adjust residuals for mileage
                if mileage == 10000 and 33 <= term <= 48:
                    residual_pct += 1
                elif mileage == 15000:
                    residual_pct -= 2

                # Toggles
                col1, col2 = st.columns(2)
                with col1:
                    include_rebate = st.toggle(f"Include Rebate", key=f"rebate_{term}_{mileage}")
                with col2:
                    apply_markup = st.toggle(f"Include MF Markup", value=True, key=f"markup_{term}_{mileage}")

                # Money factor
                mf = base_mf + 0.0004 if apply_markup else base_mf

                # Residual value
                residual_value = msrp * (residual_pct / 100)

                # Cap cost
                cap_cost = selling_price - (lease_cash if include_rebate else 0)

                # Monthly calc
                depreciation = (cap_cost - residual_value) / term
                rent_charge = (cap_cost + residual_value) * mf
                base_payment = depreciation + rent_charge

                # Tax logic
                tax_rate = 0.0725  # Placeholder for now
                monthly_tax = base_payment * tax_rate
                total_payment = base_payment + monthly_tax

                st.markdown(f"**{term} months / {mileage:,} miles:** ${total_payment:,.2f}")

