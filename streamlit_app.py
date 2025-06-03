import streamlit as st
import pandas as pd

# Load inventory and lease data
@st.cache_data
def load_data():
    try:
        inventory = pd.read_csv("Drivepath_Dealer_Inventory.csv", dtype=str)
        lease_programs = pd.read_csv("Combined_Lease_Programs.csv")
        required_inventory_cols = ["VIN", "Year", "Model", "Trim", "MSRP", "Model Number"]
        required_lease_cols = ["Model Number", "Term", "Mileage", "Residual", "Lease Cash", "MF_Tier1", "MF_Tier2", "MF_Tier3", "MF_Tier4", "MF_Tier5"]
        if not all(col in inventory.columns for col in required_inventory_cols):
            st.error("Inventory CSV missing required columns.")
            return None, None
        if not all(col in lease_programs.columns for col in required_lease_cols):
            st.error("Lease Programs CSV missing required columns.")
            return None, None
        inventory["MSRP"] = pd.to_numeric(inventory["MSRP"], errors="coerce")
        lease_programs["Residual"] = pd.to_numeric(lease_programs["Residual"], errors="coerce")
        lease_programs["Lease Cash"] = pd.to_numeric(lease_programs["Lease Cash"], errors="coerce")
        for tier in range(1, 6):
            lease_programs[f"MF_Tier{tier}"] = pd.to_numeric(lease_programs[f"MF_Tier{tier}"], errors="coerce")
        return inventory, lease_programs
    except FileNotFoundError:
        st.error("One or both CSV files not found.")
        return None, None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None, None

inventory_df, lease_df = load_data()
if inventory_df is None or lease_df is None:
    st.stop()

# Streamlit UI
st.title("Hyundai Lease Quote Tool")

vin_input = st.text_input("Enter VIN to get lease options")

if vin_input:
    vehicle = inventory_df[inventory_df["VIN"].str.upper() == vin_input.upper()]
    if vehicle.empty:
        st.error("VIN not found in inventory.")
    else:
        vehicle = vehicle.iloc[0]
        try:
            msrp = float(vehicle['MSRP'])
        except (ValueError, TypeError):
            st.error("Invalid MSRP value for this vehicle.")
            st.stop()

        st.subheader(f"{vehicle['Year']} {vehicle['Model']} {vehicle['Trim']}")
        model_number = vehicle['Model Number']

        # User Inputs
        selling_price = st.number_input("Selling Price", value=msrp, step=100.0)
        down_payment = st.number_input("Down Payment (optional)", value=0.0, step=100.0)
        credit_score = st.selectbox("Estimated Credit Score", ["720+", "680–719", "640–679", "600–639", "<600"])
        county = st.selectbox("Customer County", ["Franklin", "Cuyahoga", "Delaware", "Hamilton", "Montgomery", "Lucas", "Other"])

        # County tax rates
        county_tax_rates = {
            "Franklin": 0.0750,
            "Cuyahoga": 0.0800,
            "Delaware": 0.0700,
            "Hamilton": 0.0705,
            "Montgomery": 0.0725,
            "Lucas": 0.0725,
            "Other": 0.0700
        }
        tax_rate = county_tax_rates.get(county, 0.0700)

        # Credit Tier Mapping
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
            lease_results = []
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
                    include_rebate = st.toggle(f"Include Rebate", key=f"rebate_{model_number}_{term}_{mileage}")
                with col2:
                    apply_markup = st.toggle(f"Include MF Markup", value=True, key=f"markup_{model_number}_{term}_{mileage}")

                # Money factor
                mf = base_mf + 0.0004 if apply_markup else base_mf

                # Residual value
                residual_value = msrp * (residual_pct / 100)

                # Cap cost
                cap_cost = selling_price - (lease_cash if include_rebate else 0) - down_payment

                # Monthly calc
                depreciation = (cap_cost - residual_value) / term
                rent_charge = (cap_cost + residual_value) * mf
                base_payment = depreciation + rent_charge
                monthly_tax = base_payment * tax_rate
                total_payment = base_payment + monthly_tax

                lease_results.append({
                    "Term (Months)": term,
                    "Mileage": mileage,
                    "Monthly Payment": f"${total_payment:,.2f}",
                    "Rebate Applied": "Yes" if include_rebate else "No",
                    "MF Markup": "Yes" if apply_markup else "No"
                })

            st.markdown("## Lease Options")
            st.dataframe(lease_results)
