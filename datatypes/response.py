# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# For usage please contact the developer.
#
# This file is Copyright-protected.

# Description: method response type
# Status: VERSION 1.0
# FileID: Dt-x-0002


from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar


class Status(Enum):
    """
    Status representing the result of an operation.

    Attributes:
        FULL_SUCCESS (int): Indicates a full success.
        PARTIAL_SUCCESS (int): Indicates a partial success.
        FULL_ERROR (int): Indicates a full error.
    """

    FULL_SUCCESS = 1
    PARTIAL_SUCCESS = 0
    FULL_ERROR = -1


T = TypeVar("T") # success type
E = TypeVar("E") # error type

@dataclass
class Response(Generic[T, E]):
    """
    Response class representing the result of an operation, which can be either a success with data or an error.

    Attributes:
        _data (Optional[T]): The successful result data.
        _error (Optional[E]): The error information if the operation failed.
        _status (Status): The status of the response indicating success or error.
    """

    def __init__(self, success_list: T | None = None, error_list: E | None = None):
        """
        Initialize a Response object.

        Parameters:
            success_list (T | None): The successful result data.
            error_list (E | None): The error information if the operation failed.
        Returns:
            None
        """
        self._data = success_list if success_list is not None else []
        self._error = error_list if error_list is not None else []
        self._status = Status.FULL_SUCCESS if error_list is None else Status.FULL_ERROR if success_list is None else Status.PARTIAL_SUCCESS

    @property
    def success_list(self) -> T:
        """
        Get the list of successful results.

        Returns:
            T: The successful result data.
        """
        return self._data  # type: ignore

    @property
    def error_list(self) -> E:
        """
        Get the list of error results.

        Returns:
            E: The error result data.
        """
        return self._error  # type: ignore

    @property
    def status(self) -> Status:
        """
        Get the status of the response.

        Returns:
            Status: The status of the response.
        """
        return self._status