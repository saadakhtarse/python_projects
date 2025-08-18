from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import requests
from geopy.distance import geodesic

app = Flask(__name__)

# Load your data
df = pd.read_excel("data.xlsx")

# Normalize and clean columns
df["Latitude"] = pd.to_numeric(df.get("Latitude", 0), errors="coerce").fillna(0.0)
df["Longitude"] = pd.to_numeric(df.get("Longitude", 0), errors="coerce").fillna(0.0)

# Clean phone numbers
def clean_phone(v):
    try:
        return str(int(float(str(v).strip())))
    except:
        return ""

df["TelephoneNum"] = df.get("TelephoneNum", "").apply(clean_phone)
df["AllSEN"] = df.get("AllSEN", "").fillna("")

# Serve the index.html page
@app.route("/")
def home():
    return render_template("index.html")

# API endpoint to find schools (used by script.js)
@app.route("/find-schools", methods=["POST"])
def find_schools():
    try:
        data = request.get_json()
        postcode = data.get("postcode", "").strip()
        num_schools = int(data.get("num_schools", 3))

        if not postcode:
            return jsonify({"error": "Postcode is required"}), 400

        # Get location from Postcodes.io
        res = requests.get(f"https://api.postcodes.io/postcodes/{postcode}", timeout=10)
        if res.status_code != 200:
            return jsonify({"error": "Invalid postcode"}), 400

        location_data = res.json().get("result")
        if not location_data:
            return jsonify({"error": "Could not retrieve coordinates"}), 400

        user_coords = (location_data["latitude"], location_data["longitude"])

        # Compute distance for each school
        nearby_schools = []
        for _, row in df.iterrows():
            try:
                school_coords = (float(row["Latitude"]), float(row["Longitude"]))
                distance_km = geodesic(user_coords, school_coords).km
                school_data = {
                    "EstablishmentName": row.get("EstablishmentName", "Unknown"),
                    "Address": f"{row.get('Street', '')}, {row.get('Town', '')}",
                    "Postcode": row.get("Postcode", ""),
                    "TelephoneNum": row.get("TelephoneNum", ""),
                    "Latitude": row["Latitude"],
                    "Longitude": row["Longitude"],
                    "distance_km": round(distance_km, 2)
                }
                nearby_schools.append(school_data)
            except:
                continue

        sorted_schools = sorted(nearby_schools, key=lambda x: x["distance_km"])[:num_schools]

        return jsonify({"schools": sorted_schools})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
