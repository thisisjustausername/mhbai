import os
from api import base_data


mhbai_logo = os.path.expanduser("./api/email/assets/favicon_150.png")


def confirm_email(first_name: str, last_name: str, verification_token: str) -> dict:
    """
    Returns the email template for confirming a user's email address.
    Args:
        first_name (str): First name of the user.
        last_name (str): Last name of the user.
        verification_token (str): The verification token for email confirmation.
    Returns:
        dict: A dictionary containing the subject, body, and images for the email.
    """
    image_data = ({"name": "decrypt-images-logo", "value": mhbai_logo},)

    subject = "Neuer Benutzeraccount für MHBAI"
    body = f"""<html lang="de">
    <body style="background-color: #430101; text-align: center; font-family: Arial, sans-serif; padding: 20px; color: #ffffff;">
        <div>
            <img src="cid:{image_data[0]["name"]}" alt="MHBAI Logo" width="150">
    </div>
        <h2>Hallo {first_name} {last_name},</h2>
        <p>Du hast einen Account für MHBAI erstellt.</p>
        <p>Um die Registrierung abzuschließen, musst du noch deine Email bestätigen.</p>
        </br>
        <div style="text-align:center; margin: 20px 0;">
      <a href="https://{base_data.base_url()}/verify?token={verification_token}"
         style="
           background-color: #0b9a79;
           color: #ffffff;
           padding: 12px 24px;
           text-decoration: none;
           border-radius: 5px;
           display: inline-block;
           font-weight: bold;
           box-shadow: 0 0 10px #da6cff;
           font-family: Arial, sans-serif;
         ">
        Email bestätigen
      </a>
    </div>

        </br>
        <p>Wir freuen uns auf dich!</p>
        <p>Dein MHBAI-Team</p>
    </body>
    </html>"""
    return {"subject": subject, "body": body, "images": image_data}


def reset_password(first_name: str, last_name: str, reset_token: str):
    """
    template for password reset email

    Args:
        first_name (str): first name of the user
        last_name (str): last name of the user

    Returns:
        dict[str, str | dict]: dictionary containing subject, body and images
    """
    image_data = ({"name": "mhbai_logo", "value": mhbai_logo},)

    subject = "Passwort zurücksetzen"
    body = f"""<html lang="de">
        <body style="background-color: #430101; text-align: center; font-family: Arial, sans-serif; padding: 20px; color: #ffffff;">
            <div>
                <img src="cid:{image_data[0]["name"]}" alt="MHBAI Logo" width="150">
        </div>
            <h2>Hallo {first_name} {last_name},</h2>
            <p>hier kannst du ein neues Passwort setzen:</p>
        </br>
        <div style="text-align:center; margin: 20px 0;">
      <a href="https://{base_data.base_url()}/setup/password-reset?token={reset_token}"
         style="
           background-color: #0b9a79;
           color: #ffffff;
           padding: 12px 24px;
           text-decoration: none;
           border-radius: 5px;
           display: inline-block;
           font-weight: bold;
           box-shadow: 0 0 10px #da6cff;
           font-family: Arial, sans-serif;
         ">
        Passwort zurücksetzen
      </a>
    </div>
        <p>Falls du keine Passwort-Zurücksetzung angefordert hast, wende dich bitte umgehend an das Tutoren-Team.</p>
        </br>
        <p>Wir freuen uns auf dich!</p>
        <p>Dein MHBAI-Team</p>
        </body>
        </html>"""
    return {"subject": subject, "body": body, "images": image_data}
