# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# For usage please contact the developer.
#
# This file is Copyright-protected.

# Description: api
# Status: VERSION 1.0
# FileID: Ap-x-0002

"""
Flask api for website
"""

import time
import json
from flask import Flask, Response, request
from psycopg2.extensions import cursor as Cursor

from datatypes.response import Response as FuncRes, Status, Message
from pdf_reader import pdf_reader_toc as prt
from ai.overall_ai.data_extraction import extract_module_info as emi
from api.data_types import UserRole, Email
from api.users import UserIdentifier, Identifier
from database import database as db
from api import users, security, sessions, mail
from api.email import templates


# initialize Flask app
app = Flask(__name__)


@app.route("/auth/login", methods=["POST"])
@db.cursor_handling(manually_supply_cursor=False)
def login(cursor: Cursor | None = None) -> Response:
    """
    checks, whether a user exists and whether user is logged in (if exists and not logged in, session is created)

    Args:
        cursor (cursor | None): cursor for db connection, specified by decorator

    Returns:
        Response: flask Response object
    """

    # load data
    data = request.get_json()

    name = data.get("user", None)
    password = data.get("password", None)

    # password can't be empty
    if password == "":
        response = Response(
            response=json.dumps({"code": 400, "message": "password cannot be empty"}),
            status=401,
            mimetype="application/json",
        )
        return response

    if name is None:
        response = Response(
            response=json.dumps({"code": 400, "message": "specify user"}),
            status=400,
            mimetype="application/json",
        )
        return response
    else:
        name = name.lower()

    user_email: Email | None = None
    user_name: str | None = None

    if "@" in name:
        try:
            name = Email(email=name)
        except ValueError:
            response = Response(
                response=json.dumps({"code": 400, "message": "Invalid email format"}),
                status=400,
                mimetype="application/json",
            )
            return response
        user_email = name
    else:
        user_name = name

    # if data is not valid return error
    if password is None:
        response = Response(
            response=json.dumps({"code": 400, "message": "specify password"}),
            status=400,
            mimetype="application/json",
        )
        return response

    # get user data from table
    result = users.get_user(
        cursor=cursor,  # type: ignore
        keywords=["id", "password_hash", "user_role"],
        user_identifier=UserIdentifier(
            identifier=Identifier.EMAIL,
            value=user_email if user_email is not None else user_name,  # type: ignore
        ),
    )

    # return error
    if result.is_error:
        response = Response(
            response=json.dumps({"code": 500, "message": str(result.error)}),
            status=500,
            mimetype="application/json",
        )
        return response

    if result.data is None:
        response = Response(
            response=json.dumps({"code": 500, "message": "Failed to find user"}),
            status=500,
            mimetype="application/json",
        )
        return response

    # check password
    user = result.data

    if user[1] is None:
        response = Response(
            response=json.dumps(
                {
                    "code": 401,
                    "message": "account was deleted, can be reactivated by signup",
                }
            ),
            status=401,
            mimetype="application/json",
        )
        return response

    # if passwords don't match return error
    if not security.match_pwd(password, user[1]):
        response = Response(
            response=json.dumps({"code": 401, "message": "invalid password"}),
            status=401,
            mimetype="application/json",
        )
        return response

    # create a new session
    result = sessions.create_session(cursor=cursor, user_id=user[0])  # type: ignore

    if result.is_error:
        response = Response(
            response=json.dumps({"code": 500, "message": result.error}),
            status=500,
            mimetype="application/json",
        )
        return response

    session_id, expiration_date = result.data

    # return 204
    response = Response(status=204)

    response.set_cookie(
        "SID",
        session_id,
        expires=expiration_date,
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return response


@app.route("/auth/signup", methods=["POST"])
@db.cursor_handling(manually_supply_cursor=True)
def signup_data(cursor: Cursor | None = None):
    """
    create a new user
    """

    # load data
    data = request.get_json()

    privacy_policy = data.get("privacyPolicy", None)
    if privacy_policy is None or privacy_policy is False:
        response = Response(
            response=json.dumps(
                {"code": 400, "message": "Privacy policy needs to be accepted"}
            ),
            status=400,
            mimetype="application/json",
        )
        return response

    # initialize user_info
    user_info = {}
    user_info["first_name"] = data.get("firstName", None)
    user_info["last_name"] = data.get("lastName", None)
    user_info["email"] = data.get("email", None)
    user_info["organization"] = data.get("organization", None)
    user_info["user_name"] = data.get("username", None)
    user_info["password"] = data.get("password", None)

    # if a value wasn't set, return error
    if any(e is None for e in user_info.values()):
        response = Response(
            response=json.dumps(
                {
                    "code": 400,
                    "message": f"The following fields must be specified: {', '.join([key for key, value in user_info.items() if value is None])}",
                }
            ),
            status=400,
            mimetype="application/json",
        )
        return response
    else:
        user_info["email"] = user_info["email"].lower()
        user_info["user_name"] = user_info["user_name"].lower()

    # check, whether email is valid
    try:
        user_info["email"] = Email(email=user_info["email"])
    except ValueError:
        response = Response(
            response=json.dumps({"code": 400, "message": "Invalid email format"}),
            status=400,
            mimetype="application/json",
        )
        return response

    user_role = UserRole.USER
    user_info["user_role"] = user_role
    check_info = user_info.copy()
    del check_info["password"]
    # check whether user data is unique
    result = validate_user_data(cursor=cursor, **check_info)
    if result.is_error:
        response = Response(
            response=json.dumps(
                {
                    "code": result.code  # type: ignore
                    if result.message is None or result.message.code is None
                    else result.message.code,
                    "message": str(result.error),
                }
            ),
            status=result.code  # type: ignore
            if result.message is None or result.message.code is None
            else result.message.code,
            mimetype="application/json",
        )
        return response

    # hash password
    hashed_password = security.hash_pwd(user_info["password"])
    user_info["password_hash"] = hashed_password
    del user_info["password"]

    additional_data = user_info

    if result.data is False:
        additional_data["method"] = "update"
    else:
        additional_data["method"] = "create"

    result = users.create_verification_code(
        cursor=cursor,  # type: ignore
        user_id=None,
        additional_data=additional_data,  # type: ignore
    )

    if result.is_error:
        response = Response(
            response=json.dumps({"code": 500, "message": str(result.error)}),
            status=500,
            mimetype="application/json",
        )
        return response
    verification_token = result.data

    result = templates.confirm_email(
        first_name=user_info["first_name"],
        last_name=user_info["last_name"],
        verification_token=verification_token,
    )

    result = mail.send_mail(
        recipient=user_info["email"],
        subject=result["subject"],
        body=result["body"],
        images=result["images"],
        html=True,
    )

    if result.is_error:
        response = Response(
            response=json.dumps({"code": 500, "message": str(result.error)}),
            status=500,
            mimetype="application/json",
        )
        return response
    response = Response(status=204)
    return response


def validate_user_data(
    cursor,
    user_role: UserRole,
    organization: str,
    first_name: str,
    last_name: str,
    email: Email,
    user_name: str,
) -> FuncRes:
    """
    Validate user data for signup.

    Args:
        cursor: database cursor
        user_role (UserRole): Role of the user, must be one of UserRole except 'admin'.
        organization (str): Organization of the user, cannot be empty or None.
        first_name (str): First name of the user, cannot be empty or None.
        last_name (str): Last name of the user, cannot be empty or None.
        email (Email): Email of the user, must be of type Email.
        user_name (str): Username of the user, cannot be empty or None.

    Returns:
        dict: A dictionary with keys 'success' (bool), 'error' (str, optional), and 'status' (int).
              'success' is True if all validations pass, otherwise False with an appropriate error message.
              'status' is 200 for success, 400 for client errors, and 500 for server errors.
    """
    if not isinstance(user_role, UserRole) or (user_role.value == "admin"):
        return FuncRes(
            error_data="Invalid user role, admin not allowed",
            message=Message(
                name="Invalid user role",
                category="User error",
                type="error",
                info="Invalid user role, admin not allowed",
                code=400,
            ),
            status=Status.FULL_ERROR,
        )

    if not organization:
        return FuncRes(
            error_data="Organization cannot be empty or None",
            message=Message(
                name="Unspecified organization",
                category="User error",
                type="error",
                info="Organization cannot be empty or None",
                code=400,
            ),
            status=Status.FULL_ERROR,
        )

    if not first_name or not last_name:
        return FuncRes(
            error_data="First name and last name cannot be or None",
            message=Message(
                name="Unspecified first name or last name",
                category="User error",
                type="error",
                info="First name and last name cannot be or None",
                code=400,
            ),
            status=Status.FULL_ERROR,
        )

    if not isinstance(email, Email):
        return FuncRes(
            error_data="Invalid email format, must be of type Email",
            message=Message(
                name="Unspecified first name or last name",
                category="User error",
                type="error",
                info="Invalid email format, must be of type Email",
                code=400,
            ),
            status=Status.FULL_ERROR,
        )

    query = """SELECT email, user_name FROM users WHERE email = %s OR user_name = %s;"""
    result = db.custom_call(
        cursor=cursor,
        query=query,
        variables=[email.email, user_name],
        type_of_answer=db.ANSWER_TYPE.LIST_ANSWER,
    )

    if result.is_error:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="Database error",
                info="Failed to query database for existing users",
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    result._data = [] if result.data is None else result.data

    for i in result.data:
        if email.email == i[1]:
            return FuncRes(
                success_data=False,
                message=Message(
                    name="Account already exists",
                    type="success",
                    category="User warning",
                    details={"user_id": i[0]},
                    info="An account already exists for this email.",
                    code=200,
                ),
                user_warning="An account already exists for this email.",
                status=Status.FULL_SUCCESS,
            )

    if len(result.data) >= 1:
        return FuncRes(
            success_data=False,
            message=Message(
                name="Username already exists",
                type="success",
                category="User warning",
                info="Username already exists.",
                code=200,
            ),
            user_warning="Username already exists.",
            status=Status.FULL_SUCCESS,
        )

    return FuncRes(
        success_data=True,
        message=Message(
            name="Check successful",
            type="success",
            category="Success",
            info="Check successful",
            code=200,
        ),
        user_warning="Check successful",
        status=Status.FULL_SUCCESS,
    )


@app.route("/auth/verify_signup", methods=["POST"])
@db.cursor_handling(manually_supply_cursor=False)
def verify_signup(cursor: Cursor | None = None):
    """
    verifies the signup
    """

    # load data
    data = request.get_json()
    token = data.get("token", None)

    if token is None:
        response = Response(
            response=json.dumps(
                {"code": 400, "message": "The token must be specified"}
            ),
            status=400,
            mimetype="application/json",
        )
        return response

    # verify token
    result = users.confirm_verification_code(
        cursor=cursor,  # type: ignore
        reset_code=token,
        additional_data=True,
        expiration_minutes=30,  # type: ignore
    )
    if result.is_error:
        response = Response(
            response=json.dumps({"code": 500, "message": str(result.error)}),
            status=500,
            mimetype="application/json",
        )
        return response

    additional_data = result.data[1]
    method = additional_data["method"]
    user_info = additional_data.copy()
    del user_info["method"]

    user_info = {
        k: UserRole(v) if k == "user_role" else Email(v) if k == "email" else v
        for k, v in user_info.items()
    }

    # add user to table
    # TODO maybe check, whether correct user is updated and whether it is really allowed
    if method == "update":
        user_data = {}
        user_data["user_role"] = user_info["user_role"]
        user_data["password_hash"] = user_info["password_hash"]
        user_data["user_name"] = user_info["user_name"]
        result = users.update_user(
            cursor=cursor,  # type: ignore
            user_email=user_info["email"],
            **user_data,  # type: ignore
        )
    else:
        result = users.add_user(cursor=cursor, returning_column="id", **user_info)  # type: ignore
    # if server error occurred, return error
    if result.is_error:
        response = Response(
            response=json.dumps({"code": 500, "message": str(result.error)}),
            status=500,
            mimetype="application/json",
        )
        return response

    user_id = result.data

    # create a new session
    result = sessions.create_session(cursor=cursor, user_id=user_id)  # type: ignore

    if result.is_error:
        response = Response(
            response=json.dumps({"code": 500, "message": str(result.error)}),
            status=500,
            mimetype="application/json",
        )
        return response

    session_id, expiration_date = result.data

    # return 204
    response = Response(status=204)

    response.set_cookie(
        "SID",
        session_id,
        expires=expiration_date,
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return response


@app.route("/auth/logout", methods=["POST"])
@db.cursor_handling(manually_supply_cursor=False)
def logout(cursor: Cursor | None = None):
    """
    removes the session id
    """
    session_id = request.cookies.get("SID", None)
    if session_id is None:
        response = Response(
            response=json.dumps(
                {"code": 401, "message": "The session id must be specified"}
            ),
            status=401,
            mimetype="application/json",
        )
        return response

    # remove session from table
    result = sessions.remove_session(cursor=cursor, session_id=session_id)  # type: ignore

    # if nothing could be removed, return error
    if result.is_error:
        response = Response(
            response=json.dumps({"code": 401, "message": str(result.error)}),
            status=401,
            mimetype="application/json",
        )
        return response

    # return 204
    response = Response(status=204)
    return response


@app.route("/api/get_mhb_info", methods=["POST"])
def get_mhb_info() -> Response:
    """
    API endpoint to get MHB information.

    Returns:
        Response: Flask Response object containing MHB information.
    """
    # start time-measurement
    start = time.perf_counter()

    # initialize free limit
    limit: int | None = 4

    # get data from request
    data = request.files

    # get mhb-pdf
    mhb_pdf = data.get("file", None)
    if mhb_pdf is None:  # or mhb_pdf.content_type != "multipart/form-data":
        response = Response(
            response=json.dumps({"message": "No valid PDF-file provided"}),
            status=400,
            mimetype="application/json",
        )
        return response

    # process pdf
    modules: prt.Modules = prt.Modules(pdf_file=mhb_pdf)  # type: ignore
    raw_modules = modules.raw_module_texts()

    # in order to reduce processing time with the ai, remove duplicates
    if limit is not None and limit > 1:
        keys = raw_modules[0].keys()
        unique_modules = set(tuple(module.values()) for module in raw_modules)
        raw_modules = list(dict(zip(keys, items)) for items in unique_modules)

    process_ready_mods = raw_modules[:limit] if limit is not None else raw_modules

    num_modules = len(process_ready_mods)

    for module in process_ready_mods:
        try:
            result = emi(module_text=module["content"], model="llama3.2:3b")  # type: ignore
        except Exception as e:
            response = Response(
                response=json.dumps(
                    {
                        "message": f"Error processing module: {module['module_code']}",
                    }
                ),
                status=500,
                mimetype="application/json",
            )
            return response

        # append extracted data to module dict
        module["extracted_data"] = result.model_dump()
        credibility = 1
        if module["extracted_data"]["module_code"] is None:
            module["extracted_data"]["module_code"] = module["module_code"]
            credibility = 0
        else:
            if module["extracted_data"]["module_code"] != module["module_code"]:
                credibility = -1
        module["extracted_data"]["credibility"] = credibility

    # end time-measurement
    end = time.perf_counter()
    processing_time = end - start

    response = Response(
        response=json.dumps(
            {
                "message": f"Successfully extracted {num_modules} unique modules",
                "information": f"LIMITED TO {limit} Module",
                "processing_time": processing_time,
                "data": [i["extracted_data"] for i in process_ready_mods],
            }
        ),
        status=200,
        mimetype="application/json",
    )
    return response
