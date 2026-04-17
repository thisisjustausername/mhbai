import json

from smolagents import Any, tool
from smolagents.tools import Tool
from .data_template import exam_info, time_info, ModuleInfo, ModuleHandbook

@tool
def get_module_handbook_data():
    """
    This function retrieves module handbook data.
    The data contains raw information in the form of text and tables about modules and how they are structured.
    """
    pass

'''@tool
def final_answer(output: ModuleHandbook):
    """
    Dieses Tool wird zur Validierung der Ausgabe verwendet und gibt die finale Antwort zurück. 
    
    Dieses Tool darf nur ein einziges Mal aufgerufen werden. Der Parameter 'data' muss im gleichen Call angegeben werden. Nur, falls die Validierung fehlschläft, ist ein weiterer Aufruf erlaubt.

    """
pass'''


class FetchDescriptionForColumnTool(Tool):
    """
    Tool to fetch the description for a given column name. This tool should be used to fetch the description for a column name before using it in the final answer.

    Args:
        column_name (str): The name of the column for which the description is to be fetched.
    """
    name = "fetch_description_for_column"
    description = "Fetches the description for a given column name."
    inputs = {
        "column_name": {
            "type": "string",
            "description": "The name of the column for which the description is to be fetched.",
            "required": True
        }
    }
    output_type = "string"

    def forward(self, column_name: str) -> str:
        """
        The forward method takes the column name as input and returns the corresponding description from the key_mapping dictionary. If the column name is not found in the key_mapping, it returns an appropriate message.

        Args:
            column_name (str): The name of the column for which the description is to be fetched.
        """

class FinalAnswerTool(Tool):
    """
    Tool to validate the final answer and return it. This tool should only be called once. The parameter 'answer' must be provided in the same call. Only if the validation fails, a second call is allowed.

    Args:
        answer (ModuleHandbook): The final answer to be validated and returned.
    """
    name = "final_answer"
    description = "Provides a final answer to the given problem."
    inputs = {
        "answer": {
            "type": "object",
            "description": "The answer to be validated and returned.",
            "required": True
        }
    }
    output_type = "object"

    def forward(self, answer: ModuleHandbook) -> ModuleHandbook | ValueError:
        """
        The forward method takes the answer as input, validates it against the ModuleHandbook schema, and returns the validated answer. If the validation fails, it raises a ValueError with an appropriate message.

        Args:
            answer (ModuleHandbook): The answer to be validated and returned.
        Returns:
            ModuleHandbook: The validated answer conforming to the ModuleHandbook schema.
        Raises:
            ValueError: If the input format for the final answer is invalid.
        """
        try:
            if isinstance(answer, str):
                answer = json.loads(answer)
            answer = ModuleHandbook.model_validate(answer)
        except Exception as e:
            raise ValueError(f"Invalid input format for final answer: {e}")
        return answer