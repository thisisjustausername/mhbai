from datetime import datetime, timedelta

from psycopg2.extensions import cursor
import pytz

from database import database as db
from api.general_functions import clean_single_data
from datatypes.response import Response as FuncRes, Message, Status
from api.data_types import UserRole


def create_session(cursor: cursor, user_id: int) -> FuncRes:
    """
    creates a session for a user in the table sessions

    Args:
        cursor: cursor for the connection
        user_id (int): id of the user
    Returns:
        FuncRes: FuncRes object containing the expiration time of the session
    """

    # load the configuration variable for session expiration time in days from table configurations
    expiration_time = db.select(
        cursor=cursor,
        keywords=["value"],
        table="configurations",
        conditions={"key": "session_expiration_days"},
        type_of_answer=db.ANSWER_TYPE.SINGLE_ANSWER,
    )
    if expiration_time.is_error:
        return FuncRes(
            error_data=expiration_time.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Creation of session failed",
                details={"error": expiration_time.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )
    elif expiration_time.data is None:
        return FuncRes(
            error_data="Invalid result data",
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Creation of session failed",
                details={"error": "Invalid result data"},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    expiration_time = int(expiration_time.data[0])

    # calculate expiration date
    tz = pytz.timezone("Europe/Berlin")
    now = datetime.now(tz)
    expiration_date = now + timedelta(days=expiration_time)
    expiration_date = expiration_date.replace(
        hour=5, minute=30, second=0, microsecond=0
    )  # set expiration time to 5:30am

    # set the expiration_date
    result = db.insert(
        cursor=cursor,
        table="sessions",
        values={"user_id": user_id, "expiration_date": expiration_date},
        returning_column="session_id",
    )

    if result.is_error:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Creation of session failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )
    if result.data is None:
        return FuncRes(
            error_data="Invalid result data",
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Creation of session failed",
                details={"error": "Invalid result data"},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )
    else:
        return FuncRes(
            success_data=list(result.data) + [expiration_date],
            message=Message(
                name="success",
                type="success",
                category="data layer success",
                info="Successfully created a session",
                code=200,
            ),
            status=Status.FULL_SUCCESS,
        )


def get_session(cursor: cursor, session_id: str) -> FuncRes:
    """
    gets the session of a user from the table sessions
    Args:
        cursor: cursor for the connection
        session_id (str): id of the session
    Returns:
        FuncRes: FuncRes object containing the session_id and expiration_date
    """

    result = db.select(
        cursor=cursor,
        keywords=["session_id", "expiration_date"],
        table="sessions",
        type_of_answer=db.ANSWER_TYPE.SINGLE_ANSWER,
        specific_where="session_id = %s AND expiration_date > NOW()",
        variables=[session_id],
    )
    if result.is_error:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Creation of session failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )
    if result.data is None:
        return FuncRes(
            error_data="No session found",
            message=Message(
                name="Caller error",
                type="error",
                category="caller error",
                info="No session found",
                details={"error": "No session found, the session might have expired"},
                code=400,
            ),
            status=Status.FULL_ERROR,
        )
    return FuncRes(
        success_data=result.data,
        message=Message(
            name="success",
            type="success",
            category="data layer success",
            info="Successfully fetched session",
            code=200,
        ),
        status=Status.FULL_SUCCESS,
    )


def remove_session(cursor: cursor, session_id: str) -> FuncRes:
    """
    removes a session from the table sessions
    Args:
        cursor: cursor for the connection
        session_id (str): id of the user
    Returns:
        FuncRes: FuncRes object containing the session_id
    """

    result = db.delete(
        cursor=cursor,
        table="sessions",
        conditions={"session_id": session_id},
        returning_column="session_id",
    )
    if result.is_error:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Creation of session failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )
    if result.data is None:
        return FuncRes(
            error_data="No session found",
            message=Message(
                name="Caller error",
                type="error",
                category="caller error",
                info="No session found",
                details={"error": "No session found, the session might have expired"},
                code=400,
            ),
            status=Status.FULL_ERROR,
        )
    return FuncRes(
        success_data=result.data,
        message=Message(
            name="success",
            type="success",
            category="data layer success",
            info="Successfully deleted session",
            code=200,
        ),
        status=Status.FULL_SUCCESS,
    )


def get_user(
    cursor: cursor, session_id: str, keywords: tuple[str] | list[str] | None = None
) -> FuncRes:
    """
    gets the user role of a user from the table users via the sessions table
    Args:
        cursor: cursor for the connection
        session_id (str): id of the user
        keywords (tuple[str] | list[str]): list of keywords to be returned
    Returns:
        FuncRes: FuncRes object returning user data
    """

    allowed_keywords = [
        "id",
        "user_role",
        "user_uuid",
        "room",
        "residence",
        "first_name",
        "last_name",
        "email",
        "user_name",
    ]

    if keywords is None:
        keywords = ["id", "user_role", "user_uuid", "first_name", "last_name"]
    else:
        keywords = list(keywords)
        if not all(map(lambda k: k in allowed_keywords, keywords)):
            return FuncRes(
                error_data="Invalid keywords specified",
                message=Message(
                    name="Caller error",
                    type="error",
                    category="caller error",
                    info="No session found",
                    details={"error": "Invalid keywords specified"},
                    code=400,
                ),
                status=Status.FULL_ERROR,
            )

    result = db.select(
        cursor=cursor,
        keywords=["u." + i for i in keywords],
        table="sessions s JOIN users u ON s.user_id = u.id",
        type_of_answer=db.ANSWER_TYPE.SINGLE_ANSWER,
        conditions={"s.session_id": session_id},
    )

    if result.is_error:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Creation of session failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )
    if result.data is None:
        return FuncRes(
            error_data="No matching session and user found",
            message=Message(
                name="Caller error",
                type="error",
                category="caller error",
                info="No matching session and user found",
                details={"error": "No matching session and user found"},
                code=400,
            ),
            status=Status.FULL_ERROR,
        )
    elif len(keywords) == 1:
        return FuncRes(
            success_data=clean_single_data(result.data),
            message=Message(
                name="success",
                type="success",
                category="data layer success",
                info="Successfully fetched user",
                code=200,
            ),
            status=Status.FULL_SUCCESS,
        )

    return FuncRes(
        success_data=clean_single_data(result.data),
        message=Message(
            name="success",
            type="success",
            category="data layer success",
            info="Successfully fetched user",
            code=200,
        ),
        status=Status.FULL_SUCCESS,
    )


def remove_user_sessions(cursor: cursor, user_id: int) -> FuncRes:
    """
    removes all sessions of a user from the table sessions
    Args:
        cursor: cursor for the connection
        user_id (int): id of the user
    Returns:
        FuncRes: FuncRes object containing removed session ids
    """

    result = db.delete(
        cursor=cursor,
        table="sessions",
        conditions={"user_id": user_id},
        returning_column="session_id",
    )

    if result.is_error:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Removal of sessions failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    if result.data is None:
        return FuncRes(
            success_data=None,
            message=Message(
                name="success",
                type="success",
                category="data layer success",
                info="Successfully deleted all user sessions",
                details={"info": "No sessions found for user"},
                code=200,
            ),
            status=Status.PARTIAL_SUCCESS,
        )

    return FuncRes(
        success_data=result.data,
        message=Message(
            name="success",
            type="success",
            category="data layer success",
            info="Successfully deleted all sessions",
            code=200,
        ),
        status=Status.FULL_SUCCESS,
    )


def check_session_id(cursor: cursor, session_id: int) -> FuncRes:
    """
    checks, whether a session_id is valid

    Args:
        cursor: cursor for the db connection
        session_id: id of the session
    """

    result = db.select(
        cursor=cursor,
        table="sessions",
        conditions={"id": session_id},
        type_of_answer=db.ANSWER_TYPE.SINGLE_ANSWER,
    )
    if result.is_error:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Check of session failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    if result.data is None:
        return FuncRes(
            success_data=False,
            message=Message(
                name="success",
                type="success",
                category="data layer success",
                info="Successfully deleted all sessions",
                code=200,
            ),
            status=Status.FULL_SUCCESS,
        )

    return FuncRes(
        success_data=True,
        message=Message(
            name="success",
            type="success",
            category="data layer success",
            info="Successfully deleted all sessions",
            code=200,
        ),
        status=Status.FULL_SUCCESS,
    )


def get_session_ids(cursor: cursor, user_id: int, uuid: bool = False) -> FuncRes:
    """
    gets all session ids of a user from the table sessions
    Args:
        cursor: cursor for the connection
        user_id (int): id of the user
        uuid (bool): whether to return the session_id (uuid) or the internal id
    Returns:
        FuncRes: FuncRes object containing session ids
    """

    result = db.select(
        cursor=cursor,
        keywords=["id"] if uuid is False else ["session_id"],
        table="sessions",
        conditions={"user_id": user_id},
        type_of_answer=db.ANSWER_TYPE.LIST_ANSWER,
    )

    if result.is_error:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Fetching of user sessions failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )
    if result.data is None:
        return FuncRes(
            success_data=[],
            message=Message(
                name="success",
                type="success",
                category="data layer success",
                info="Successfully fetched all user sessions",
                details={"info": "No sessions found for user"},
                code=200,
            ),
            status=Status.PARTIAL_SUCCESS,
        )

    return FuncRes(
        success_data=[row[0] for row in result.data],
        message=Message(
            name="success",
            type="success",
            category="data layer success",
            info="Successfully fetched all user sessions",
            details={"info": "No sessions found for user"},
            code=200,
        ),
        status=Status.FULL_SUCCESS,
    )


def check_permissions(
    cursor, session_id: str | None, required_role: UserRole
) -> FuncRes:
    """
    checks whether the user with the given session_id has the required role
    Args:
        cursor: cursor for the connection
        session_id (str): session id of the user
        required_role (UserRole): required role of the user
    Returns:
        FuncRes: result of the permission check
    """

    if session_id is None:
        return FuncRes(
            error_data="The session id must be specified",
            message=Message(
                name="MissingSessionID",
                type="error",
                category="MissingSessionID",
                info="The session id must be specified",
                code=400,
            ),
            status=Status.FULL_ERROR,
        )

    # get the user_id, user_role by session_id
    result = get_user(cursor=cursor, session_id=session_id)

    # if error occurred, return error
    if result.is_error:
        return result

    user_id = result.data[0]
    user_role = UserRole(result.data[1])
    user_uuid = result.data[2]
    first_name = result.data[3]
    last_name = result.data[4]
    if user_role >= required_role:
        return FuncRes(
            success_data={
                "allowed": True,
                "user_id": user_id,
                "user_role": user_role,
                "user_uuid": user_uuid,
                "first_name": first_name,
                "last_name": last_name,
            },
            message=Message(
                name="user allowed",
                type="success",
                category="PermissionCheck",
                info="User has the required permissions",
                code=200,
            ),
            status=Status.FULL_SUCCESS,
        )

    return FuncRes(
        success_data={
            "allowed": False,
            "user_id": user_id,
            "user_role": user_role,
            "user_uuid": user_uuid,
            "first_name": first_name,
            "last_name": last_name,
        },
        message=Message(
            name="user forbidden",
            type="success",
            category="PermissionCheck",
            info="User is missing required permissions",
            code=200,
        ),
        status=Status.FULL_SUCCESS,
    )
