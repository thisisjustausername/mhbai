# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# For usage please contact the developer.
#
# This file is Copyright-protected.

# Description: load data from sql db and reconstruct dict
# Status: VERSION 1.0
# FileID: Ai-re-0001


from dataclasses import dataclass
from typeguard import typechecked

from database import database as db
from datatypes.result import Result


# TODO: will be changes so that params holds a dict where the keys are the column names and the
# values are the arguments to find in the db
@dataclass(init=False)
class SearchParams:
    """
    Dataclass for search attributes for database colums

    Attributes:
        params (list): list of specified parameters
        allowed_params (list): list of allowed params
    """

    @typechecked
    def __init__(
        self, params: list[str], allowed_params: None | list[str] = None
    ) -> None:
        """
        Init function for SearchParams class

        Args:
            params (list[str]): list of specified parameter names
            allowed_params (list[str]): list of allowed parameters

        Returns: None
        """
        self.params = params
        self.allowed_params = allowed_params

    @typechecked
    def set_allowed_params(self, allowed_params: list[str]) -> None:
        """
        set the allowed_params afterwards

        Args:
            allowed_params (list[str]): list of allowed_params to set

        Returns:
            None
        """
        self.allowed_params = allowed_params

    def check_validity(self) -> bool | UserWarning:
        """
        check the validity of the provided parameters

        Args:
            None

        Returns:
            bool | UserWarning: True, when matching, False otherwise, UserWarning when no
                                allowed_params set
        """
        if self.allowed_params is None:
            raise UserWarning("Please set allowed_params")

        return all(i in self.allowed_params for i in self.params)


@db.cursor_handling(manually_supply_cursor=False)
def load_data(mhb_url: str, uni_a: bool = True, cursor=None, **kwargs) -> dict:
    """
    Load data from SQL database and reconstruct it into a dictionary.

    Args:
        cursor: Database cursor to execute SQL queries.
        uni_a (bool): Flag to determine the type of data to load.
        mhb_url (str): ulr of the mhb file
        **kwargs (Any): values to search for in the database
    Returns:
        dict: Reconstructed data as a dictionary.
    """

    if not uni_a:
        raise NotImplementedError("Only uni_a=True is implemented.")
    result = load_unia_modules(cursor=cursor, search_params=search_params, **kwargs)
    return result


@db.cursor_handling(manually_supply_cursor=True)
def load_unia_modules(cursor, search_params: SearchParams, **kwargs) -> Result:
    """
    Load uni_a modules from the database and reconstruct them into a dictionary.

    Args:
        cursor: Database cursor to execute SQL queries.
        search_params (SearchParams): SearchParams object containing search parameters.
        module_code (str): module code to search

    Returns:
        dict: Reconstructed uni_a modules as a dictionary.
    """
    general_keywords = [
        "id",
        "title",
        "module_code",
        "ects",
        "lecturer",
        "contents",
        "goals",
        "requirements",
        "expense",
        "success_requirements",
        "weekly_hours",
        "exams",
        "module_parts",
    ]

    search_params.set_allowed_params(general_keywords)
    valid = search_params.check_validity()
    if not valid:
        raise Exception("Invalid Parameters specified")

    if search_params.params == []:
        search_params.params = general_keywords

    allowed_search_params = ["id", "title", "module_code", "ects", "lecturer"]
    if any(i not in allowed_search_params for i in kwargs):
        raise UserWarning(
            f"Only these parameters are allowed to search by by now: {allowed_search_params}"
        )

    result = db.select(
        cursor=cursor,
        table="unia.modules_ai_extracted",
        answer_type=db.ANSWER_TYPE.LIST_ANSWER,
        keywords=search_params.params,
        conditions=kwargs,
    )

    return result


if __name__ == "__main__":
    module_code = "KTH-3000"
    result = load_data(search_params=SearchParams(params=[]), module_code=module_code)
    import json

    print(json.dumps(result.data[0], indent=4))

