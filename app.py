from flask import Flask, request, redirect, url_for, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import pyotp
import urllib.parse

app = Flask(__name__)
app.secret_key = "simple-2fa-secret"

# --------------------
# Database
# --------------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            secret TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

# --------------------
# Helper: CSS style for forms
# --------------------
form_style = """
<div style="max-width:400px; margin:auto; padding:20px; border:1px solid #ccc;
            border-radius:10px; box-shadow:2px 2px 15px #eee; font-family:Arial;">
<h2 style="text-align:center; color:#333;">{title}</h2>
{body}
<a href='/' style="display:block; text-align:center; margin-top:10px; color:#555;">Back to Home</a>
</div>
"""

input_style = "style='width:100%; padding:8px; margin:5px 0; border-radius:5px; border:1px solid #ccc;'"
button_style = "style='width:100%; padding:10px; background-color:#4CAF50; color:white; border:none; border-radius:5px; cursor:pointer;'"

# --------------------
# Routes
# --------------------
@app.route("/")
def home():
    if "user" in session:
        return f"""
        <div style='text-align:center; font-family:Arial; margin-top:50px;'>
            <h2>Welcome, {session['user']} ✅</h2>
            <a href='/logout' style='text-decoration:none; color:white; background-color:#f44336;
               padding:10px 20px; border-radius:5px;'>Logout</a>
        </div>
        """
    return """
    <div style='text-align:center; font-family:Arial; margin-top:50px;'>
        <h2>Welcome to Simple 2FA Demo</h2>
        <a href='/register' style='margin:0 10px;'>Register</a> | 
        <a href='/login' style='margin:0 10px;'>Login</a>
    </div>
    """

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if get_user(username):
            return render_template_string(form_style.format(
                title="Register",
                body="<p style='color:red;'>❌ User already exists!</p>"
            ))

        secret = pyotp.random_base32()

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute(
            "INSERT INTO users (username, password_hash, secret) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), secret)
        )
        conn.commit()
        conn.close()

        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=username, issuer_name="Simple2FA")
        qr_url = (
            "https://api.qrserver.com/v1/create-qr-code/"
            "?size=200x200&data=" + urllib.parse.quote(uri)
        )

        return render_template_string(form_style.format(
            title="2FA QR Code",
            body=f"""
                <p style='text-align:center;'>Scan this QR code using Google Authenticator:</p>
                <img src="{qr_url}" style='display:block; margin:auto;'><br>
                <p style='text-align:center;'>Then <a href='/login'>Login</a></p>
            """
        ))

    return render_template_string(form_style.format(
        title="Register New User",
        body=f"""
        <form method='post'>
            <label>Username:</label><br>
            <input name='username' {input_style} required><br>
            
            <label>Password:</label><br>
            <input type='password' name='password' {input_style} required><br><br>
            
            <input type='submit' value='Register' {button_style}>
        </form>
        """
    ))

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        otp = request.form["otp"]

        user = get_user(username)
        if not user or not check_password_hash(user[2], password):
            return render_template_string(form_style.format(
                title="Login",
                body="<p style='color:red;'>❌ Invalid username or password</p>"
            ))

        totp = pyotp.TOTP(user[3])
        if not totp.verify(otp):
            return render_template_string(form_style.format(
                title="Login",
                body="<p style='color:red;'>❌ Invalid OTP</p>"
            ))

        session["user"] = username
        return redirect(url_for("home"))

    return render_template_string(form_style.format(
        title="Login",
        body=f"""
        <form method='post'>
            <label>Username:</label><br>
            <input name='username' {input_style} required><br>
            
            <label>Password:</label><br>
            <input type='password' name='password' {input_style} required><br>
            
            <label>OTP (Google Authenticator):</label><br>
            <input name='otp' {input_style} required><br><br>
            
            <input type='submit' value='Login' {button_style}>
        </form>
        """
    ))

# Logout
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)

