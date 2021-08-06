from flask import Flask
import hmac
import sqlite3

from flask_jwt import *
from flask_cors import CORS
import re

from flask_mail import Mail, Message

regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'


class User(object):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password


class Product(object):
    def __init__(self, title, category, quantity, total, cost):
        self.title = title
        self.category = category
        self.quantity = quantity
        self.total = total
        self.cost = cost


class dbase(object):
    def __init__(self):
        self.conn = sqlite3.connect('sales.db')
        self.cursor = self.conn.cursor()

    def sending_to_dbase(self, query, values):
        self.cursor.execute(query, values)
        self.conn.commit()

    def item_select(self, query):
        self.cursor.execute(query)

    def fetch(self):
        return self.cursor.fetchall()


def fetch_users():
    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        the_users = cursor.fetchall()

        new_data = []

        for data in the_users:
            new_data.append(User(data[0], data[4], data[5]))
    return new_data


def fetch_items():
    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * from items")
        items = cursor.fetchall()

        new_data = []

        for data in items:
            new_data.append(Product(data[0], data[1], data[2], data[3], data[4]))
        return new_data


users = fetch_users()
products = fetch_items()


def init_user_table():
    conn = sqlite3.connect('sales.db')
    print("Opened database successfully")

    conn.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "cell_number TEXT NOT NULL,"
                 "email TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


def init_item_table():
    with sqlite3.connect('sales.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "title TEXT NOT NULL,"
                     "category TEXT NOT NULL,"
                     "quantity TEXT NOT NULL,"
                     "total TEXT NOT NULL,"
                     "cost TEXT NOT NULL)")
    print("item table created successfully.")
    conn.close()


init_user_table()
init_item_table()

our_users = fetch_users()

username_table = {u.username: u for u in our_users}
userid_table = {u.id: u for u in our_users}


def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)


app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'this-should-be-a-secret'
CORS(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'testingflask005@gmail.com'
app.config['MAIL_PASSWORD'] = 'TestingFlask001'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


@app.route('/register/', methods=["POST"])
def user_registration():
    response = {}
    db = dbase

    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        cell = request.form['cell_number']
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        if re.search(regex, email):
            query = "INSERT INTO users(first_name, last_name, cell_number, email, username, password) VALUES(?, ?, ?, ?, ?, ?)"
            values = first_name, last_name, cell, email, username, password
            db.sending_to_dbase(query, values)
            mail = Mail(app)
            msg = Message('You have successfully been registered', sender='testingflask005@gmail.com', recipients=[email])
            msg.body = 'This is where you should be'
            mail.send(msg)
            response["message"] = "success"
            response["status_code"] = 201
        return response

    else:
        return 'The email could not be sent'


@app.route("/see-profile/<int:user_id>", methods=["GET"])
@jwt_required()
def view_profile(user_id):
    response = {}
    db = dbase()

    query = "SELECT * FROM user WHERE user_id= " + str(user_id)
    db.item_select(query)

    if user_id == []:

        return "User does not exist"
    else:
        response['status_code'] = 200
        response['data'] = db.fetch()

        return response


@app.route('/product-create/', methods=['POST'])
@jwt_required()
def products_create():
    response = {}
    db = dbase

    if request.method == "POST":
        title = request.form['title']
        category = request.form['category']
        quantity = request.form['quantity']
        cost = request.form['cost']
        total = int(cost) * int(quantity)

        if quantity or cost != int:
            return "Please enter integer values for price and quantity"
        else:

            query = "INSERT INTO products(title, category, quantity, cost, total) VALUES(?, ?, ?, ?, ?)"
            values = title, category, quantity, cost, total
            db.sending_to_dbase(query, values)
            response['description'] = 'Items has been added successfully'
            response['status_code'] = '201'

            return response


@app.route('/show-products/', methods=['GET'])
def get_products():
    response = {}
    db = dbase()

    query = "SELECT * FROM items"
    db.item_select(query)

    response['status_code'] = 201
    response['data'] = db.fetch()
    return response


@app.route("/adding-items/", methods=["POST"])
@jwt_required()
def add():
    response = {}
    db = dbase()

    if request.method == "POST":
        title = request.form['title']
        category = request.form['category']
        quantity = request.form['quantity']
        cost = request.form['cost']
        total = int(cost) * int(quantity)

        if quantity or cost != int:
            return "Please enter integer values for cost and quantity"
        else:

            query = "INSERT INTO products(title, category, quantity, cost, total) VALUES(?, ?, ?, ?, ?)"
            values = title, category, quantity, cost, total
            db.sending_to_dbase(query, values)
            response["status_code"] = 201
            response['description'] = "item is added"

            return response


@app.route("/updating-items/<int:id>", methods=["PUT"])
@jwt_required()
def edit(product_id):
    response = {}
    db = dbase()

    if request.method == "PUT":
        title = request.form['title']
        category = request.form['category']
        quantity = request.form['quantity']
        cost = request.form['cost']
        total = int(cost) * int(quantity)

        if quantity or cost != int:
            return "Please enter integer values for cost and quantity"
        else:

            query = "UPDATE product SET title=?, category=?, quantity=?, cost=?, total=?" \
                    " WHERE product_id='" + str(product_id) + "'"
            values = title, category, quantity, cost, total

            db.sending_to_dbase(query, values)

            response['message'] = 201
            response['message'] = "Product has been added"
            return response


@app.route("/delete-product/<int:id>")
@jwt_required()
def delete(id):
    response = {}
    db = dbase()

    query = "DELETE FROM products WHERE id=" + str(id)
    db.item_select(query)
    # error handling to check if the id exists
    if id == []:
        return "product doesn't exist"
    else:
        response['status_code'] = 201
        response['message'] = "item deleted successfully."
        return response


if __name__ == "__main__":
    app.debug = True
    app.run()
