import streamlit as st
import pandas as pd
import os

# Function to load CSV files with error handling
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        st.error(f"{file_path} not found in the app directory. Please upload it or check the path.")
        return pd.DataFrame()
    return pd.read_csv(file_path)

# Lease payment calculation function
def calculate_lease_payment(selling_price, lease_cash, residual_percentage, residual_value_range, lease_term, credit_tier, down_payment, tax_rate, acquisition_fee=650, money_factor_markup=0.0004, apply_markup=True):
    # Parse residual value (money factor) range
    if residual_value_range and isinstance(residual_value_range, str):
        if "-" in residual_value_range:
            low, high = map(float, residual_value_range.replace("$", "").split("-"))
            money_factor = (low + high) / 2
        else:
            money_factor = float(residual_value_range.replace("$", ""))
    else:
        money_factor = 0.0025  # Default if not provided

    # Apply money factor markup if selected
    if apply_markup:
        money_factor += money_factor_markup

    # Use residual percentage from the data, with term-specific fallbacks
    if residual_percentage:
        residual_value = selling_price * float(residual_percentage)
    else:
        # Fallback residual percentages based on lease term
        if lease_term == 24:
            residual_value = selling_price * 0.60  # Higher residual for shorter term
        elif lease_term == 36:
            residual_value = selling_price * 0.55
        elif lease_term == 39:
            residual_value = selling_price * 0.52
        elif lease_term == 48:
            residual_value = selling_price * 0.45  # Lower residual for longer term
        else:
            residual_value = selling_price * 0.50  # Generic fallback

    # Apply lease cash (rebate) if selected
    capitalized_cost = selling_price - lease_cash - down_payment

    # Calculate depreciation
    depreciation = (capitalized_cost - residual_value) / lease_term

    # Calculate finance charge
    finance_charge = (capitalized_cost + residual_value) * money_factor

    # Monthly payment before tax
    monthly_payment = depreciation + finance_charge

    # Add tax on monthly payment
    monthly_tax = monthly_payment * tax_rate
    monthly_payment_with_tax = monthly_payment + monthly_tax

    # Due at signing: First payment + acquisition fee + down payment + tax on down payment
    due_at_signing = monthly_payment_with_tax + acquisition_fee + down_payment + (down_payment * tax_rate)

    return {
        "Lease Term (Months)": lease_term,
        "Tier": credit_tier,
        "Money Factor": round(money_factor, 5),
        "Monthly Payment": round(monthly_payment_with_tax, 2),
        "Due at Signing": round(due_at_signing, 2),
        "Available Lease Cash": f"${lease_cash}" if lease_cash > 0 else "None"
    }

# Title of the app
st.title("Hyundai Dealer Inventory and Lease Tool")

# Load data files
inventory_file = "Drivepath_Dealer_Inventory.csv"
lease_file = "Combined_Lease_Programs.csv"
tax_file = "ohio_county_tax.csv"

inventory_data = load_data(inventory_file)
lease_data = load_data(lease_file)
tax_data = load_data(tax_file)

# Stop if required data is missing
if inventory_data.empty:
    st.write("Inventory data is required to proceed. Please upload Drivepath_Dealer_Inventory.csv.")
    st.stop()
if tax_data.empty:
    st.write("Ohio county tax data is required. Please upload ohio_county_tax.csv.")
    st.stop()

# Verify required columns in inventory_data
required_inventory_cols = ["VIN", "MODEL", "TRIM", "MSRP", "MODEL NUMBER", "YEAR"]
if not all(col in inventory_data.columns for col in required_inventory_cols):
    st.error("Inventory data is missing required columns: " + ", ".join([col for col in required_inventory_cols if col not in inventory_data.columns]))
    st.stop()

# Extract available credit tiers from lease programs
if not lease_data.empty and "Tier" in lease_data.columns and not lease_data["Tier"].dropna().empty:
    credit_tiers = sorted(lease_data["
