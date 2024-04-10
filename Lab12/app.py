import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    data = pd.read_csv('car_data.csv')
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
    if car_name:
        filtered_data = filtered_data[filtered_data['car_name'].str.contains(car_name, case=False)]
    if selected_transmission:
        filtered_data = filtered_data[filtered_data['transmission'].isin(selected_transmission)]

    filtered_data = filtered_data[(filtered_data['selling_price'] >= min_price) & (filtered_data['selling_price'] <= max_price)]
    filtered_data = filtered_data[(filtered_data['year'] >= min_year) & (filtered_data['year'] <= max_year)]
    
    st.write(filtered_data)
else:
    st.write(data)

