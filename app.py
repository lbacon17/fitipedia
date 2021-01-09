import os
import datetime
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/home_page")
def home_page():
    terms = mongo.db.terms.find()
    users = mongo.db.users.find()
    return render_template("index.html", terms=terms, users=users)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one({"username": request.form.get("username").lower()})
        existing_email = mongo.db.users.find_one({"email_address": request.form.get("email").lower()})
        is_superuser = True if request.form.get("username").lower == "admin" else False

        # check whether user already exists
        if existing_user:
            flash("User already exists")
            return redirect(url_for("register"))
        
        # check whether e-mail address was already used to sign up
        if existing_email:
            flash("An account already exists for this e-mail address!")
            return redirect(url_for("register"))
        
        create_account = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password")),
            "email_address": request.form.get("email").lower(),
            "is_superuser": is_superuser
        }
        mongo.db.users.insert_one(create_account)

        session["user"] = request.form.get("username").lower()
        flash("Registration successful!")
        return redirect(url_for("home_page", username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})    
        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                existing_user["password"], request.form.get("password")):
                    session["user"] = request.form.get("username").lower()
                    return redirect(url_for(
                        "home_page", username=session["user"]))

            else:
                # invalid password match
                flash("Invalid login credentials!")
                return redirect(url_for("login"))

        else: 
            # username doesn't exist
            flash("Invalid login credentials!")
            return redirect(url_for("login"))

    return render_template("login.html")  


@app.route("/logout")
def logout():
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("home_page"))


@app.route("/view_dictionary")
def view_dictionary():
    terms = mongo.db.terms.find().sort("term_name", 1)
    return render_template("dictionary.html", terms=terms)


@app.route("/add_definition", methods=["GET", "POST"])
def add_definition():
    if request.method == "POST":
        new_term = {
            "term_name": request.form.get("term_name"),
            "term_definition": request.form.get("term_definition"),
            "created_by": session["user"],
            "created_on": datetime.datetime.today()
        }
        mongo.db.terms.insert_one(new_term)
        flash("Term successfully created. You will now be redirected to the dictionary page where you can see your contribution!")
        return redirect(url_for("view_dictionary"))
    
    terms = mongo.db.terms.find()
    users = mongo.db.users.find()
    return render_template("add_definition.html")


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"), 
    port=int(os.environ.get("PORT")), 
    debug=True)