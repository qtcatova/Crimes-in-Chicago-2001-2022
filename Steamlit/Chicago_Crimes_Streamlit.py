import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from Chicago_Crimes_Cleaning import clean_data

# Avoid blur
st.markdown(
    """
    <style>
    .overlay, .block-container .main .stApp [data-testid="stMarkdownContainer"] > div:first-child {
        backdrop-filter: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# Page config
st.set_page_config(page_title="Chicago Crime Analysis", layout="wide")

# Load Data (once)
@st.cache_data
def load_data(sample_frac=0.5):
    df = pd.read_csv("Crimes_-_2001_to_Present.csv", low_memory=False)
    df = clean_data(df)
    df = df.sample(frac=sample_frac, random_state=42)
    df["Primary Type"] = df["Primary Type"].replace({
    "NON-CRIMINAL": "NON-CRIMINAL",
    "NON - CRIMINAL": "NON-CRIMINAL",
    "NON-CRIMINAL (SUBJECT SPECIFIED)": "NON-CRIMINAL"})
    return df

df = load_data()

# Session State init
if "df_filt" not in st.session_state:
    st.session_state.df_filt = df.sample(frac=0.2, random_state=42)

if "filters_applied" not in st.session_state:
    st.session_state.filters_applied = False

# Sidebar filters
st.sidebar.header("Filters")

year_range = st.sidebar.slider(
    "Select Year Range",
    int(df["Year"].min()),
    int(df["Year"].max()),
    (2001, 2022)
)

sorted_types = df["Primary Type"].value_counts().index.tolist()

crime_types = st.sidebar.multiselect(
    "Primary Crime Type",
    options=sorted_types,
    default=sorted_types[:5]
)

if len(crime_types) == 0:
    crime_types = sorted_types

domestic_filter = st.sidebar.checkbox("Only Domestic Crimes")

# Apply button
apply_filters = st.sidebar.button("Apply Filters")

if apply_filters:
    df_filt = df[
        (df["Year"].between(*year_range)) &
        (df["Primary Type"].isin(crime_types))
    ]
    if domestic_filter:
        df_filt = df_filt[df_filt["Domestic"]]

    st.session_state.df_filt = df_filt.sample(frac=0.2, random_state=42)
    st.session_state.filters_applied = True


# Use last filtered data
df_filt = st.session_state.df_filt
num_selected = len(df_filt["Primary Type"].unique())

# Header
st.markdown("<h1 style='text-align: center;'>Chicago Crime Analysis</h1>", unsafe_allow_html=True)
st.image("chicago_skyline.jpg", use_container_width=True)
st.markdown("""
Chicago is one of the largest cities in the United States and has a long history of crime, 
ranging from thefts and assaults to gun-related incidents. This analysis provides an overview 
of crimes in the city using data from 2001 to 2022. 

You can explore the most common crimes, see which hours have the highest activity, 
compare arrest rates by crime type, and discover where most incidents occur.
""")
st.markdown("---")

# Tabs
tab1, tab2, tab3, tab5, tab4,  = st.tabs(
    ["Overview", "Time", "Arrest Rate", "Trends","Map"]
)

# Tab 1: Top Crime Types
with tab1:
    st.subheader(f"Top {num_selected} Crime Types")
    top10 = df_filt["Primary Type"].value_counts().head(num_selected).reset_index()
    top10.columns = ["Primary Type", "Count"]
    fig = px.bar(top10, x="Primary Type", y="Count", text="Count")
    st.plotly_chart(fig, use_container_width=True)

# Tab 2: Crimes per Hour
with tab2:
    st.subheader("Crimes per Hour")
    hour_counts = df_filt["Hour"].value_counts().sort_index().reset_index()
    hour_counts.columns = ["Hour", "Count"]
    fig = px.line(hour_counts, x="Hour", y="Count", markers=True)
    st.plotly_chart(fig, use_container_width=True)

# Tab 3: Arrest Rate by Crime Type
with tab3:
    st.subheader("Arrest Rate by Crime Type")
    arrest_rate = df_filt.groupby("Primary Type")["Arrest"].mean().sort_values(ascending=False).reset_index()
    arrest_rate.columns = ["Primary Type", "Arrest Rate"]
    fig = px.bar(arrest_rate.head(num_selected), x="Primary Type", y="Arrest Rate", text="Arrest Rate")
    st.plotly_chart(fig, use_container_width=True)

# Tab 5: Crime Trends Over Time
with tab5:
    st.subheader("Crime Trends Over Time")
    year_type = df_filt.groupby(["Year","Primary Type"]).size().reset_index(name="Count")
    top10_crimes = df_filt["Primary Type"].value_counts().head(num_selected).index.tolist()
    year_type = year_type[year_type["Primary Type"].isin(top10_crimes)]
    
    if year_type.empty:
        st.warning("Empty")
    else:
        fig = px.line(year_type, x="Year", y="Count", color="Primary Type", markers=True)
        st.plotly_chart(fig, use_container_width=True)

# Tab 4: Crime Locations (Map)
with tab4:
    st.subheader("Crime Locations")

    df_map = df_filt.dropna(subset=["Latitude","Longitude"])

    @st.cache_data
    def get_sample(df_map, n=5000):
        return df_map.sample(min(n, len(df_map)), random_state=42)

    df_sample = get_sample(df_map)
    m = folium.Map(location=[41.8781, -87.6298], zoom_start=11)

    marker_cluster = MarkerCluster().add_to(m)

    for _, row in df_sample.iterrows():
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=4,
            color='red' if row["Arrest"] else 'blue',
            fill=True,
            fill_opacity=0.3,
            popup=f"{row['Primary Type']}<br>Arrest: {row['Arrest']}"
        ).add_to(marker_cluster)

    st_folium(
        m,
        width=1000,
        height=600,
        returned_objects=[]
    )
