"""Authentication utilities for exam grading package.

This module handles OAuth2 authentication for the prprpr grading service
using the PKCE (Proof Key for Code Exchange) flow for enhanced security.
"""
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
    """Get OAuth2 access token using PKCE flow for prprpr API.
    
    This function implements the OAuth2 authorization code flow with PKCE
    (Proof Key for Code Exchange) for enhanced security. It:
    1. Generates a cryptographically secure code verifier and challenge
    2. Opens a local web server to receive the OAuth callback
    3. Opens the user's browser for authentication
    4. Exchanges the authorization code for an access token
    
    Returns:
        str: Access token for authenticating API requests
        
    Raises:
        requests.HTTPError: If token exchange fails
        KeyError: If authorization code is missing from callback
    """
    # Generate code verifier - a random string of 43-128 characters
    # This is used in PKCE to prevent authorization code interception attacks
    code_verifier = ''.join(random.choice(string.ascii_uppercase + string.digits) 
                           for _ in range(random.randint(43, 128)))

    # Generate code challenge by hashing the verifier
    # The challenge is sent with the auth request, verifier is kept secret until token exchange
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8').replace('=', '')

    # Open a socket to listen for the OAuth callback
    with socket.socket() as s:
        # Bind to localhost on any available port
        s.bind(("localhost", 0))
        s.listen()

        # Get the assigned port number for the redirect URI
        port = s.getsockname()[1]
        redirect_uri = f"http://127.0.0.1:{port}"
        
        # Construct the authorization URL with PKCE parameters
        auth_url = (f"{PRPRPR_BASE_URL}/o/authorize/?response_type=code&"
                   f"code_challenge={code_challenge}&code_challenge_method=S256&"
                   f"client_id={PRPRPR_CLIENT_ID}&redirect_uri={redirect_uri}")
        
        print(f"Please visit this URL to authorize this application: {auth_url}")

        # Open the authorization URL in the user's default browser
        webbrowser.open(auth_url)

        # Wait for the OAuth callback
        conn, _ = s.accept()
        request = conn.recv(4096)

        # Send success message to browser
        conn.send(b"HTTP/1.1 200 OK\n"
                  b"Content-Type: text/html\n\n"
                  b"<html><body>The authentication flow has completed. You may close this window and return to the terminal.</body></html>")

    # Extract authorization code from the callback URL
    url = request.decode().split()[1]
    query = parse_qs(urlparse(url).query)
    auth_code = query["code"][0]

    # Exchange authorization code for access token
    # Include the code verifier to complete the PKCE flow
    data = {
        "client_id": PRPRPR_CLIENT_ID,
        "client_secret": PRPRPR_CLIENT_SECRET,
        "code": auth_code,
        "code_verifier": code_verifier,  # This proves we initiated the auth request
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    # Make token exchange request
    r = requests.post(f"{PRPRPR_BASE_URL}/o/token/", data=data)
    r.raise_for_status()
    
    # Return the access token for API authentication
    return r.json()["access_token"]