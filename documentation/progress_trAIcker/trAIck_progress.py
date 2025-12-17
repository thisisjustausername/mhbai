import os
import re
import json
import sys
from ollama import chat
from ollama import ChatResponse
from datetime import datetime
from itertools import groupby


# get ollama using
# pip install ollama
# curl -fsSL https://ollama.com/install.sh | sh
# ollama run llama3.1


def fetch_history(history_file: str = "~/.zsh_history", save_to_json: bool = False) -> list[dict]:
    """
    Fetch and parse Zsh shell history from the specified history file.

    Args:
        history_file (str): Path to the Zsh history file. Defaults to "~/.zsh_history".
        save_to_json (bool): Whether to save the parsed history to a JSON file. Defaults to False.
    Returns:
        list[dict]: A list of dictionaries containing parsed history entries.
    """

    # Path to Zsh history file
    history_file = os.path.expanduser(history_file)

    # initialize list to hold history entries
    entries = []
    current_timestamp = None

    # Read and parse the Zsh history file
    with open(history_file, "r") as f:
        data = re.split(r"(?=\n: \d+:\d+;)", f.read())

    # Clean and process each line
    data = [i.strip() for i in data]
    data = [i for i in data if i != ""]

    # Process each entry
    for index, line in enumerate(data):
        # Each line starts with ": <timestamp>:<duration>;<command>"
        line_data = line[2:].split(":", 1)
        current_timestamp = int(line_data[0])
        duration, command = line_data[1].split(";", 1)
        duration = int(duration)
        command = command.strip()
        
        # Create entry dictionary
        entry = {
            "timestamp": current_timestamp,
            "datetime": datetime.fromtimestamp(current_timestamp),
            "duration": duration,
            "command": command
        }

        # Append entry to the list
        entries.append(entry)

    if save_to_json:
        json_entries = [
            {key: value for key, value in entry.items() if key != "datetime"}
            for entry in entries
        ]
        # Export to JSON
        with open("zsh_history.json", "w") as f:
            json.dump(json_entries, f, indent=4)
    
    return entries

def question_ai(data: list[dict]) -> str:
    """
    Use an AI model to comprehense the daily progress and group it into tasks.

    Args:
        data (list[dict]): List of dictionaries containing Zsh history entries.

    Returns:
        str: The AI model's response to the question.
    """

    # group data by date
    grouped_data = groupby(data, key=lambda x: x["datetime"].date())
    grouped_data = {str(key): list(group) for key, group in grouped_data}
    grouped_data = {key: {"commands ordered by time": [val["command"] for val in value]} for key, value in grouped_data.items()}

    # comprehend the commands for each day
    for key, value in grouped_data.items():
        print(key)

        # query ai, use description and data specification
        response: ChatResponse = chat(model="llama3.1", 
                                    messages=[
                                        {
                                            "role": "system",
                                            "content": """Added is a list of terminal commands. 
These commands are ordered by time with the newest commands at the end. now please group these commands into tasks that I worked on during that day. 
A task is a group of commands that are related to each other by context and contribute to a specific goal or project. 
For example, if I was working on a web development project, the commands related to setting up the server, writing code, and testing the application would all be grouped together under the task 'Web Development'. 
Please provide a summary of each task along with the list of commands that belong to it. 
You are a content-filtering system.
Your output MUST be valid JSON only. No explanations.
Schema:
{
  "category": string (Which category the group falls in),
  "information": string (further information about what was done), 
  "commands": the commands of the group
}"""
                                        },
                                        {
                                            "role": "user",
                                            "content": json.dumps(value)
                                        }
                                    ])

        # add result to data
        grouped_data[key]["tasks"] = response['message']['content']
        # print response
        print(response["message"]["content"])

    with open("comprehension.json", "w") as file:
        json.dump(grouped_data, file, indent=4)

if __name__ == "__main__":
    history_data = fetch_history(save_to_json=True)
    ai_response = question_ai(history_data)
    print("AI Response:\n", ai_response)
