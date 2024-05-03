import streamlit as st
import pandas as pd
import numpy as np
import csv
import os
import sqlite3
from streamlit_option_menu import option_menu
import altair as alt
import pickle



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
    st.title("Analysis of Community Resources and Their Influence on house Values")
    st.header("Angie Tang")
    st.header("How to Use This Webapp")
    st.subheader("Interactivity and Navigation")
    st.write("""
    - **Comparative Analysis of High Rating Neighborhood Amenities in Orange County (Line plot)**: Explore the relationship between house prices per square foot and the count of neighborhood amenities. 
             You can select specific city within Orange County or view data for the entire Orange County by default.
             The line plot provides insights into how amenities add value to properties on a per-square-foot basis across different locales.
    - **Analysis of Amenities Impact on Price by Bedroom Count (Bar chart)**: Investigate how neighborhood amenities impact house prices based on the size of the house (measured by the number of bedrooms). 
             Adjust the number of bedrooms to see how the prices fluctuate.
             The bar chart helps visualize the influence of amenities on homes of different sizes, suggesting tailored strategies for different types of properties.
    - **Local Income vs Price in Orange County (Scatter Plot)**: Examine the relationship between local income and house prices in various zip codes to determine the influence of economic status on property values.
             The scatter plot offers a perspective on how average local incomes correlate with house prices, indicating economic factors at play.      
    - **Predictive Analysis**: Estimate house prices based on selected features. This tool is designed for potential home buyers or investors to forecast house prices tailored to specific preferences.
    """)


    st.subheader("Conclusions from the Analysis")
    st.write("""
    - **Influence of Parks and Schools**: The presence of highly-rated parks and schools within a 1-mile radius notably boosts house prices. This trend underscores the value that buyers place on educational and recreational facilities close to home.
    - **Impact of House Size on Price Sensitivity**: Larger houses show a steeper increase in price with the addition of amenities such as parks and schools, likely because larger families with children prioritize these features.
    - **Local Income vs. House Prices**: Only a marginal increase in house prices is observed with higher local incomes. This could be attributed to a demographic with a higher proportion of older residents who are less inclined to move, thus dampening the income effect on house prices.
    """)
    st.subheader("Major \"Gotchas\"")
    st.write("""
    - **Performance Issues**: Due to api limitation, there might not have enough data for a accurate analysis. Some cities are too small to have enough data for visulization and prediction. 
             Therefore, I have put the cities with more population on the top for the city select boxes. Please choose a city showed on top of the list.
    - **Improvement Opportunities**: The predictive tool currently uses a limited set of features. Expanding this to include more detailed aspects like crime rates, public transport accessibility, and historical price trends could enhance its accuracy and usefulness.
    """)

def question_page():
    st.subheader("4. Purpose of the Project") 
    st.write("""
    - ***riginal Focus***: The project was initially aimed at predicting house values, focusing on the impact of high-rated community resources such as parks, schools, and local income levels on house prices. 
             The intent was to analyze how amenities and demographic factors influence pricing, and to provide accurate price predictions using a range of features (beds, baths, square footage, year built, nearby amenities).
    - **Discoveries and Conclusions**
        **Key Findings**: 
            **Influence of Parks and Schools**: As hypothesized, the presence of highly-rated parks and schools within a 1-mile radius significantly increases house prices, reflecting the premium buyers place on accessible educational and recreational amenities.
            **Variable Impact in Different Cities**: In cities like Aliso Viejo, Fullerton, and Laguna Beach, house prices showed an unexpected decrease with improved school accessibility. 
            This may be attributed to these cities having a higher proportion of older residents or tourists, who may prioritize different features in housing.
            **Impact of House Size on Price Sensitivity**: Larger homes demonstrated a more pronounced price increase with better amenities, supporting the idea that families, particularly those with children, value these features more.
            **Local Income vs. House Prices**: Contrary to expectations, only a slight correlation was found between higher local incomes and house prices, possibly due to a demographic with older residents who are less likely to move, thus reducing the impact of income on house prices.
            **Original Assumptions Revisited**: While the influence of parks and schools was confirmed, other factors like local average income and proximity to grocery stores did not show a clear correlation with house prices.
    - **Difficulties Encountered**
             The major challenge was the API limitation, which restricted access to comprehensive historical price data. This limitation hindered the ability to predict future house prices effectively, as the most recent data available was from October 2023.
    - **Desired Skills**
             During the project, I wished I had stronger skills in Machine Learning. Having better skills in machine learning could have allowed me to apply more sophisticated models to predict house prices, especially models that can handle large datasets and complex relationships between features.
    - **Future Directions**
            **Expanding the Predictive Model**: To augment the project, I would enhance the predictive tool by incorporating additional features such as crime rates, public transportation options, and historical price trends. These factors could provide a more comprehensive view of the factors influencing house prices.
            **Incorporating Machine Learning**: Implementing more advanced machine learning models to predict price trends based on a broader array of indicators would also be a valuable next step. This could include time series analysis to better understand price fluctuations over time.
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
    st.write("""This is the dataset downloaded from Rapid Zillow api. Variables includes the basic characteristic of a house, id on zillow, days on zillow,
             as well as the location info.
             Api document: https://rapidapi.com/SwongF/api/zillow69/""")
    houses_data = pd.read_sql_query(houses_table_query, conn)
    st.dataframe(houses_data)

    st.subheader("Table for Parks, Schools, Grocery Stores within 1 mile from the houses")
    st.write("""This is the dataset downloaded from Geopify api. It's used for searching places around a specific coordinate. Downloaded using longitude and latitude of a house from the house dataset, set the radius to 1 mile. 
             Variables includes the name of the place, the category(school, park, grocery store)
             Api document: https://myprojects.geoapify.com/api/Pf47Z39bYWpsz49G55MD/keys""")
    places_data = pd.read_sql_query(places_table_query, conn)
    st.dataframe(places_data)

    st.subheader("Table average income in Orange County by zipcode")
    st.write("""This dataset contains local average income in Orange County by zipcode.
             url: https://localistica.com/usa/ca/county/orange/zipcodes/highest-household-income-zipcodes/#google_vignette
        """)
    income_data = pd.read_sql_query(income_table_query, conn)
    st.dataframe(income_data)

    st.subheader("High rating parks in Orange County")
    pd.read_csv("saved_datasets/park_rating.csv")
    st.dataframe

    conn.close()

    st.subheader("Table for the whole joined dataset")
    st.dataframe(data)




def main():
    # Load data from the database
    data = load_data()

    # Sidebar, the main menu
    with st.sidebar:
        selected = option_menu(
        menu_title = "Main Menu",
        options = ["Home","Statistical Analysis","Predictive Analysis","Q&A","Dataset"],
        icons = ["house","graph-up-arrow","house-check", "book", "database"],
        menu_icon = "cast",
        default_index = 0,
    )
        
    # Nevigation
    if selected == "Statistical Analysis": 
        # Shows the three analysis plots 
        statistical_analysis_plots(data)
        statistical_analysis_charts(data)
        statistical_analysis_scatter(data)
    elif selected == "Home":
        # Shows the homepage
        home_page()
    elif selected == "Predictive Analysis":
        # Shows the prediction function of my app
        predictive_analysis_input(data)
    elif selected == "Dataset":
        # Shows my database tables
        database_page(data)
    elif selected == "Q&A":
        # Shows the answers to questions from 4 - 8 in the rubric
        question_page()
if __name__ == "__main__":
    main()


