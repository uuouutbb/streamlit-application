import streamlit as st
import pandas as pd
import numpy as np
import csv
import os
import sqlite3
from streamlit_option_menu import option_menu
import altair as alt
import pickle
os.chdir('/FinalProject/')



def load_data():
    conn = sqlite3.connect('510project.db')
    query = """
    SELECT
        h.*,
        h.price / h.livingArea AS price_per_sqft,
        p.groceryCount AS grocery_count,
        p.parkCount AS park_count,
        p.schoolCount AS school_count,
        i.income AS local_income
    FROM
        HOUSES h
    LEFT JOIN PLACESCOUNT p ON h.zpid = p.zpid
    LEFT JOIN OCINCOMEBYZIP i ON h.zipcode = i.zipcode
    """

    data = pd.read_sql_query(query, conn)
    data['builtYear'] = data['builtYear'].str[:-1].astype(int)
    data['local_income'] = data['local_income'].replace(r'[\$,]', '', regex=True).astype(float)

    # Close the connection
    conn.close()

    return data

def home_page():
    st.header("Angie Tang")
    st.header("How to Use This Webapp")
    st.title("Analysis of Community Resources and Their Influence on house Values")
    st.subheader("Features")
    st.write("""
    - **Statistical Analysis**: Explore the relationship between house prices per square foot and the count of neighborhood amenities. 
    You can select specific city within Orange County or view data for the entire Orange County by default.
    - **Predictive Analysis**: Estimate house prices based on selected features. This tool is designed for potential home buyers or investors to forecast house prices tailored to specific preferences.
    """)


    st.subheader("Conclusions from the Analysis")
    st.write("""
    Through my statistical analysis, it can be observed that the presence of highly-rated parks (top 120 on Yelp) and schools (with ratings of 8 or higher) within a 1-mile radius significantly impacts house prices. However, the proximity to popular grocery stores, despite their convenience, does not show a substantial influence on the pricing. This insight can be particularly useful for buyers who value educational and recreational amenities.
    """)

def statistical_analysis_plots(data):
    st.subheader('Comparative Analysis of High Rating Neighborhood Amenities in Orange County')
    popular_cities = ['Anaheim', 'Costa Mesa', 'Laguna Beach', 'Irvine', 'Santa Ana', 'San Clemente']
    other_cities = sorted(set(data['city']) - set(popular_cities))
    all_cities = ['All Cities in Orange County'] + popular_cities + other_cities
    
    city = st.selectbox('Select a city or view all:', all_cities)

    if city != 'All Cities in Orange County':
        filtered_df = data[data['city'] == city]
    else:
        filtered_df = data  

    yfeature = 'price_per_sqft'


    long_df = pd.DataFrame()

    feature_label_mapping = {
        'park_count': 'Parks',
        'grocery_count': 'Grocery Stores',
        'school_count': 'Schools'
    }

    for feature in feature_label_mapping.keys():
        if feature in filtered_df.columns:
            temp_df = filtered_df.groupby(feature)[yfeature].median().reset_index()
            temp_df.rename(columns={yfeature: 'median_price_per_sqft', feature: 'amenity_count'}, inplace=True)
            temp_df['amenity_type'] = feature_label_mapping[feature] 
            long_df = pd.concat([long_df, temp_df])


    if not long_df.empty:
        min_price = long_df['median_price_per_sqft'].min()
        max_price = long_df['median_price_per_sqft'].max()

        chart = alt.Chart(long_df).mark_line(point=True).encode(
            x=alt.X('amenity_count:O', title='Number of Amenities within 1 Mile', axis=alt.Axis(labelAngle=-0)),
            y=alt.Y('median_price_per_sqft:Q', title='Median Price per SqFt', scale=alt.Scale(domain=(min_price - 100, max_price + 100))),
            color=alt.Color('amenity_type:N', legend=alt.Legend(title='Amenity Types')),
            tooltip=['amenity_type:N', 'median_price_per_sqft:Q']
        ).properties(
            title=f'Analysis of High Rating Neighborhood Amenities in {city}',
            width=600,
            height=500
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.error('No valid data available to display the chart.')

def statistical_analysis_charts(data):
    st.subheader('Analysis of Amenities Impact on Price by Bedroom Count')

    # Interactive widgets for user input
    bedrooms = st.selectbox('Select number of bedrooms:', range(1,6), index = 1)
    
    # Filter data based on selections
    filtered_data = data[(data['bedrooms'] == bedrooms)]
    st.subheader(f'{bedrooms} bedrooms')
    # Prepare data for the bar chart
    results = []
    amenity_types = ['grocery_count', 'park_count', 'school_count']
    amenity_labels = ['Grocery Stores', 'Parks', 'Schools']
    for amenity, label in zip(amenity_types, amenity_labels):
        if amenity in filtered_data.columns:
            grouped = filtered_data.groupby(amenity)['price_per_sqft'].median().reset_index()
            grouped['Amenity Type'] = label
            grouped.rename(columns={amenity: 'Count', 'price_per_sqft': 'Median Price per SqFt'}, inplace=True)
            results.append(grouped)

    result_df = pd.concat(results)

    # Create an Altair chart
    chart = alt.Chart(result_df).mark_bar().encode(
        x='Count:O',
        y=alt.Y('Median Price per SqFt:Q', scale=alt.Scale(zero=False)),
        color='Amenity Type:N',
        tooltip=['Count', 'Median Price per SqFt']
    ).properties(
        width=200
    ).facet(
        column='Amenity Type:N'
    )

    st.altair_chart(chart, use_container_width=True)

def statistical_analysis_scatter(data):
    st.subheader("Local Income vs Price in Orange County")
    st.scatter_chart(
        data,
        x='local_income',
        y=['price_per_sqft'],
        size=100 
    )

def predictive_analysis_calculate(inputs):
    wholeTable_encoded = pd.read_csv("encoded_house_data_whole.csv")
    filename = 'lasso_model.pkl'

    with open(filename, 'rb') as file:
        lasso_model = pickle.load(file)
        feature_names = [col for col in wholeTable_encoded.columns if col != 'price']
        
        # Create a feature array with zeros for all columns
        X = pd.DataFrame(0, index=np.arange(1), columns=feature_names)
        if inputs['propertyType'] == 'Single Family':
            inputs['propertyType'] = 'SINGLE_FAMILY'
        elif inputs['propertyType'] == 'Condo':
            inputs['propertyType'] = 'CONDO'
        elif inputs['propertyType'] == 'Town House':
            inputs['propertyType'] = 'TOWNHOUSE'

        # Set the values from inputs
        X['bedrooms'] = inputs['bedrooms']
        X['bathrooms'] = inputs['bathrooms']
        X['livingArea'] = inputs['livingArea']
        X['builtYear'] = inputs['builtYear']
        X[f'city_{inputs["city"]}'] = True
        X[f'propertyType_{inputs["propertyType"]}'] = True
        X['grocery_count'] = inputs['grocery_count']
        X['park_count'] = inputs['park_count']
        X['school_count'] = inputs['school_count']

        predicted_price = lasso_model.predict(X)

    return {
        'predicted_price': predicted_price[0], 
        'contributions': {key: value for key, value in inputs.items() if key not in ['propertyType', 'city']}
    }

def predictive_analysis_input(data):
    col1, col2 = st.columns(2)
    with col1:
        popular_cities = ['Anaheim', 'Costa Mesa', 'Laguna Beach', 'Irvine', 'Santa Ana', 'San Clemente']
        other_cities = sorted(set(data['city']) - set(popular_cities))
        all_cities = popular_cities + other_cities
        city = st.selectbox("Select a city", all_cities)

        bedrooms = st.selectbox('Number of Bedrooms', range(1,7), 2, key='bedrooms')

        livingArea = st.slider('Living Area (sq ft)', 600, 5000, 1100, 50, key='livingArea')

    with col2:
        propertyType = st.selectbox('Property Type', ['Single Family', 'Condo', 'Town House'], key='propertyType')
        bathrooms = st.selectbox('Number of Bathrooms', range(1,7), 2, key='bathrooms')
        builtYear = st.slider('Year Built', 1970, 2024, 1980, 2, key='builtYear')
    
    st.write("Select the number of community amenities you wish to have in 1 mile radius to your home.")
    col3 ,col4, col5 = st.columns(3)
    with col3:
        park_count = st.selectbox("Parks", range(0, 10))
    with col4:
        school_count = st.selectbox("schools", range(0, 7))
    with col5:
        grocery_count = st.selectbox("Grocery Stores", range(0,6))

        
    inputs = {
        'bedrooms': bedrooms,
        'bathrooms': bathrooms,
        'livingArea': livingArea,
        'builtYear': builtYear,
        'propertyType': propertyType,
        'city': city,
        'grocery_count': grocery_count,
        'park_count': park_count,
        'school_count': school_count
    }

    # Calculate prediction whenever any input changes
    if any(st.session_state[key] for key in ['bedrooms', 'bathrooms', 'livingArea', 'builtYear', 'propertyType', 'city',
                                             'grocery_count', 'park_count', 'school_count']):
        results = predictive_analysis_calculate(inputs)
        predicted_price = results['predicted_price']
        contributions = results['contributions']
        
        st.subheader(f"Predicted House Price: ${predicted_price:,.2f}")

def database_page(data):
    # Houses database
    
    houses_table_query = """SELECT * FROM HOUSES"""
    places_table_query = """SELECT * FROM PLACESAROUND"""
    income_table_query= """SELECT * FROM OCINCOMEBYZIP"""
    conn = sqlite3.connect('510project.db')

    st.subheader("Table for house data")
    houses_data = pd.read_sql_query(houses_table_query, conn)
    st.dataframe(houses_data)

    st.subheader("Table for Parks, Schools, Grocery Stores within 1 mile from the houses")
    places_data = pd.read_sql_query(places_table_query, conn)
    st.dataframe(places_data)

    st.subheader("Table average income in Orange County by zipcode")
    income_data = pd.read_sql_query(income_table_query, conn)
    st.dataframe(income_data)

    conn.close()

    st.subheader("Table for the whole joined dataset")
    st.dataframe(data)




def main():
    data = load_data()
    with st.sidebar:
        selected = option_menu(
        menu_title = "Main Menu",
        options = ["Home","Statistical Analysis","Predictive Analysis","Q&A","Dataset"],
        icons = ["house","graph-up-arrow","house-check", "book", "database"],
        menu_icon = "cast",
        default_index = 0,
    )
    if selected == "Statistical Analysis":
        statistical_analysis_plots(data)
        statistical_analysis_charts(data)
        statistical_analysis_scatter(data)
    elif selected == "Home":
        home_page()
    elif selected == "Predictive Analysis":
        predictive_analysis_input(data)
    elif selected == "Dataset":
        database_page(data)

if __name__ == "__main__":
    main()


st.sidebar.title("Menu")
value = st.sidebar.slider(
    label='Select a value',  # Text displayed above the slider
    min_value=0,            # Minimum value of the slider
    max_value=100,          # Maximum value of the slider
    value=50,               # Initial value of the slider
    step=5                  # Incremental step of the slider
)
menu = ["Home", "Profile", "Settings", "About"]
