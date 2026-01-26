import streamlit as st
from weather_utils import *

# Sets title of the application
url = "https://api.openweathermap.org/data/2.5"
st.title('Travel Guide')

city = st.text_input('Enter your city name', '')
if not city:
    st.stop()
if any(ch.isdigit() for ch in city):
    st.error("City name must not contain numbers")
    st.stop()

if city:
    st.write(f'Weather in {city}, welcome to the weather app!')


weather_url = f"{url}/weather"
data = get_json_data(weather_url,city)
#create row with left and right where 3/4
#parts of the screen is left and 1/4 is right
#this is needed for screen rendering by streamlit
left, right = st.columns([3,1])
show_weather(data,side=left)
show_local_time(data,side=right)

forecast_url = f"{url}/forecast"
forecast_data = get_json_data(forecast_url, city)
show_forecast(forecast_data)
show_daily_conditions(forecast_data)

show_city_map(data)

