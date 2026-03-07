# Importing flask
from flask import *

# import pymysql module => it helps us to create a connection between python flask and my sql database.
import pymysql


# Create a flask application and give it a name
app = Flask(__name__)

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













# run the application
app.run(debug=True)