import pydeck as pdk
from unidecode import unidecode
import xml.etree.ElementTree as ET
import requests as req
import pandas as pd
import streamlit as st


class CityMap:
    def __init__(self, overpass_url, city_data):
        self.overpass_url = overpass_url
        self.city_data = city_data

    def fetch_with_retry(self, url, data, max_retries=3, timeout=15):
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

    def normalize_name(self, text):
        """Convert text to English by transliterating non-Latin characters"""
        if not text:
            return ""
        normalized = unidecode(text)
        return normalized

    def get_bbox_from_zoom(self, lat, lon, zoom):
        """Calculate bounding box based on zoom level"""
        degrees = 0.05 * (2 ** (13 - zoom))
        return f"{lat - degrees},{lon - degrees},{lat + degrees},{lon + degrees}"

    def fetch_museums(self, bbox, overpass_url):
        """Fetch both museums and entertainment for given bbox"""
        pointsOfInterests_data = []

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
            resp = self.fetch_with_retry(overpass_url, query_museums)
            if resp.status_code != 200:
                return pointsOfInterests_data

            root = ET.fromstring(resp.text)

            for node in root.findall("node"):
                name_tag = node.find("tag[@k='name']")

                # Skip if no name or name is empty
                if name_tag is None or not name_tag.get("v"):
                    continue

                name = self.normalize_name(name_tag.get("v"))

                # Skip if name is empty after normalization
                if not name or name.strip() == "":
                    continue

                lat_node = float(node.get("lat"))
                lon_node = float(node.get("lon"))
                addr_tag = node.find("tag[@k='addr:full']")
                address = (
                    self.normalize_name(addr_tag.get("v"))
                    if addr_tag is not None
                    else "Address not available"
                )

                pointsOfInterests_data.append({
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

                    name = self.normalize_name(name_tag.get("v"))

                    # Skip if name is empty after normalization
                    if not name or name.strip() == "":
                        continue

                    lat_way = float(center.get("lat"))
                    lon_way = float(center.get("lon"))
                    addr_tag = way.find("tag[@k='addr:full']")
                    address = (
                        self.normalize_name(addr_tag.get("v"))
                        if addr_tag is not None
                        else "Address not available"
                    )

                    pointsOfInterests_data.append({
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

        return pointsOfInterests_data

    def fetch_intertainments(self, bbox, overpass_url):
       # Fetch entertainment venues
        pointsOfInterests_data = []

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
            resp = self.fetch_with_retry(overpass_url, query_entertainment)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)

                for node in root.findall("node"):
                    name_tag = node.find("tag[@k='name']")

                    # Skip if no name or name is empty
                    if name_tag is None or not name_tag.get("v"):
                        continue

                    name = self.normalize_name(name_tag.get("v"))

                    # Skip if name is empty after normalization
                    if not name or name.strip() == "":
                        continue

                    lat_node = float(node.get("lat"))
                    lon_node = float(node.get("lon"))
                    addr_tag = node.find("tag[@k='addr:full']")
                    address = (
                        self.normalize_name(addr_tag.get("v"))
                        if addr_tag is not None
                        else "Address not available"
                    )

                    pointsOfInterests_data.append({
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

                        name = self.normalize_name(name_tag.get("v"))

                        # Skip if name is empty after normalization
                        if not name or name.strip() == "":
                            continue

                        lat_way = float(center.get("lat"))
                        lon_way = float(center.get("lon"))
                        addr_tag = way.find("tag[@k='addr:full']")
                        address = (
                            self.normalize_name(addr_tag.get("v"))
                            if addr_tag is not None
                            else "Address not available"
                        )

                        pointsOfInterests_data.append({
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

        return pointsOfInterests_data

    def show_city_map(self):
        initial_lat = self.city_data["coord"]["lat"]
        initial_lon = self.city_data["coord"]["lon"]

        st.subheader("City map: Museums and Entertainment")

        loading_placeholder = st.empty()

        try:
            bbox = self.get_bbox_from_zoom(initial_lat, initial_lon, 13)

            loading_placeholder.write("🔍 Loading map data...")

            museums_data = pd.DataFrame(
                self.fetch_museums(bbox, self.overpass_url)
            )
            interests_data = pd.DataFrame(
                self.fetch_intertainments(bbox, self.overpass_url)
            )

               # Clear loading message after data is loaded
            loading_placeholder.empty()

        except Exception as e:
            loading_placeholder.empty()
            st.warning(f"Error fetching POI data: {str(e)}")
            return

        try:
            layers = []

            if len(museums_data) > 0:
                museum_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=museums_data,
                    get_position="[lon, lat]",
                    get_color=[138, 43, 226, 200],
                    get_radius=25,
                    pickable=True,
                    auto_highlight=True,
                )
                layers.append(museum_layer)

            if len(interests_data) > 0:
                entertainment_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=interests_data,
                    get_position="[lon, lat]",
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
                pitch=0,
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


               # Statistics of points of interests
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📍 City Center", 1)
            with col2:
                museum_count = len(museums_data)
                st.metric("🏛️ Museums", museum_count)
            with col3:
                entertainment_count = len(interests_data)
                st.metric("🎭 Entertainment", entertainment_count)

        except ImportError:
            st.map(pd.DataFrame([{"lat": initial_lat, "lon": initial_lon}]))

