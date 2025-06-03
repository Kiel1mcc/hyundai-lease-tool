import streamlit as st
import pandas as pd
import os

# Function to load CSV files with error handling
@st.cache_data
def load_data(file_path):
    if not os.path.exists(file_path):
        st.error(f"{file_path} not found in the app directory. Please upload it or check the path.")
        return pd.DataFrame()  # Return empty DataFrame if file not found
    return pd.read_csv(file_path)

# Title of the app
st.title("Hyundai Dealer Inventory and Lease Tool")

# Load inventory data
inventory_file = "Drivepath_Dealer_Inventory.csv"
inventory_data = load_data(inventory_file)

# Load lease programs data (optional)
lease_file = "Combined_Lease_Programs.csv"
lease_data = load_data(lease_file)

# Stop if inventory data is missing (required)
if inventory_data.empty:
    st.write("Inventory data is required to proceed. Please upload Drivepath_Dealer_Inventory.csv.")
    st.stop()

# Sidebar for filters on inventory
st.sidebar.header("Inventory Filters")
model_filter = st.sidebar.selectbox("Select Model", ["All"] + sorted(inventory_data["MODEL"].unique().tolist()))
year_filter = st.sidebar.selectbox("Select Year", ["All"] + sorted(inventory_data["YEAR"].unique().tolist()))

# Apply filters to inventory
filtered_inventory = inventory_data.copy()
if model_filter != "All":
    filtered_inventory = filtered_inventory[filtered_inventory["MODEL"] == model_filter]
if year_filter != "All":
    filtered_inventory = filtered_inventory[filtered_inventory["YEAR"] == year_filter]

# Display inventory data
st.write("### Inventory Data")
st.dataframe(filtered_inventory)

# Display inventory summary
st.write("### Inventory Summary")
st.write(f"Total Vehicles: {len(filtered_inventory)}")

# Display lease programs if available
if not lease_data.empty:
    st.write("### Lease Programs (Optional)")
    st.dataframe(lease_data)
    st.write(f"Total Lease Programs: {len(lease_data)}")
else:
    st.write("Lease programs data not found. Upload Combined_Lease_Programs.csv to view lease details.")
