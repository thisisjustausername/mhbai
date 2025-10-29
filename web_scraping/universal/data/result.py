# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# For usage please contact the developer.
#
# This file is Copyright-protected.

# Description: connect to postgresql database and perform basic operations
# Status: IN DEVELOPMENT

from typing import Generic, TypeVar, Union, Optional

Data = TypeVar("Data") # success type
Error = TypeVar("Error") # error type

class DB_Result(Generic[Data, Error]):
    def __init__(self, data: Optional[Data] = None, error: Optional[Error] = None):
        if all(i is not None for i in (data, error)):
            raise ValueError("DB_Result cannot have both data and error.")
        self._data = data
        self._error = error

    @property
    def is_success(self) -> bool:
        return self._error is None

    @property
    def is_error(self) -> bool:
        return self._error is not None

    @property
    def data(self) -> Data:
        if self.is_error:
            raise ValueError("No data available, operation resulted in an error.")
        return self._data  # type: ignore

    @property
    def error(self) -> Error:
        if self.is_success:
            raise ValueError("No error available, operation was successful.")
        return self._error  # type: ignore