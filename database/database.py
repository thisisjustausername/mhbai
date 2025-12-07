# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# For usage please contact the developer.
#
# This file is Copyright-protected.

# Description: connect to postgresql database and perform basic operations
# Status: TESTING
# FileID: Sc-da-0003

from collections.abc import Callable
from enum import Enum
from functools import wraps
import inspect
import os
import traceback
import types
from typing import Any
import warnings
from dotenv import load_dotenv
import psycopg2 as pg
from psycopg2.extensions import cursor

from datatypes.result import Result


load_dotenv()

USER = os.getenv("USERDB") # (like the linux user name!)
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST") # localhost
PORT = os.getenv("PORT") # 5432
DBNAME = os.getenv("DBNAME") # mhbs

class ANSWER_TYPE(str, Enum):
    NO_ANSWER = "NO_ANSWER"
    SINGLE_ANSWER = "SINGLE_ANSWER"
    LIST_ANSWER = "LIST_ANSWER"

def is_valid_answer_type(value):
    return value in ANSWER_TYPE._value2member_map_

class ORDER(str, Enum):
    ASC = "ASC"
    DESC = "DESC"

def is_valid_order(value):
    return value in ORDER._value2member_map_

def full_pack(func: Callable[..., Any]):
    """
    full_pack \n
    wrapper function to make just one function call for initializing, closing and the actual function

    Parameters:
        func (func): function
    Returns:
        function: wrapped function
    """
    def wrapped(*args, **kwargs):
        _, cursor = connect()
        result = func(cursor, *args, **kwargs)
        close(cursor=cursor) # type: ignore
        return result
    return wrapped

def cursor_handling(*, manually_supply_cursor: bool = False) -> Callable[..., Any]:
    """
    decorator to handle cursor opening and closing
    specify whether the cursor is supplied manually

    Parameters:
        manually_supply_cursor (bool): whether the cursor is supplied manually, default False
    Returns:
        function: decorated function
    """

    def decorator(func: Callable[..., Any]):
        """
        wrapper function to make sure cursor is closed after function call
        

        Parameters:
            func (func): function
        Returns:
            function: wrapped function
        """

        @wraps(func)
        def wrapped(*args, **kwargs) -> Any:
            """
            Wrapped function

            Parameters:
                args: arguments for the function
                kwargs: keyword arguments for the function
            Returns:
                any: return value of the function
            """

            # initialize cursor handling
            close_cursor = manually_supply_cursor

            # bind all arguments and keywords to check for cursor
            bound = inspect.signature(func).bind_partial(*args, **kwargs)
            bound.apply_defaults()
            
            # check whether cursor is a valid keyword argument
            try:
                _ = bound.arguments['cursor']
            except KeyError:
                raise ValueError(f"cursor must be a valid keyword argument of the function {func.__name__}")
            
            # set cursor based on whether it is supplied manually or not
            
            # if cursor is not supplied manually and is None, create a new one
            if (cursor := bound.arguments.get('cursor', None)) is None and manually_supply_cursor is False:                
                # connect to db
                cursor = connect()

            # if cursor is supplied manually but manually_supply_cursor is False, raise error
            elif cursor is None and manually_supply_cursor is True:
                raise ValueError(f"cursor must be supplied manually for function {func.__name__} but is None")
            
            # if cursor is supplied manually and manually_supply_cursor is True, respond with user warning and create a new cursor
            elif cursor is not None and manually_supply_cursor is False:
                warnings.warn(f"cursor is supplied manually for function {func.__name__} but manually_supply_cursor is set to False; the manually set cursor will be IGNORED", UserWarning)
                
                # set close_cursor to True since the cursor is only used locally
                close_cursor = True

                # connect to db
                cursor = connect()

            # if manually_supply_cursor is not of type bool, raise error
            elif isinstance(manually_supply_cursor, bool) is False:
                raise ValueError("manually_supply_cursor must be of type bool")

            try:
                # run function
                kwargs["cursor"] = cursor
                return func(*args, **kwargs)
            
            finally:
                # if cursor was created in this function, close it
                if close_cursor is True:
                    # close the cursor after the function call
                    close(cursor=cursor) # type: ignore
        return wrapped
    return decorator

# TODO right now for development and testing enabled, for website rather use failsafes (SAME AS IN often_used_db_calls.py)
def catch_exception(func):
    """
    catches errors
    connect, pool, update, remove functions DON'T use this wrapper

    Parameters:
        func (func): function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return Result(data=func(*args, **kwargs))
        except Exception as e:
            return Result(error=e, stack_trace=traceback.format_exc())
    return wrapper

def connect(**kwargs):
    """
    connect \n
    kwargs format: user, password, host, port, database \n
    kwargs format if lazy: database (takes longer, so if called often use first option)

    Parameters:
        kwargs (dict):
    Returns:
        cursor: cursor to interact with db
    """
    if len(kwargs) > 0:
        return pg.connect(**kwargs).cursor()
    return pg.connect(user=USER, password=PASSWORD, host=HOST,
                                 port=PORT, database=DBNAME).cursor()

# TODO can't return success: False right now
# TODO for arguments as list might not be completely implemented
# TODO: specific_where and variables don't work together
# @catch_exception
def select(
        cursor: cursor, 
        table: str, 
        answer_type: ANSWER_TYPE = ANSWER_TYPE.LIST_ANSWER, 
        keywords: tuple[str] | list[str] = ("*",), 
        conditions: dict[str, Any] | None = None, 
        negated_conditions: dict[str, Any] | None = None, 
        select_max_of_key: str = "", 
        specific_where: str = "", 
        variables: list[str] | None = None,
        order_by: tuple[str, ORDER] | None = None) -> Result[Any, Exception]:
    """
    read_table \n
    read data from a table
    
    Parameters:
        cursor (from): cursor for db
        table (str): table to select from
        keywords (tuple[str] | list[str]): columns, that should be selected, if empty, get all
        conditions (dict): under which conditions (key: column, value: value) values should be selected, if empty, no conditions
        negated_conditions (dict): under which conditions (key: column, value: value) values should NOT be selected, if empty, no negated conditions
        answer_type (ANSWER_TYPE): specify whether one or more answers are to be received, therefore it changes, whether list or single object will be returned
        select_max_of_key (bool): conditions must be empty, otherwise it won't be used
        specific_where (str): select_max_of_key must be empty as well as conditions must be empty, else specific_where is ignored, allows to pass in a unique where statement (WHERE is already in the string),
        variables (list | None): list of variables that should be passed into the specific_where statement
        order_by (str, ORDER) | None: ORDER by default no ordering
    Returns:
        Result: result object with data or error
    """

    # check, whether answer_type is valid
    if not is_valid_answer_type(answer_type) or answer_type == ANSWER_TYPE.NO_ANSWER:
        raise ValueError("parameter answer_type of the function must be of enum type LIST_ANSWER and not SINGLE_ANSWER")

    # specific_where and variables can't be used together
    if specific_where == "" and variables is not None:
        raise ValueError("if specific_where is empty, variables must be None as well")

    # initialize variables
    keywords = list(keywords)
    conditions = {} if conditions is None else conditions
    negated_conditions = {} if negated_conditions is None else negated_conditions
    result = {"success": False, "data": None, "error": None}

    # build query
    all_conditions = {key: {"value": value, "negated": False} for key, value in conditions.items()} | {key: {"value": value, "negated": True} for key, value in negated_conditions.items()}
    query = f"""SELECT {', '.join(keywords)} FROM {table}"""

    # add conditions if any
    if len(all_conditions) > 0:
        query += f" WHERE {' AND '.join([f'{key} {'!' if value_data['negated'] is True else ''}= %s' for key, value_data in all_conditions.items()])}"
        if order_by is not None:
            query += f" ORDER BY {order_by[0]} {order_by[1].value}"
        cursor.execute(query, tuple([i["value"] for i in all_conditions.values()]))
        # get data based on answer type
        if answer_type == ANSWER_TYPE.SINGLE_ANSWER:
            data = cursor.fetchone()
        else:
            data = [list(i) for i in cursor.fetchall()]

    # add select max of key condition
    elif select_max_of_key != "":
        query += f" WHERE {select_max_of_key} = (SELECT MAX({select_max_of_key}) FROM {table}) LIMIT 1"
        if order_by is not None:
            query += f" ORDER BY {order_by[0]} {order_by[1].value}"

    # add specific where condition
    elif specific_where != "":
        query += f" WHERE {specific_where}"
        if order_by is not None:
            query += f" ORDER BY {order_by[0]} {order_by[1].value}"

    # add order by condition
    if variables is None:
        cursor.execute(query)
    else:
        cursor.execute(query, variables)

    # get data based on answer type
    if answer_type == ANSWER_TYPE.SINGLE_ANSWER:
        data = cursor.fetchone()
    else:
        data = [list(i) for i in cursor.fetchall()]
    
    # map the data to the keywords if keywords are explicitly specified
    if keywords is not None and "*" not in keywords:
        result = {key: value for key, value in zip(keywords, data)} if answer_type == ANSWER_TYPE.SINGLE_ANSWER else [{key: value for key, value in zip(keywords, vals)} for vals in data] # type: ignore
    return Result(data=result)

# NOTE arguments is either of type dict or of type list
# @catch_exception
def insert(
    cursor: cursor, 
    table: str, 
    values: dict[str, Any] | list[str], 
    returning_column: str | None = None) -> Result[Any, Exception]:
    """
    insert data into table

    Parameters:
        cursor (cursor): cursor for interaction with db
        table (str): table to insert into, if empty set all
        values (dict | list): values that should be entered (key: column, value: value), if empty, no conditions, if values is of type list, then list has to contain all values that have to be entered
        returning_column (int): returns the column
    Returns:
        Result: result object with data or error
    """

    # initialize variables
    if values is None:
        values = {}
    if returning_column == "":
        returning_column = None
    query = ""
    vals = []

    # try insert
    try:
        # build parametrized query
        if type(values) == list:
            query = f"""INSERT INTO {table}
                        VALUES ({', '.join('%s' for _ in range(len(values)))})"""
            vals = values
        elif type(values) == dict:
            query = f"""INSERT INTO {table} ({', '.join(values.keys())})
                    VALUES ({', '.join('%s' for _, _ in enumerate(values.keys()))})"""
            vals = list(values.values())

        # add returning_column !NOT PARAMETRIZED!
        if returning_column != None:
            query += f" RETURNING {returning_column}"

        # run query
        cursor.execute(query, vals)
        cursor.connection.commit()

        # return data if requested
        if returning_column != None:
            data = cursor.fetchone()
            return Result(data=data)
        return Result()

    # rollback if error occurred
    except Exception as e:
        cursor.connection.rollback()
        return Result(error=e, stack_trace=traceback.format_exc())

# for specific_where conditions must be empty, otherwise conditions will be ignored IMPORTANT what is being ignored differs from the other functions
def update(
    cursor: cursor, 
    table: str, 
    returning_column: str | None = None, 
    arguments: dict[str, Any] | None = None,
    conditions: dict[str, Any] | None = None, 
    specific_where: str = "", 
    specific_set: str = "") -> Result[Any, Exception]:
    """
    updates values in a table \n
    already has try catch

    Parameters:
        cursor (cursor): cursor to interact with db
        table (str): table to insert into, if empty set all
        arguments (dict | None): values that should be entered (key: column, value: value)
        conditions (dict | None): specify to insert into the correct row
        specific_where (str): conditions must be empty, otherwise conditions will be ignored, specifies where should be set, IMPORTANT what is being ignored differs from the other functions
        specific_set (str): arguments must be empty, otherwise arguments will be ignored, specifies what should be set
        returning_column (str): returns the specified column, returns just a single column
    Returns:
        Result: result object with data or error
    """

    # initialize variables
    if arguments is None:
        arguments = {}
    if conditions is None:
        conditions = {}
    if returning_column == "":
        returning_column = None

    # try update
    try:
        # build query
        query = f"""UPDATE {table}"""

        # set part
        if specific_set != "":
            query += f""" SET {specific_set}"""
        else:
             query += f""" SET  {', '.join(key + ' = %s' for _, key in enumerate(arguments.keys()))}"""

        # where part
        if specific_where != "":
            query += " WHERE " + specific_where
        else:
            query += f""" WHERE {' AND '.join(key + " = %s" for _, key in enumerate(conditions))}"""
        
        # returning part
        if returning_column != None:
            query += f" RETURNING {returning_column}"

        # execute query
        cursor.execute(query, list(arguments.values()) + list(conditions.values()))
        cursor.connection.commit()

        # get data if requested
        if returning_column != None:
            data = cursor.fetchone()
            return Result(data=data)
        return Result()

    # rollback if error occurred
    except Exception as e:
        cursor.connection.rollback()
        return Result(error=e, stack_trace=traceback.format_exc())

def remove(
        cursor: cursor, 
        table: str, 
        conditions: dict[str, Any],
        returning_column: str | None = None) -> Result[Any, Exception]:
    """
    removes data from table \n
    already has try catch

    Parameters:
        cursor (cursor): cursor to interact with db
        table (str): table to insert into, if empty set all
        conditions (dict): specify from which row to remove the data
        returning_column (str): returns the specified column, returns just a single value
    Returns:
        Result: result object with data or error
    """

    # initialize variables
    if returning_column == "":
        returning_column = None

    # try remove
    try:
        # build query
        query = f"""DELETE FROM {table}
                    WHERE {' AND '.join(key + " = %s" for _, key in enumerate(conditions))}"""

        # returning part
        if returning_column != None:
            query += f" RETURNING {returning_column}"

        # execute query
        cursor.execute(query, list(conditions.values()))
        cursor.connection.commit()

        # get data if requested
        if returning_column != None:
            data = cursor.fetchone()
            return Result(data=data)
        return Result()
    
    # rollback if error occurred
    except Exception as e:
        cursor.connection.rollback()
        return Result(error=e, stack_trace=traceback.format_exc())

def custom_call(
        cursor: cursor, 
        query: str, 
        type_of_answer: ANSWER_TYPE, 
        variables: list[Any] | tuple[Any] | None = None) -> Result[Any, Exception]:
    """
    send a custom query to the database

    Parameters:
        cursor (cursor): cursor to interact with db
        query (str):
        type_of_answer (ANSWER_TYPE): what answer to expect
        variables (list | None): list of variables that should be passed into the query
    Returns:
        Result: result object with data or error
    """

    # try custom call
    try:
        # execute query
        cursor.execute(query, variables)

        # Always commit (TODO: Filter SELECT statements)
        if query.startswith("SELECT") is False:
            cursor.connection.commit()
        
        if type_of_answer == ANSWER_TYPE.NO_ANSWER:
            return Result()
        elif type_of_answer == ANSWER_TYPE.SINGLE_ANSWER:
            return Result(data=cursor.fetchone())
        elif type_of_answer == ANSWER_TYPE.LIST_ANSWER:
            return Result(data=cursor.fetchall())
        else:
            # would usually be better to check at the beginning, but since code is used backend, function is mostly used correctly. Therefore, it is more effective to check at the end if no other case matches
            return Result(error="parameter type_of_answer of the function must be of enum type ANSWER_TYPE")
    
    # rollback if error occurred
    except Exception as e:
        cursor.connection.rollback()
        return Result(error=e, stack_trace=traceback.format_exc())

# TODO can only return success True right now
# @catch_exception
def get_time(cursor: cursor) -> Result[Any, Exception]:
    """
    returns the current berlin time

    Parameters:
        cursor (cursor): cursor to interact with db
    Returns:
    Result: result object with data or error
    """
    # execute query
    query = """SELECT NOW() AT TIME ZONE 'Europe/Berlin' AS current_time"""
    cursor.execute(query)
    data = cursor.fetchone()
    return Result(data=data[0] if data is not None else None)

def close(cursor: cursor):
    """
    closes the current cursor
    
    Parameters:
        cursor: cursor that should be closed
    """
    cursor.close()
    conn = getattr(cursor, 'connection', None)
    if conn is not None:
        conn.close()

if __name__ == "__main__":
    connect()