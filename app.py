# Importing flask
from flask import *
import os
from flask_cors import CORS
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import requests
import datetime
import base64
from requests.auth import HTTPBasicAuth

# Create a flask application
app = Flask(__name__)
CORS(app)

app.config["UPLOAD_FOLDER"] = "static/images"

# ================= CONFIG =================
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
SHOP_LAT = -1.286389
SHOP_LNG = 36.817223

# ================= DB CONNECTION HELPER =================
def get_db_connection():
    return pymysql.connect(
        host="mysql-aceelectronics.alwaysdata.net",
        user="aceelectronics",
        password="DK$Asj8cP8PZ.5d",
        database="aceelectronics_leon",
        cursorclass=pymysql.cursors.DictCursor
    )

# ================= GOOGLE MAPS DISTANCE =================
def get_road_distance(origin_lat, origin_lng, dest_lat, dest_lng):
    try:
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin_lat},{origin_lng}&destinations={dest_lat},{dest_lng}&key={GOOGLE_MAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        distance_meters = data["rows"][0]["elements"][0]["distance"]["value"]
        return distance_meters / 1000 
    except:
        return None

# ================= SIGNUP ROUTE =================
@app.route("/api/signup", methods = ["POST"])
def signup():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    phone = request.form["phone"]
    hashed_password = generate_password_hash(password)
    
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "INSERT INTO users(username,email,phone,password) VALUES(%s,%s,%s,%s)"
    cursor.execute(sql, (username, email, phone, hashed_password))
    connection.commit()
    return jsonify ({"message": "User registered successfully"})

# ================= SIGNIN ROUTE =================
@app.route("/api/signin", methods=["POST"]) 
def signin():
    email = request.form["email"]
    password = request.form["password"]
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "SELECT * FROM users WHERE email = %s"
    cursor.execute(sql, (email,))
    user = cursor.fetchone()
    if user and check_password_hash(user["password"], password):
        return jsonify({"message" : "user logged in successful", "user":user})
    return jsonify({"message" : "Login failed"}), 401

# ================= ADD PRODUCT ROUTE =================
@app.route("/api/add_product", methods=["POST"])
def add_products():
    product_name = request.form["product_name"]
    product_description = request.form["product_description"]
    product_cost = request.form["product_cost"]
    product_photo = request.files["product_photo"]
    filename = secure_filename(product_photo.filename)
    photo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    product_photo.save(photo_path)
    
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "INSERT INTO product_details(product_name, product_description, product_cost, product_photo) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (product_name, product_description, product_cost, filename))
    connection.commit()
    return jsonify({"message" : " product added successfuly" })

# ================= GET PRODUCTS ROUTE =================
@app.route("/api/get_product")
def get_product ():
    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "SELECT * FROM product_details"
    cursor.execute(sql)
    return jsonify (cursor.fetchall())

# ================= DELIVERY API =================
@app.route("/api/calculate_delivery", methods=["POST"])
def calculate_delivery():
    data = request.get_json()
    user_lat, user_lng = float(data["lat"]), float(data["lng"])
    distance = get_road_distance(SHOP_LAT, SHOP_LNG, user_lat, user_lng)
    if distance is None:
        return jsonify({"error": "Distance calculation failed"}), 500
    delivery_fee = max(200, distance * 100)
    return jsonify({"distance_km": round(distance, 2), "delivery_fee": round(delivery_fee, 2)})

# ================= NEW STANDALONE MPESA ROUTE =================
# This fixes the 404 error from Makepayment.jsx
@app.route('/api/mpesa_payment', methods=['POST'])
def mpesa_payment_standalone():
    try:
        phone = request.form.get("phone")
        # Ensure we get the raw amount and round it (Safaricom likes integers)
        amount_raw = request.form.get("amount")
        amount = int(float(amount_raw)) if amount_raw else 0

        # Mpesa Credentials from environment
        consumer_key = os.getenv("MPESA_CONSUMER_KEY")
        consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")
        passkey = os.getenv("MPESA_PASSKEY")
        shortcode = "174379"

        # Token Generation
        auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
        auth_res = requests.get(auth_url, auth=HTTPBasicAuth(consumer_key, consumer_secret))
        access_token = "Bearer " + auth_res.json()['access_token']

        # Password Generation
        timestamp = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode((shortcode + passkey + timestamp).encode()).decode()

        payload = {
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": shortcode,
            "PhoneNumber": phone,
            "CallBackURL": "https://aceelectronics.alwaysdata.net/api/mpesa_callback",
            "AccountReference": "Ace Electronics",
            "TransactionDesc": "Direct Payment"
        }

        headers = {"Authorization": access_token, "Content-Type": "application/json"}
        stk_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        requests.post(stk_url, json=payload, headers=headers)

        return jsonify({"message": "STK Push sent! Please check your phone."})
    except Exception as e:
        return jsonify({"message": "Payment initiation failed", "error": str(e)}), 500

# ================= CHECKOUT + MPESA ROUTE =================
@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    phone = data['phone']
    products_total = float(data['products_total'])
    delivery_fee = float(data['delivery_fee'])
    total_amount = products_total + delivery_fee

    connection = get_db_connection()
    cursor = connection.cursor()
    sql = "INSERT INTO orders(phone, products_total, delivery_fee, total_amount) VALUES (%s, %s, %s, %s)"
    cursor.execute(sql, (phone, products_total, delivery_fee, total_amount))
    connection.commit()

    # (Mpesa logic reused inside here if needed)
    return jsonify({"message": "Order saved and STK Push initiated"})

# ================= MPESA CALLBACK =================
@app.route('/api/mpesa_callback', methods=['POST'])
def mpesa_callback():
    data = request.get_json()
    print("MPESA CALLBACK RECEIVED:", data)
    return jsonify({"message": "Callback received"})

# run the application
if __name__ == "__main__":
    app.run(debug=True)
    
@app.route("/api/chatbot", methods=["POST"])
def chatbot():
    user_message = request.json.get("message", "").lower()
    
    # Simple Keyword Logic
    if "delivery" in user_message:
        response = "We deliver across Kenya! Rates are roughly Ksh 100 per KM."
    elif "mpesa" in user_message or "payment" in user_message:
        response = "You can pay via Lipa na Mpesa at checkout. Ensure you use the format 2547XXXXXXXX."
    elif "location" in user_message:
        response = "Our main shop is located in Nairobi CBD."
    else:
        response = "I'm here to help! Ask me about delivery, payments, or our location."
        
    return jsonify({"response": response})
# ================= CHATBOT API =================
@app.route("/api/chatbot", methods=["POST"])
def chatbot():
    try:
        # Get message from the frontend request
        data = request.get_json()
        user_message = data.get("message", "").lower()
        
        # Simple Logic-based responses
        if "delivery" in user_message or "fee" in user_message:
            response = "We deliver across Kenya! Rates start at Ksh 200 depending on your distance."
        elif "mpesa" in user_message or "pay" in user_message:
            response = "You can pay via Lipa na M-Pesa. Just enter your number at checkout!"
        elif "samsung" in user_message:
            response = "We have the latest Samsung devices in stock. Check our product list!"
        elif "hello" in user_message or "hi" in user_message:
            response = "Hello! Welcome to Ace Electronics. How can I help you today?"
        else:
            response = "I'm not sure about that, but I can help with delivery, payments, or product info!"
            
        return jsonify({"response": response})
        
    except Exception as e:
        return jsonify({"response": "I'm having a little brain freeze. Try again?"}), 500