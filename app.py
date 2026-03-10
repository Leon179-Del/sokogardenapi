# Importing flask
from flask import *
import os

# import pymysql module => it helps us to create a connection between python flask and my sql database.
import pymysql

# CORS = 


# Create a flask application and give it a name
app = Flask(__name__)

# configure the location where your product imageswill be saved on your application
app.config["UPLOAD_FOLDER"] = "static/images"

# Below is the sign up route
@app.route("/api/signup", methods = ["POST"])
def signup():
    if request.method == "POST":
        #extract the different details entered on the form
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]

        # by use of the print function lets print all the details sent with the the upcoming requests
        # print(username,email,password,phone) 

        # Establish a connection between flask/python and my sql
        connection = pymysql.connect(host="localhost", user="root",password="",database="sokogardenonline")
        
        # create a cursor to execute the sql queries
        cursor = connection.cursor()

        # Structure an sql to insert details received from the form
        # The %s is a place holder=> it stands in places of actual values we shall replace them later
        sql = "INSERT INTO users(username,email,phone,password) VALUES(%s,%s,%s,%s)"

        # Create a tuple that will hold all the data gotten from the form
        data = (username, email, phone, password)

        # By use of the cursor execute the sql as you replace the placeholders with the actual values.
        cursor.execute(sql, data)

        # commit the changes to the database
        connection.commit()

        


        return jsonify ({"message": "User registered successfully"})
    

#Below is the signin rout
@app.route("/api/signin", methods=["POST"]) 
def signin():
    if request.method == "POST":
        # extract the two details entered on the form
        email = request.form["email"]
        password = request.form["password"]

        # print out the details entered
        # print(email,password)

        # Establish a connection to the database
        connection = pymysql.connect(host="localhost", user="root", password="", database="sokogardenonline" )

        # create a cursor
        cursor = connection.cursor(pymysql.cursors.DictCursor)

        # structure the sql query that will check weather the email and the password entered are correct
        sql = "SELECT * FROM users WHERE email = %s AND password = %s"

        # put the data received from into tupple
        data = (email, password)

        # By use of the cursor execute the sql

        cursor.execute(sql, data)

        # check weather there row returned and store them on a variable
        count= cursor.rowcount

        # if there are records returned it means the password and email is correct otherwise its wrong
        if count == 0:
            return jsonify({"message" : "Login failed"})
        else:
            # THere must be a user so we create a variable that will hold the details of the users fetched from the database
            user = cursor.fetchone()
            # return the details to the front end as well as a message
            return jsonify({"message" : "user loged in successful", "user":user})
        

 
# below is a route for adding products
@app.route("/api/add_product", methods=["POST"])
def add_products():
    if request.method == "POST":
        # extract the data entered on the form
        product_name = request.form["product_name"]
        product_description = request.form["product_description"]
        product_cost = request.form["product_cost"]
        # for the product photo we shall fetch it from the files
        product_photo = request.files["product_photo"]
        
        # extract the filename of the product photo
        filename = product_photo.filename
        # by use of the os module(operating system) we can extract the file name where the image is currently saved
        photo_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        # save the product photo image into the new location
        product_photo.save(photo_path)
        
        # print them out to test weather you are receiving the details sent with the request
        # print(  product_name, product_description, product_cost , product_photo )
        # establish a connection with the DB
        connection = pymysql.connect(host= "localhost", user="root", password="", database="sokogardenonline")
        
        # create a cursor
        cursor = connection.cursor()
        sql = "INSERT INTO product_details(product_name, product_description, product_cost, product_photo) VALUES (%s, %s, %s, %s)"
        # create a tupple that will hold the data from a form that which are current held onto different variable
       
        data = ( product_name, product_description,  product_cost,
        filename )
        # use the cursor to execute the sql while replacing the place holders with the data
        cursor.execute(sql,data)
        
        # commit the changes to the database
        connection.commit()
        
        
        return jsonify({"message" : " product added successfuly" })

# Get functionality API
@app.route("/api/get_product")
def get_product ():
    # create a connection to the database
    connection = pymysql.connect(host = "localhost", user = "root",passwd="",database="sokogardenonline" )
    # create a cursor
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    # structure an sql querry to fetch all the products from the database
    sql = "SELECT * FROM product_details"
    
    # Execute the querry
    cursor.execute(sql)
    
    # create a variable that will hold the data fetched from the table
    products = cursor.fetchall()
    
    
    return jsonify (products)

# Mpesa Payment Route/Endpoint 
import requests
import datetime
import base64
from requests.auth import HTTPBasicAuth
 
@app.route('/api/mpesa_payment', methods=['POST'])
def mpesa_payment():
    if request.method == 'POST':
        amount = request.form['amount']
        phone = request.form['phone']
        # GENERATING THE ACCESS TOKEN
        # create an account on safaricom daraja
        consumer_key = "GTWADFxIpUfDoNikNGqq1C3023evM6UH"
        consumer_secret = "amFbAoUByPV2rM5A"
 
        api_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"  # AUTH URL
        r = requests.get(api_URL, auth=HTTPBasicAuth(consumer_key, consumer_secret))
 
        data = r.json()
        access_token = "Bearer" + ' ' + data['access_token']
 
        #  GETTING THE PASSWORD
        timestamp = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'
        business_short_code = "174379"
        data = business_short_code + passkey + timestamp
        encoded = base64.b64encode(data.encode())
        password = encoded.decode('utf-8')
 
        # BODY OR PAYLOAD
        payload = {
            "BusinessShortCode": "174379",
            "Password": "{}".format(password),
            "Timestamp": "{}".format(timestamp),
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,  # use 1 when testing
            "PartyA": phone,  # change to your number
            "PartyB": "174379",
            "PhoneNumber": phone,
            "CallBackURL": "https://modcom.co.ke/api/confirmation.php",
            "AccountReference": "account",
            "TransactionDesc": "account"
        }
 
        # POPULAING THE HTTP HEADER
        headers = {
            "Authorization": access_token,
            "Content-Type": "application/json"
        }
 
        url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"  # C2B URL
 
        response = requests.post(url, json=payload, headers=headers)
        print(response.text)
        return jsonify({"message": "Please Complete Payment in Your Phone and we will deliver in minutes"})





# run the application
app.run(debug=True)