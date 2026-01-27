# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: setup database connection parameters
# Status: VERSION 1.0
# FileID: Sc-da-0005

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import os
import base64
from dotenv import load_dotenv, set_key

# Set path for .env file
env_path = os.getcwd().split("/mhbai")[0] + "/mhbai/.env"


def b64url_encode(data) -> str:
    """
    b64 url encode data

    Args:
        data: data to urlsafe_b64encode

    Returns:
        str: encoded data
    """
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


# Generate private key
private_key_obj = ed25519.Ed25519PrivateKey.generate()
# Extract public key
public_key_obj = private_key_obj.public_key()

pem_private = private_key_obj.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)
private_key_string = pem_private.decode("utf-8")
pem_public = public_key_obj.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)
public_key_string = pem_public.decode("utf-8")

# Save to .env file
set_key(env_path, "PRIVATE_KEY", private_key_string)
set_key(env_path, "PUBLIC_KEY", public_key_string)


# Load environment variables from .env file
load_dotenv()
USERDB = "gatterle"
HOST = "localhost"
PORT = "5432"
DBNAME = "mhbs"
PASSWORD = input(f"Enter the postgresql database password for user {USERDB}: ")
set_key(env_path, "USERDB", USERDB)
set_key(env_path, "HOST", HOST)
set_key(env_path, "PORT", PORT)
set_key(env_path, "DBNAME", DBNAME)
set_key(env_path, "PASSWORD", PASSWORD)

inputted_email_data = input(
    "Enter the password for the email account (if using gmail enable 2FA, then add an app-password): "
)
set_key(env_path, "EMAIL_PASSWORD", inputted_email_data)
print("Keys saved to .env file.")
