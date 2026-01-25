from datetime import datetime, timezone, timedelta
import altair as alt
import pandas as pd
import streamlit as st
import requests as req
from geopy.geocoders import Nominatim
from typing import Optional, Dict


def get_json_data(url,city):
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
    return r.json()

def show_local_time(data,side):
    # st.metric("Temperature", f"{temp} °C", delta=f"{temp_delta} °C")
    utc_time = datetime.fromtimestamp(data["dt"], tz=timezone.utc)
    city_time = utc_time + timedelta(seconds=data["timezone"])

    with side:
        st.subheader("Local time")
        st.markdown(
                f"**<div style='font-size:24px'>{city_time.strftime('%d  %b  %Y')} <br>{city_time.strftime('%H:%M')}</div>**",
                unsafe_allow_html=True,
        )


def show_weather(data,side):
    temp = int(data["main"]["temp"])
    humidity = data["main"]["humidity"]
    wind = data["wind"]["speed"]

    with side:
        st.subheader("Current Conditions")
        # Table 3 columns from streamlit
        col1, col2, col3 = st.columns(3)
        col1.metric("Temperature (°C)", temp)
        col2.metric("Humidity (%)", humidity)
        col3.metric("Wind (m/s)", wind)

def show_forecast(forecast_data):
    # forecast graph 
    df = pd.DataFrame({
        "time": [x["dt_txt"] for x in forecast_data["list"]],
        "temp": [x["main"]["temp"] for x in forecast_data["list"]],
        })
    st.subheader("Forecast for the next 5 days")
    chart = (
        alt.Chart(df)
        .mark_line(point=True)
        .encode(
            x=alt.X("time:T", title="Date / Time"),
            y=alt.Y("temp:Q", title="Temperature (°C)"),
            tooltip=["time:T", "temp:Q"],
        )
        .properties(height=300)
    )

    st.altair_chart(chart, width='stretch')

def show_daily_conditions(forecast_data):
    daily = {}

    for x in forecast_data["list"]:
        day = x["dt_txt"].split(" ")[0]
        condition = x["weather"][0]


        if day not in daily:
            daily[day] = {
                    "condition": condition["main"],
                    "icon": condition["icon"],
            }

    df = pd.DataFrame(
            [{"Date": d, "Condition": c} for d, c in daily.items()]
    )
    st.subheader("Daily forecast summary")

    cols = st.columns(len(df))
    for col, (day,info) in zip(cols,daily.items()):
        with col:
            st.markdown(f"**{day}**")
            st.image(f"https://openweathermap.org/img/wn/{info['icon']}@2x.png", width=60)
            st.write(info["condition"])

'''
def show_city_map(data):
    lat = data["coord"]["lat"]
    lon = data["coord"]["lon"]

    map_url = (
        "https://staticmap.openstreetmap.org/staticmap.php"
        f"?center={lat},{lon}&zoom=12&size=600x400&markers={lat},{lon},red-pushpin"
    )

    st.subheader("City map")
    st.image(map_url)
'''


def create_city_map(city: str) -> Optional[Dict[str, str]]:

    # Get coordinates Nominatim (OpenStreetMap)
    geolocator = Nominatim(user_agent="my_python_app_2026")
    location = geolocator.geocode(city)


    # 2. Get API Cartes.io doc:https://github.com/M-Media-Group/Cartes.io/wiki/API
    api_url = "https://cartes.io/api/maps"

    payload = {
        "title": f"Карта города {city}",
        "privacy": "public",
        "center_lat": location.latitude,
        "center_lng": location.longitude,
        "zoom": 12
    }

    try:
        response = req.post(api_url, json=payload)
        response.raise_for_status()
        data = response.json()

        map_uuid = data.get("uuid")
        # Get map
        map_url = f"https://cartes.io/maps/{map_uuid}"

        # Get size frame 600x400
        embed_code = (
            f'<iframe src="{map_url}/embed" '
            f'width="600" height="400" '
            f'frameborder="0"></iframe>'
        )

        return {
            "uuid": map_uuid,
            "url": map_url,
            "embed_code": embed_code,
            "coords": (location.latitude, location.longitude)
        }

    except req.exceptions.RequestException as e:
        print(f"Ошибка API Cartes.io: {e}")
        return None