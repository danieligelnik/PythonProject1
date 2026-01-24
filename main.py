import streamlit as st
import requests as req

# Sets title of the application
st.title('Weather App')

name = st.text_input('Enter your city name', '')
if not name:
    st.stop()
if any(ch.isdigit() for ch in city):
    st.error("City name must not contain numbers")
    st.stop()

if name:
    st.write(f'Weather in {name}, welcome to the weather app!')

city = name
url = "https://api.openweathermap.org/data/2.5/weather"


# api_key = st.secrets["DB_TOKEN"]
# username = st.secrets["DB_USERNAME"]
# units = st.secrets["weather"]["units"]

# Parameters for Weather API past to get request
params = {
    "q": city,
    "appid": st.secrets["DB_TOKEN"],
    "units": st.secrets["weather"]["units"],
}

# Sent request to weather site
r = req.get(url, params=params)
if r.status_code != 200:
    st.error("City not found")
    st.stop()

# Get response from weather site in JSON format and parse it
data = r.json()
temp = data["main"]["temp"]
humidity = data["main"]["humidity"]
wind = data["wind"]["speed"]

st.subheader("Current Conditions")

# Table 3 columns from streamlit
col1, col2, col3 = st.columns(3)
col1.metric("Temperature (°C)", temp)
col2.metric("Humidity (%)", humidity)
col3.metric("Wind (m/s)", wind)

# st.metric("Temperature", f"{temp} °C", delta=f"{temp_delta} °C")

