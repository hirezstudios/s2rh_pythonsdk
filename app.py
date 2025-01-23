import os
import json
from flask import Flask, request, jsonify, render_template, send_from_directory
from smite2_rh_sdk import Smite2RallyHereSDK

app = Flask(__name__)

# Initialize the SDK (be sure your environment variables are set 
# or your constructor is configured properly)
sdk = Smite2RallyHereSDK()

@app.route("/")
def index():
    # Serve the main HTML page
    return render_template("index.html")

@app.route("/api/s2_fetch_full_data", methods=["GET"])
def api_s2_fetch_full_data():
    """
    Example endpoint that calls S2_fetch_full_player_data_by_displayname
    using query params: ?platform=Steam&display_name=Weak3n

    Returns detailed data under:
      {
        "PlayerInfo": {...},
        "PlayerStats": [...],
        "MatchHistory": [...]
      }
    """
    platform = request.args.get("platform", "").strip()
    display_name = request.args.get("display_name", "").strip()
    max_matches_str = request.args.get("max_matches", "10")
    
    if not platform or not display_name:
        return jsonify({"error": "Missing 'platform' or 'display_name'"}), 400

    try:
        max_matches = int(max_matches_str)
        if max_matches < 1 or max_matches > 300:
            max_matches = 10
    except ValueError:
        max_matches = 10

    try:
        result = sdk.S2_fetch_full_player_data_by_displayname(
            platform=platform,
            display_name=display_name,
            max_matches=max_matches
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Optionally, an endpoint to serve items.json if you want the client to load it via /items.json
@app.route("/items.json", methods=["GET"])
def serve_items_json():
    """
    Serve the items.json file from your local directory. Alternatively,
    you can configure the server to simply serve static files from 
    a directory. This example is for demonstration.
    """
    items_path = os.path.join(os.path.dirname(__file__), "items.json")
    if not os.path.exists(items_path):
        return jsonify({"error": "items.json not found"}), 404

    with open(items_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

if __name__ == "__main__":
    # You could also use 'flask run' if you prefer
    app.run(debug=True) 