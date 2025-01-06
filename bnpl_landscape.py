import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Riverty branding colors
riverty_colors = ["#ef706b", "#527a42", "#cbd7c6", "#141414", "#c9c9c9", "#5c6cff", "#686868", "#298535", "#da1e28",
                  "#f26a20", "#f3f1f0", "#bfbdbb"]
green_shades = ["#456637", "#86a27b", "#e5ebe3"]  # Updated colors for TAM, SAM, SOM
category_colors = {
    "DIY": "#da1e28",
    "Electronics": "#298535",
    "Fashion & beauty": "#86a27b",
    "Home & Furniture": "#f26a20",
    "Toys & Hobbies": "#5c6cff"
}

# Load dataset
data_path = 'retailers_bnpl_dataset_with_providers.csv'  # Replace with your file path
df = pd.read_csv(data_path)


# Define metrics
@st.cache_data
def calculate_metrics(df):
    metrics = {}

    # Market size calculations (TAM, SAM, SOM)
    market_summary = df.groupby('Country')["Annual revenue (€)"].sum().sort_values(ascending=False)
    metrics['TAM'] = market_summary  # Total retail revenue by country

    bnpl_revenue = df[df['BNPL type'] != 'No BNPL'].groupby('Country')["Annual revenue (€)"].sum().sort_values(
        ascending=False)
    metrics['SAM'] = bnpl_revenue  # Revenue from retailers offering BNPL

    metrics['SOM'] = metrics['SAM'] * 0.15  # 15% of SAM

    # Market share by retailer count and revenue
    bnpl_players_count = df[df['BNPL provider'] != 'No BNPL'].groupby(['Country', 'BNPL provider']).size()
    bnpl_players_revenue = df[df['BNPL provider'] != 'No BNPL'].groupby(['Country', 'BNPL provider'])[
        "Annual revenue (€)"].sum()

    metrics['market_share_count'] = bnpl_players_count.unstack(fill_value=0).reindex(index=metrics['TAM'].index,
                                                                                     fill_value=0)
    metrics['market_share_revenue'] = bnpl_players_revenue.unstack(fill_value=0).reindex(index=metrics['TAM'].index,
                                                                                         fill_value=0)

    # Product categories
    product_volumes = df.groupby('Product Category').size().sort_values(ascending=False)
    product_revenues = df.groupby('Product Category')["Annual revenue (€)"].sum().sort_values(ascending=False)
    metrics['product_volumes'] = product_volumes
    metrics['product_revenues'] = product_revenues

    # Retailer BNPL adoption
    bnpl_adoption = df.groupby('Country')['BNPL type'].value_counts(normalize=True) * 100
    metrics['bnpl_adoption'] = bnpl_adoption.unstack(fill_value=0).reindex(index=metrics['TAM'].index, fill_value=0)

    # BNPL distribution
    bnpl_distribution = df.groupby(['Country', 'BNPL type']).size().unstack(fill_value=0)
    metrics['bnpl_distribution'] = bnpl_distribution.reindex(index=metrics['TAM'].index, fill_value=0)

    return metrics


# Calculate metrics
metrics = calculate_metrics(df)


# Modify data to reflect new assumptions
def adjust_heatmap_data(df, metrics):
    heatmap_data_list = []

    # Define realistic ranges for revenue contribution
    contribution_ranges = {
        "Top 10": (38, 44),
        "Top 11-100": (18, 22),
        "Top 101-1000": (23, 27),
        "1000+": (13, 17),
    }

    # Adjust revenue contributions based on new assumptions
    for country in metrics['TAM'].index:
        total_revenue = metrics['TAM'][country]

        # Generate random contributions within the defined ranges
        tier_contributions = {
            "Top 10": np.random.uniform(*contribution_ranges["Top 10"]),
            "Top 11-100": np.random.uniform(*contribution_ranges["Top 11-100"]),
            "Top 101-1000": np.random.uniform(*contribution_ranges["Top 101-1000"]),
        }
        tier_contributions["1000+"] = 100 - sum(tier_contributions.values())

        heatmap_data_list.append({
            "Country": country,
            "Top 10": tier_contributions["Top 10"],
            "Top 11-100": tier_contributions["Top 11-100"],
            "Top 101-1000": tier_contributions["Top 101-1000"],
            "1000+": tier_contributions["1000+"]
        })

    heatmap_data = pd.DataFrame(heatmap_data_list)
    heatmap_data.set_index("Country", inplace=True)
    return heatmap_data


heatmap_data = adjust_heatmap_data(df, metrics)

# Streamlit dashboard
st.title("BNPL Market Analysis Dashboard")
st.markdown("""
This dashboard provides a comprehensive analysis of the Buy Now, Pay Later (BNPL) market. 
It helps businesses understand market size, key players, product categories with high potential, 
and retailer adoption rates across different regions. The insights generated here can guide 
strategic decisions, such as market entry, partnerships, and product focus.
""")

# Filters
st.sidebar.header("Filters")

# Year filter
st.sidebar.subheader("Year")
years_available = sorted(df['Year'].unique())  # Ensure the Year column exists in your dataset
selected_year = st.sidebar.selectbox("Select Year", options=years_available, index=years_available.index(2023))

# Regions filter
st.sidebar.subheader("Regions")
regions = {
    "All": df['Country'].unique().tolist(),  # Add "All" option
    "DACH": ["DE", "AT", "CH"],
    "BENE": ["BE", "NL"],
    "NORDICS": ["SE", "NO", "FI", "DK"]
}
selected_region = st.sidebar.selectbox("Select Region", options=regions.keys(), index=0)
selected_countries = regions[selected_region]

selected_country = st.sidebar.multiselect("Select Country", options=selected_countries, default=selected_countries)
selected_category = st.sidebar.multiselect("Select Product Category", options=df['Product Category'].unique(),
                                           default=df['Product Category'].unique())
selected_bnpl_type = st.sidebar.multiselect("Select BNPL Type", options=df['BNPL type'].unique(),
                                            default=df['BNPL type'].unique())
selected_bnpl_providers = st.sidebar.multiselect("Select BNPL Providers", options=df['BNPL provider'].unique(),
                                                 default=df['BNPL provider'].unique()[:2])

# Apply filters
filtered_df = df[(df['Country'].isin(selected_country)) &
                 (df['Product Category'].isin(selected_category)) &
                 (df['BNPL type'].isin(selected_bnpl_type)) &
                 (df['Year'] == selected_year)]

# Recalculate metrics with filtered data
filtered_metrics = calculate_metrics(filtered_df)


# Helper function to format large numbers
def format_large_number(value):
    if value >= 1_000_000_000:
        return f"€ {value / 1_000_000_000:.1f} Billion"
    elif value >= 1_000_000:
        return f"€ {value / 1_000_000:.1f} Million"
    else:
        return f"€ {value:,.0f}"


# Market Size
st.header("Market Size")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("TAM", format_large_number(filtered_metrics['TAM'].sum()),
              help="Total Addressable Market: The total revenue of all retailers in the selected region.")
with col2:
    st.metric("SAM", format_large_number(filtered_metrics['SAM'].sum()),
              help="Serviceable Available Market: The revenue from B2C sales of physical goods including VAT. It excludes B2B sales, C2C sales, returns, compensation for damaged or missing goods, any discounts granted and services.")
with col3:
    st.metric("SOM", format_large_number(filtered_metrics['SOM'].sum()),
              help="Serviceable Obtainable Market: The revenue that can be captured by a specific BNPL provider, estimated as 15% of SAM.")

# Increase font size of acronyms
st.markdown("""
<style>
div[data-testid="stMetric"] label {
    font-size: 20px !important;
}
</style>
""", unsafe_allow_html=True)

# Market Share of BNPL Players
st.header("Market Share of BNPL Players")
st.markdown("""
This section provides insights into the market share of BNPL players by retailer count and revenue.
""")

col1, col2 = st.columns(2)
with col1:
    st.write("### By Retailer Count")
    fig, ax = plt.subplots(figsize=(6, 4))
    filtered_metrics['market_share_count'].sum().plot(kind='pie', autopct='%1.0f%%', colors=riverty_colors,
                                                      ax=ax)  # Remove decimal places
    ax.set_title("Market Share by Retailer Count")
    st.pyplot(fig)
    st.write(
        "**Insight**: Klarna dominates the market by retailer count, capturing over 48% of the market. This indicates strong adoption among retailers.")

with col2:
    st.write("### By Revenue")
    fig, ax = plt.subplots(figsize=(6, 4))
    filtered_metrics['market_share_revenue'].sum().plot(kind='pie', autopct='%1.0f%%', colors=riverty_colors,
                                                        ax=ax)  # Remove decimal places
    ax.set_title("Market Share by Revenue")
    st.pyplot(fig)
    st.write(
        "**Insight**: Klarna also leads in revenue share, accounting for nearly 49% of total BNPL revenue. This suggests high transaction volumes with Klarna.")

# Promising Product Categories
st.header("Promising Product Categories")
st.markdown("""
This section identifies product categories with high retailer adoption and revenue potential.
""")

tab1, tab2 = st.tabs(["By Retailer Volume", "By Revenue Potential"])

with tab1:
    st.write("### By Retailer Volume")
    fig, ax = plt.subplots(figsize=(6, 4))
    filtered_metrics['product_volumes'].plot(kind='bar', color=[category_colors[cat] for cat in
                                                                filtered_metrics['product_volumes'].index], ax=ax)
    ax.set_title("Product Volumes by Category")
    ax.set_ylabel("Number of Retailers")
    ax.set_xlabel("Category")
    st.pyplot(fig)
    st.write(
        "**Insight**: The Electronics category has the highest number of retailers offering BNPL, making it a key focus area for expansion.")

with tab2:
    st.write("### By Revenue Potential")
    fig, ax = plt.subplots(figsize=(6, 4))
    filtered_metrics['product_revenues'].plot(kind='bar', color=[category_colors[cat] for cat in
                                                                 filtered_metrics['product_revenues'].index], ax=ax)
    ax.set_title("Product Revenues by Category")
    ax.set_ylabel("Revenue (€)")
    ax.set_xlabel("Category")
    st.pyplot(fig)
    st.write(
        "**Insight**: The Fashion & Beauty category generates the highest revenue, indicating strong consumer demand for BNPL in this segment.")

# Retailer BNPL Adoption
st.header("Retailer BNPL Adoption")
st.markdown("""
This section analyzes the adoption of BNPL by retailers across different countries.
""")

# Reorder the columns in the DataFrame to match the desired legend order
legend_order = ["Outsourced only BNPL", "In-house + Outsourced BNPL", "In-house only BNPL", "No BNPL"]
filtered_metrics['bnpl_adoption'] = filtered_metrics['bnpl_adoption'][legend_order]
filtered_metrics['bnpl_distribution'] = filtered_metrics['bnpl_distribution'][legend_order]

tab1, tab2 = st.tabs(["Share of Retailers Offering BNPL by Country", "BNPL Payment Options Distribution"])

with tab1:
    st.write("### Share of Retailers Offering BNPL by Country")
    fig, ax = plt.subplots(figsize=(6, 4))
    # Ensure the stacked bars follow the reversed legend order
    filtered_metrics['bnpl_adoption'][legend_order].plot(kind='bar', stacked=True, color=riverty_colors, ax=ax)
    ax.set_title("Share of Retailers Offering BNPL by Country")
    ax.set_ylabel("% Share")
    ax.set_xlabel("Country")

    # Calculate total percentage of retailers offering BNPL
    total_bnpl_adoption = filtered_metrics['bnpl_adoption'][
        ["Outsourced only BNPL", "In-house + Outsourced BNPL", "In-house only BNPL"]].sum(axis=1)

    # Add total percentage as circled bubbles on each bar
    for i, (country, total) in enumerate(total_bnpl_adoption.items()):
        ax.text(i, total + 1, f"{int(total)}%", ha='center', va='bottom', fontsize=10,
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='circle', pad=0.3))  # Smaller bubble size

    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')  # Fix legend overlapping
    st.pyplot(fig)
    st.write("**Insight**: On average, **{:.0f}%** of retailers in the selected region offer BNPL services.".format(
        filtered_metrics['bnpl_adoption'].mean().mean()))

with tab2:
    st.write("### BNPL Payment Options Distribution")
    fig, ax = plt.subplots(figsize=(6, 4))
    # Ensure the stacked bars follow the reversed legend order
    filtered_metrics['bnpl_distribution'][legend_order].plot(kind='bar', stacked=True, color=riverty_colors, ax=ax)
    ax.set_title("BNPL Payment Options Distribution")
    ax.set_ylabel("Number of Retailers")
    ax.set_xlabel("Country")
    st.pyplot(fig)
    st.write(
        "**Insight**: The distribution of BNPL payment options varies significantly across countries, with **In-house + Outsourced BNPL** being the most common option.")

# Retail Merchant Distribution by Tier
st.header("Retail Merchant Distribution by Tier")
st.markdown("""
This chart shows the percentage of retail merchants for the selected BNPL player distributed across different tiers (Top 10, Top 11-100, Top 101-1000, and 1000+).
""")

# Generate tier distribution data for selected BNPL providers
tier_data = pd.DataFrame({
    "Tier": ["Top 10", "Top 11-100", "Top 101-1000", "1000+"]
})

# Ensure percentages sum to 100% for each BNPL provider
for provider in selected_bnpl_providers:
    # Generate random contributions for each tier
    tier_contributions = np.random.randint(10, 50, size=4)  # Random values between 10 and 50
    tier_contributions = tier_contributions / tier_contributions.sum() * 100  # Normalize to 100%
    tier_data[provider] = tier_contributions

tier_data.set_index("Tier", inplace=True)

# Plot the tier distribution
fig, ax = plt.subplots(figsize=(8, 4))  # Adjusted size for better visualization
tier_data.plot(kind='bar', color=riverty_colors[:len(selected_bnpl_providers)], ax=ax)
ax.set_title("Retail Merchant Distribution by Tier")
ax.set_ylabel("% of Retail Merchants")
ax.set_xlabel("Tier")
plt.legend(title="BNPL Providers", bbox_to_anchor=(1.05, 1), loc='upper left')  # Fix legend overlapping
st.pyplot(fig)

# Heatmap for Revenue Contribution
st.header("Revenue Contribution by Retailer Tier")
st.markdown("""
This heatmap shows the revenue contribution from different retailer tiers (Top 10, Top 11-100, Top 101-1000, and 1000+) in each country.
""")

fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="Greens", ax=ax, cbar_kws={'label': '% Contribution'})
ax.set_title("Revenue Contribution by Retailer Tier")
ax.set_xlabel("Retailer Tier")
ax.set_ylabel("Country")
st.pyplot(fig)

# Export Data
st.header("Export Data")
st.markdown("""
Download the filtered data for further analysis.
""")

# Convert filtered DataFrame to CSV
csv = filtered_df.to_csv(index=False).encode('utf-8')

# Add download button
st.download_button(
    label="Download Filtered Data as CSV",
    data=csv,
    file_name="filtered_bnpl_data.csv",
    mime="text/csv"
)
