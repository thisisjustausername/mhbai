"""
turns the filestructure into a markdown representation
"""

from pathlib import Path

with open(".gitignore", "r") as file:
    ignore_list = file.readlines()
ignore_list = [i.strip() for i in ignore_list]


def folder_to_markdown(folder_path: Path, stringer="", indent=0, indent_type="│   ", info_list=[], show_local_folders=True, show_local_files=True) -> str:
    if folder_path.is_dir() is False:
        raise ValueError(f"The path {folder_path} is not a valid directory.")
    for item in folder_path.iterdir():
        if item.is_file():
            '''
            if item.name.endswith(".py"):
                with open(item, 'r') as file:
                    data = file.read()
                if data.startswith('"""'):
                    if "License" in data.split('"""', 2)[1]:
            '''
            stringer += f"{indent_type * indent}└──📄 {item.name}{' (local file)' if item.name in ignore_list and show_local_files else ''}\t\n"
            continue
        if item.is_dir():
            if show_local_folders and item.name in ignore_list:
                stringer += f"{indent_type * indent}├──📁 {item.name}/ (local folder)\t\n"
                stringer += f"{indent_type * (indent+1)}└── ...\t\n"
                continue
            elif item.name in ignore_list:
                continue
            stringer += f"{indent_type * indent}├──📁 {item.name}/\t\n"
            stringer = folder_to_markdown(item, stringer, indent=indent+1, show_local_folders=show_local_folders, show_local_files=show_local_files)
    return stringer

if __name__ == "__main__":
    p = Path(".").expanduser()
    print(folder_to_markdown(p, show_local_folders=False, show_local_files=True))