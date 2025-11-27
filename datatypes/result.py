# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# For usage please contact the developer.
#
# This file is Copyright-protected.

# Description: database result type
# Status: VERSION 1.0
# FileID: Dt-x-0001

# TODO: implement .succes Enum datatype of success values: FULL_SUCCESS, PARTIAL_SUCCESS, ERROR

from dataclasses import dataclass
from typing import Generic, TypeVar, Optional

Data = TypeVar("Data") # success type
Error = TypeVar("Error") # error type

@dataclass
class Result(Generic[Data, Error]):
    """
    Result class representing the outcome of an operation, which can be either a success with data or an error.
    Especially useful for database operations.
    """

    def __init__(self, data: Optional[Data] = None, error: Optional[Error] = None):
        """
        Initialization of the Result object.

        Parameters:
            data (Optional[Data]): The successful result data.
            error (Optional[Error]): The error information if the operation failed.
        Returns:
            None
        """
        # if data and error are specified, return error
        if all(i is not None for i in (data, error)):
            raise ValueError("Result cannot have both data and error.")
        self._data = data
        self._error = error

    @property
    def is_success(self) -> bool:
        """
        Represents whether the result is a success.

        Returns:
            bool: True if the result is a success, False otherwise.
        """
        return self._error is None

    @property
    def is_error(self) -> bool:
        """
        Represents whether the result is an error.

        Returns:
            bool: True if the result is an error, False otherwise.
        """
        return self._error is not None

    @property
    def data(self) -> Data:
        """
        Represents the successful result data.

        Returns:
            Data: The successful result data.
        """
        if self.is_error:
            raise ValueError("No data available, operation resulted in an error.")
        return self._data  # type: ignore

    @property
    def error(self) -> Error:
        """
        Represents the error information if the operation failed.

        Returns:
            Error: The error information if the operation failed.
        """
        if self.is_success:
            raise ValueError("No error available, operation was successful.")
        return self._error  # type: ignore