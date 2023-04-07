# ? Cross-origin Resource Sharing - here it allows the view and core applications deployed on different ports to communicate. No need to know anything about it since it's only used once
import datetime
from flask_cors import CORS, cross_origin
# ? Python's built-in library for JSON operations. Here, is used to convert JSON strings into Python dictionaries and vice-versa
import json
# ? flask - library used to write REST API endpoints (functions in simple words) to communicate with the client (view) application's interactions
# ? request - is the default object used in the flask endpoints to get data from the requests
# ? Response - is the default HTTP Response object, defining the format of the returned data by this api
from flask import Flask, request, Response
# ? sqlalchemy is the main library we'll use here to interact with PostgresQL DBMS
import sqlalchemy
# ? Just a class to help while coding by suggesting methods etc. Can be totally removed if wanted, no change
from typing import Dict

from flask import render_template, redirect, url_for
from flask import Flask, request, Response, session
from flask_login import current_user, login_required, login_user, logout_user, UserMixin
from flask_login.login_manager import LoginManager
from sqlalchemy.sql import func
from flask_sqlalchemy import SQLAlchemy

# ? web-based applications written in flask are simply called apps are initialized in this format from the Flask base class. You may see the contents of `__name__` by hovering on it while debugging if you're curious
app = Flask(__name__)

app.secret_key = 'postgres'

# ? Just enabling the flask app to be able to communicate with any request source
CORS(app)

# ? building our `engine` object from a custom configuration string
# ? for this project, we'll use the default postgres user, on a database called `postgres` deployed on the same machine
YOUR_POSTGRES_PASSWORD = "postgres"
connection_string = f"postgresql://postgres:{YOUR_POSTGRES_PASSWORD}@localhost/postgres"
engine = sqlalchemy.create_engine(
    "postgresql://postgres:postgres@localhost/postgres", future=False
)

# ? `db` - the database (connection) object will be used for executing queries on the connected database named `postgres` in our deployed Postgres DBMS
db = engine.connect()

# ? A dictionary containing
data_types = {
    'boolean': 'BOOL',
    'integer': 'INT',
    'text': 'TEXT',
    'time': 'TIME',
}

# ? @app.get is called a decorator, from the Flask class, converting a simple python function to a REST API endpoint (function)

# Define routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == "admin@rentronics.com" and password == "admin":
            return redirect(url_for('sql'))
        x = db.execute("SELECT * FROM users WHERE email=%s AND passwords=%s", [(email, password)])
        user = x.fetchone()
        session["user_id"] = email
        if user is not None:
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid email or password. Please try again.'
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        contact_number = request.form['phone_num']
        password = request.form['password']
        db.execute("INSERT INTO users (first_name, last_name, passwords, email, contact_information) VALUES (%s, %s, %s, %s, %s)", [(first_name, last_name, password, email, contact_number)])
#        db.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    listbrands = db.execute("SELECT distinct brand FROM items").fetchall()      
    listcat = db.execute("SELECT distinct category FROM items").fetchall()   
    session.get("user_id")
    x = db.execute("SELECT * FROM items WHERE upper(availability) like 'YES' AND poster_user <> %s",(session.get("user_id"),))
    rentable_items = x.fetchall()
    # get current user name
    
    sql_users = db.execute("SELECT * FROM users WHERE email = %s",(session.get("user_id"),))
    sql_user = sql_users.fetchone()
    
    if request.method == 'POST':
        nametemp = request.form['name']
        name = "%" + nametemp + "%"
        desctemp = request.form['description']
        desc = "%" + desctemp + "%"
        selectedbrand_t = request.form['brands']
        if selectedbrand_t == 'none':
            selectedbrand = '%%'
        else:
            selectedbrand = selectedbrand_t
        selectedcat_t = request.form['category']
        if selectedcat_t == "none":
            selectedcat = '%%'
        else:
            selectedcat = selectedcat_t
        ratetemp = request.form.get('rate',type = int)
        if ratetemp is None:
            rate = 1000000000
        else:
            rate = ratetemp
        no_rents_t = request.form["no_rents"]
        collecttemp = request.form['collection']
        collect = "%" + collecttemp + "%"
        print(no_rents_t)
        
        if no_rents_t == "":
            no_rents = "0"
            query = "SELECT * FROM items where lower(availability) like lower('Yes') and lower(item_name) like lower(%s) and lower(description) like lower(%s) and lower(brand) like lower(%s) and lower(category) like lower(%s) and rate_per_day < %s and lower(collection_point) like lower(%s) and poster_user <> %s --%s"
            rowcount = "SELECT count(*) FROM items where lower(availability) like lower('Yes') and lower(item_name) like lower(%s) and lower(description) like lower(%s) and lower(brand) like lower(%s) and lower(category) like lower(%s) and rate_per_day < %s and lower(collection_point) like lower(%s) and poster_user <> %s --%s"
        elif no_rents_t == "1" or no_rents_t == "0": #query for never rented before
            no_rents = no_rents_t
            query = "SELECT * FROM items i where lower(availability) like lower('Yes') and lower(item_name) like lower(%s) and lower(description) like lower(%s) and lower(brand) like lower(%s) and lower(category) like lower(%s) and rate_per_day < %s and lower(collection_point) like lower(%s) and poster_user <> %s and not exists (select * from rentals r where r.item_id = i.item_id) --%s"
            rowcount = "SELECT count(*) FROM items where lower(availability) like lower('Yes') and lower(item_name) like lower(%s) and lower(description) like lower(%s) and lower(brand) like lower(%s) and lower(category) like lower(%s) and rate_per_day < %s and lower(collection_point) like lower(%s) and poster_user <> %s and not exists (select * from rentals r where r.item_id = items.item_id) --%s"
        else: #query for rented before
            no_rents = no_rents_t
            query = "SELECT * FROM items where lower(availability) like lower('Yes') and lower(item_name) like lower(%s) and lower(description) like lower(%s) and lower(brand) like lower(%s) and lower(category) like lower(%s) and rate_per_day < %s and lower(collection_point) like lower(%s) and poster_user <> %s and exists (select r.item_id, count(r.item_id) from rentals r where r.item_id = items.item_id group by r.item_id having count(r.item_id) < %s )"
            rowcount = "SELECT count(*) FROM items where lower(availability) like lower('Yes') and lower(item_name) like lower(%s) and lower(description) like lower(%s) and lower(brand) like lower(%s) and lower(category) like lower(%s) and rate_per_day < %s and lower(collection_point) like lower(%s) and poster_user <> %s and exists (select r.item_id, count(r.item_id) from rentals r where r.item_id = items.item_id group by r.item_id having count(r.item_id) < %s )"
        x  = db.execute(query, (name,desc,selectedbrand,selectedcat,rate,collect,session.get("user_id"),no_rents))
        filtered_items = x.fetchall()
        row_counter = db.execute(rowcount,(name,desc,selectedbrand,selectedcat,rate,collect,session.get("user_id"),int(no_rents))).fetchall()
        return render_template('dashboard.html',brands=listbrands,category=listcat,current_user=sql_user, items=filtered_items, rowcount=row_counter)
    rowcounter = db.execute("SELECT count(*) FROM items WHERE upper(availability) like 'YES' AND poster_user <> %s",(session.get("user_id"),)).fetchall()
    return render_template('dashboard.html',brands=listbrands,category=listcat,current_user=sql_user, items=rentable_items, rowcount=rowcounter)

@app.route('/rented_items', methods=['GET','POST'])
def rented_items():
    # Assuming there is a 'rentals' table in the database that stores rental data
    # Get the items that the user has rented based on their user ID (you'll need to pass this as a parameter)
    session.get("user_id")
    query = "SELECT * FROM rentals where RENTEE_ID = %s and lower(returned) = lower(%s)"
    x  = db.execute(query, (session.get("user_id"),"no"))
    rented_items = x.fetchall()
    #add a return button to return the item
    if request.method == 'POST':
        item_id = request.form['item_id']
        query = "UPDATE items SET availability = 'Yes' WHERE item_id = %s"
        db.execute(query, (item_id,))
        query = "UPDATE rentals SET returned = 'Yes' WHERE item_id = %s"
        db.execute(query, (item_id,))
        return redirect(url_for('rate', item_id=item_id))
    return render_template('rented_items.html',rented_items=rented_items)

@app.route('/transactions', methods=['GET','POST'])
def transactions():
    session.get("user_id")
    x = db.execute("SELECT SUM(total_paid) FROM transactions where RENTEE_ID = %s",(session.get("user_id")))
    sum = x.fetchone()
    x = db.execute("SELECT SUM(total_paid) FROM transactions where RENTER_ID = %s", (session.get("user_id")))
    revenue = x.fetchone()
    query = "SELECT * FROM transactions where RENTEE_ID = %s"
    x  = db.execute(query, (session.get("user_id"),))
    transactions = x.fetchall()
    query = "SELECT * FROM transactions where RENTER_ID = %s"
    x  = db.execute(query, (session.get("user_id"),))
    transactions_rentedout = x.fetchall()
    return render_template('transactions.html',transactions=transactions, trans_out=transactions_rentedout, sum=sum, revenue=revenue)


#create a new item for payment, the payment button will be available when the user open a listing that they want to rent
#after they clicked that button, it will extract the information from the current listing, auto fill the rental id, name, description, brand, category, rate per day, collection point, 
#and the user just need to fill in the card number, card holder, expiration date, security code, and amount based on my payment page.
@app.route('/payment/<int:item_id>/<int:days>', methods=['GET','POST'])
def payment(item_id, days):
    # Query the database to get the details of the item with the given item_id
    item_query = db.execute("SELECT * FROM items WHERE ITEM_ID = %s", (str(item_id),))
    item = item_query.fetchone()

    #count the number of rows in the transactions table and add 1
    x = db.execute("SELECT COUNT(*) FROM transactions")
    transaction_id = x.fetchone()[0] + 1
    payment_type = 'Card'
    rentee_id = session.get("user_id")
    #select the poster_user from items where the item_id = item_id
    x = db.execute("SELECT poster_user FROM items WHERE item_id = %s", (str(item_id),))
    renter_id = x.fetchone()[0]
    
    x = db.execute("SELECT RATE_PER_DAY FROM items WHERE item_id = %s", (str(item_id),))
    rate = x.fetchone()[0]
    amount = rate * days
    #extract the current date and convert to string, then add the number of days to get the end date and convert to string
    start_date = datetime.datetime.now().strftime("%Y-%m-%d")
    end_date = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    rental_id = transaction_id
    
    if request.method == 'POST':
        card_number = request.form['card_number']
        card_holder = request.form['card_holder']
        expiration_date = request.form['expiration_date']
        security_code = request.form['security_code']

        db.execute("INSERT INTO transactions (transaction_id, payment_type, rentee_id, renter_id, total_paid) VALUES (%s, %s, %s, %s, %s)", (transaction_id, payment_type, rentee_id, renter_id, amount))
        db.execute("UPDATE items SET availability = 'No' WHERE item_id = %s", (str(item_id),))
        db.execute("INSERT INTO rentals (rental_id, item_id, renter_id, rentee_id, start_date, end_date) VALUES (%s, %s, %s, %s, %s, %s)", (transaction_id, item_id, renter_id, rentee_id, start_date, end_date))
        return redirect(url_for('dashboard'))
    return render_template('payment.html', item=item, transaction_id=transaction_id, item_id=item_id, renter_id=renter_id, rentee_id=rentee_id, start_date=start_date, end_date=end_date, amount=amount)

@app.route('/sql', methods=['GET', 'POST'])
def sql():
    if request.method == 'POST':
        # Get user's SQL code from the form
        sql = request.form['sql']

        # Execute the SQL code against the database
        try:
            db.execute(sql)
            message = "SQL code executed successfully"
        except Exception as e:
            message = f"Error executing SQL code: {str(e)}"

        return render_template('sql.html', message=message)

    return render_template('sql.html')

@app.route('/item_details/<int:item_id>', methods=['GET', 'POST'])
def item_details(item_id):
    item_id = str(item_id)
    if request.method == 'POST':
        days = request.form["day"]
        return redirect(url_for('payment', item_id=item_id, days=days))

    # Query the database to get the details of the item with the given item_id
    item_query = db.execute("SELECT * FROM items WHERE ITEM_ID=%s", (item_id,))
    item = item_query.fetchone()
    print(item)
    # Render the item details page with the retrieved details
    return render_template('item_details.html', item=item)

@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method =='POST':
        current_user = session.get("user_id")
        name = request.form["name"]
        desc = request.form["description"]
        avail = 'Yes'
        rating = "0"
        brand = request.form["brand"]
        cat = request.form["category"]
        rate = request.form["rate"]
        collect = request.form["collection"]
        y = db.execute("Select * from items")
        item_count = y.fetchall()
        if item_count is not None:
            item_id = len(item_count) + 1
        else:
            item_id = 1            
        query = "INSERT INTO items VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        db.execute(query, (item_id, current_user,name,desc,avail,rating,brand,cat,rate,collect))
        return redirect(url_for('dashboard'))
    return render_template('post.html')

@app.route('/rate/<int:item_id>', methods=['GET','POST'])
def rate(item_id):
    item_query = db.execute("SELECT * FROM items WHERE ITEM_ID = %s", (str(item_id),))
    item = item_query.fetchone()
    #count the number of rows in the transactions table and add 1
    rentee_id = session.get("user_id")
    #select the poster_user from items where the item_id = item_id
    x = db.execute("SELECT poster_user FROM items WHERE item_id = %s", (str(item_id),))
    renter_id = x.fetchone()[0]

    x = db.execute("SELECT * FROM rentals WHERE item_id = %s", (str(item_id),))
    rental_details = x.fetchone()
    #extract the current date and convert to string, then add the number of days to get the end date and convert to string
    if request.method =='POST':
        current_user = session.get("user_id")
        rating = str(request.form["rating"])
        db.execute("UPDATE ITEMS SET item_rating = %s where item_id=%s",(rating,str(item_id)))
        return redirect(url_for('dashboard'))
    return render_template('rate.html', item=item, item_id=item_id, renter_id=renter_id, rentee_id=rentee_id, rental_details=rental_details)
    
@app.route('/posted_items', methods=["POST", 'GET'])
def posted_items():
    # Get the items that the user has posted for rent based on their user ID
    user_id = session.get("user_id") 
    #create a nested query to get the items that the user has posted for rent.
    query = '''
    SELECT *
    FROM items i
    LEFT JOIN rentals ON i.item_id = rentals.item_id
    LEFT JOIN users ON rentals.rentee_id = users.EMAIL
    LEFT JOIN transactions ON rentals.rental_id = transactions.transaction_id
    WHERE rentals.renter_id = %s
	and exists (select * from items i2 where i2.item_id = i.item_id and item_rating < %s)
    '''
    item_rating = "6"
    if request.method == 'POST':
        item_rating = request.form["item_rating"]
        posted_items = db.execute(query, (str(user_id,)),item_rating).fetchall()
        return render_template('posted_items.html', posted_items=posted_items)
    
    posted_items = db.execute(query, (str(user_id,)),item_rating).fetchall()
    # Render the posted items in a template
    return render_template('posted_items.html', posted_items=posted_items)

if __name__ == '__main__':
    app.secret_key = "test"
    app.run(debug=True)
