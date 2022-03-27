import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("IEX_KEY"):
    raise RuntimeError("IEX_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session["user_id"]

    holdings = db.execute(
        "SELECT * FROM holdings WHERE user_id = :user_id EXCEPT SELECT * FROM holdings WHERE symbol = 'CASH'", user_id=user_id)

    # update prices
    for holding in holdings:
        symbol = holding["symbol"]
        price = lookup(symbol)["price"]
        total = int(holding["shares"]) * price
        db.execute("UPDATE holdings SET price = :price, total = :total WHERE symbol = :symbol AND user_id = :user_id",
                                    price = price, total=total, symbol=symbol, user_id=user_id)

    grand_total = usd(db.execute("SELECT SUM(total) FROM holdings WHERE user_id = :user_id", user_id=user_id)[0]["SUM(total)"])

    cash = usd(db.execute("SELECT * FROM holdings WHERE user_id = :user_id AND symbol = 'CASH'", user_id=user_id)[0]["total"])

    # convert to USD format
    for holding in holdings:
        holding["price"] = usd(float(holding["price"]))
        holding["total"] = usd(float(holding["total"]))
    return render_template("index.html", holdings=holdings, grand_total=grand_total, cash=cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    user_id = session["user_id"]
    if request.method == "GET":
        return render_template("buy.html")
    else:

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("must enter symbol", 400)

        # Ensure number of shares was submitted
        elif not request.form.get("shares"):
            return apology("must provide number of shares to buy", 403)

        try:
            whatever = int(request.form.get("shares"))
        except:
            return apology("invalid shares", 400)

        if int(request.form.get("shares")) < 1:
            return apology("Must buy at leat 1 share, dumbass", 400)

        symbol = lookup(request.form.get("symbol"))
        if symbol == None:
            return apology("no such stock")
        symbol = symbol["symbol"].upper()

        curr_price = lookup(symbol)["price"]
        curr_cash = float(db.execute("SELECT * FROM holdings WHERE user_id = :user_id AND symbol = 'CASH'",
                                user_id = user_id)[0]["total"])
        shares = int(request.form.get("shares"))

        if curr_cash < float(curr_price) * float(shares):
            return apology("insufficient funds, sucks to be you!")

        # datetime object containing current date and time
        now = datetime.now()

        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transacted) VALUES (:user_id, :symbol, :shares, :price, :transacted)",
                        user_id = user_id, symbol=symbol, shares=shares, price=curr_price, transacted=dt_string)

        new_cash = curr_cash - (float(shares) * float(curr_price))

        db.execute("UPDATE users SET cash = :new_cash WHERE id = :user_id", new_cash = new_cash, user_id = user_id)
        db.execute("UPDATE holdings SET total = :new_cash WHERE user_id = :user_id AND symbol = 'CASH'",
                    new_cash=new_cash, user_id=user_id)

        name = lookup(symbol)["name"]
        total = float(shares) * float(curr_price)

        # check if user already owns the stock they bought
        rows = db.execute("SELECT * FROM holdings WHERE user_id = :user_id AND symbol = :symbol", user_id=user_id, symbol=symbol)
        if len(rows) != 0:
            curr_shares = int(rows[0]["shares"])
            new_shares = int(shares) + curr_shares
            price = lookup(symbol)["price"]
            total = price * new_shares
            db.execute("UPDATE holdings SET shares = :shares, price = :price, total = :total WHERE user_id = :user_id AND symbol = :symbol",
                        shares=new_shares, price=price, total=total, user_id=user_id, symbol=symbol)
        else:
            db.execute("INSERT INTO holdings (user_id, symbol, name, shares, price, total) VALUES (:uid, :symbol, :name, :shares, :price, :total)",
                        uid=user_id, symbol=symbol, name=name, shares=shares, price=curr_price, total=total)

        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ?", user_id)

    # convert to USD format
    for transaction in transactions:
        transaction["price"] = usd(float(transaction["price"]))

    return render_template("history.html", transactions=transactions)


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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
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
    if request.method == "GET":
        return render_template("quote.html")
    else:
        stock = lookup(request.form.get("symbol"))
        if stock == None:
            return apology("no such stock")
        return render_template("quoted.html", name=stock["name"], symbol=stock["symbol"], price=usd(stock["price"]))


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username, you know, so we know who you are ;)", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password, we don't want you to be hacked!", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match you fool!", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username doesn't exist
        if len(rows) == 1:
            return apology("username already exists, soz!", 400)

        username = request.form.get("username")
        password = request.form.get("password")
        pwhash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        db.execute("INSERT INTO users (username, hash) VALUES (:username, :pwhash)",
                username=username, pwhash=pwhash)
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))
        user_id = rows[0]["id"]

        db.execute("INSERT INTO holdings (user_id, symbol, total) VALUES (:user_id, 'CASH', 10000)", user_id=user_id)

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():
    user_id = session["user_id"]
    if request.method == "POST":
        """Deposit Money"""

        # check a calue is entered
        if not request.form.get("amount"):
            return apology("Must enter sum to deposit", 400)

        #get current cash & add to it entered cash
        curr_cash = float(db.execute("SELECT * FROM holdings WHERE user_id = :user_id AND symbol = 'CASH'",
                                    user_id = user_id)[0]["total"])
        new_cash = curr_cash + float(request.form.get("amount"))

        db.execute("UPDATE holdings SET total = :new_cash WHERE user_id = :user_id AND symbol = 'CASH'",
                    new_cash=new_cash, user_id=user_id)
        db.execute("UPDATE users SET cash = :new_cash WHERE id = :user_id",
                    new_cash=new_cash, user_id=user_id)

        # datetime object containing current date and time
        now = datetime.now()

        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        # record transaction
        db.execute("INSERT INTO transactions(user_id, symbol, price, transacted) VALUES (:user_id, 'CASH', :cash_added, :transacted)",
                    user_id = user_id, cash_added = float(request.form.get("amount")), transacted=dt_string)

        return redirect("/")
    else:
        return render_template("deposit.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session["user_id"]
    if request.method == "POST":

        user_id = session["user_id"]

        # Ensure symbol was submitted
        if not request.form.get("symbol"):
            return apology("pls select stock", 403)

        # Ensure number of shares was submitted
        elif not request.form.get("shares"):
            return apology("must provide number of shares to sell", 403)

        try:
            whatever = int(request.form.get("shares"))
        except:
            return apology("invalid shares", 400)

        if int(request.form.get("shares")) < 1:
            return apology("Must buy at leat 1 share, dumbass", 400)

        symbol = request.form.get("symbol")

        # Ensure user owns the stock
        rows = db.execute("SELECT * FROM holdings WHERE user_id = :user_id AND symbol = :symbol", user_id=user_id, symbol=symbol)
        if len(rows) == 0:
            return apology("you don't own that stock", 403)

        shares = int(request.form.get("shares"))
        curr_holding = int(db.execute("SELECT * FROM holdings WHERE user_id = :user_id AND symbol = :symbol",
                                    user_id=user_id, symbol=symbol)[0]["shares"])

        # check number of shares to sell is not higher than current holding
        if shares > curr_holding:
            return apology("you don't even own that many shares")

        curr_cash = float(db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])[0]["cash"])
        curr_price = lookup(symbol)["price"]
        new_cash = curr_cash + (float(shares) * float(curr_price))

        db.execute("UPDATE users SET cash = :new_cash WHERE id = :user_id", new_cash=new_cash, user_id=user_id)
        db.execute("UPDATE holdings SET total = :new_cash WHERE user_id = :user_id AND symbol = 'CASH'",
                    new_cash=new_cash, user_id=user_id)

        # if user is selling their entire holding
        if shares == curr_holding:
            db.execute("DELETE FROM holdings WHERE user_id = :user_id AND symbol = :symbol", symbol=symbol, user_id=user_id)

        # if user is selling part of their holding
        if shares < curr_holding:
            new_shares = curr_holding - shares
            price = lookup(symbol)["price"]
            total = price * new_shares
            db.execute("UPDATE holdings SET shares = :shares, price = :price, total = :total WHERE user_id = :user_id AND symbol = :symbol",
                            shares=new_shares, price=price, total=total, symbol=symbol, user_id=user_id)

        # datetime object containing current date and time
        now = datetime.now()

        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

        # record transaction
        sold_shares = -shares
        db.execute("INSERT INTO transactions (user_id, symbol, shares, price, transacted) VALUES (:user_id, :symbol, :shares, :price, :transacted)",
                user_id = user_id, symbol = symbol, shares = sold_shares, price = curr_price, transacted = dt_string)

        return redirect("/")
    else:
        #get all stocks owned
        holdings = db.execute(
            "SELECT * FROM holdings WHERE user_id = ? EXCEPT SELECT * FROM holdings WHERE symbol = 'CASH'", user_id)
        return render_template("sell.html", holdings=holdings)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
