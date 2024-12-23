import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Riverty branding colors
riverty_colors = ["#ef706b", "#527a42", "#cbd7c6", "#141414", "#c9c9c9", "#5c6cff", "#686868", "#298535", "#da1e28", "#f26a20", "#f3f1f0", "#bfbdbb"]
green_shades = ["#456637", "#86a27b", "#e5ebe3"]  # Updated colors for TAM, SAM, SOM
category_colors = {  # New distinct colors for categories
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

    bnpl_revenue = df[df['BNPL type'] != 'No BNPL'].groupby('Country')["Annual revenue (€)"].sum().sort_values(ascending=False)
    metrics['SAM'] = bnpl_revenue  # Revenue from retailers offering BNPL

    metrics['SOM'] = metrics['SAM'] * 0.15  # 15% of SAM

    # Market share by retailer count and revenue
    bnpl_players_count = df[df['BNPL provider'] != 'No BNPL'].groupby(['Country', 'BNPL provider']).size()
    bnpl_players_revenue = df[df['BNPL provider'] != 'No BNPL'].groupby(['Country', 'BNPL provider'])["Annual revenue (€)"].sum()

    metrics['market_share_count'] = bnpl_players_count.unstack(fill_value=0).reindex(index=metrics['TAM'].index, fill_value=0)
    metrics['market_share_revenue'] = bnpl_players_revenue.unstack(fill_value=0).reindex(index=metrics['TAM'].index, fill_value=0)

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
# Define new revenue contribution assumptions

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

# Filters
st.sidebar.header("Filters")
st.sidebar.subheader("Regions")
regions = {
    "DACH": ["DE", "AT", "CH"],
    "BENE": ["BE", "NL"],
    "NORDICS": ["SE", "NO", "FI", "DK"]
}
selected_region = st.sidebar.selectbox("Select Region", options=regions.keys(), index=0)
selected_countries = regions[selected_region]

selected_country = st.sidebar.multiselect("Select Country", options=selected_countries, default=selected_countries)
selected_category = st.sidebar.multiselect("Select Product Category", options=df['Product Category'].unique(), default=df['Product Category'].unique())
selected_bnpl_type = st.sidebar.multiselect("Select BNPL Type", options=df['BNPL type'].unique(), default=df['BNPL type'].unique())
selected_bnpl_provider = st.sidebar.selectbox("Select BNPL Provider", options=df['BNPL provider'].unique(), index=0)

# Apply filters
filtered_df = df[(df['Country'].isin(selected_country)) &
                 (df['Product Category'].isin(selected_category)) &
                 (df['BNPL type'].isin(selected_bnpl_type))]

# Recalculate metrics with filtered data
filtered_metrics = calculate_metrics(filtered_df)

# Market Size
st.header("Market Size (TAM, SAM, SOM)")
st.write("Insight: This visualization allows you to see the total market size (TAM), the subset of that market serviced by BNPL (SAM), and the obtainable portion of that market (SOM) for each country.")
fig, ax = plt.subplots()
filtered_metrics['TAM'].plot(kind='bar', color=green_shades[0], ax=ax, legend=False)
filtered_metrics['SAM'].plot(kind='bar', color=green_shades[1], ax=ax, legend=False)
filtered_metrics['SOM'].plot(kind='bar', color=green_shades[2], ax=ax, legend=False)
ax.set_title("Market Size (TAM, SAM, SOM) by Country")
ax.set_ylabel("Value (€)")
ax.set_xlabel("Country")
ax.legend(["TAM", "SAM", "SOM"], title="Market Size Metrics", bbox_to_anchor=(1.05, 1), loc='upper left')
st.pyplot(fig)

# Market Share
st.header("Market Share of BNPL Players")
st.write("### By Retailer Count")
st.write("Insight: This chart shows the share of retailers partnering with different BNPL providers, highlighting market dominance by number of retailers.")
fig, ax = plt.subplots()
filtered_metrics['market_share_count'].plot(kind='bar', stacked=True, color=riverty_colors, ax=ax)
ax.set_title("Market Share by Retailer Count")
ax.set_ylabel("Number of Retailers")
ax.set_xlabel("Country")
ax.legend(title="BNPL Provider", bbox_to_anchor=(1.05, 1), loc='upper left')
st.pyplot(fig)

st.write("### By Revenue")
st.write("Insight: This chart compares revenue contribution by retailers for each BNPL provider, showing provider strength in terms of revenue.")
fig, ax = plt.subplots()
filtered_metrics['market_share_revenue'].plot(kind='bar', stacked=True, color=riverty_colors, ax=ax)
ax.set_title("Market Share by Revenue")
ax.set_ylabel("Revenue (€)")
ax.set_xlabel("Country")
ax.legend(title="BNPL Provider", bbox_to_anchor=(1.05, 1), loc='upper left')
st.pyplot(fig)

# Product Categories
st.header("Promising Product Categories")
st.write("### By Retailer Volume")
st.write("Insight: This chart highlights which product categories have the highest number of retailers using BNPL, offering insights into market potential.")
fig, ax = plt.subplots()
filtered_metrics['product_volumes'].plot(kind='bar', color=[category_colors[cat] for cat in filtered_metrics['product_volumes'].index], ax=ax)
ax.set_title("Product Volumes by Category")
ax.set_ylabel("Number of Retailers")
ax.set_xlabel("Category")
st.pyplot(fig)

st.write("### By Revenue Potential")
st.write("Insight: This visualization identifies product categories with the highest revenue potential, showcasing profitability opportunities.")
fig, ax = plt.subplots()
filtered_metrics['product_revenues'].plot(kind='bar', color=[category_colors[cat] for cat in filtered_metrics['product_revenues'].index], ax=ax, legend=False)
ax.set_title("Product Revenues by Category")
ax.set_ylabel("Revenue (€)")
ax.set_xlabel("Category")
st.pyplot(fig)

# BNPL Adoption
st.header("Retailer BNPL Adoption")
st.write("### Share of Retailers Offering BNPL")
st.write("Insight: This chart shows the percentage of retailers offering BNPL options, broken down by BNPL type for each country.")
fig, ax = plt.subplots()
filtered_metrics['bnpl_adoption'].plot(kind='bar', stacked=True, color=riverty_colors, ax=ax)
ax.set_title("Share of Retailers Offering BNPL by Country")
ax.set_ylabel("% Share")
ax.set_xlabel("Country")
ax.legend(title="BNPL Type", bbox_to_anchor=(1.05, 1), loc='upper left')
st.pyplot(fig)

# BNPL Distribution
st.header("Distribution of BNPL Payment Options")
st.write("### By Country")
st.write("Insight: This visualization provides the distribution of BNPL payment types across retailers in each country, helping identify preferred BNPL setups.")
fig, ax = plt.subplots()
filtered_metrics['bnpl_distribution'].plot(kind='bar', stacked=True, color=riverty_colors, ax=ax)
ax.set_title("BNPL Payment Options Distribution")
ax.set_ylabel("Number of Retailers")
ax.set_xlabel("Country")
ax.legend(title="BNPL Type", bbox_to_anchor=(1.05, 1), loc='upper left')
st.pyplot(fig)

# Heatmap for Revenue Contribution
st.header("Revenue Contribution by Retailer Tier")
st.write("Insight: This heatmap shows the revenue contribution from different retailer tiers (Top 10, Top 11-100, Top 101-1000, and 1000+) in each country.")

# Plot heatmap
fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="Greens", ax=ax, cbar_kws={'label': '% Contribution'})
ax.set_title("Revenue Contribution by Retailer Tier")
ax.set_xlabel("Retailer Tier")
ax.set_ylabel("Country")
st.pyplot(fig)

# BNPL Players and Product Categories Analysis
st.header("BNPL Players and Product Categories")
st.write("Insight: This chart allows you to select a BNPL provider and see the product categories where it is most active.")
filtered_player_df = df[df['BNPL provider'] == selected_bnpl_provider]
category_distribution = filtered_player_df['Product Category'].value_counts()
fig, ax = plt.subplots()
category_distribution.plot(kind='bar', color=[category_colors[cat] for cat in category_distribution.index], ax=ax)
ax.set_title(f"Product Categories for {selected_bnpl_provider}")
ax.set_ylabel("Number of Retailers")
ax.set_xlabel("Product Category")
st.pyplot(fig)

st.header("Tier Distribution of BNPL Players")
st.write("Insight: This chart displays the percentage of retail merchants for the selected BNPL player distributed across different tiers (Top 10, Top 11-100, Top 101-1000, and 1000+).")
filtered_player_tiers = {
    "Top 10": filtered_player_df[filtered_player_df['Retailer rank'] <= 10].shape[0],
    "Top 11-100": filtered_player_df[(filtered_player_df['Retailer rank'] > 10) & (filtered_player_df['Retailer rank'] <= 100)].shape[0],
    "Top 101-1000": filtered_player_df[(filtered_player_df['Retailer rank'] > 100) & (filtered_player_df['Retailer rank'] <= 1000)].shape[0],
    "1000+": filtered_player_df[filtered_player_df['Retailer rank'] > 1000].shape[0],
}

player_tier_df = pd.DataFrame.from_dict(filtered_player_tiers, orient='index', columns=['Count'])
player_tier_df['Percentage'] = (player_tier_df['Count'] / player_tier_df['Count'].sum()) * 100
fig, ax = plt.subplots()
player_tier_df['Percentage'].plot(kind='bar', color=green_shades, ax=ax)
ax.set_title(f"Tier Distribution for {selected_bnpl_provider}")
ax.set_ylabel("% Share")
ax.set_xlabel("Retailer Tier")
st.pyplot(fig)
