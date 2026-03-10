"""
VibeCheck Backend — Python/Flask REST API
AI Fashion Styling Platform
Run: pip install flask flask-cors pillow && python server.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json, os, uuid, random
from datetime import datetime
from werkzeug.utils import secure_filename

# ─────────────────────────────────────────
#  App Setup
# ─────────────────────────────────────────
app = Flask(__name__)
CORS(app)

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_FILE     = os.path.join(BASE_DIR, "db.json")
UPLOAD_DIR  = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXT = {"png", "jpg", "jpeg", "webp", "gif"}

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─────────────────────────────────────────
#  Database Helpers
# ─────────────────────────────────────────
DEFAULT_DB = {
    "wardrobe":     [],
    "outfits":      [],
    "wishlist":     [],
    "ratings":      [],
    "feedback":     [],
    "styleHistory": []
}

def read_db() -> dict:
    if not os.path.exists(DB_FILE):
        write_db(DEFAULT_DB)
        return DEFAULT_DB.copy()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def write_db(data: dict) -> None:
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def new_id() -> str:
    return str(uuid.uuid4())[:8]

def ok(data=None, msg="Success", code=200):
    body = {"success": True, "message": msg}
    if data is not None:
        body["data"] = data
    return jsonify(body), code

def err(msg="Error", code=400):
    return jsonify({"success": False, "message": msg}), code

# ─────────────────────────────────────────
#  Price List & Outfit Rules
# ─────────────────────────────────────────
PRICE_LIST = {
    "shirt":        1200,
    "jeans":        2000,
    "shoes":        3000,
    "jacket":       3500,
    "tshirt":        800,
    "trousers":     1800,
    "formal shoes": 2800,
    "sneakers":     2200,
    "boots":        3200,
    "rain jacket":  4000,
    "sweater":      1500,
    "coat":         5000,
    "shorts":        900,
    "dress":        2500,
    "skirt":        1400,
    "hoodie":       1600,
    "blazer":       4500,
    "saree":        3000,
    "kurta":        1200,
}

OCCASION_OUTFITS = {
    "party":   {"items": ["jacket", "jeans", "sneakers"],   "style": "Party Glam"},
    "office":  {"items": ["shirt", "trousers", "formal shoes"], "style": "Office Smart"},
    "wedding": {"items": ["blazer", "trousers", "formal shoes"], "style": "Wedding Formal"},
    "date":    {"items": ["shirt", "jeans", "sneakers"],    "style": "Date Night"},
    "casual":  {"items": ["tshirt", "jeans", "sneakers"],   "style": "Casual Cool"},
    "gym":     {"items": ["tshirt", "shorts", "sneakers"],  "style": "Athleisure"},
    "beach":   {"items": ["tshirt", "shorts", "shoes"],     "style": "Beach Vibes"},
}

WEATHER_OUTFITS = {
    "rainy":  {"items": ["rain jacket", "jeans", "boots"],   "tip": "Stay dry in style!"},
    "winter": {"items": ["coat", "sweater", "boots"],        "tip": "Layer up for warmth."},
    "summer": {"items": ["tshirt", "shorts", "sneakers"],    "tip": "Keep it light & breezy."},
    "spring": {"items": ["shirt", "jeans", "sneakers"],      "tip": "Fresh pastels work great."},
    "windy":  {"items": ["jacket", "trousers", "boots"],     "tip": "Avoid loose accessories."},
    "cloudy": {"items": ["hoodie", "jeans", "sneakers"],     "tip": "Comfortable layers advised."},
}

# ─────────────────────────────────────────
#  1. Wardrobe
# ─────────────────────────────────────────
@app.route("/wardrobe", methods=["POST"])
def add_wardrobe():
    body = request.get_json(silent=True) or {}
    name = (body.get("name") or "").strip()
    if not name:
        return err("Field 'name' is required.")
    item = {
        "id":       new_id(),
        "name":     name,
        "category": body.get("category", "other"),
        "color":    body.get("color", "unknown"),
        "style":    body.get("style", "casual"),
        "addedAt":  now_str(),
    }
    db = read_db()
    db["wardrobe"].append(item)
    write_db(db)
    return ok(item, "Item added to wardrobe.", 201)

@app.route("/wardrobe", methods=["GET"])
def get_wardrobe():
    db = read_db()
    return ok(db["wardrobe"], f"{len(db['wardrobe'])} items found.")

# ─────────────────────────────────────────
#  2. Smart Wardrobe Mixer
# ─────────────────────────────────────────
@app.route("/wardrobe-mix", methods=["GET"])
def wardrobe_mix():
    db = read_db()
    wardrobe = db["wardrobe"]
    if len(wardrobe) < 3:
        return err("Add at least 3 items to your wardrobe first.")
    combo = random.sample(wardrobe, 3)
    mix = {
        "id":        new_id(),
        "items":     combo,
        "mixedAt":   now_str(),
        "styleNote": "AI-mixed combination — try it out! ✨"
    }
    return ok(mix, "Smart mix generated!")

# ─────────────────────────────────────────
#  3. AI Outfit Generator
# ─────────────────────────────────────────
@app.route("/generate-outfit", methods=["POST"])
def generate_outfit():
    body     = request.get_json(silent=True) or {}
    occasion = (body.get("occasion") or "casual").lower().strip()
    weather  = (body.get("weather")  or "").lower().strip()

    # Pick by occasion, fallback to casual
    rule = OCCASION_OUTFITS.get(occasion, OCCASION_OUTFITS["casual"])

    # Weather override tip
    weather_tip = ""
    if weather and weather in WEATHER_OUTFITS:
        weather_tip = WEATHER_OUTFITS[weather]["tip"]

    outfit = {
        "id":         new_id(),
        "occasion":   occasion,
        "weather":    weather or "not specified",
        "items":      rule["items"],
        "style":      rule["style"],
        "weatherTip": weather_tip,
        "generatedAt": now_str(),
    }

    db = read_db()
    db["outfits"].append(outfit)

    # Also log to styleHistory
    db["styleHistory"].append({
        "id":        new_id(),
        "outfitId":  outfit["id"],
        "occasion":  occasion,
        "date":      now_str(),
    })
    write_db(db)
    return ok(outfit, "Outfit generated by AI!", 201)

@app.route("/outfits", methods=["GET"])
def get_outfits():
    db = read_db()
    return ok(db["outfits"], f"{len(db['outfits'])} outfits found.")

# ─────────────────────────────────────────
#  4. Weather-Based Styling
# ─────────────────────────────────────────
@app.route("/weather-style", methods=["GET"])
def weather_style():
    weather = (request.args.get("weather") or "").lower().strip()
    if not weather:
        return err("Query param 'weather' is required. e.g. ?weather=summer")
    rec = WEATHER_OUTFITS.get(weather)
    if not rec:
        options = ", ".join(WEATHER_OUTFITS.keys())
        return err(f"Unknown weather '{weather}'. Options: {options}")
    return ok({
        "weather":     weather,
        "recommended": rec["items"],
        "tip":         rec["tip"],
    }, f"Style for {weather} weather!")

# ─────────────────────────────────────────
#  5. Outfit Cost Estimator
# ─────────────────────────────────────────
@app.route("/estimate-cost", methods=["GET"])
def estimate_cost():
    raw = request.args.get("items") or ""
    if not raw:
        return err("Query param 'items' required. e.g. ?items=shirt,jeans,shoes")
    items      = [i.strip().lower() for i in raw.split(",") if i.strip()]
    breakdown  = {}
    total      = 0
    not_found  = []
    for item in items:
        price = PRICE_LIST.get(item)
        if price:
            breakdown[item] = price
            total += price
        else:
            not_found.append(item)
    return ok({
        "items":     items,
        "breakdown": breakdown,
        "total":     total,
        "currency":  "INR ₹",
        "notFound":  not_found,
    }, f"Estimated cost: ₹{total}")

# ─────────────────────────────────────────
#  6. Wishlist
# ─────────────────────────────────────────
@app.route("/wishlist", methods=["POST"])
def add_wishlist():
    body = request.get_json(silent=True) or {}
    name = (body.get("outfitName") or body.get("name") or "").strip()
    if not name:
        return err("Field 'outfitName' is required.")
    entry = {
        "id":          new_id(),
        "outfitName":  name,
        "outfitId":    body.get("outfitId", ""),
        "notes":       body.get("notes", ""),
        "addedAt":     now_str(),
    }
    db = read_db()
    db["wishlist"].append(entry)
    write_db(db)
    return ok(entry, "Saved to wishlist!", 201)

@app.route("/wishlist", methods=["GET"])
def get_wishlist():
    db = read_db()
    return ok(db["wishlist"], f"{len(db['wishlist'])} wishlist items.")

# ─────────────────────────────────────────
#  7. Style Ratings
# ─────────────────────────────────────────
@app.route("/ratings", methods=["POST"])
def add_rating():
    body = request.get_json(silent=True) or {}
    outfit_id = (body.get("outfitId") or "").strip()
    try:
        stars = int(body.get("stars", 0))
    except (ValueError, TypeError):
        stars = 0
    if not outfit_id:
        return err("Field 'outfitId' is required.")
    if stars < 1 or stars > 5:
        return err("Field 'stars' must be between 1 and 5.")
    rating = {
        "id":        new_id(),
        "outfitId":  outfit_id,
        "stars":     stars,
        "ratedAt":   now_str(),
    }
    db = read_db()
    db["ratings"].append(rating)
    write_db(db)
    return ok(rating, f"Rated {stars} ⭐", 201)

@app.route("/ratings", methods=["GET"])
def get_ratings():
    db = read_db()
    ratings = db["ratings"]
    avg = round(sum(r["stars"] for r in ratings) / len(ratings), 2) if ratings else 0
    return ok({"ratings": ratings, "average": avg, "count": len(ratings)})

# ─────────────────────────────────────────
#  8. Style Feedback
# ─────────────────────────────────────────
@app.route("/feedback", methods=["POST"])
def add_feedback():
    body = request.get_json(silent=True) or {}
    msg  = (body.get("message") or "").strip()
    if not msg:
        return err("Field 'message' is required.")
    fb = {
        "id":        new_id(),
        "message":   msg,
        "outfitId":  body.get("outfitId", ""),
        "emoji":     body.get("emoji", ""),
        "date":      now_str(),
    }
    db = read_db()
    db["feedback"].append(fb)
    write_db(db)
    return ok(fb, "Feedback submitted!", 201)

@app.route("/feedback", methods=["GET"])
def get_feedback():
    db = read_db()
    return ok(db["feedback"], f"{len(db['feedback'])} feedback entries.")

# ─────────────────────────────────────────
#  9. Search Outfits
# ─────────────────────────────────────────
@app.route("/search", methods=["GET"])
def search():
    q = (request.args.get("q") or "").lower().strip()
    if not q:
        return err("Query param 'q' is required. e.g. ?q=jeans")
    db      = read_db()
    results = []
    for outfit in db["outfits"]:
        items_str = " ".join(outfit.get("items", [])).lower()
        if (q in outfit.get("occasion", "").lower() or
            q in outfit.get("style", "").lower()    or
            q in items_str):
            results.append(outfit)
    return ok(results, f"{len(results)} results for '{q}'.")

# ─────────────────────────────────────────
#  10. Image Upload
# ─────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@app.route("/upload-image", methods=["POST"])
def upload_image():
    if "image" not in request.files:
        return err("No file field named 'image' in the request.")
    file = request.files["image"]
    if file.filename == "":
        return err("No file selected.")
    if not allowed_file(file.filename):
        return err(f"File type not allowed. Allowed: {', '.join(ALLOWED_EXT)}")
    ext      = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{new_id()}.{ext}"
    save_path = os.path.join(UPLOAD_DIR, secure_filename(filename))
    file.save(save_path)
    return ok({
        "filename":  filename,
        "url":       f"/uploads/{filename}",
        "uploadedAt": now_str(),
    }, "Image uploaded successfully!", 201)

# Serve uploaded files
from flask import send_from_directory
@app.route("/uploads/<filename>")
def serve_upload(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ─────────────────────────────────────────
#  11. Style History
# ─────────────────────────────────────────
@app.route("/history", methods=["GET"])
def get_history():
    db = read_db()
    history = sorted(db["styleHistory"], key=lambda x: x["date"], reverse=True)
    return ok(history, f"{len(history)} history records.")

# ─────────────────────────────────────────
#  12. Stats Dashboard
# ─────────────────────────────────────────
@app.route("/stats", methods=["GET"])
def get_stats():
    db = read_db()
    ratings = db["ratings"]
    avg_rating = round(sum(r["stars"] for r in ratings) / len(ratings), 2) if ratings else 0
    return ok({
        "wardrobe":     len(db["wardrobe"]),
        "outfits":      len(db["outfits"]),
        "wishlist":     len(db["wishlist"]),
        "ratings":      len(ratings),
        "avgRating":    avg_rating,
        "feedback":     len(db["feedback"]),
        "styleHistory": len(db["styleHistory"]),
    }, "Platform stats retrieved.")

# ─────────────────────────────────────────
#  13. Health Check
# ─────────────────────────────────────────
@app.route("/", methods=["GET"])
@app.route("/health", methods=["GET"])
def health():
    return ok({
        "platform": "VibeCheck AI Fashion",
        "version":  "1.0.0",
        "status":   "running",
        "port":     5000,
    }, "VibeCheck backend is live! 🚀")

# ─────────────────────────────────────────
#  Error Handlers
# ─────────────────────────────────────────
@app.errorhandler(404)
def not_found(_):
    return err("Route not found.", 404)

@app.errorhandler(405)
def method_not_allowed(_):
    return err("Method not allowed.", 405)

@app.errorhandler(500)
def server_error(_):
    return err("Internal server error.", 500)

# ─────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────
if __name__ == "__main__":
    # Ensure fresh db.json exists
    read_db()

    print("=" * 50)
    print("🚀 VibeCheck Backend Running on Port 5000")
    print("=" * 50)
    print("📌 Base URL  : http://localhost:5000")
    print()
    print("📋 Available Endpoints:")
    endpoints = [
        ("POST", "/wardrobe",         "Add wardrobe item"),
        ("GET",  "/wardrobe",         "Get all wardrobe items"),
        ("GET",  "/wardrobe-mix",     "Smart outfit mix"),
        ("POST", "/generate-outfit",  "AI outfit generator"),
        ("GET",  "/outfits",          "Get all outfits"),
        ("GET",  "/weather-style",    "Weather-based styling"),
        ("GET",  "/estimate-cost",    "Outfit cost estimator"),
        ("POST", "/wishlist",         "Add to wishlist"),
        ("GET",  "/wishlist",         "Get wishlist"),
        ("POST", "/ratings",          "Rate an outfit"),
        ("GET",  "/ratings",          "Get all ratings"),
        ("POST", "/feedback",         "Submit feedback"),
        ("GET",  "/feedback",         "Get all feedback"),
        ("GET",  "/search",           "Search outfits"),
        ("POST", "/upload-image",     "Upload clothing image"),
        ("GET",  "/history",          "Style history"),
        ("GET",  "/stats",            "Platform statistics"),
        ("GET",  "/health",           "Health check"),
    ]
    for method, route, desc in endpoints:
        print(f"  {method:<5}  {route:<22}  {desc}")
    print()
    print("📦 Database : db.json")
    print("🖼️  Uploads  : ./uploads/")
    print("=" * 50)

    app.run(host="0.0.0.0", port=5000, debug=True)
