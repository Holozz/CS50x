import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///birthdays.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
def index():
    FormName=request.form.get("FormName")
    if request.method == "POST":
        if FormName == "Add":
            # TODO: Add the user's entry into the database
            Name=request.form.get("Name")
            Month=request.form.get("Month")
            Day=request.form.get("Day")
            db.execute("INSERT INTO birthdays (name, month, day) VALUES(?, ?, ?)", Name, Month, Day )
        else:
            id=request.form.get("id")
            db.execute("DELETE FROM birthdays WHERE id = ?", id)
        return redirect("/")

    else:

        # TODO: Display the entries in the database on index.html
        persons=db.execute("SELECT * FROM birthdays")
        return render_template("index.html", persons=persons)
