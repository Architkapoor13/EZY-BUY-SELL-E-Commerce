import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from helpers import apology, login_required, lookup, usd
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Mail, Message

# Configure application
app = Flask(__name__)


app.config.update(
    DEBUG=True,
    #EMAIL SETTINGS
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME = 'anything@gmail.com',
    MAIL_PASSWORD = 'anything'

    )
mail = Mail(app)
# mail.init_app(app)

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
# app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///buy&sell.db")


# Make sure API key is set
# if not os.environ.get("API_KEY"):
# raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show Different Items on Sale"""
    user_id = session["user_id"]
    propic = db.execute("SELECT profilepicpath FROM profilepicture WHERE id=:id", id=user_id)
    username = db.execute("SELECT username FROM users WHERE id=:id", id=user_id)
    return render_template("index.html", propic=propic[0]["profilepicpath"], username=username[0]["username"])



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """buy items"""
    user_id = session["user_id"]
    if request.method == "GET":
        propic = db.execute("SELECT profilepicpath FROM profilepicture WHERE id=:id", id=user_id)
        username= db.execute("SELECT username FROM users WHERE id=:id", id=user_id)
        # saleitems = db.execute("SELECT imagename, name, discription, price FROM buydisplayimage JOIN sdetails ON buydisplayimage.code = sdetails.code")
        saleitems = db.execute(
            "SELECT buydisplayimage.bimagename, sdetails.name, sdetails.discription, sdetails.price, sdetails.code, udetails.fullname, udetails.mobilenumber, udetails.email FROM sdetails "
            "JOIN buydisplayimage ON sdetails.code=buydisplayimage.code "
            "JOIN users ON sdetails.id=users.id "
            "JOIN udetails ON users.username = udetails.username "
            # "JOIN images ON sdetails.code=images.code"
        )
        images = db.execute("SELECT * FROM images")
        return render_template("buy.html", saleitems=saleitems, propic=propic[0]["profilepicpath"], username=username[0]["username"], images=images)
    else:
        itemtype = request.form.get("itemtype")
        itemname = request.form.get("itemname")
        propic = db.execute("SELECT profilepicpath FROM profilepicture WHERE id=:id", id=user_id)
        username = db.execute("SELECT username FROM users WHERE id=:id", id=user_id)
        saleitems = db.execute(
            "SELECT buydisplayimage.bimagename, sdetails.name, sdetails.discription, sdetails.price, sdetails.code, udetails.fullname, udetails.mobilenumber, udetails.email FROM sdetails "
            "JOIN buydisplayimage ON sdetails.code=buydisplayimage.code "
            "JOIN users ON sdetails.id=users.id "
            "JOIN udetails ON users.username = udetails.username "
            # "JOIN images ON sdetails.code=images.code "
            "WHERE sdetails.itemname=:itemname", itemname=itemname)
        images = db.execute("SELECT * FROM images")
        # images = db.execute("SELECT ")
        # saleitems = db.execute("SELECT buydisplayimage.imagename, sdetails.name, sdetails.discription, sdetails.price FROM buydisplayimage JOIN sdetails ON buydisplayimage.code = sdetails.code WHERE sdetails.itemname=:itemname", itemname=itemname)
        # saleitems = db.execute("SELECT * FROM sdetails WHERE itemname=:itemname AND type=:itemtype", itemname=itemname,
        #                        itemtype=itemtype)
        return render_template("buy.html", saleitems=saleitems, propic=propic[0]["profilepicpath"], images=images, username=username[0]["username"])

    # return apology("TODO")
    
@app.route("/sellingorders")
@login_required
def history():
    """Show history of transactions"""
    if request.method == "GET":
        user_id = session["user_id"]
        details = db.execute("SELECT buydisplayimage.bimagename, sdetails.name, sdetails.itemname, sdetails.price, sdetails.code FROM sdetails "
                             "JOIN buydisplayimage ON sdetails.code=buydisplayimage.code WHERE id = :user_id", user_id=user_id)
        return render_template("orders.html", details=details)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("must provide username")
            return render_template("login.html")
            # return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Password not provided!")
            return render_template("login.html")

        username = request.form.get("username")


        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("invalid username and/or password")
            return render_template("login.html")
            # return apology("invalid username and/or password", 403)


        username_c = db.execute("SELECT confirmed FROM udetails WHERE username=:username", username=username)
        if username_c[0]["confirmed"] == 1:

            # Remember which user has logged in
            session["user_id"] = rows[0]["id"]
            username = request.form.get("username")
            username_c = db.execute("SELECT confirmed FROM udetails WHERE username=:username", username=username)

            # Redirect user to home page
            flash("login Successfull")
            return render_template("index.html")
        if username_c[0]["confirmed"] == 0:
            flash("Your email has not yet verified, please verify your email to continue")
            return render_template("login.html")

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
    return apology("TODO")

s = URLSafeTimedSerializer("thisisasecret")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    else:
        fullname = request.form.get("fullname")
        if not fullname:
            flash("Please fill all the fields")
            return redirect("/register")
        phonenumber = request.form.get("phonenumber")
        email = request.form.get("mail")
        address = request.form.get("address")
        username = request.form.get("username")
        if not username:
            flash("Please fill all the fields")
            return redirect("/register")
            # return apology("please provide username")
        password = request.form.get("password")
        if not password:
            flash("Please fill all the fields")
            return redirect("/register")
            # return apology("Please provide a password")
        confirm = request.form.get("confirmation")
        if not confirm or not password == confirm:
            flash("Passwords do not match!")
            return redirect("/register")
            # return apology("Passwords do not match!")
        if len(password) < 8:
            flash("Password must be 8 chracters long!")
            return redirect("/register")
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
        coloumns = db.execute("SELECT * FROM udetails WHERE email = :email", email=email)
        if len(rows) != 1 and len(coloumns) != 1:
            hash_p = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash_p)", username=username,
                       hash_p=hash_p)
            db.execute("INSERT INTO udetails (fullname, mobilenumber,email, address, username, password) VALUES (:fullname, :phonenumber, :email, :address, :username, :hash_p)",
                       fullname=fullname, phonenumber=phonenumber , email=email, address=address, username=username, hash_p=hash_p)
            id = db.execute("SELECT id FROM users WHERE username=:username", username=username)
            db.execute("INSERT INTO profilepicture (id) VALUES (:id)", id=id[0]["id"])

            token = s.dumps(email, salt="email-confirm")
            db.execute("UPDATE udetails SET token=:token WHERE username=:username", token=token, username=username)

            msg = Message("Account-Activation",
                          sender="ezybuysell.noreply@gmail.com",
                          recipients=[email])

            link = url_for("confirm_email", token=token, _external=True)

            # msg.body = f"your link is {link}"
            msg.body = f"Welcome to EZY-BUY-SELL, we are delightful to have you on our website! \r\n\n To Activate your account click on the link below: \r\n\n {link}"
            mail.send(msg)
            print("mail sent!")
            flash("An email regarding the activation of your account has been sent on your registered email, activate your account to login your account. ")
            return render_template("login.html")
        else:
            flash("Username/email already exists")
            return render_template("register.html")
            # return apology("Username already exists")


@app.route("/confirm/<token>")
def confirm_email(token):
    if request.method == "GET":
        try:
            email = s.loads(token, salt="email-confirm", max_age=3600)
        except SignatureExpired:
            return "token expired!"
        db.execute("UPDATE udetails SET confirmed=1 WHERE token=:token", token=token)
        new_token="0"
        db.execute("UPDATE udetails SET token=:new_token WHERE token=:token", new_token=new_token, token=token)
        return redirect("/login")

app.config["IMAGE_UPLOADS"] = "C:/Users/ARCHIT/Desktop/cs50final/static"
app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["PNG", "JPG", "JPEG", "GIF"]


def allowed_ext(filename):
    if not "." in filename:
        return False
    ext = filename.rsplit(".", 1)[1]
    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell an Item"""
    user_id = session["user_id"]
    if request.method == "GET":
        propic = db.execute("SELECT profilepicpath FROM profilepicture WHERE id=:id", id=user_id)
        username = db.execute("SELECT username FROM users WHERE id=:id", id=user_id)
        return render_template("sell.html", propic=propic[0]["profilepicpath"], username=username[0]["username"])
    else:
        propic = db.execute("SELECT profilepicpath FROM profilepicture WHERE id=:id", id=user_id)
        iname = request.form.get("status")
        type = request.form.get("source")
        price = request.form.get("price")
        discription = request.form.get("discription")
        name = request.form.get("name")
        if not iname or not type or not price or not discription or not name:
            flash("Please fill all the fields!")
            return render_template("sell.html", propic=propic[0]["profilepicpath"])
            # return apology("Please fill all the fields!")
        if 'files[]' not in request.files:
            flash("no files selected")
            return render_template("sell.html")
            # return apology("no files selected")
        db.execute("INSERT INTO sdetails (id, name, itemname, type, price, discription) VALUES (:user_id, :name, :itemname, :type, :price, :discription)",
            user_id=user_id, name=name, itemname=iname, type=type, price=price, discription=discription)
        files = request.files.getlist("files[]")
        code = db.execute("SELECT code FROM sdetails WHERE id=:id AND name=:name AND itemname=:itemname AND type=:type AND price=:price AND discription=:discription",
            id=user_id, name=name, itemname=iname, type=type, price=price, discription=discription)
        number = 1
        for file in files:
            filename = secure_filename(file.filename)
            if filename == "":
                flash("No image selected")
                return render_template("sell.html", propic=propic[0]["profilepicpath"])
            if number == 1:
                file.save(os.path.join(app.config['IMAGE_UPLOADS'], filename))
                path = "../static/" + filename
                db.execute("INSERT INTO buydisplayimage VALUES (:code, :imagename)", code=code[0]["code"], imagename=path)
                db.execute("INSERT INTO images VALUES (:code, :imagename)", code=code[0]["code"], imagename=path)
                print("images uploaded successfully")
                number = number + 1

            else:
                file.save(os.path.join(app.config['IMAGE_UPLOADS'], filename))
                path= "../static/" + filename
                db.execute("INSERT INTO images VALUES (:code, :imagename)", code=code[0]["code"], imagename=path)
                print("images uploaded successfully")
        flash("Selling order placed!")
        return render_template("index.html")


@app.route("/account", methods=["GET", "POST"])
def account():
    user_id = session["user_id"]
    if request.method == "GET":
        details = db.execute("SELECT fullname, mobilenumber, email, address, username FROM udetails WHERE username = (SELECT username FROM users WHERE id = :user_id)", user_id= user_id)
        name = details[0]["fullname"]
        email = details[0]["email"]
        address = details[0]["address"]
        username = details[0]["username"]
        phonenumber = details[0]["mobilenumber"]
        propic = db.execute("SELECT profilepicpath FROM profilepicture WHERE id=:id", id=user_id)
        # filename = "noimage.png"
        return render_template("account.html", propic=propic[0]["profilepicpath"], name=name, email=email, username=username, address=address, phonenumber=phonenumber)

    if 'dp' not in request.files:
        flash("No image selected")
        return redirect("/account")
        # return apology("no image Selected")

    propic = request.files["dp"]
    if not propic:
        flash("No image selected")
        return redirect("/account")
        # return apology("No file selected")
        # flash("No file selected!")
        # return redirect('/account')
    filename = secure_filename(propic.filename)
    if filename == "":
        flash("No image selected")
        return render_template("/account")
    path = "../static/" + filename
    propic.save(os.path.join(app.config['IMAGE_UPLOADS'], filename))
    db.execute("UPDATE profilepicture SET profilepicpath=:filename WHERE id=:user_id", filename=path, user_id=user_id)
    print("image uploaded")
    return redirect("/account")

@app.route("/edit", methods=["GET", "POST"])
def edit():
    if request.method == "POST":
        code = request.form.get("code")
        saleitems = db.execute(
            "SELECT buydisplayimage.bimagename, sdetails.name, sdetails.discription, sdetails.price, sdetails.code, udetails.username, udetails.mobilenumber, udetails.email FROM sdetails "
            "JOIN buydisplayimage ON sdetails.code=buydisplayimage.code "
            "JOIN users ON sdetails.id=users.id "
            "JOIN udetails ON users.username = udetails.username "
            # "JOIN images ON sdetails.code=images.code "
            "WHERE sdetails.code=:code", code=code)
        images = db.execute("SELECT imagename FROM images WHERE code=:code", code=code)
        return render_template("edit.html", saleitems=saleitems,code=code, images=images)
@app.route("/editorders", methods=["GET", "POST"])
def editorders():
    if request.method == "POST":
        name = request.form.get("name")
        discription = request.form.get("discription")
        price = request.form.get("price")
        code = request.form.get("code")
        if name:
            db.execute("UPDATE sdetails SET name=:name WHERE code=:code", name=name, code=code)
        if discription:
            db.execute("UPDATE sdetails SET discription=:discription WHERE code=:code", discription=discription, code=code)
        if price:
            db.execute("UPDATE sdetails SET price=:price WHERE code=:code", price=price, code=code)
        flash("Order updated!")
        return render_template("index.html")



@app.route("/delete", methods=["GET", "POST"])
def delete():
    if request.method == "POST":
        code = request.form.get("code")
        db.execute("DELETE FROM sdetails WHERE code=:code", code=code)
        db.execute("DELETE FROM images WHERE code=:code", code=code)
        db.execute("DELETE FROM buydisplayimage WHERE code=:code", code=code)
        flash("Deleted successfully!")
        return render_template("index.html")

@app.route("/forgetp", methods=["GET", "POST"])
def forgetp():
    if request.method == "GET":
        return render_template("forgetp.html")

    else:
        email = request.form.get("email")

        # token = s.dumps(email, salt="password-forget")

        msg = Message("Reset-Password",
                      sender="ezybuysell.noreply@gmail.com",
                      recipients=[email])

        link = url_for("forget_password", email=email, _external=True)

        # msg.body = f"your link is {link}"
        msg.body = f"Welcome to EZY-BUY-SELL, Forgotten password? \r\n\n No worries! Click on the link below to reset your password: \r\n\n {link}"
        mail.send(msg)
        print("mail sent!")
        flash(
            "An email regarding the resetting your password has been sent on your registered email, you can change your password through that mail ")
        return render_template("login.html")
    # else:
    #     flash("Username already exists")
    #     return render_template("register.html")
    #     # return apology("Username already exists")


@app.route("/forgetp/<email>", methods=["GET", "POST"])
def forget_password(email):
    if request.method == "GET":
        return render_template("newpassword.html", email=email)
    else:
        new_password = request.form.get("newpassword")
        cnew_password = request.form.get("cnewpassword")
        hash_p = generate_password_hash(new_password)
        db.execute("UPDATE udetails SET password=:password WHERE email=:email", password=hash_p, email=email)
        db.execute("UPDATE users SET hash=:password WHERE username=(SELECT username FROM udetails WHERE email=:email)", password=hash_p, email=email)
        # db.execute("UPDATE udetails SET token=:new_token WHERE token=:token", new_token=new_token, token=token)
        flash("New password registered Successfully!")
        return redirect("/login")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
