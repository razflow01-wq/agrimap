import streamlit as st
import folium
from streamlit_folium import st_folium
from folium.plugins import Draw
import json
import pandas as pd
import random
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from PIL import Image
from fpdf import FPDF
import ee

if "champs" not in st.session_state:
    st.session_state.champs = []

# ================= CONFIG =================
st.set_page_config(page_title="Agri Burkina 🇧🇫", layout="wide")

# ================= EARTH ENGINE =================
try:
    ee.Initialize(project='capable-passage-502408-t5')
except:
    ee.Initialize(project='capable-passage-502408-t5')

# ================= LOGIN =================
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

users = load_users()

st.sidebar.title("🔐 Connexion / Inscription")

mode = st.sidebar.radio("Choix", ["Connexion", "Inscription"])

username = st.sidebar.text_input("Nom utilisateur")
password = st.sidebar.text_input("Mot de passe", type="password")

# INSCRIPTION
if mode == "Inscription":

    if st.sidebar.button("Créer compte"):

        if username in users:
            st.sidebar.error("Utilisateur existe déjà")
        else:
            users[username] = {
                "password": hash_password(password)
            }
            save_users(users)
            st.sidebar.success("Compte créé !")

    st.stop()

# CONNEXION
if username not in users or users[username]["password"] != hash_password(password):
    st.warning("❌ Mauvais identifiants")
    st.stop()

st.sidebar.success(f"✅ Connecté : {username}")
# ================= IA =================
def train_model():
    X, y = [], []
    cultures = ["maïs", "riz", "mil"]

    for _ in range(300):
        lat = random.uniform(10, 15)
        lon = random.uniform(-3, 2)
        culture = random.choice(cultures)

        base = random.uniform(1, 5)

        if culture == "maïs":
            rendement = base + 2
        elif culture == "riz":
            rendement = base + 1
        else:
            rendement = base

        X.append([lat, lon, cultures.index(culture)])
        y.append(rendement)

    model = RandomForestRegressor(n_estimators=200)
    model.fit(X, y)
    return model

model = train_model()
@st.cache_data
def predict_rendement(lat, lon, culture):

    # ================= SOL =================
    if lat < 11:
        sol = "argileux"
        sol_score = 0.9
    elif lat < 13:
        sol = "limoneux"
        sol_score = 1.2
    else:
        sol = "sableux"
        sol_score = 0.7

    # ================= CLIMAT =================
    if lat < 11:
        climat = "humide"
        pluie = random.uniform(800, 1200)  # mm/an
    elif lat < 13:
        climat = "sub-humide"
        pluie = random.uniform(600, 900)
    else:
        climat = "sec"
        pluie = random.uniform(300, 600)

    pluie_score = pluie / 800  # normalisation

    # ================= NDVI (simulation satellite) =================
    ndvi = random.uniform(0.2, 0.9)

    # ================= CULTURE =================
    culture = culture.lower()

    if "maïs" in culture:
        culture_score = 1.3
    elif "riz" in culture:
        culture_score = 1.2
    elif "mil" in culture:
        culture_score = 1.0
    else:
        culture_score = 0.9

    # ================= CALCUL FINAL =================
    base = random.uniform(1, 2)

    rendement = base * sol_score * pluie_score * culture_score * (ndvi + 0.5)

    rendement = round(rendement, 2)

    return rendement, sol, climat, round(ndvi, 2), int(pluie)

# ================= DATA =================
def load_champs():
    try:
        with open("champs.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_champs(data):
    with open("champs.json", "w") as f:
        json.dump(data, f)

data = load_champs()

if username not in data:
    data[username] = []

st.session_state.champs = data.get(username, [])
# ================= SIDEBAR =================
menu = st.sidebar.radio(
    "Navigation",
    ["🗺️ Carte", "➕ Ajouter", "📊 Statistiques", "🛰️ NDVI", "📤 Analyse IA", "🌡️ Météo", "📄 Rapport"]
)

st.sidebar.markdown("### 🗺️ Type de carte")

if "type_carte" not in st.session_state:
    st.session_state.type_carte = "Normal"

st.session_state.type_carte = st.sidebar.radio(
    "Fond de carte",
    ["Normal", "Satellite", "Terrain"]
)

# ================= HEADER =================
st.title("🌾 Agri Burkina 🇧🇫")
st.markdown("---")

# ================= CARTE =================
if menu == "🗺️ Carte":

    type_carte = st.session_state.type_carte

    if type_carte == "Normal":
        tiles = "OpenStreetMap"
        attr = None
    elif type_carte == "Satellite":
        tiles = "Esri.WorldImagery"
        attr = None
    else:
        tiles = "OpenTopoMap"
        attr = "© OpenTopoMap"

    # 🇧🇫 Carte centrée Burkina Faso
    carte = folium.Map(
        location=[12.3, -1.6],
        zoom_start=7,
        tiles=tiles,
        attr=attr,
        max_bounds=True
    )

    # 🔒 Limites Burkina
    carte.fit_bounds([
        [9.4, -5.5],
        [15.1, 2.5]
    ])

    # ✏️ Dessin
    Draw(export=True).add_to(carte)

    # 🌾 Zones agricoles importantes
    zones = [
        {"nom": "Bagré", "lat": 11.5, "lon": -0.5},
        {"nom": "Vallée du Sourou", "lat": 13.2, "lon": -3.4},
        {"nom": "Bobo-Dioulasso (Houet)", "lat": 11.2, "lon": -4.3},
        {"nom": "Vallée du Kou", "lat": 11.3, "lon": -4.4},
    ]

    for z in zones:
        folium.Circle(
            location=[z["lat"], z["lon"]],
            radius=15000,
            color="green",
            fill=True,
            fill_opacity=0.2,
            popup=f"🌾 Zone agricole : {z['nom']}"
        ).add_to(carte)

    # 📍 Champs utilisateur
    for champ in st.session_state.champs:
        couleur = "green" if champ["rendement"] > 4 else "orange"

        folium.Marker(
            [champ["lat"], champ["lon"]],
            popup=f"""
🌾 {champ['nom']}
Culture: {champ['culture']}
📊 Rendement: {champ['rendement']} t/ha
🌱 Sol: {champ.get('sol','?')}
🌦️ Climat: {champ.get('climat','?')}
🛰️ NDVI: {champ.get('ndvi','?')}
🌧️ Pluie: {champ.get('pluie','?')} mm
""",
            icon=folium.Icon(color=couleur)
        ).add_to(carte)

    # 🗺️ Affichage
    map_data = st_folium(carte, use_container_width=True, height=600)

    # 📍 Clic
    if map_data and map_data.get("last_clicked"):
        st.session_state.last_location = (
            map_data["last_clicked"]["lat"],
            map_data["last_clicked"]["lng"]
        )

        st.success(f"📍 Position : {st.session_state.last_location}")

    # ✏️ Dessin récupéré
    if map_data and map_data.get("all_drawings"):
        st.session_state.polygone = map_data["all_drawings"]
        st.success("✏️ Champ dessiné !")

# ================= AJOUT =================
elif menu == "➕ Ajouter":

    st.subheader("Ajouter un champ")

    carte = folium.Map(location=[12.5, -1.5], zoom_start=6)
    map_data = st_folium(carte, use_container_width=True, height=400)

    if map_data and map_data.get("last_clicked"):
        st.session_state.last_location = (
            map_data["last_clicked"]["lat"],
            map_data["last_clicked"]["lng"]
        )
        st.success(f"📍 Position sélectionnée")

    nom = st.text_input("Nom du champ")
    culture = st.text_input("Culture libre")

    st.markdown("### 📍 Ou entrer manuellement")
    lat_manual = st.number_input("Latitude", value=0.0)
    lon_manual = st.number_input("Longitude", value=0.0)

    if st.button("Ajouter"):

     if "last_location" in st.session_state:
        lat, lon = st.session_state.last_location
    else:
        lat, lon = lat_manual, lon_manual

    rendement, sol, climat, ndvi, pluie = predict_rendement(lat, lon, culture)

    nouveau = {
        "nom": nom,
        "culture": culture,
        "lat": lat,
        "lon": lon,
        "rendement": rendement,
        "sol": sol,
        "climat": climat,
        "ndvi": ndvi,
        "pluie": pluie
    }

    st.session_state.champs.append(nouveau)

    data[username] = st.session_state.champs
    save_champs(data)

    st.success("✅ Champ ajouté !")

# ================= STATS =================
elif menu == "📊 Statistiques":

    if len(st.session_state.champs) == 0:
        st.warning("Aucune donnée")
    else:
        df = pd.DataFrame(st.session_state.champs)
        st.bar_chart(df["culture"].value_counts())

# ================= NDVI =================
elif menu == "🛰️ NDVI":

    st.subheader("🛰️ NDVI Satellite Réel")

    if len(st.session_state.champs) == 0:
        st.warning("Aucun champ")
    else:
        champ = st.selectbox(
            "Choisir champ",
            st.session_state.champs,
            format_func=lambda x: x["nom"]
        )

        lat = champ["lat"]
        lon = champ["lon"]

        point = ee.Geometry.Point([lon, lat])

        image = (
            ee.ImageCollection("COPERNICUS/S2")
            .filterBounds(point)
            .filterDate("2023-01-01", "2023-12-31")
            .sort("CLOUDY_PIXEL_PERCENTAGE")
            .first()
        )

        ndvi = image.normalizedDifference(["B8", "B4"])

        map_id = ndvi.getMapId({
            "min": 0,
            "max": 1,
            "palette": ["red", "yellow", "green"]
        })

        carte = folium.Map(location=[lat, lon], zoom_start=12)

        folium.TileLayer(
            tiles=map_id["tile_fetcher"].url_format,
            attr="Google Earth Engine",
            overlay=True
        ).add_to(carte)

        folium.Marker([lat, lon]).add_to(carte)

        st_folium(carte, height=600)

# ================= IA IMAGE =================
elif menu == "📤 Analyse IA":

    file = st.file_uploader("Image plante", type=["jpg", "png"])

    if file:
        img = Image.open(file)
        st.image(img)
        st.success("🌿 Plante saine (simulation IA)")

# ================= METEO =================
elif menu == "🌡️ Météo":

    data = pd.DataFrame({
        "Jour": ["Lun", "Mar", "Mer", "Jeu", "Ven"],
        "Température": [30, 32, 31, 33, 34]
    })

    st.line_chart(data.set_index("Jour"))

# ================= PDF =================
elif menu == "📄 Rapport":

    if st.button("Générer PDF"):

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        pdf.cell(200, 10, txt="Rapport Agricole", ln=True)

        for champ in st.session_state.champs:
            pdf.cell(200, 10, txt=f"{champ['nom']} - {champ['culture']}", ln=True)

        pdf.output("rapport.pdf")

        st.success("📄 PDF créé !")
