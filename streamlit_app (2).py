
import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    dealer_stock = pd.read_csv("Drivepath_Dealer_Inventory.csv")
    lease_programs = pd.read_csv("Combined_Lease_Programs.csv")
    county_tax = pd.read_csv("ohio_county_tax_reference.csv")
    return dealer_stock, lease_programs, county_tax

def main():
    st.title("Hyundai Lease Quote Tool")

    dealer_stock, lease_data, county_tax = load_data()

    vin_input = st.text_input("Enter VIN")
    matched = dealer_stock[dealer_stock["VIN"] == vin_input.strip()]

    if matched.empty:
        st.warning("VIN not in dealer stock.")
        return

    msrp = matched["MSRP"].values[0]
    model_number = matched["Model Number"].values[0]

    st.success(f"Model Number: {model_number}")
    st.write(f"**MSRP:** ${msrp:,.2f}")

    selling_price = st.number_input("Selling Price", value=float(msrp), step=100.0)
    credit_tier = st.selectbox("Estimated Credit Score / Tier", ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5"])
    tier_map = {"Tier 1": 1, "Tier 2": 2, "Tier 3": 3, "Tier 4": 4, "Tier 5": 5}
    selected_tier = tier_map[credit_tier]

    county = st.selectbox("Customer County", sorted(county_tax["County"]))
    tax_rate = float(county_tax[county_tax["County"] == county]["Tax Rate"].values[0])

    offers = lease_data[lease_data["Model Number"] == model_number]
    offers = offers[offers["Tier"] == selected_tier]

    if offers.empty:
        st.warning("No lease programs found for this model and tier.")
        return

    st.write("### Available Lease Scenarios")

    def calculate_residual(residual_pct, msrp, miles):
        if miles == 10000 and offers["Term"].between(33, 48).any():
            residual_pct += 0.01
        elif miles == 15000:
            residual_pct -= 0.02
        return round(msrp * residual_pct, 2)

    for _, row in offers.iterrows():
        for miles in [10000, 12000, 15000]:
            show_rebate = st.toggle(f"Apply Rebate – ${int(row['Lease Cash'])} for {int(row['Term'])} mo / {miles:,} mi", key=f"{row['Term']}-{miles}-rebate")
            show_markup = st.toggle("Include MF Markup (+.00040)", value=True, key=f"{row['Term']}-{miles}-markup")

            mf_display = row["MF"] + (0.0004 if show_markup else 0)
            rebate_used = row["Lease Cash"] if show_rebate else 0

            residual = calculate_residual(row["Residual"], msrp, miles)
            cap_cost = selling_price - rebate_used + 962.50
            depreciation = cap_cost - residual
            base_payment = depreciation / int(row["Term"])
            rent = (cap_cost + residual) * mf_display
            pretax = base_payment + rent
            with_tax = pretax * (1 + tax_rate)

            st.write(f"📆 **{int(row['Term'])} mo / {miles:,} mi**  — 💰 **${with_tax:.2f}**/mo")

if __name__ == "__main__":
    main()
