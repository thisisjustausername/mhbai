"""
convert xml to json and clean the html tags in the process
"""

from pathlib import Path
from typing import Any
import re
import xmltodict, json


def clean_dict(diction: dict[str, Any]) -> dict[str, Any]:
    """
    clean the dict by removing the @ from the keys and converting camelCase to snake_case

    Args:
        diction (dict[str, Any]): the dict to clean
    Returns:
        dict[str, Any]: the cleaned dict
    """
    # initialize new dict
    new_dict = dict()

    # clean the dict recursively
    for key, value in diction.items():
        # remove @ from the key if it exists
        if key.startswith("@"):
            key = key[1:] if key.startswith("@") else key
        # convert camelCase to snake_case
        key = camel_to_snake(key)
        # clean the value recursively if it is a dict, list or tuple, that contain dicts
        if isinstance(value, dict):
            value = clean_dict(value)
        elif isinstance(value, list):
            value = [clean_dict(item) if isinstance(item, dict) else item for item in value]
        elif isinstance(value, tuple):
            value = tuple(clean_dict(item) if isinstance(item, dict) else item for item in value)
        # add the cleaned key and value to the new dict
        new_dict[key] = value
    return new_dict


def camel_to_snake(name: str) -> str:
    """
    convert camelCase to snake_case

    Args:
        name (str): the name to convert
    Returns:
        str: the converted name
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def clean_html_only(data: dict[str, str | list | dict | None], none_separator: str = "--NONE--") -> str:
    """
    pass in the body of the html or recursively elements inside the body

    Args:
        data (dict[str, str | list | dict | None]): the data to clean
        none_separator (str): the separator to use for None values
    Returns:
        str: the cleaned data
    """
    # elements to convert differently
    html_map: dict[str, str] = {
        "br": "\n",
        "style": "",
    }
    # mapper for the special html elements
    html_mapper = lambda key, value: "".join([html_map.get(key, "") for _ in range(len(value) if isinstance(value, list) else 1)])

    # initialize text output
    output: str = ""
    # for each key and value in the data clean it based on the type
    for key, value in data.items():
        # check first
        if key in html_map:
            output += html_mapper(key, value)
            continue

        # add strings directly
        if isinstance(value, str):
            output += value
            continue
        
        # add <None> separator
        if value is None:
            output += none_separator
        if isinstance(value, dict):
            output += clean_html_only(value)
            continue
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    output += clean_html_only(item)
                else:
                    output += str(item)
        """
        if len(output) % 8 == 0 and output == ("--NONE--" * (len(output) // 8)):
            output = None
        """
    return output


# convert html
def clean_html_dict(data: dict[str, str | list | dict | None] | list[Any]) -> dict[str, str | list | dict | None] | list[Any]:
    """
    clean the json dict by replacing html with its content

    Args:
        data (dict[str, str | list | dict | None] | list[Any]): the data to clean
    Returns:
        dict[str, str | list | dict | None] | list[Any]: cleaned dict / list
    """

    if isinstance(data, dict):
        new = dict()
        for key, value in data.items():
            if isinstance(value, dict) and len(value) == 1 and "html" in value:
                if "body" in value["html"]:
                    html = value["html"]["body"]
                    if isinstance(html, str):
                        new[key] = html
                        continue
                    if isinstance(html, dict):
                        new[key] = clean_html_only(html)
                        continue
            if not isinstance(value, (list, dict)):
                new[key] = value
            new[key] = clean_html_dict(value) # type: ignore
        return new
    if isinstance(data, list):
        return [clean_html_dict(item) if isinstance(item, (dict, list)) else item for item in data]
    return data


def xml_to_json(xml_path: Path) -> tuple[dict[str, Any], Path]:
    """
    Finished pipeline step, that combines all of the steps above.
    Convert xml to json and clean the html tags in the process.

    Args:
        xml_path (Path): The path to the XML file to convert
    Returns:
        tuple(dict[str, Any], Path): the converted and cleaned json and the path to the XML file
    """
    # parse xml to json
    diction = xmltodict.parse(xml_path.read_text(encoding="utf-8"))

    # clean json by replacing html with its content
    data = clean_html_dict(clean_dict(diction))

    return data, xml_path # type: ignore


if __name__ == "__main__":
    # 1. read xml
    with open("test.xml", "r") as f:
        xml = f.read()
    
    # 2. parse xml to json
    diction = xmltodict.parse(xml)

    # 3. clean json by replacing html with its content
    data = clean_html_dict(clean_dict(diction))

    # 4. save data
    json.dump(data, open("test_cleaned.json", "w"), indent=4)
    print(json.dumps(data, indent=4))
