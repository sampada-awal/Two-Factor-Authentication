from flask import Flask, render_template_string, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import pyotp, qrcode
import io, base64
import sqlite3
from cryptography.fernet import Fernet

app = Flask("MyApp")
app.secret_key = "supersecretkey"

fernet= Fernet(Fernet.generate_key())
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(''' CREATE TABLE IF NOT EXISTS usertbl
              (id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE,
              password_hash TEXT,
              secret TEXT)'''
              )
    conn.commit()
    conn.close()
init_db()

def add_user(username, password, secret):
    conn= sqlite3.connect("users.db")
    c= conn.cursor()
    enc_secret= fernet.encrypt(secret.encode()).decode()
    c.execute ("INSERT INTO usertbl (username,password_hash,secret)VALUES(?,?,?)",
               (username, generate_password_hash(password),enc_secret))
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash, secret FROM usertbl WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row


# Home
@app.route("/")
def home():
    if "username" in session:
        return f"✅ Logged in as {session['username']} <a href='/logout'>Logout</a>"
    return "<a href='/register'>Register</a> | <a href='/login'>Login</a>"

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if get_user(username):
            return "⚠️ User already exists!"
        secret = pyotp.random_base32()
        add_user(username,password,secret)
        return redirect(url_for("qrcode_page",username=username))

    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Register">
        </form>
    '''

# Show QR Code for Google Authenticator
@app.route("/qrcode/<username>")
def qrcode_page(username):
    user= get_user(username)
    if not user:
        return "User not found!"

    enc_secret= user[3]
    secret = fernet.decrypt(enc_secret.encode()).decode()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=username, issuer_name="My2FAApp")

    # Generate QR code as base64
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return render_template_string('''
        <h2>Scan this QR Code with Google Authenticator</h2>
        <img src="data:image/png;base64,{{qr_b64}}">
        <p>Or use this secret: <b>{{secret}}</b></p>
        <a href="/login">Go to Login</a>
    ''', qr_b64=qr_b64, secret=secret)

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        otp = request.form["otp"]

        user= get_user(username)
        if user and check_password_hash(user[2], password):
            enc_secret= user[3]
            secret= fernet.decrypt(enc_secret.encode()).decode()
            totp = pyotp.TOTP(secret)
            if totp.verify(otp):
                session["username"] = username
                return redirect(url_for("home"))
            else:
                return "❌ Invalid OTP!"
        else:
            return "❌ Invalid credentials!"

    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            OTP: <input type="text" name="otp"><br>
            <input type="submit" value="Login">
        </form>
    '''

# Logout
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)
