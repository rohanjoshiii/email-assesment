from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from imapclient import IMAPClient
import email
from email.header import decode_header
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Allow CORS so that the frontend can communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Email credentials from environment variables
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

@app.get("/emails")
def get_emails():
    emails_list = []
    try:
        # Connect to Gmail IMAP server
        with IMAPClient("imap.gmail.com") as client:
            client.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            client.select_folder("INBOX")

            # Search for all non-deleted emails
            messages = client.search(["NOT", "DELETED"])

            # Fetch and process each email
            for uid, message_data in client.fetch(messages, ["RFC822"]).items():
                msg = email.message_from_bytes(message_data[b"RFC822"])

                # Decode subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")

                from_ = msg.get("From")

                # Extract body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()

                # Append to emails list
                emails_list.append({
                    "id": uid,
                    "subject": subject,
                    "from": from_,
                    "body": body
                })

    except Exception as e:
        return {"error": str(e)}

    return emails_list
