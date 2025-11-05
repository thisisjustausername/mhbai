# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: turns the filestructure into a markdown representation with added descriptions
# Status: VERSION 1.0
# FileID: D-x-0001

from pathlib import Path

with open(".gitignore", "r") as file:
    ignore_list = file.readlines()
ignore_list = [i.strip() for i in ignore_list]


def folder_to_markdown(folder_path: Path, 
                       stringer="", 
                       indent=0, 
                       indent_type="│   ",
                       show_local_folders=True, 
                       show_local_files=True) -> str:
    if folder_path.is_dir() is False:
        raise ValueError(f"The path {folder_path} is not a valid directory.")
    for item in folder_path.iterdir():
        if item.is_file():
            description = ""
            if item.name.endswith(".py"):
                with open(item, 'r') as file:
                    data = file.read()
                if "# Description: " in data:
                    description = data.split("# Description: ", 1)[1].split("\n")[0]
            stringer += f"{indent_type * indent}└──📄 {item.name}{' (local file)' if item.name in ignore_list and show_local_files else ''}  {'$' + description if description != '' else ''}\n"
            continue
        if item.is_dir():
            if show_local_folders and item.name in ignore_list:
                stringer += f"{indent_type * indent}├──📁 {item.name}/ (local folder)  \n"
                stringer += f"{indent_type * (indent+1)}└── ...  \n"
                continue
            elif item.name in ignore_list:
                continue
            stringer += f"{indent_type * indent}├──📁 {item.name}/  \n"
            stringer = folder_to_markdown(item, stringer, indent=indent+1, show_local_folders=show_local_folders, show_local_files=show_local_files)
    return stringer

def do_all(folder_path: Path,
           stringer="",
           indent=0,
           indent_type="│   ",
           show_local_folders=True,
           show_local_files=True) -> str:
    stringer = folder_to_markdown(folder_path, stringer, indent, indent_type, show_local_folders, show_local_files)
    strings = stringer.split("\n")

    max_len = max(len(i.split("$")[0]) for i in strings)
    strings = [i.split("$")[0] + " " * (max_len - len(i.split("$")[0])) + (i.split("$")[1] if "$" in i else "") for i in strings]
    stringer = "\n".join(strings)
    return stringer

if __name__ == "__main__":
    p = Path(".").expanduser()
    print(do_all(p, show_local_folders=False, show_local_files=True))