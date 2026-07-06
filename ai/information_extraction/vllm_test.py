"""
load vllm using:  python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3.5-9B \
    --max-model-len 256000 \
    --port 8000
"""


from smolagents import CodeAgent, LiteLLMModel

model = LiteLLMModel(
    model_id="openai/Qwen/Qwen3.5-9B",
    api_base="http://localhost:8000/v1",
    api_key="dummy-key",
    
    # --- Generation Parameters go here ---
    max_tokens=128000,          # Equivalent to max_new_tokens
    temperature=0.7,          # Controls randomness (lower = more deterministic)
    top_p=0.95,                # Nucleus sampling (alternative to temperature)
    top_k=20,
    # frequency_penalty=0.0,    # Penalizes tokens that have already appeared often
    presence_penalty=1.5,     # Penalizes tokens based on if they appeared at all
    stop=["<|eot_id|>"],      # Custom stop sequences to halt generation early
)


base_path = "/home/gatterle/mhbai/"
module_break = "--- NEUES MODUL ---"
page_break = "---Page Break---"
token_input_percentage = 0.3

with open("ai/information_extraction/test-docling.md", "r") as f:
    md_doc = f.read()

pages = md_doc.split("\n" + page_break + "\n")
toc = [pages[1]]
for index, i in enumerate(pages[2:]):
    if "\n| Modul" in i[:15]:
        break
    toc.append(i)

toc = "\n\n".join(e.strip() for e in toc)
pages = pages[index + 2 :]

# initialize list of modules
modules = []

# group pages into modules
mod = []
for i in pages:
    if "\n| Modul" in i[:15]:
        modules.append(mod)
        mod = [i]
    else:
        mod.append(i)
modules.append(mod)

# combine module pages to single module string and remove empty modules
modules = ["\n\n".join(e.strip() for e in i) for i in modules]
modules = [i for i in modules if i.strip() != ""]

# remove duplicates while preserving order
mods = []
for i in modules:
    if i not in mods:
        mods.append(i)
modules = mods

import json
from ai.information_extraction.data_template import exam_info, time_info, ModuleInfo, ModuleHandbook

from ai.information_extraction.smolagent import prompt

full_prompt = prompt.format(module_handbook=md_doc)

from smolagents import CodeAgent, LiteLLMModel
from smolagents.default_tools import FinalAnswerTool # , PythonInterpreterTool
from ai.information_extraction.tools import ValidateOutput
from ai.information_extraction.prompts import system_prompt, instructions, prompt
from tokenizers import Tokenizer

tokenizer = Tokenizer.from_file("ai/information_extraction/gemma-4-31b-tokenizer.json")

mods = [(i, len(tokenizer.encode(i).ids)) for i in modules]
inputs = []
inp = []
inp_size = 0
context_window = 256000
limit = token_input_percentage * context_window
limit = 15000
for i in mods:
    if inp_size + i[1] < limit:
        inp.append(i[0])
        inp_size += i[1]
    else:
        inputs.append(f"\n\n{module_break}\n\n".join(e.strip() for e in inp))
        inp = [i[0]]
        inp_size = i[1]
inputs.append(f"\n\n{module_break}\n\n".join(e.strip() for e in inp))

agent = CodeAgent(
            tools=[FinalAnswerTool(), ValidateOutput()],
            additional_authorized_imports=["json", "pydantic", "typing", "ai.information_extraction.data_template", "ai.information_extraction.tools"],
            instructions=instructions,
            max_steps=7,
            model=model)

print(f"Number of input chunks: {len(inputs)}")
results = []
for i in inputs:
    agent.prompt_templates["system_prompt"] = agent.prompt_templates["system_prompt"] + "\n\nAdditional rules (German):\n" + system_prompt.format(module_break="--- NEUES MODUL ---")
    full_prompt = prompt.format(module_handbook=i)
    result = agent.run(full_prompt, reset=True)
    results.append(result)
print(results)
final_result = "\n\n".join(e.strip() for e in results)