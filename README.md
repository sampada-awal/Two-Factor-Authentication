🔐 Two-Factor Authentication (2FA) – Python Web Application

This project implements a secure Two-Factor Authentication (2FA) system using Python, Google Authenticator (TOTP), and strong cryptographic methods. It demonstrates how to securely manage users, generate TOTP codes, and protect sensitive information using industry-standard security practices.

🚀 Features

✔️ User registration & login
✔️ Google Authenticator (TOTP) setup
✔️ QR code generation for TOTP pairing
✔️ Secure password hashing using bcrypt
✔️ Secure storage of user TOTP secrets using Fernet encryption
✔️ SQLite database for persistent user management
✔️ 2FA verification during login
✔️ Session handling (optional depending on your implementation)

🛠️ Technologies Used

Python 3.x

Flask 

bcrypt (password hashing)

cryptography.fernet (encrypt TOTP secrets)

pyotp (Google Authenticator / TOTP)

qrcode (QR code generation)

SQLite (database)

🔑 How It Works (Authentication Flow)
1️⃣ User Registers

User creates an account → password is hashed using bcrypt.

A TOTP secret key is generated.

Secret key is encrypted with Fernet and stored in the database.

A QR code is shown to the user for adding the account to Google Authenticator.

2️⃣ User Logs In

User enters email + password
→ Password is verified using bcrypt.

If correct, user proceeds to 2FA step.

User enters the 6-digit Google Authenticator code.

Server validates the TOTP using pyotp.

If valid → User is authenticated.
