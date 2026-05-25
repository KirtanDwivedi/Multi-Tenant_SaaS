import json
import secrets
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType

app = FastAPI()

# Enable CORS so your frontend can communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your specific frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load variables from configuration JSON
with open("config.json", "r") as config_file:
    config_data = json.load(config_file)

ALLOWED_DOMAIN = config_data["ALLOWED_DOMAIN"]

# Set up SMTP configuration using JSON parameters
mail_config = ConnectionConfig(
    MAIL_USERNAME=config_data["MAIL_USERNAME"],
    MAIL_PASSWORD=config_data["MAIL_PASSWORD"],
    MAIL_FROM=config_data["MAIL_FROM"],
    MAIL_PORT=config_data["MAIL_PORT"],
    MAIL_SERVER=config_data["MAIL_SERVER"],
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Temporary in-memory token database (Use Redis or a real DB in production for expiration)
TOKEN_DB = {}

class EmailSchema(BaseModel):
    email: EmailStr

@app.post("/auth/send-link")
async def send_magic_link(data: EmailSchema):
    email_domain = data.email.split("@")[-1].lower()
    
    # 1. Strong backend enforcement check
    if email_domain != ALLOWED_DOMAIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not in Organization. Access denied."
        )
    
    # 2. Secure token generation
    token = secrets.token_urlsafe(32)
    TOKEN_DB[token] = data.email
    
    # 3. Construct your frontend routing link
    verification_link = f"{config_data['FRONTEND_VERIFY_URL']}?token={token}"
    
    # 4. Craft email payload
    message = MessageSchema(
        subject="Your Thapar Workspace Login Link",
        recipients=[data.email],
        body=f"""
        <h3>Thapar Authentication</h3>
        <p>Click the link below to securely log into your account:</p>
        <p><a href="{verification_link}" style="padding:10px 20px; background-color:#4F46E5; color:white; text-decoration:none; border-radius:5px;">Log In</a></p>
        <p>Or copy paste this link: {verification_link}</p>
        """,
        subtype=MessageType.html
    )
    
    # 5. Dispatch email via Gmail SMTP server
    try:
        fm = FastMail(mail_config)
        await fm.send_message(message)
        return {"message": "Magic link sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deliver email: {str(e)}")

@app.get("/auth/verify")
async def verify_magic_link(token: str):
    # 1. Search for stored token validation
    email = TOKEN_DB.get(token)
    if not email:
        raise HTTPException(status_code=400, detail="The validation token is invalid or has expired.")
    
    # 2. Immediately consume token to prevent replay attacks
    del TOKEN_DB[token]
    
    # 3. Parse username identifier from prefix
    username = email.split("@")[0]
    
    return {
        "status": "success",
        "username": username,
        "email": email
    }
