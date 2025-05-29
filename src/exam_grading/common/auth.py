"""Authentication utilities for exam grading package."""
import random
import string
import base64
import socket
import hashlib
import requests
import webbrowser
from urllib.parse import urlparse, parse_qs

from .config import PRPRPR_CLIENT_ID, PRPRPR_CLIENT_SECRET, PRPRPR_BASE_URL


def get_prprpr_access_token() -> str:
    """Get OAuth2 access token using PKCE flow for prprpr API."""
    code_verifier = ''.join(random.choice(string.ascii_uppercase + string.digits) 
                           for _ in range(random.randint(43, 128)))

    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8').replace('=', '')

    # Open a socket to listen for the response from authentication
    with socket.socket() as s:
        s.bind(("localhost", 0))
        s.listen()

        port = s.getsockname()[1]
        redirect_uri = f"http://127.0.0.1:{port}"
        auth_url = (f"{PRPRPR_BASE_URL}/o/authorize/?response_type=code&"
                   f"code_challenge={code_challenge}&code_challenge_method=S256&"
                   f"client_id={PRPRPR_CLIENT_ID}&redirect_uri={redirect_uri}")
        
        print(f"Please visit this URL to authorize this application: {auth_url}")

        webbrowser.open(auth_url)

        conn, _ = s.accept()
        request = conn.recv(4096)

        # Send success message to browser
        conn.send(b"HTTP/1.1 200 OK\n"
                  b"Content-Type: text/html\n\n"
                  b"<html><body>The authentication flow has completed. You may close this window and return to the terminal.</body></html>")

    # Extract authorization code from URL
    url = request.decode().split()[1]
    query = parse_qs(urlparse(url).query)
    auth_code = query["code"][0]

    # Exchange authorization code for access token
    data = {
        "client_id": PRPRPR_CLIENT_ID,
        "client_secret": PRPRPR_CLIENT_SECRET,
        "code": auth_code,
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    r = requests.post(f"{PRPRPR_BASE_URL}/o/token/", data=data)
    r.raise_for_status()
    return r.json()["access_token"]