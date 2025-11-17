"""
Simple authentication for login page
"""
from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "giraffe-payslip-secret-2024"
ALGORITHM = "HS256"

# Hardcoded users - plain passwords for simplicity
USERS = {
    "ohadb@giraffe.co.il": "12345",
    "aviv@giraffe.co.il": "12345"
}

def create_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=8)
    return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def authenticate(email: str, password: str) -> bool:
    if email not in USERS:
        return False
    return USERS[email] == password
