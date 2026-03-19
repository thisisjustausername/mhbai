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
from psycopg import sql
from bidict import bidict
from flask import Flask, Response, request

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
def login() -> Response:
    """
    checks, whether a user exists and whether user is logged in (if exists and not logged in, session is created)

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
    result = sessions.create_session(user_id=user[0])  # type: ignore

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
def signup_data() -> Response:
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
    result = validate_user_data(**check_info)
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

    query = (
        """SELECT email, user_name FROM api.users WHERE email = %s OR user_name = %s;"""
    )
    result = db.custom_call(
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
def verify_signup() -> Response:
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
            user_email=user_info["email"],
            **user_data,  # type: ignore
        )
    else:
        result = users.add_user(returning_column="id", **user_info)  # type: ignore
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
    result = sessions.create_session(user_id=user_id)  # type: ignore

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
def logout() -> Response:
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
    result = sessions.remove_session(session_id=session_id)

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


def replace_none_with_dash(obj):
    """
    helper function to replace None values with a dash in a nested data structure (dicts, lists, tuples, sets).

    Args:
        obj: The input data structure which can be a dict, list, tuple, set,
    Returns:
        The same data structure with None values replaced by a dash.
    """
    if obj is None:
        return "-"
    elif isinstance(obj, dict):
        return {k: replace_none_with_dash(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [replace_none_with_dash(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(replace_none_with_dash(item) for item in obj)
    elif isinstance(obj, set):
        return {replace_none_with_dash(item) for item in obj}
    else:
        return obj
    
@app.route("/get-module/filters", methods=["GET"])
def get_module_filters() -> Response:
    """
    API endpoint to get allowed filter values for specified filter

    Returns:
        Response: Flask Response object containing valid options for the specified filter.
    """

    filter = request.args.get("filter", None)
    
    filters_with_options = ["version", "subject"]
    filters = filters_with_options if filter is None else [filter]
    if filter is not None and filter not in filters_with_options:
        response = Response(
            response=json.dumps({"message": f"Filter '{filter}' does not have data dependent options"}),
            status=400,
            mimetype="application/json",
        )
        return response
    
    res = dict()
    for f in filters:
        if f == "version":
            query = """SELECT DISTINCT version FROM unia.mhbs WHERE version IS NOT NULL ORDER BY version DESC;"""
        else:
            query = """SELECT DISTINCT UPPER(substring(module_code, 1, POSITION('-' IN module_code) - 1)) as subject FROM unia.modules_raw ORDER BY subject ASC;"""

        result = db.custom_call(
            query=query,
            type_of_answer=db.ANSWER_TYPE.LIST_ANSWER
        )

        if result.is_error:
            response = Response(
                response=json.dumps({"message": "Error occurred in the backend"}),
                status=500,
                content_type="application/json",
            )
            return response
        
        # NOTE: This can't happen, but still is added for safety
        if result.data is None:
            response = Response(
                response=json.dumps({"message": "No data found for the specified filter"}),
                status=404,
                content_type="application/json",
            )
            return response
        
        if f == "version":
            res[f] = [("W" if (winter := int(str(i[0])[-1]) == 1) else "S") + "S " + (year := str(i[0])[:-1]) + (("/" + str(int(year) + 1)) if winter else "") for i in result.data]
        else:
            res[f] = [a if "\\" not in (a := i[0]) else a.encode('latin1').decode('unicode_escape') for i in result.data]
            
    return Response(
        response=json.dumps(res if filter is None else res[filter]),
        status=200,
        content_type="application/json"
    )


@app.route("/get-modules", methods=["POST"])
def get_modules() -> Response:
    """
    API endpoint to get module information based on search query.

    Returns:
        Response: Flask Response object containing module information.
    """

    allowed_filter_supplements = bidict({
        "ects_type": "ects",
        "weekly_hours_type": "weekly_hours",
        "recommended_semester_type": "recommended_semester"
    })

    allowed_comparison_methods = ["=", "<=", ">="]

    allowed_filters = {
        "module_code": (lambda _: sql.SQL("(raw.module_code ILIKE %s OR (raw.module_code IS NULL AND ai.module_code ILIKE %s))"), lambda x: [f"%{x}%", f"%{x}%"]),
        "title": (lambda _: sql.SQL("(modules.title ILIKE %s OR ai.title ILIKE %s)"), lambda x: [f"%{x}%", f"%{x}%"]),
        "ects": (lambda comparison_method: sql.SQL("(modules.ects {comparison_method} %s OR (modules.ects IS NULL AND ai.ects {comparison_method} %s))").format(comparison_method=sql.SQL(comparison_method)), lambda x: [x, x]),
        "lecturer": (lambda _: sql.SQL("(ai.lecturer ILIKE %s)"), lambda x: [f"%{x}%"]),
        "requirements": (lambda _: sql.SQL("(ai.requirements ILIKE %s)"), lambda x: [f"%{x}%"]),
        "success_requirements": (lambda _: sql.SQL("(ai.success_requirements ILIKE %s)"), lambda x: [f"%{x}%"]),
        "weekly_hours": (lambda comparison_method: sql.SQL("(ai.weekly_hours {comparison_method} %s)").format(comparison_method=sql.SQL(comparison_method)), lambda x: [x]),
        "recommended_semester": (lambda comparison_method: sql.SQL("ai.recommended_semester {comparison_method} %s").format(comparison_method=sql.SQL(comparison_method)), lambda x: [x]),
        "exams": (lambda _: sql.SQL("(ai.exams ILIKE %s)"), lambda x: [f"%{x}%"]),
        "version": (lambda _: sql.SQL("(mhbs.version = %s)"), lambda x: [int(x.split("/")[0][3:] + str(1 if x[0] == "W" else 0))]),
        "subject": (lambda _: sql.SQL("(raw.module_code ILIKE %s OR (raw.module_code IS NULL AND ai.module_code ILIKE %s))"), lambda x: [f"{x}-%", f"{x}-%"])
    }

    # get data from request
    filters = request.get_json()
    if any(k not in (allowed := tuple(allowed_filters.keys()) + tuple(allowed_filter_supplements.keys())) for k in filters.keys()):
        response = Response(
            response=json.dumps({"message": f"{', '.join(invalid := [k for k in filters.keys() if k not in allowed])} {('is' if len(invalid) == 1 else 'are')} not allowed as filter or filter supplement. Allowed filters and filter supplements are: {', '.join(allowed)}"}),
            status=400,
            mimetype="application/json",
        )
        return response

    if len([k for k, v in filters.items() if k in allowed_filters and v is not None and v.strip() != ""]) == 0:
        response = Response(
            response=json.dumps({"message": "No search parameters provided"}),
            status=400,
            mimetype="application/json",
        )
        return response
    
    if any(k in allowed_filter_supplements and v is not None and v not in allowed_comparison_methods for k, v in filters.items()):
        response = Response(
            response=json.dumps({"message": f"Invalid comparison method for filter supplement. Allowed comparison methods are: {', '.join(allowed_comparison_methods)}"}),
            status=400,
            mimetype="application/json",
        )
        return response
    
    filters = {k: v for k, v in filters.items() if v is not None and v.strip() != ""}

    filter_strings = []
    filter_values = []
    for k, v in filters.items():
        if k in allowed_filters:
            filter_strings.append(allowed_filters[k][0](filters[allowed_filter_supplements.inverse[k]] if k in allowed_filter_supplements.values() else None))
            filter_values.extend(allowed_filters[k][1](v))

    query = sql.SQL("""
        SELECT 
            ai.raw_module_id AS ai_raw_module_id,
            ai.title AS ai_title,
            ai.module_code AS ai_module_code,
            ai.ects AS ai_ects,
            ai.lecturer AS ai_lecturer,
            ai.contents AS ai_contents,
            ai.goals AS ai_goals,
            ai.requirements AS ai_requirements,
            ai.expense AS ai_expense,
            ai.success_requirements AS ai_success_requirements,
            ai.weekly_hours AS ai_weekly_hours,
            ai.recommended_semester AS ai_recommended_semester,
            ai.exams AS ai_exams,
            ai.module_parts AS ai_module_parts,

            modules.id AS module_id, 
            modules.title AS module_title, 
            modules.module_code AS module_code, 
            modules.ects AS module_ects, 
            modules.content AS module_content, 
            modules.goals AS module_goals, 
            modules.pages AS module_pages, 
            modules.mhb_id AS module_mhb_id, 

            raw.content AS raw_content,
                    
            mhbs.version AS version,

            CASE 
                WHEN ai.module_code IS NULL THEN 0.5
                WHEN ai.module_code = modules.module_code THEN 1
                ELSE 0
            END AS correct_module_code,
            CASE 
                WHEN ai.ects IS NULL THEN 0.5
                WHEN ai.ects = modules.ects THEN 1
                ELSE 0
            END AS correct_ects,
            CASE 
                WHEN ai.title IS NULL THEN 0.5
                WHEN ai.title = modules.title THEN 1
                ELSE 0
            END AS correct_title

        FROM unia.modules_ai_extracted AS ai
        JOIN unia.modules_raw AS raw ON ai.raw_module_id = raw.id
        JOIN unia.modules ON raw.mhb_id = modules.mhb_id AND raw.module_code = modules.module_code
        JOIN unia.mhbs ON modules.mhb_id = mhbs.id
        WHERE {filter_contents}
        ;
        """).format(filter_contents=sql.SQL(" AND ").join(filter_strings))

    result = db.custom_call(
        query=query,
        variables=filter_values,
        type_of_answer=db.ANSWER_TYPE.LIST_ANSWER,
    )

    if result.is_error:
        return Response(
            response=json.dumps({"message": "Error occurred in the backend"}),
            status=500,
            content_type="application/json",
        )

    modules = []
    for mod in result.data:
        columns = [
            "raw_module_id",
            "ai_title",
            "ai_module_code",
            "ai_ects",
            "ai_lecturer",
            "ai_contents",
            "ai_goals",
            "ai_requirements",
            "ai_expense",
            "ai_success_requirements",
            "ai_weekly_hours",
            "ai_recommended_semester",
            "ai_exams",
            "ai_module_parts",

            "module_id",
            "module_title",
            "module_code",
            "module_ects",
            "module_content",
            "module_goals",
            "module_pages",
            "module_mhb_id",

            "raw_content",

            "version",

            "correct_module_code",
            "correct_ects",
            "correct_title"
        ]

        raw_module = {key: value for key, value in zip(columns, mod)}

        # could be handled in sql (maybe is)
        if raw_module["module_code"] is None and raw_module["ai_module_code"] is None:
            continue

        module = {
            "module_code": raw_module["ai_module_code"] if raw_module["module_code"] is None else raw_module["module_code"],
            "title": raw_module["ai_title"] if raw_module["module_title"] is None else raw_module["module_title"],
            "ects": raw_module["ai_ects"] if raw_module["module_ects"] is None else raw_module["module_ects"],
            "lecturer": raw_module["ai_lecturer"],
            "contents": raw_module["ai_contents"],
            "goals": raw_module["ai_goals"],
            "requirements": raw_module["ai_requirements"],
            "expense": raw_module["ai_expense"],
            "success_requirements": raw_module["ai_success_requirements"],
            "weekly_hours": raw_module["ai_weekly_hours"],
            "recommended_semester": raw_module["ai_recommended_semester"],
            "exams": raw_module["ai_exams"],
            "module_parts": raw_module["ai_module_parts"],
            "version": ("Winter" if (winter := int((version := str(raw_module["version"]))[-1]) == 1) else "Sommer") + "semester " + (year := version[:-1]) + (("/" + str(int(year) + 1)) if winter else ""),
            "correct_module_code": float(raw_module["correct_module_code"]),
            "correct_ects": float(raw_module["correct_ects"]),
            "correct_title": float(raw_module["correct_title"]),
            "correctness_score": float((raw_module["correct_module_code"] + raw_module["correct_ects"] + raw_module["correct_title"]) / 3)
        }

        modules.append(module)

    modules = replace_none_with_dash(modules)

    return Response(
        response=json.dumps(modules), status=200, mimetype="application/json"
    )