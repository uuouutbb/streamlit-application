import streamlit as st
import pandas as pd
import sqlite3
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib


@st.cache_data

def load_data():
    conn = sqlite3.connect('510project.db')
    query = "SELECT * FROM car_data"

    # Use pandas to read the query into a DataFrame
    data = pd.read_sql_query(query, conn)

    # Close the connection
    conn.close()

    return data

data = load_data()

car_name = st.sidebar.text_input('Car Name')
transmission_options = ['Manual', 'Automatic']
selected_transmission = st.sidebar.multiselect('Transmission', transmission_options, default=transmission_options)

min_price, max_price = st.sidebar.slider('Selling Price Range', 0, 20, (0,20))

min_year, max_year = st.sidebar.slider('Year Range', 2000, 2024, (2000, 2024))
submit = st.sidebar.button('Submit')

if submit:
    filtered_data = data.copy()
    if car_name is not None:
        print(car_name)
        filtered_data = filtered_data[filtered_data['Car_Name'].str.contains(car_name)]
    if selected_transmission:
        filtered_data = filtered_data[filtered_data['Transmission'].isin(selected_transmission)]

    filtered_data = filtered_data[(filtered_data['Selling_Price'] >= min_price) & (filtered_data['Selling_Price'] <= max_price)]
    filtered_data = filtered_data[(filtered_data['Year'] >= min_year) & (filtered_data['Year'] <= max_year)]
    
    st.write(filtered_data)
else:
    st.write(data)
