from flask import Flask, render_template, request, jsonify
import pandas as pd
import folium
from geopy.distance import geodesic
import requests

app = Flask(__name__)

# ---------- LOAD & PREPARE DATA ----------
DATA_FILE = "data.xlsx"
df = pd.read_excel(DATA_FILE)

# Rename columns for consistency
rename_map = {
    "SpecialClasses (name)": "HasSpecialClasses",
    "Gender (name)": "Gender",
    "HeadTitle (name)": "HeadTitle",
    "OfstedRating (name)": "Rating",
}
df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

# Fill missing expected columns
for col in ["TelephoneNum", "AllSEN", "Gender", "Rating"]:
    if col not in df.columns:
        df[col] = ""

# Format phone numbers
def fmt_phone(v):
    s = str(v).strip()
    if s == "" or s.lower() == "nan":
        return ""
    try:
        return str(int(float(s)))
    except Exception:
        return s

df["TelephoneNum"] = df["TelephoneNum"].apply(fmt_phone)

# Clean coordinate data
df["Latitude"] = pd.to_numeric(df.get("Latitude", 0), errors="coerce").fillna(0.0)
df["Longitude"] = pd.to_numeric(df.get("Longitude", 0), errors="coerce").fillna(0.0)

# ---------- ROUTES ----------
@app.route("/", methods=["GET", "POST"])
def index():
    schools = []
    map_html = ""
    error = None

    if request.method == "POST":
        postcode = request.form.get("postcode", "").strip()
        limit = int(request.form.get("limit", 3))
        gender = request.form.get("gender", "").strip()
        ofsted = request.form.get("ofsted", "").strip()
        sen_raw = request.form.get("sen", "").strip()

        # Get coordinates using Postcodes.io
        try:
            res = requests.get(f"https://api.postcodes.io/postcodes/{postcode}", timeout=10).json()
            if res.get("status") != 200:
                raise ValueError("Invalid postcode")
            user_lat = res["result"]["latitude"]
            user_lon = res["result"]["longitude"]
        except Exception:
            error = "Invalid postcode or network issue. Please try again."
            return render_template("index.html", error=error)

        # Apply filters
        filtered_df = df.copy()
        if gender:
            filtered_df = filtered_df[filtered_df["Gender"] == gender]
        if ofsted:
            filtered_df = filtered_df[filtered_df["Rating"] == ofsted]

        if sen_raw:
            terms = [t.strip().lower() for t in sen_raw.split(",") if t.strip()]
            allsen = filtered_df["AllSEN"].astype(str).str.lower()
            mask = allsen.apply(lambda txt: any(term in txt for term in terms))
            filtered_df = filtered_df[mask]

        # Calculate distances
        results = []
        for _, row in filtered_df.iterrows():
            lat, lon = row["Latitude"], row["Longitude"]
            if lat == 0.0 or lon == 0.0:
                continue

            distance = round(geodesic((user_lat, user_lon), (lat, lon)).miles)
            results.append({
                "EstablishmentName": row.get("EstablishmentName", ""),
                "Street": row.get("Street", ""),
                "Town": row.get("Town", ""),
                "Postcode": row.get("Postcode", ""),
                "TelephoneNum": row.get("TelephoneNum", ""),
                "Gender": row.get("Gender", ""),
                "HasSpecialClasses": row.get("HasSpecialClasses", ""),
                "Rating": row.get("Rating", "N/A"),
                "AllSEN": row.get("AllSEN", ""),
                "Latitude": lat,
                "Longitude": lon,
                "distance_miles": distance
            })

        schools = sorted(results, key=lambda x: x["distance_miles"])[:limit]

        # Create Map
        if schools:
            m = folium.Map(location=[user_lat, user_lon], zoom_start=12, control_scale=True)
            folium.Marker([user_lat, user_lon], tooltip="You", icon=folium.Icon(color="green")).add_to(m)

            for s in schools:
                folium.Marker(
                    [s["Latitude"], s["Longitude"]],
                    tooltip=f"{s['EstablishmentName']} ({s['distance_miles']} miles)",
                    icon=folium.Icon(color="red")
                ).add_to(m)
                folium.PolyLine(
                    [(user_lat, user_lon), (s["Latitude"], s["Longitude"])],
                    color="blue", weight=2, opacity=0.6
                ).add_to(m)

            map_html = m._repr_html_()

    return render_template("index.html", schools=schools, map_html=map_html, error=error)

# ---------- MAIN ----------
if __name__ == "__main__":
    #app.run(debug=False, use_reloader=False)
    app.run(host="0.0.0.0", port=5000)
