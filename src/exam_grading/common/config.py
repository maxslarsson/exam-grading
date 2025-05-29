"""Configuration constants for exam grading package."""
import os

# prprpr API configuration
PRPRPR_DEBUG = os.getenv("PRPRPR_DEBUG", "0") == "1"

if PRPRPR_DEBUG:
    PRPRPR_CLIENT_ID = "w1pagvvYT00eDrxMykMyPDviS1gMwO4XJtiHajCN"
    PRPRPR_CLIENT_SECRET = "oawdfeOl6eqAiemWePB4k8M19HhjT4VNgSzR1MialtusFfltcExzYhfoeOAzat0N6pNoE6E7aMMXFASOIBEFEWlUqwq9qRm4Aw2xJ283upImVu8vKJdy6zHmudKxUzF6"
    PRPRPR_BASE_URL = "http://127.0.0.1:8000"
else:
    PRPRPR_CLIENT_ID = "Wf42oWVR2YsYfwQYT2Aoh6dqgZyo23FQ0ofOIdEZ"
    PRPRPR_CLIENT_SECRET = "BIojMEaDVRcnKgmMdoUNnSv3FErvimiFhQnInv7zZrE5ZYYVODpbdfUOYPYn5O6OKJAguKdCMc3Xd3WxA99242fMG4l8JjtcorrOYwkuBJ92VpneVAuKSxPO55e9FIp7"
    PRPRPR_BASE_URL = "https://clrify.it"

# AWS configuration
AWS_BUCKET_NAME = "prprpr-s3"

# Google Sheets configuration
GOOGLE_SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GOOGLE_CLIENT_CONFIG = {
    "installed": {
        "client_id": "1007793518905-fgcltlggqtd8r1mgdrucr0vaj9moj8m9.apps.googleusercontent.com",
        "project_id": "automated-grading-2",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",
        "redirect_uris": ["http://localhost"],
    }
}