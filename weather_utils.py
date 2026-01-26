from datetime import datetime, timezone, timedelta
import altair as alt
import pandas as pd
import streamlit as st
import requests as req
import time


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


def fetch_with_retry(url, data, max_retries=3, timeout=15):
    """Fetch data from API with retry logic and exponential backoff"""
    for attempt in range(max_retries):
        try:
            resp = req.post(url, data=data, timeout=timeout)
            return resp
        except req.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                st.warning(f"⏳ Timeout, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"⚠️ Connection error, retrying...")
                time.sleep(1)
            else:
                raise


def show_city_map(data):
    try:
        import pydeck as pdk
        from unidecode import unidecode

        def normalize_name(text):
            """Convert text to English by transliterating non-Latin characters"""
            if not text:
                return ""
            normalized = unidecode(text)
            return normalized

        def get_bbox_from_zoom(lat, lon, zoom):
            """Calculate bounding box based on zoom level"""
            degrees = 0.05 * (2 ** (13 - zoom))
            return f"{lat - degrees},{lon - degrees},{lat + degrees},{lon + degrees}"

        def fetch_poi_data(bbox, overpass_url):
            """Fetch both museums and entertainment for given bbox"""
            poi_data = []

            # Fetch museums
            query_museums = f"""
            [bbox:{bbox}];
            (
              node["tourism"="museum"];
              way["tourism"="museum"];
            );
            out center;
            """

            try:
                resp = fetch_with_retry(overpass_url, query_museums)
                if resp.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.text)

                    for node in root.findall("node"):
                        name_tag = node.find("tag[@k='name']")
                        
                        # Skip if no name or name is empty
                        if name_tag is None or not name_tag.get("v"):
                            continue
                        
                        name = normalize_name(name_tag.get("v"))
                        
                        # Skip if name is empty after normalization
                        if not name or name.strip() == "":
                            continue
                        
                        lat_node = float(node.get("lat"))
                        lon_node = float(node.get("lon"))
                        addr_tag = node.find("tag[@k='addr:full']")
                        address = normalize_name(addr_tag.get("v")) if addr_tag is not None else "Address not available"

                        poi_data.append({
                            "lat": lat_node,
                            "lon": lon_node,
                            "type": "Museum 🏛️",
                            "name": name,
                            "address": address,
                            "phone": "",
                            "icon": "🏛️"
                        })

                    for way in root.findall("way"):
                        center = way.find("center")
                        if center is not None:
                            name_tag = way.find("tag[@k='name']")
                            
                            # Skip if no name or name is empty
                            if name_tag is None or not name_tag.get("v"):
                                continue
                            
                            name = normalize_name(name_tag.get("v"))
                            
                            # Skip if name is empty after normalization
                            if not name or name.strip() == "":
                                continue
                            
                            lat_way = float(center.get("lat"))
                            lon_way = float(center.get("lon"))
                            addr_tag = way.find("tag[@k='addr:full']")
                            address = normalize_name(addr_tag.get("v")) if addr_tag is not None else "Address not available"

                            poi_data.append({
                                "lat": lat_way,
                                "lon": lon_way,
                                "type": "Museum 🏛️",
                                "name": name,
                                "address": address,
                                "phone": "",
                                "icon": "🏛️"
                            })
            except Exception as e:
                st.warning(f"Could not fetch museums: {str(e)}")

            # Fetch entertainment venues
            query_entertainment = f"""
            [bbox:{bbox}];
            (
              node["amenity"="cinema"];
              node["amenity"="theatre"];
              node["amenity"="nightclub"];
              node["leisure"="playground"];
              node["leisure"="park"];
              way["amenity"="cinema"];
              way["amenity"="theatre"];
              way["amenity"="nightclub"];
              way["leisure"="playground"];
              way["leisure"="park"];
            );
            out center;
            """

            try:
                resp = fetch_with_retry(overpass_url, query_entertainment)
                if resp.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.text)

                    for node in root.findall("node"):
                        name_tag = node.find("tag[@k='name']")
                        
                        # Skip if no name or name is empty
                        if name_tag is None or not name_tag.get("v"):
                            continue
                        
                        name = normalize_name(name_tag.get("v"))
                        
                        # Skip if name is empty after normalization
                        if not name or name.strip() == "":
                            continue
                        
                        lat_node = float(node.get("lat"))
                        lon_node = float(node.get("lon"))
                        addr_tag = node.find("tag[@k='addr:full']")
                        address = normalize_name(addr_tag.get("v")) if addr_tag is not None else "Address not available"

                        poi_data.append({
                            "lat": lat_node,
                            "lon": lon_node,
                            "type": "Entertainment 🎭",
                            "name": name,
                            "address": address,
                            "phone": "",
                            "icon": "🎭"
                        })

                    for way in root.findall("way"):
                        center = way.find("center")
                        if center is not None:
                            name_tag = way.find("tag[@k='name']")
                            
                            # Skip if no name or name is empty
                            if name_tag is None or not name_tag.get("v"):
                                continue
                            
                            name = normalize_name(name_tag.get("v"))
                            
                            # Skip if name is empty after normalization
                            if not name or name.strip() == "":
                                continue
                            
                            lat_way = float(center.get("lat"))
                            lon_way = float(center.get("lon"))
                            addr_tag = way.find("tag[@k='addr:full']")
                            address = normalize_name(addr_tag.get("v")) if addr_tag is not None else "Address not available"

                            poi_data.append({
                                "lat": lat_way,
                                "lon": lon_way,
                                "type": "Entertainment 🎭",
                                "name": name,
                                "address": address,
                                "phone": "",
                                "icon": "🎭"
                            })
            except Exception as e:
                st.warning(f"Could not fetch entertainment venues: {str(e)}")

            return poi_data

        initial_lat = data["coord"]["lat"]
        initial_lon = data["coord"]["lon"]

        st.subheader("City map: Museums and Entertainment")

        # City center marker (always at original location)
        map_data = [{
            "lat": initial_lat,
            "lon": initial_lon,
            "type": "City Center",
            "name": "Current Location",
            "address": "",
            "phone": "",
            "icon": "🔵"
        }]

        # Load POI for initial city location
        loading_placeholder = st.empty()

        try:
            overpass_url = "https://overpass-api.de/api/interpreter"
            bbox = get_bbox_from_zoom(initial_lat, initial_lon, 13)

            loading_placeholder.write("🔍 Loading map data...")

            poi_data = fetch_poi_data(bbox, overpass_url)
            map_data.extend(poi_data)

            # Clear loading message after data is loaded
            loading_placeholder.empty()

        except Exception as e:
            loading_placeholder.empty()
            st.warning(f"Error fetching POI data: {str(e)}")

        if map_data:
            df_map = pd.DataFrame(map_data)

            try:
                museums = df_map[df_map['type'].str.contains('Museum')]
                entertainment = df_map[df_map['type'].str.contains('Entertainment')]

                layers = []

                if len(museums) > 0:
                    museum_layer = pdk.Layer(
                        'ScatterplotLayer',
                        data=museums,
                        get_position='[lon, lat]',
                        get_color=[138, 43, 226, 200],
                        get_radius=25,
                        pickable=True,
                        auto_highlight=True,
                    )
                    layers.append(museum_layer)

                if len(entertainment) > 0:
                    entertainment_layer = pdk.Layer(
                        'ScatterplotLayer',
                        data=entertainment,
                        get_position='[lon, lat]',
                        get_color=[255, 165, 0, 200],
                        get_radius=25,
                        pickable=True,
                        auto_highlight=True,
                    )
                    layers.append(entertainment_layer)

                view_state = pdk.ViewState(
                    latitude=initial_lat,
                    longitude=initial_lon,
                    zoom=13,
                    bearing=0,
                    pitch=0
                )

                deck_obj = pdk.Deck(
                    layers=layers,
                    initial_view_state=view_state,
                    tooltip={
                        "html": "<div style='font-family: Arial, sans-serif;'>"
                                "<b style='font-size: 14px;'>{icon} {name}</b>"
                                "</div>",
                        "style": {
                            "backgroundColor": "steelblue",
                            "color": "white",
                            "padding": "10px",
                            "borderRadius": "6px",
                            "fontSize": "10px",
                            "boxShadow": "0 2px 8px rgba(0,0,0,0.3)"
                        }
                    }
                )
                st.pydeck_chart(deck_obj)


                # Statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📍 City Center", 1)
                with col2:
                    museum_count = len([x for x in map_data if "Museum" in x["type"]])
                    st.metric("🏛️ Museums", museum_count)
                with col3:
                    entertainment_count = len([x for x in map_data if "Entertainment" in x["type"]])
                    st.metric("🎭 Entertainment", entertainment_count)

            except ImportError:
                st.map(df_map)

        else:
            st.info("No museums or entertainment venues found in this area")

    except (KeyError, TypeError) as e:
        st.warning(f"Unable to display city map: {str(e)}")