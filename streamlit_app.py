import streamlit as st
import pandas as pd
import os
import re

# Function to load CSV files with error handling
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        st.error(f"{file_path} not found in the app directory. Please upload it or check the path.")
        return pd.DataFrame()
    return pd.read_csv(file_path)

# Lease payment calculation function
def calculate_lease_payment(
    selling_price,
    lease_cash,
    residual_percentage,
    residual_value_range,
    lease_term,
    credit_tier,
    down_payment,
    tax_rate,
    acquisition_fee=650,
    money_factor_markup=0.0004,
    apply_markup=True,
    apply_lease_cash=True,
):
    # Residual value column actually stores the money factor. Values may
    # come in as strings or floats, so handle both cases.
    if residual_value_range is not None:
        if isinstance(residual_value_range, str):
            cleaned = re.sub(r"[^0-9.-]", "", residual_value_range)
            if "-" in residual_value_range:
                parts = [float(p) for p in cleaned.split("-") if p]
                money_factor = sum(parts) / len(parts) if parts else 0.0025
            else:
                money_factor = float(cleaned) if cleaned else 0.0025
        else:
            money_factor = float(residual_value_range)
    else:
        money_factor = 0.0025

    if apply_markup:
        money_factor += money_factor_markup

    if residual_percentage:
        rpct = float(residual_percentage)
        residual_value = selling_price * (rpct / 100 if rpct > 1 else rpct)
    else:
        if lease_term == 24:
            residual_value = selling_price * 0.60
        elif lease_term == 36:
            residual_value = selling_price * 0.55
        elif lease_term == 39:
            residual_value = selling_price * 0.52
        elif lease_term == 48:
            residual_value = selling_price * 0.45
        else:
            residual_value = selling_price * 0.50

    capitalized_cost = selling_price - down_payment
    if apply_lease_cash:
        capitalized_cost -= lease_cash

    depreciation = (capitalized_cost - residual_value) / lease_term
    finance_charge = (capitalized_cost + residual_value) * money_factor
    monthly_payment = depreciation + finance_charge
    monthly_tax = monthly_payment * tax_rate
    monthly_payment_with_tax = monthly_payment + monthly_tax
    due_at_signing = monthly_payment_with_tax + acquisition_fee + down_payment + (down_payment * tax_rate)

    return {
        "Lease Term (Months)": lease_term,
        "Tier": credit_tier,
        "Money Factor": round(money_factor, 5),
        "Monthly Payment": round(monthly_payment_with_tax, 2),
        "Due at Signing": round(due_at_signing, 2),
        "Available Lease Cash": f"${lease_cash}" if lease_cash > 0 else "None"
    }

st.title("Hyundai Dealer Inventory and Lease Tool")

inventory_data = load_data("Drivepath_Dealer_Inventory.csv")
lease_data = load_data("Combined_Lease_Programs.csv")
tax_data = load_data("ohio_county_tax.csv")

if inventory_data.empty:
    st.write("Inventory data is required to proceed. Please upload Drivepath_Dealer_Inventory.csv.")
    st.stop()
if tax_data.empty:
    st.write("Ohio county tax data is required. Please upload ohio_county_tax.csv.")
    st.stop()

required_inventory_cols = ["VIN", "MODEL", "TRIM", "MSRP", "YEAR"]
if not all(col in inventory_data.columns for col in required_inventory_cols):
    st.error("Inventory data is missing required columns: " + ", ".join([col for col in required_inventory_cols if col not in inventory_data.columns]))
    st.stop()

credit_tiers = sorted(lease_data["Tier"].dropna().unique().tolist()) if not lease_data.empty else ["1", "2", "5"]

counties = ["Select County"] + tax_data["County"].tolist()
# Tax rates are already stored as decimal values (e.g. 0.0725 for 7.25%),
# so no additional scaling is required.
tax_rates = dict(zip(tax_data["County"], tax_data["Tax Rate"].astype(float)))

st.write("### Calculate Lease Payment")
vin_input = st.text_input(
    "Enter VIN",
    placeholder="e.g., 3KMJCCDE7SE006095",
).strip().upper()
county = st.selectbox("Ohio County", counties)

if vin_input and county != "Select County":
    vehicle = inventory_data[inventory_data["VIN"] == vin_input]
    if vehicle.empty:
        st.error("VIN not found in inventory. Please check the VIN and try again.")
    else:
        vehicle = vehicle.iloc[0]
        st.write(f"**Vehicle Found**: {vehicle['MODEL']} {vehicle['TRIM']} ({vehicle['YEAR']})")

        try:
            default_msrp = float(str(vehicle["MSRP"]).replace("$", ""))
        except:
            default_msrp = 0.0

        selling_price = st.number_input("Selling Price ($)", min_value=0.0, value=default_msrp, step=100.0)
        st.write(f"**Model Number**: {vehicle['MODEL']}")

        credit_tier_display = st.selectbox("Customer Credit Tier", credit_tiers)
        credit_tier = credit_tier_display.split()[0]  # Get just the number

        model_year = int(vehicle["YEAR"])
        model_number = vehicle["MODEL"]

        # Match lease programs by exact model number when available. This avoids
        # failures when the inventory trim name doesn't appear in the lease data.
        applicable_leases = lease_data[
            (lease_data["Model_Year"] == model_year)
            & (lease_data["Model_Number"] == model_number)
            & (lease_data["Tier"] == credit_tier)
        ]

        if applicable_leases.empty:
            st.warning("No lease programs found for this vehicle. Using default assumptions.")
            st.code(
                f"DEBUG INFO:\nYear: {model_year}, Model: {model_number}, Tier: {credit_tier}"
            )
            applicable_leases = pd.DataFrame({
                "Lease_Term": [36, 39],
                "Tier": [credit_tier, credit_tier],
                "Lease_Cash": ["$0", "$0"],
                "Residual_Value": ["0.0025", "0.0025"],
                "Residual_Percentage": [0.55, 0.52],
            })

        st.write("#### Lease Options")
        down_payment = st.number_input("Down Payment ($)", min_value=0.0, value=0.0, step=100.0)
        tax_rate = tax_rates.get(county, 0.0725)

        apply_markup = st.toggle("Apply 0.0004 Money Factor Markup", value=True)
        apply_lease_cash = st.toggle("Apply Lease Cash Discount", value=False)

        lease_results = []
        for _, lease in applicable_leases.iterrows():
            lease_cash_str = lease["Lease_Cash"].replace("$", "")
            lease_cash = float(lease_cash_str) if lease_cash_str else 0
            residual_pct = float(lease["Residual_Percentage"])

            result = calculate_lease_payment(
                selling_price=selling_price,
                lease_cash=lease_cash,
                residual_percentage=residual_pct,
                residual_value_range=lease["Residual_Value"],
                lease_term=lease["Lease_Term"],
                credit_tier=credit_tier,
                down_payment=down_payment,
                tax_rate=tax_rate,
                apply_markup=apply_markup,
                apply_lease_cash=apply_lease_cash
            )
            lease_results.append(result)

        if lease_results:
            st.write("#### Lease Payment Options")
            lease_df = pd.DataFrame(lease_results)
            st.dataframe(lease_df)
        else:
            st.error("No lease options available. Check lease program data.")
else:
    st.info("Enter a VIN and select a county to view lease options.")
