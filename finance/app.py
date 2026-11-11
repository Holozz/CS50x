import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    id=session["user_id"]
    rows = db.execute("SELECT * FROM portfolio WHERE user_id == ?", id)
    cash = db.execute("SELECT cash FROM users WHERE id = ?", id)[0]["cash"]
    grand = 0
    for row in rows:
        row["name"] = lookup(row["symbol"])["name"]
        row["price"] = lookup(row["symbol"]).get("price")
        grand += row["shares"]*row["price"]
    return render_template("index.html", rows=rows, cash=cash, grand=grand)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method=="POST":
        if not request.form.get("symbol"):#
            return apology("please provide symbol")
        elif not lookup(request.form.get("symbol")):#
            return apology("symbol doesnt exist")
        elif not request.form.get("shares"):#
            return apology("please provide shares")

        #存储购买信息
        symbol=lookup(request.form.get("symbol"))["symbol"]
        buy_price=lookup(symbol).get("price")
        buy_shares=int(request.form.get("shares"))

        id=session["user_id"]
        username=db.execute("SELECT username FROM users WHERE id == ?", id)[0]['username']
        cash = db.execute("SELECT cash FROM users WHERE id = ?", id)[0]["cash"]

        #判断买的份额是否合规以及是否有足够本金
        if buy_shares % 1 != 0 or buy_shares<=0:
            return apology("shares must be positive integers")
        if buy_shares*buy_price > cash:
            return apology("you have not enough money to afford")

        #判断可以购买之后直接记录这次购买
        db.execute("INSERT INTO history (id, username, type, symbol, price, shares, time) VALUES(?, ?, ?, ?, ?, ?, ?)",
                   id, username, "buy", symbol, buy_price, buy_shares, datetime.now())

        #寻找当前用户买过的该股票
        row = db.execute("SELECT * FROM portfolio WHERE user_id = ? AND symbol = ?", id, symbol)

        #如果当前未持有，直接插入
        if not row:
            db.execute("INSERT INTO portfolio (user_id, symbol, shares, avg_price, username) VALUES (?, ?, ?, ?, ?)",id, symbol, buy_shares, buy_price, username)

        #如果已存在于仓库，更新信息
        else:
            # 把原先每一列赋值给对应的变量
            row = row[0]
            portfolio_id = row["portfolio_id"]
            shares = row["shares"]
            avg_price = row["avg_price"]
            #更新股份和购入均价
            shares += buy_shares
            avg_price = (avg_price * (shares-buy_shares) + buy_price * buy_shares) / shares
            #更新表格
            db.execute("UPDATE portfolio " \
            "SET shares = ?," \
                "avg_price = ? " \
                "WHERE user_id = ? AND symbol = ?;",
                shares, avg_price, id, symbol)
        #购买完毕，更新当前余额
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash+buy_shares*buy_price, id)

        return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
            )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method=="POST":
        if not request.form.get("symbol"):
            return apology("must input a symbol")
        result = lookup(request.form.get("symbol"))
        return render_template("/result.html", result=result)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method=="POST":
        if not request.form.get("Username"):
            return apology("must set your username", 403)

        # Ensure password was submitted
        elif not request.form.get("Password"):
            return apology("must set your password", 403)

        elif not request.form.get("Confirmation"):
            return apology("must confirm your password")

        elif not request.form.get("Password")==request.form.get("Confirmation"):
            return apology("passwords do not match")

        Username=request.form.get("Username")
        Password=request.form.get("Password")

        # Insert username
        try:
            db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", Username,  generate_password_hash(Password))
        except ValueError:
            return apology("username already exits")

        return redirect("/login")

    else:
        return render_template("register.html")



@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    id=session["user_id"]
    username=db.execute("SELECT username FROM users WHERE id == ?", id)[0]['username']
    cash = db.execute("SELECT cash FROM users WHERE id = ?", id)[0]["cash"]

    if request.method=="POST":
        if not request.form.get("symbol"):#
            return apology("please provide symbol")
        elif not request.form.get("shares"):#
            return apology("please provide shares")

        #存储售卖信息
        symbol=lookup(request.form.get("symbol"))["symbol"]
        sell_price=lookup(symbol).get("price")
        sell_shares=int(request.form.get("shares"))

        #尝试寻找并比对用户当前持有的股票
        row = db.execute("SELECT * FROM portfolio WHERE user_id = ? AND symbol = ?", id, symbol)
        if len(row) == 0:
            return apology("you haven't had this yet!")
        row = row[0]

        if sell_shares % 1 != 0 or sell_shares<=0 or sell_shares>row["shares"]:
            return apology("shares must be a positive integer that is less than the current number you have")

        #检查完可以出售，记录出售历史
        db.execute("INSERT INTO history (id, username, type, symbol, price, shares, time) VALUES(?, ?, ?, ?, ?, ?, ?)",
                   id, username, "sell", symbol, sell_price, sell_shares, datetime.now())

        #把原先每一列赋值给对应的变量
        portfolio_id = row["portfolio_id"]
        shares = row["shares"]
        #更新股份
        shares -= sell_shares

        #更新表格
        if shares == 0:
            db.execute("DELETE FROM portfolio WHERE user_id = ? AND symbol = ?", id, symbol)
        else:
            db.execute("UPDATE portfolio SET shares = ? WHERE user_id = ? AND symbol = ?", shares, id, symbol)
        #售卖完毕，更新当前余额
        db.execute("UPDATE users SET cash = ? WHERE id = ?", cash+sell_shares*sell_price, id)

        return redirect("/")
    else:
        portfolio = db.execute("SELECT symbol, shares FROM portfolio WHERE user_id = ?", id)
        return render_template("sell.html", portfolio=portfolio)
