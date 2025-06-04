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
    # Parse residual value (money factor) range
    if residual_value_range:
        if isinstance(residual_value_range, str):
            if "-" in residual_value_range:
                low, high = map(
                    float, residual_value_range.replace("$", "").split("-")
                )
                money_factor = (low + high) / 2
            else:
                money_factor = float(residual_value_range.replace("$", ""))
        else:
            money_factor = float(residual_value_range)
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

    # Calculate capitalized cost applying lease cash only if selected
    capitalized_cost = selling_price - down_payment
    if apply_lease_cash:
        capitalized_cost -= lease_cash

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
required_inventory_cols = ["VIN", "MODEL", "TRIM", "MSRP", "YEAR"]
if not all(col in inventory_data.columns for col in required_inventory_cols):
    st.error("Inventory data is missing required columns: " + ", ".join([col for col in required_inventory_cols if col not in inventory_data.columns]))
    st.stop()

# Extract available credit tiers from lease programs
if not lease_data.empty:
    credit_tiers = sorted(lease_data["Tier"].dropna().unique().tolist())
else:
    credit_tiers = ["1 (740-999)", "2 (730-739)", "5 (660-679)"]
    st.warning("Lease programs not found. Using default credit tiers.")

# Extract Ohio counties and tax rates
# County list with placeholder for selection
counties = ["Select County"] + tax_data["County"].tolist()
# The CSV uses a space in the column name, so access it directly
tax_rates = dict(zip(tax_data["County"], tax_data["Tax Rate"].astype(float) / 100))

# Section for lease calculation
st.write("### Calculate Lease Payment")
vin_input = st.text_input("Enter VIN", placeholder="e.g., 3KMJCCDE7SE006095")
county = st.selectbox("Ohio County", counties)

if vin_input and county != "Select County":
    # Find the vehicle in inventory
    vehicle = inventory_data[inventory_data["VIN"] == vin_input]
    if vehicle.empty:
        st.error("VIN not found in inventory. Please check the VIN and try again.")
    else:
        vehicle = vehicle.iloc[0]
        st.write(f"**Vehicle Found**: {vehicle['MODEL']} {vehicle['TRIM']} ({vehicle['YEAR']})")

        # Make selling price editable
        default_msrp = float(vehicle["MSRP"].replace("$", ""))
        selling_price = st.number_input("Selling Price ($)", min_value=0.0, value=default_msrp, step=100.0, key="selling_price")

        # Inventory CSV stores the model code in the `MODEL` column
        st.write(f"**Model Number**: {vehicle['MODEL']}")


                    "Residual_Value": [0.0025, 0.0025],

        # Find applicable lease programs for the selected tier

        credit_tier = st.selectbox("Customer Credit Tier", credit_tiers)

        # Find applicable lease programs for the selected tier
        # Find applicable lease programs

        model_year_match = lease_data["Model_Year"] == vehicle["YEAR"]
        model_number_match = lease_data["Model_Number"].str.contains(
            vehicle["MODEL"].split("F")[0]
        )
        trim_match = (
            lease_data["Trim"].str.lower() == vehicle["TRIM"].split()[0].lower()
        )


        tier_match = lease_data["Tier"] == credit_tier
        applicable_leases = lease_data[
            model_year_match & model_number_match & trim_match & tier_match
        ]
        applicable_leases = lease_data[model_year_match & model_number_match & trim_match]


        if applicable_leases.empty:
            st.warning(
                "No lease programs found for this vehicle. Using default assumptions."
            )
            applicable_leases = pd.DataFrame(
                {
                    "Lease_Term": [36, 39],
                    "Tier": [credit_tier, credit_tier],
                    "Lease_Cash": ["$0", "$0"],
                    "Residual_Value": ["$0.0025", "$0.0025"],
                    "Residual_Percentage": [0.55, 0.52],
                }
            )

        # User inputs for lease calculation
        st.write("#### Lease Options")
        down_payment = st.number_input("Down Payment ($)", min_value=0.0, value=0.0, step=100.0)
        tax_rate = tax_rates.get(county, 0.0725)  # Default to 7.25% if county not found

        apply_markup = st.toggle("Apply 0.0004 Money Factor Markup", value=True)
        apply_lease_cash = st.toggle(
            "Apply Lease Cash Discount",
            value=False,
            help="If enabled, subtract available lease cash from the selling price"
        )

        # Calculate lease payments for all terms and applicable tiers
        lease_results = []
        for _, lease in applicable_leases.iterrows():
            lease_cash_str = lease["Lease_Cash"].replace("$", "")
            lease_cash = float(lease_cash_str) if lease_cash_str else 0
            result = calculate_lease_payment(
                selling_price=selling_price,
                lease_cash=lease_cash,
                residual_percentage=float(lease["Residual_Percentage"]),
                residual_value_range=lease["Residual_Value"],
                lease_term=lease["Lease_Term"],
                credit_tier=credit_tier,
                down_payment=down_payment,
                tax_rate=tax_rate,
                apply_markup=apply_markup,
                apply_lease_cash=apply_lease_cash
            )
            lease_results.append(result)

        # Display results
        if lease_results:
            st.write("#### Lease Payment Options")
            lease_df = pd.DataFrame(lease_results)
            st.dataframe(lease_df)
        else:
            st.error("No lease options available. Check lease program data.")
else:
    st.info("Enter a VIN and select a county to view lease options.")

# Existing inventory display section commented out for streamlined view
# st.write("### Inventory Data")
# model_filter = st.sidebar.selectbox("Select Model", ["All"] + sorted(inventory_data["MODEL"].unique().tolist()))
# year_filter = st.sidebar.selectbox("Select Year", ["All"] + sorted(inventory_data["YEAR"].unique().tolist()))

# filtered_inventory = inventory_data.copy()
# if model_filter != "All":
#     filtered_inventory = filtered_inventory[filtered_inventory["MODEL"] == model_filter]
# if year_filter != "All":
#     filtered_inventory = filtered_inventory[filtered_inventory["YEAR"] == year_filter]

# st.dataframe(filtered_inventory)

# Summary with editable selling price
# st.write("### Inventory Summary")
# total_vehicles = len(filtered_inventory)
# st.write(f"Total Vehicles: {total_vehicles}")

# if not filtered_inventory.empty:
#     st.write("#### Adjust Selling Price for Summary")
#     for idx, row in filtered_inventory.iterrows():
#         default_msrp = float(row["MSRP"].replace("$", ""))
#         new_price = st.number_input(
#             f"Selling Price for {row['VIN']} ({row['MODEL']} {row['TRIM']})",
#             min_value=0.0,
#             value=default_msrp,
#             step=100.0,
#             key=f"summary_price_{row['VIN']}"
#         )
#         filtered_inventory.at[idx, "MSRP"] = f"${new_price}"

#     st.write("#### Updated Inventory Summary")
#     # st.dataframe(filtered_inventory)

# Display lease programs if available
# if not lease_data.empty:
#     st.write("### Lease Programs (Optional)")
#     # st.dataframe(lease_data)
#     st.write(f"Total Lease Programs: {len(lease_data)}")
# else:
#     st.write("Lease programs data not found. Upload Combined_Lease_Programs.csv to view lease details.")
