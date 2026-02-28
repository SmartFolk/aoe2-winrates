from flask import Flask, render_template, jsonify
import pandas as pd
import glob
import os
from civ_mapper import CIV_ID_TO_NAME

app = Flask(__name__)

DATA_FOLDER = "data"

def load_all_csvs():
    csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    
    dataframes = []
    
    for file in csv_files:
        df = pd.read_csv(file)
        dataframes.append(df)
    
    if not dataframes:
        return pd.DataFrame()
    
    return pd.concat(dataframes, ignore_index=True)


def calculate_winrates():
    df = load_all_csvs()

    if df.empty:
        return []

    # Safely convert numeric columns
    df["civ"] = pd.to_numeric(df["civ"], errors="coerce")
    df["leaderboard_id"] = pd.to_numeric(df["leaderboard_id"], errors="coerce")

    # Drop rows missing required data
    df = df.dropna(subset=["civ", "leaderboard_id"])

    # Convert to integers
    df["civ"] = df["civ"].astype(int)
    df["leaderboard_id"] = df["leaderboard_id"].astype(int)

    # Normalize won column
    df["won"] = df["won"].astype(str).str.lower() == "t"

    # Filter only leaderboard_id = 3
    df = df[df["leaderboard_id"] == 3]

    # Map civ ID → civ name
    df["civ_name"] = df["civ"].map(CIV_ID_TO_NAME)
    df["civ_name"] = df["civ_name"].fillna("Unknown Civ")

    # Group and calculate win rates
    summary = df.groupby("civ_name")["won"].agg(["count", "sum"]).reset_index()
    summary["winrate"] = round((summary["sum"] / summary["count"]) * 100, 2)

    results = summary.rename(columns={
        "civ_name": "name",
        "count": "games"
    })[["name", "winrate", "games"]]

    return results.sort_values("winrate", ascending=False).to_dict(orient="records")


WINRATE_CACHE = calculate_winrates()


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/winrates")
def winrates():
    return jsonify(WINRATE_CACHE)


if __name__ == "__main__":
    app.run()