import enum
import json
from enum import Enum
from typing import Annotated, Any, Literal, TypedDict, cast, overload

from psycopg2.extensions import cursor
from typeguard import typechecked

from api.data_types import Email, UserRole
from database import database as db
from api.general_functions import clean_single_data
from datatypes.response import Response as FuncRes, Status, Message


class Identifier(Enum):
    """
    Identifier fields in the database for table users
    """

    ID = "id"
    USERNAME = "user_name"
    UUID = "user_uuid"
    EMAIL = "email"


class UserIdentifier:
    """
    Class for identifying user in database for table users

    Attributes:
        identifier (Identifier): specifies, which unique column should be used as identifier
        value (str | int | Email): specifies, what the value in that column should be
    """

    def __init__(self, identifier: Identifier, value: str | int | Email):
        """
        Init function for UserIndentifier

        Args:
            identifier (Identifier): specifies, which unique column should be used as identifier
            value (str | int | Email): specifies, what the value in that column should be
        """
        if identifier == Identifier.ID:
            if not isinstance(value, int):
                raise ValueError("identification value for ID must be of type int")
        if identifier == Identifier.EMAIL:
            if not isinstance(value, Email):
                raise ValueError("identification value for EMAIL must be of type Email")
        else:
            if not isinstance(value, str):
                raise ValueError(
                    f"identification value for {Identifier.name} must be of type str"
                )
        self.identifier = identifier
        self.value = value

    def get_data(self) -> dict[str, str | int]:
        """
        returns identifier and value

        Returns:
            dict[str, str | int | Email]: dictionary with identifier value as key and value as value
        """
        return {
            self.identifier.value: self.value
            if self.identifier != Identifier.EMAIL
            else self.value.email  # type: ignore
        }


def add_user(
    cursor: cursor,
    user_role: UserRole,
    first_name: str,
    last_name: str,
    email: Email,
    organization: str,
    password_hash: str,
    user_name: str,
    returning_column: str | None = None,
) -> FuncRes:
    """
    adds a user to the table users

    Args:
        cursor: cursor for the connection
        user_role (UserRole): available roles for the user
        first_name (str): first name of the user
        last_name (str): last name of the user
        email (Email): email of the user
        organization (str): organization
        password_hash (str): password hash of the user
        user_name (str): username of the user
        returning (str | None): which column to return
    Returns:
        dict: FuncRes object
    """

    # values, that need to be set
    values_set = any(
        i is None
        for i in [
            organization,
            email,
            password_hash,
            user_name,
            first_name,
            last_name,
        ]
    )

    # if needed value isn't set, return error
    if values_set is True:
        return FuncRes(
            error_data="Email, password hash, user_name, organization, first name, last name must be set.",
            message=Message(
                name="Insufficient parameters",
                type="error",
                info="Missing parameters",
                category="Caller error",
                details={"information": "Missing parameters"},
                code=400,
            ),
            status=Status.FULL_ERROR,
        )

    # values to insert into the db
    values = {
        "user_role": user_role.value,
        "first_name": first_name,
        "last_name": last_name,
        "password_has": password_hash,
        "organization": organization,
        "user_name": user_name,
        "email": email,
    }

    result = db.insert(
        cursor=cursor,
        table="users",
        values=values,
        returning_column=returning_column,
    )

    # check for error
    if result.is_error is True:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Insert of user failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    # if no return values were specified, return success
    if returning_column is None:
        return FuncRes(
            message=Message(
                name="success",
                type="success",
                category="data layer success",
                info="Successfully inserted user into database",
                code=200,
            ),
            status=Status.FULL_SUCCESS,
        )

    # if only a single return value was specified, turn list answer to single answer
    if ", " not in returning_column:
        result = clean_single_data(result)

    # if no data was returned despite specifying so, return error
    if result.data is None or result.data == []:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Insert of user failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    # return success
    return FuncRes(
        message=Message(
            name="success",
            type="success",
            category="data layer success",
            info="Successfully inserted user into database",
            code=200,
        ),
        status=Status.FULL_SUCCESS,
    )


def remove_user(cursor: cursor, user_identifier: UserIdentifier) -> FuncRes:
    """
    removes a user from the table users \n
    actually not the whole user but just their password will be set to NULL

    Args:
        cursor: cursor for the connection
        user_identifier (UserIdentifier): identifier with value for identification of user
    Returns:
        FuncRes: return FuncRes object
    """

    # set conditions for removal of user
    conditions: dict[str, str | int] = user_identifier.get_data()
    # delete password_hash from database
    result = db.update(
        cursor=cursor,
        table="users",
        arguments={"password_hash": None},
        conditions=conditions,
        returning_column="id, user_role",
    )

    if result.is_error is True:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Removal of user failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )
    if result.data is None:
        return FuncRes(
            error_data="User does not exist",
            message=Message(
                name="Caller error",
                type="error",
                category="caller error",
                info="Removal of user failed",
                details={"error": "User does not exist"},
                code=400,
            ),
            status=Status.FULL_ERROR,
        )

    return FuncRes(
        message=Message(
            name="success",
            type="success",
            category="data layer success",
            info="Successfully deleted user from database",
            code=200,
        ),
        status=Status.FULL_SUCCESS,
    )


def update_user(
    cursor: cursor,
    user_identifier: UserIdentifier,
    **kwargs,
) -> FuncRes:
    """
    updates a user in the table users

    Args:
        cursor: cursor for the connection
        user_identifier (UserIdentifier): identifier for user in database in table users
        **kwargs: fields to update
    Returns:
        FuncRes: FuncRes object
    """

    # TODO: disallow unallowed fields in db

    # allowed fields for database insert
    allowed_fields = [
        "user_role",
        "first_name",
        "last_name",
        "email",
        "password_hash",
        "user_name",
        "verified",
    ]

    # check for forbidden parameters
    for k in kwargs.keys():
        if k not in allowed_fields:
            return FuncRes(
                error_data=f"Field {k} is not allowed to be changed or does not exist.",
                message=Message(
                    name="Wrong parameters",
                    type="error",
                    category="Caller error",
                    details={"information": "Forbidden parameters"},
                    code=400,
                ),
                status=Status.FULL_ERROR,
            )

    # set conditions to specify user
    conditions = user_identifier.get_data()

    # update user in db
    result = db.update(
        cursor=cursor,
        table="users",
        arguments=kwargs,
        conditions=conditions,
        returning_column="id",
    )

    # check for error
    if result.is_error is True:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Update of user failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    # if no id was returned, return user doesn't exist
    if result.data is None:
        return FuncRes(
            error_data="User does not exist",
            message=Message(
                name="Caller error",
                type="error",
                category="caller error",
                info="Update of user failed",
                details={"error": "User does not exist"},
                code=400,
            ),
            status=Status.FULL_ERROR,
        )

    # clean the result data
    result = clean_single_data(result)
    return FuncRes(
        success_data=result.data,
        message=Message(
            name="success",
            type="success",
            category="data layer success",
            info="Successfully updated user from database",
            code=200,
            details={"user_id": result},
        ),
        status=Status.FULL_SUCCESS,
    )


def get_user(
    cursor: cursor,
    user_identifier: Annotated[
        UserIdentifier | None,
        "Explicit with select_max_of_key, conditions, specific_where",
    ],
    expect_single_answer: bool = True,
    keywords: tuple[str] | list[str] = ("*",),
    conditions: Annotated[
        dict[str, Any] | None,
        "Explicit with user_identifier, select_max_of_key, specific_where",
    ] = None,
    select_max_of_key: Annotated[
        str, "Explicit with user_identifier, conditions, specific_where"
    ] = "",
    specific_where: Annotated[
        str, "Explicit with user_identifier, select_max_of_key, conditions"
    ] = "",
    order_by: Annotated[
        tuple[str, Literal[0, 1]] | None,
        "Explicit with expect_single_answer",
    ] = None,
) -> FuncRes:
    """
    retrieves a user from the table users

    Args:
        cursor: cursor for the connection
        user_identifier (UserIdentifier | None): used to identify user in table users
        keywords (tuple[str] | list[str]): list of fields to be retrieved, defaults to ["*"]
        conditions (dict | None): additional conditions for the query
        expect_single_answer (bool): whether to expect a single user or multiple users
        select_max_of_key (str): if set, will select the max of this key
        specific_where (str): if set, will add this specific where clause
        order_by (tuple): if set, will order the results by this tuple
    Returns:
        dict: {"success": False, "error": e} if unsuccessful, {"success": bool, "data": user} otherwise
    """
    keywords = list(keywords)
    if conditions is None:
        conditions = {}
    # check, whether explicitly of expect_single_answer and order_by is met
    if expect_single_answer and order_by is not None:
        return FuncRes(
            error_data="Either expect_single_answer=True or order_by can be set.",
            message=Message(
                name="Caller error",
                type="error",
                category="caller error",
                info="Explicit parameters set together",
                details={
                    "information": "Two parameters, that are explicit to each other were set together"
                },
                code=400,
            ),
        )

    # check, whether a where statement is set for sql query
    if user_identifier is None and not conditions and specific_where == "":
        return FuncRes(
            error_data="Either user_id, user_email, user_name, user_uuid, conditions or specific_where must be set.",
            message=Message(
                name="Insufficient parameters",
                type="error",
                category="Caller error",
                details={"information": "Missing values"},
                code=400,
            ),
            status=Status.FULL_ERROR,
        )

    # check, whether too many explicit arguments were set
    conditions_counter = 0
    if user_identifier is not None:
        conditions_counter += 1
    if select_max_of_key != "":
        conditions_counter += 1
    if specific_where != "":
        conditions_counter += 1
    if conditions:
        conditions_counter += 1
    if conditions_counter > 1:
        return FuncRes(
            error_data="user_id, user_email, user_uuid, user_name, select_max_of_key, specific_where and conditions are explicit. Therefore just one of them can be set.",
            message=Message(
                name="Insufficient parameters",
                type="error",
                category="Caller error",
                details={"information": "Missing values"},
                code=400,
            ),
            status=Status.FULL_ERROR,
        )

    if user_identifier is not None:
        conditions = user_identifier.get_data()
    value = dict()
    if order_by is not None:
        value["order_by"] = order_by

    result = db.select(
        cursor=cursor,
        table="users",
        keywords=keywords,
        type_of_answer=db.ANSWER_TYPE.SINGLE_ANSWER
        if expect_single_answer
        else db.ANSWER_TYPE.LIST_ANSWER,
        conditions=conditions,
        select_max_of_key=select_max_of_key,
        specific_where=specific_where,
        **value,
    )

    if result.is_error is True:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Update of user failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    # if no id was returned, return user doesn't exist
    if result.data is None or (isinstance(result.data, list) and len(result.data) == 0):
        return FuncRes(
            error_data="No matching user found",
            message=Message(
                name="Caller error",
                type="error",
                category="caller error",
                info="Update of user failed",
                details={"error": "User does not exist"},
                code=400,
            ),
            status=Status.FULL_ERROR,
        )

    # clean the result data
    return FuncRes(
        success_data=result.data,
        message=Message(
            name="success",
            type="success",
            category="data layer success",
            info="Successfully searched for user from database",
            code=200,
            details={"user_id": result},
        ),
        status=Status.FULL_SUCCESS,
    )


def create_verification_code(
    cursor: cursor, user_id: int | None, additional_data: dict[str, Any] | None = None
) -> FuncRes:
    """
    creates a password reset code for a specific user

    Args:
        cursor: cursor for the connection
        user_id (int | None): id of the user
        additional_data (dict | None): additional data to be stored in the table; can be None
    Returns:
        FuncRes: FuncRes object
    """

    values: dict[str, Any] | None = dict()
    values["user_id"] = user_id
    if additional_data is not None:
        additional_data = {
            k: v.value
            if isinstance(v, enum.Enum)
            else v.email
            if isinstance(v, Email)
            else v
            for k, v in additional_data.items()
        }
        values["additional_data"] = json.dumps(additional_data)

    result = db.insert(
        cursor=cursor,
        table="verification_codes",
        values=values,
        returning_column="reset_code",
    )

    if result.is_error is True:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Creating verification code failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )
    # maybe shouldn't be possible, but still left in
    if result.is_success and result.data is None:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Creating verification code failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    result = clean_single_data(result.data)
    return FuncRes(
        success_data=result.data,
        message=Message(
            name="success",
            type="success",
            category="data layer success",
            info="Successfully searched for user from database",
            code=200,
            details={"verification_code": result},
        ),
        status=Status.FULL_SUCCESS,
    )


def confirm_verification_code(
    cursor: cursor,
    reset_code: str,
    additional_data: bool = False,
    expiration_minutes: int | None = None,
) -> FuncRes:
    """
    confirms a password reset code for a specific user

    Args:
        cursor: cursor for the connection
        reset_code (str): reset code of the user
        additional_data (bool): whether to return additional data
        expiration_minutes (int | None): if set, the code is only valid for this many minutes
    Returns:
        FuncRes: FuncRes object
    """

    keywords = ["user_id"]
    if additional_data:
        keywords.append("additional_data")

    arguments = {}
    if expiration_minutes is not None:
        arguments["specific_where"] = (
            "reset_code = %s AND used = FALSE AND created_at >= NOW() - (%s * INTERVAL '1 minute')"
        )
        arguments["variables"] = (
            reset_code,
            expiration_minutes,
        )
    else:
        arguments["specific_where"] = (
            "reset_code = %s AND created_at >= NOW() - ((SELECT value::int FROM configurations WHERE key = 'reset_code_expiration_minutes') * INTERVAL '1 minute') AND used = FALSE"
        )
        arguments["variables"] = (reset_code,)
    result = db.select(
        cursor=cursor,
        table="verification_codes",
        keywords=keywords,
        type_of_answer=db.ANSWER_TYPE.SINGLE_ANSWER,
        **arguments,
    )

    if result.is_error is True:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Verification of code failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    if result.data is None:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Caller error",
                type="error",
                category="caller error",
                info="Reset code doesn't exist or expired",
                details={"error": "Reset code is in valid or expired"},
                code=400,
            ),
            status=Status.FULL_ERROR,
        )

    result_insert = db.update(
        cursor=cursor,
        table="verification_codes",
        arguments={"used": True},
        conditions={"reset_code": reset_code},
    )
    if result_insert.is_error:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Updating verification code failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )

    return FuncRes(
        success_data=result.data,
        message=Message(
            name="success",
            type="success",
            category="data layer success",
            info="Successfully checked and udated verification code",
            code=200,
            details={"verification_code": result},
        ),
        status=Status.FULL_SUCCESS,
    )


def get_users(
    cursor: cursor, user_uuids: list[str], keywords: list[str] | tuple[str] = ("id",)
) -> FuncRes:
    """
    retrieves users from the table users

    Args:
        cursor: cursor for the connection
        user_uuids (list[str | int]): list of user uuids
        keywords (tuple[str] | list[str]): list of fields to be retrieved, defaults to ["*"]
    Returns:
        FuncRes: FuncRes object
    """
    keywords = list(keywords)
    # users_list = [(i, "email") if isinstance(i, str) and "@" in i else (i, "user_name") for i in information]

    query = f"SELECT {', '.join(keywords)} FROM users WHERE user_uuid IN ({', '.join(['%s' for _ in range(len(user_uuids))])})"
    result = db.custom_call(
        cursor=cursor,
        query=query,
        type_of_answer=db.ANSWER_TYPE.LIST_ANSWER,
        variables=tuple(user_uuids),
    )

    if result.is_error is True:
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Database error",
                type="error",
                category="data layer error",
                info="Fetching users from db failed",
                details={"error": result.error},
                code=500,
            ),
            status=Status.FULL_ERROR,
        )
    if len(result.data) != len(user_uuids):
        return FuncRes(
            error_data=result.error,
            message=Message(
                name="Caller error",
                type="error",
                category="caller error",
                info="Not all users found",
                details={"error": "Not all users found"},
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
            info="Successfully fetched information to all requested users",
            code=200,
            details={"verification_code": result},
        ),
        status=Status.FULL_SUCCESS,
    )
