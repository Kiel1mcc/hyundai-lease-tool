
import streamlit as st
import pandas as pd

# Load data files
@st.cache_data
def load_data():
    stock_df = pd.read_csv("Dealer_Stock_Summary_Clean.csv", dtype=str)
    lease_df = pd.read_csv("Table_17.csv", dtype=str)
    tax_df = pd.read_csv("Ohio_County_Tax_Rates.csv")
    return stock_df, lease_df, tax_df

stock_df, lease_df, tax_df = load_data()

# Helper functions
def get_vehicle_info(vin):
    match = stock_df[stock_df['VIN'] == vin]
    if not match.empty:
        return match.iloc[0]
    return None

def get_tax_rate(county):
    match = tax_df[tax_df['County'] == county]
    return float(match['Tax Rate'].values[0]) if not match.empty else 0.0

def calculate_lease_payment(msrp, sell_price, mf, residual_pct, months, tax_rate, cash_down):
    residual_amount = msrp * (residual_pct / 100)
    depreciation = (sell_price - residual_amount) / months
    rent = (sell_price + residual_amount) * mf
    base_payment = depreciation + rent
    monthly_tax = base_payment * tax_rate
    total_payment = base_payment + monthly_tax
    return round(total_payment, 2)

# Streamlit layout
st.title("Hyundai Lease Quote Tool")

vin = st.text_input("Enter VIN")
if vin:
    vehicle = get_vehicle_info(vin)
    if vehicle is not None:
        st.markdown(f"**Model:** {vehicle['Model']}  
**Trim:** {vehicle['Trim']}  
**Model #**: {vehicle['Model Number']}")

        msrp = float(vehicle['MSRP'])
        default_price = st.number_input("Selling Price (defaults to MSRP)", value=msrp)
        money_down = st.number_input("Money Down / Trade", value=0)
        county = st.selectbox("Select County", tax_df['County'].unique())
        tax_rate = get_tax_rate(county)

        credit_score = st.selectbox("Estimated Credit Score Range", ["750+", "700–749", "660–699", "620–659", "Below 620"])
        tier_mapping = {
            "750+": "Tier 1",
            "700–749": "Tier 2",
            "660–699": "Tier 3",
            "620–659": "Tier 4",
            "Below 620": "Tier 5"
        }
        credit_tier = tier_mapping[credit_score]

        # Filter lease program
        model_number = vehicle['Model Number']
        programs = lease_df[lease_df['Model Number'] == model_number]

        # Show table
        st.markdown("### Lease Options")
        for idx, row in programs.iterrows():
            term = int(row['Term'])
            miles = row['Miles']
            base_mf = float(row[credit_tier])
            mf = base_mf + 0.0004  # default markup
            residual = float(row['Residual'])

            # Toggles
            col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
            with col1:
                st.markdown(f"**{term} mo**")
            with col2:
                st.markdown(f"{int(miles):,} mi/yr")
            with col3:
                apply_rebate = st.toggle(f"Rebate ({row['Lease Cash']})", key=f"rebate_{idx}")
            with col4:
                remove_markup = st.toggle("MF Markup", value=True, key=f"markup_{idx}")
            with col5:
                display_payment = True

            # Adjust MF
            if not remove_markup:
                mf -= 0.0004

            # Adjust price if rebate applied
            adjusted_price = default_price
            if apply_rebate and row['Lease Cash']:
                try:
                    adjusted_price -= float(row['Lease Cash'].replace('$','').replace(',',''))
                except:
                    pass

            payment = calculate_lease_payment(msrp, adjusted_price, mf, residual, term, tax_rate, money_down / term)
            st.markdown(f"**Payment:** ${payment:,.2f}")
            st.markdown("---")
    else:
        st.error("VIN not found in Dealer Stock.")
