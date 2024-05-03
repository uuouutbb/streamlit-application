# %% [markdown]
# # DSCI 510 Project
# 
# Angie Tang
# Api/Web crwaling
# Data model
# Store data


# %%
import requests
import pprint
import json
import pandas as pd
from bs4 import BeautifulSoup
import csv
import datetime
from requests.structures import CaseInsensitiveDict
import os
import re
os.chdir('/Users/guotang/Desktop/510/proj/')

# %% [markdown]
# # Define api/Web crawling functions

# %% [markdown]
# Data source #1
# 
# Rapid api zillow listing data
# 
# Includes two steps
# 
# Using endpoint/search and endpoint/property

# %%
def get_rapid_zillow_api(city, minYear, maxYear):	
    

    endpoint = "https://zillow69.p.rapidapi.com/search"
    querystring = {"location": f"{city}, CA", "status_type": "RecentlySold",
    "home_type": "Houses, Condos, Townhomes",
    "minPrice": "600000",               # Accroding to the average house price in Orange County
    "maxPrice": "5000000",              # I set up this range to fillter out co-ownership house and luxury mansion
    "bathsMin": "1",                    # Setting minimun bathrooms and bedroom to avoid Null value
    "bedsMin": "1",
    "buildYearMin": minYear,            # Since the downloaded json file does not contain year built info
    "buildYearMax": maxYear}            # I set up a year range each time e.g. minYear 1970, maxYear 1979
                                        # And save the year range as 1970s
    headers = {
        "X-RapidAPI-Key": "eb078392c0mshb582f825887b6c0p1037d9jsn9dab1abef7e1",
        "X-RapidAPI-Host": "zillow69.p.rapidapi.com",   
    }
    
    try:
        response = requests.get(endpoint, headers=headers, params=querystring)
        response.raise_for_status()     # Raise response error
        try:
            response_data = response.json()
            pprint.pprint(response_data)
            return response_data
        
        except ValueError:
            print("Error: Failed to decode JSON from response")
            return []
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Timeout error: {e}")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error: {e}")

    return []


# %%
def save_search_result():
    data = []
    cities = pd.read_csv("OC_city_names.csv")
    cities = cities['city']

    # Do get api call for every city in Orange County
    for city in cities:
        minYear = 1970
        maxYear = 1979
        # For each city, get 4 times, each time with different year range
        for i in range(1,5):
            source = get_rapid_zillow_api(city, minYear, maxYear)
            if source is not None:
                data.append({'source': source, 'built_year': f"{minYear}s"})
            minYear += 10
            maxYear += 10
            # Due to api limitation, I will combine year from 2000 to 2019 as 2000s
            if minYear == 2000:
                maxYear = 2019
    filename = 'zillowapi.json'
    with open(filename, 'w') as f:
        json.dump(data, f)

# %% [markdown]
# Data source #2
# 
# Geoapify places api
# 
# Get places (Park, Grocery Store, School) around a house address

# %%
def get_places_geoapify_api(longitude, latitude):

    # spare keys change when reach limit
    # api_key = '22ef190cdf034a98b197ceeded0e1db9'
    # api_key = 'f27b1f01a2c349469713c8d87ba4cc85'
    api_key = '86e6167d33c343ff9b225be3c9585c16'
    url = f"https://api.geoapify.com/v2/places?categories=leisure.park,commercial.supermarket,education.school&filter=circle:{longitude},{latitude},1400&limit=20&apiKey={api_key}"

    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    
    try:
        response = requests.get(url, headers=headers)
       
        response.raise_for_status()          # raise response error
        try:
            response_data = response.json()
            pprint.pprint(response_data)
            return response_data
        except ValueError:      # JSON decoding fails 
            print("Error: Failed to decode JSON from response")
            return []
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")

    return []

# %%
def save_places_geoapify():
    # Read the downloaded house listing data (cleaned)
    coordinates = pd.read_csv('houseSold.csv')
    all_data = []
    features_data = []

    for index, row in coordinates.iterrows():

        longitude = row['longitude']
        latitude = row['latitude']
        zpid = row['zpid']
        address = row['address']

        # Use the longitude and latitude for every house to find nearby parks, schools, grocery stores
        response_data = get_places_geoapify_api(longitude, latitude)

        # Record the zpid and address for future join and reference.
        features_data = []
        features_data.append({'places around' : address})
        features_data.append({'zpid' : zpid})

        if 'features' in response_data and isinstance(response_data['features'], list):
            for feature in response_data['features']:
                if isinstance(feature, dict): 
                    features_data.append(feature)

        all_data.append(features_data)
    with open('places_around.json', 'w') as json_file:
        json.dump(all_data, json_file, indent=4)

# %% [markdown]
# Data source #3
# 
# Household income by zip web crawling from
# 
# https://localistica.com/usa/ca/county/orange/zipcodes/highest-household-income-zipcodes/#google_vignette

# %%
def craw_income_by_zip():
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    base_url = 'https://localistica.com/usa/ca/county/orange/zipcodes/highest-household-income-zipcodes/#google_vignette'
    try:
        response = requests.get(base_url, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html')
        print(soup)
        return soup
    except Exception as e:
        print(f"An error occurred: {e}")

    return None


def download_income_by_zip():
    income_by_zip = []
    data = craw_income_by_zip()

    if data is not None:
        rows = data.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 6:
                zip_code = cells[0].text.strip()
                income = cells[5].text.strip()
                income_by_zip.append((zip_code, income))
        return income_by_zip

# %%
def craw_park_rating():
    start = 0
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    base_url = 'https://www.yelp.com/search?cflt=parks&find_loc=orange+county%2C+CA&start='
    parks = []
    unwanted = ['Yelp', 'Active Life']
    for i in range(12):
        url = f'{base_url}{start}'
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            parks_temp = soup.findAll('a', {"class": "yelp-emotion-idvn5q"})
            for park in parks_temp:
                if park.text not in unwanted:
                    parks.append(park.text)

            start += 10

        except Exception as e:
            print(f"An error occurred: {e}")
    return parks

    
def csv_park_rating():
    parks = craw_park_rating()
    df = pd.DataFrame(parks, columns=['parks'])
    df.to_csv('park_rating.csv', index = False)


#%%

def craw_grocery_rating():
    groceries = []
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    base_url = 'https://strawpoll.com/most-popular-grocery-store-california'

    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        grocerys = soup.find_all('h3', class_='text-xl sm:text-2xl font-bold custom-title')
        grocerys = [store.get_text() for store in grocerys]
        grocerys = [name.strip() for name in grocerys]

        for g in grocerys:
            groceries.append(g)
            print(g)

    except Exception as e:
        print(f"An error occurred: {e}")
    return groceries

    
def csv_grocery_rating():
    groceryStores = craw_grocery_rating()
    groceryStores = [re.sub(r'^\d+\.\s*', '',g ) for g in groceryStores]
    df = pd.DataFrame(groceryStores, columns=['groceryStore'])
    
    df.to_csv('grocery_rating.csv', index = False)


# %%
def scrape_schools():
    schools = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    base_url = 'https://school-ratings.com/counties/Orange.html'

    try:
        response = requests.get(base_url, headers = headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for i in range(588):
            li = soup.find('li', id=str(i))
            if li:
                school_name = li.find('a').text.strip() if li.find('a') else 'No Name'
                rank_text = li.find('span', class_='rank').text.strip() if li.find('span', class_='rank') else 'No Rank'
                rank_numbers = re.findall(r'\d+', rank_text)
                if rank_numbers:
                    # schools.append((school_name))
                    if int(rank_numbers[0]) >= 8:
                        schools.append((school_name))
                        print(school_name, rank_text)
    except Exception as e:
        print(f"An error occurred: {e}")
    return schools

    
def csv_high_rating_school():
    schools = scrape_schools()
    df = pd.DataFrame(schools, columns=['schools'])
    df.to_csv('school_high_rating.csv', index = False)




# %% [markdown]
# 
# Not a dataset. City names of Orange County

# %%
def craw_OC_city_names():
    # headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    base_url = 'https://www.ocgov.com/about-county/info-oc/oc-links/orange-county-links/orange-county-cities'
    try:
        response = requests.get(base_url, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return None

def download_OC_city_names():
    OC_city_names = []
    data = craw_OC_city_names()
    if data is not None:
        OC_city_names = data.find_all('a',text=lambda text: text and "City of" in text)
        OC_city_names = [(a.text).replace("City of ", "") for a in OC_city_names]
        return OC_city_names




# %% [markdown]
# # Data Model

# %%
import sqlite3
import datetime
import pandas as pd

# %%
def house_sold_table():
    conn = sqlite3.connect('510project.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    cur = conn.cursor()
    df = pd.read_csv("houseSold.csv")
    
    # Create table
    cur.execute('DROP TABLE IF EXISTS HOUSES')
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS HOUSES (
            zpid TEXT PRIMARY KEY,
            city TEXT,
            zipcode TEXT,
            yearSold INTEGER,
            propertyType TEXT,
            price REAL,
            bedrooms INTEGER,
            bathrooms INTEGER,
            livingArea REAL,
            builtYear TEXT,
            longitude TEXT,
            latitude TEXT,
            daysOnZillow INTEGER,
            FOREIGN KEY (zipcode) REFERENCES OCINCOMEBYZIP(zipcode)

        )''')
    
    # Insert data to the table
    for index, row in df.iterrows():
        zpid = row['zpid']
        city = row['city']
        zipcode = row['zip']
        yearSold = row['year']
        propertyType = row['propertyType']
        price = row['price'] 
        bedrooms = row['bedrooms']
        bathrooms = row['bathrooms']
        livingArea = row['livingArea']  
        builtYear = row['built_year']
        longitude = row['longitude']
        latitude = row['latitude']
        daysOnZillow = row['daysOnZillow']

        cur.execute(
            'INSERT INTO HOUSES (zpid, city, zipcode, yearSold, propertyType, price, bedrooms, bathrooms, livingArea, builtYear, longitude, latitude, daysOnZillow) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
        (zpid, city, zipcode, yearSold, propertyType, price, bedrooms, bathrooms, livingArea, builtYear,longitude, latitude, daysOnZillow))
    
    table = pd.read_sql_query('SELECT * FROM HOUSES LIMIT 5', conn)
    print(table)
    

    conn.commit()
    conn.close()

def updateHOUSES():
    conn = sqlite3.connect('510project.db')
    cur = conn.cursor()
    sql_query = """
    UPDATE HOUSES
    SET city = 'Dana Point'
    WHERE city = 'Dana Pt';
    """

    cur.execute(sql_query)
    conn.commit()
    cur.close()
    conn.close()

# %%
def places_table():
    conn = sqlite3.connect('510project.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    cur = conn.cursor()
    df = pd.read_csv("saved_datasets/places_around.csv")
    
    # Create table
    cur.execute('DROP TABLE IF EXISTS PLACESAROUND')
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS PLACESAROUND (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            zpid TEXT,
            name TEXT,
            category TEXT,
            lon TEXT,
            lat TEXT,
            FOREIGN KEY (zpid) REFERENCES HOUSES(zpid)
        )''')
    
    # Insert data to the table
    for index, row in df.iterrows():
        zpid = row['zpid_of_the_house']
        name = row['place name']
        category = row['category']
        lon = row['lon']
        lat = row['lat']

        cur.execute(
            'INSERT INTO PLACESAROUND (zpid, name, category, lon, lat) VALUES (?, ?, ?, ?, ?)', 
        (zpid, name, category, lon, lat))
    
    table = pd.read_sql_query('SELECT * FROM PLACESAROUND LIMIT 5', conn)
    print(table)
    
    conn.commit()
    conn.close()

# %%
def OC_income_zip_table():
    conn = sqlite3.connect('510project.db', detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    cur = conn.cursor()
    df = pd.read_csv("income_by_zip_OC.csv")
    
    # Create table
    cur.execute('DROP TABLE IF EXISTS OCINCOMEBYZIP')
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS OCINCOMEBYZIP (
            zipcode TEXT PRIMARY KEY,
            income TEXT
        )''')
    
    # Insert data to the table
    for index, row in df.iterrows():
        zipcode = row['zip']
        income = row['income']

        cur.execute(
            'INSERT INTO OCINCOMEBYZIP (zipcode, income) VALUES (?, ?)', 
        (zipcode, income))
    
    table = pd.read_sql_query('SELECT * FROM OCINCOMEBYZIP LIMIT 5', conn)
    print(table)
    
    conn.commit()
    conn.close()




# %% [markdown]
# # Store the data

# %% [markdown]
# Store data from rapid zillow api

# %%
# Convert zillowapi.json to zillowData_whole.csv
def csv_results():
    with open('zillowapi.json', 'r') as f:
        data = json.load(f)   
        # Insert built year to every houses downloaded from the same get call
        for item in data:
            built_year = item['built_year']
            for prop in item['source']['props']:
                prop['built_year'] = built_year

        # Normalize the list of properties
        props_data = [prop for item in data for prop in item['source']['props']]
        df = pd.json_normalize(props_data)
        df.to_csv('zillowData_whole.csv', index=False)

# Optimize zillowData_whole.csv to houseSold.csv
def csv_optimal_house_sold_data():
    house_sold = pd.read_csv('zillowData_whole.csv')
    # Days on zillow limit to 180 days since house sold within 180 considered has reasonable price and conditions
    house_sold = house_sold[house_sold['daysOnZillow'] <= 180]

    # Data cleaning
    house_sold = house_sold.drop_duplicates(subset=['zpid'])
    house_sold['zip'] = house_sold['address'].apply(extract_zip)
    house_sold['city'] = house_sold['address'].apply(extract_city)
    house_sold = house_sold[house_sold['zip'].str.contains("CA", na=False)] 
    house_sold['zip'] = house_sold['zip'].str.replace('CA ', '')
    house_sold['year'] = house_sold['variableData.text'].apply(extract_or_assign_year)
    house_sold.head()
    house_sold.to_csv('houseSold.csv', index=False)

# Functions for data cleaning
def extract_or_assign_year(text):
    if pd.isna(text):
        return datetime.datetime.now().year 
    if isinstance(text, str) and 'Sold' in text:
        return text[-4:] 
    else:
        return datetime.datetime.now().year 

def extract_city(address):
    parts = address.split(',')
    if len(parts) > 1:
        return parts[1].strip()
    else:
        return "City not found"

def extract_zip(address):
    parts = address.split(',')
    if len(parts) > 2:
        return parts[2].strip()
    else:
        return "Zip not found"

# %% [markdown]
# Store data from Geoapify places api

# %%
# Convert places_around.json to places_around.csv
def csv_places():
    with open('places_around.json', 'r') as f:
        data = json.load(f) 

    places_around = {
        'zpid_of_the_house': [],
        'place name': [],
        'category': [],
        'lon': [],
        'lat': []
    }

    # Save each place corresponding to the zpid, with specified categories
    for ad in data:
        zpid_of_the_house = []
        place_names = []
        category = []
        longitude = []
        latitude = []

        for item in ad:
            current_zpid = ad[1]['zpid']
            if 'properties' in item:
                name = item['properties'].get('name', None)
                lon = item['properties'].get('lon', None)
                lat = item['properties'].get('lat', None)
                if 'categories' in item['properties']:
                    for c in item['properties']['categories']:
                        if 'supermarket' in c:
                            zpid_of_the_house.append(current_zpid)
                            category.append('grocery store')
                            place_names.append(name)   
                            longitude.append(lon)
                            latitude.append(lat)          
                        elif 'park' in c:     
                            zpid_of_the_house.append(current_zpid)
                            category.append('park')
                            place_names.append(name)
                            longitude.append(lon)
                            latitude.append(lat) 
                        elif 'school' in c:
                            zpid_of_the_house.append(current_zpid)
                            category.append('school')
                            place_names.append(name)
                            longitude.append(lon)
                            latitude.append(lat) 
    
        places_around['zpid_of_the_house'].extend(zpid_of_the_house)
        places_around['place name'].extend(place_names)
        places_around['category'].extend(category)
        places_around['lon'].extend(longitude)
        places_around['lat'].extend(latitude)

        
    df = pd.DataFrame(places_around)
    df = df.drop_duplicates(subset=['zpid_of_the_house', 'place name'])  
    df.to_csv('places_around.csv')



# %% [markdown]
# Store data from 
# 
# https://localistica.com/usa/ca/county/orange/zipcodes/highest-household-income-zipcodes/#google_vignette

# %%
def csv_income_by_zip():
    data = download_income_by_zip()
    df = pd.DataFrame(data, columns=['zip', 'income'])
    df = df.drop(df.index[0])
    df.to_csv('income_by_zip_OC.csv', index = False)

# %%
def csv_OC_city_names():
    data = download_OC_city_names()
    df = pd.DataFrame(data, columns=['city'])
    df.to_csv('OC_city_names.csv', index = False)




# %% [markdown]
# # Logistic
#
# %%
csv_OC_city_names()    # Get city names - OC_city_names.csv
save_search_result()   # Get House listing - Call the get request method and download as - zillowapi.json
csv_results()          # Convert zillowapi.json to zillowData_whole.csv
csv_optimal_house_sold_data()   # Clean data houseSold.csv
save_places_geoapify() # takes 34 mins - place_around.json
csv_places()           # Take useful info and convert place_around.json to place_around.csv
csv_income_by_zip()    # Get income by zip income_by_zip_OC.csv
csv_park_rating()      # Get the first 120 high rating parks from yelp
csv_grocery_rating()   # Get the top 10 grocery stores in California
csv_high_rating_school() # Get the school list with the rating >= 8 in Orange County 

# Finally, I will use three csv files: houseSold.csv, places_around.csv, income_by_zip_OC.csv
# Create database and store these three data source into three tables:
house_sold_table()     # Create and print data model houses table
updateHOUSES()
places_table()         # Create and print data model places around table
OC_income_zip_table()  # Create and print data model income by zip table





