# # Parsing PDF-MHBs into JSON for general universities in Germany
# In order to convert PDFs into JSON and extract all the necessary information out of it, different approaches are viable.
# 1. Extracting data using NER-models by cutting the PDF, that was converted to MD using LLM, into blocks and then classifying which block means what
# 2. Extracting data using LLMs, either directly or after OCR with LLM e.g. Docling
# 3. Extracting data using Agent, either directly or after OCR to MD using LLM e.g. Docling or Mineru
# 4. Using XML, Regex and NER-models combined with LLMs and agents since most MHBs are very similar as the tool for generating them (flexnow) has a monopoly in this area
# 
# In this case option 3 will be used

# Installing all needed dependencies:
import os
import sys
os.environ['PYTHONPATH'] = os.path.expanduser('~/mhbai')
sys.path.append(os.path.expanduser('~/mhbai'))

base_path = "/home/gatterle/mhbai/"
module_break = "--- NEUES MODUL ---"
page_break = "---Page Break---"
token_input_percentage = 0.3

# USER-INPUT:
# Please choose the path to a pdf

path_to_pdf = "pdfs/1.pdf"
save_files = True
printing = True

# ## 1. Converting PDF into .md using docling (mineru is an alternative)

# ### 1.1 Convert PDF to Markdown

from docling.document_converter import DocumentConverter

path = base_path + path_to_pdf

# create converter
converter = DocumentConverter()

# convert document to markdown
result = converter.convert(path)
md_doc = result.document.export_to_markdown(page_break_placeholder=page_break)

if save_files:
    with open("test-docling.md", "w") as f:
        f.write(md_doc)
if printing:
    print(md_doc)

# alternatively load previously saved markdown
# with open("test-docling.md", "r") as f:
#     md_doc = f.read()

# ### 1.2 Split document into module-chunks

pages = md_doc.split("\n" + page_break + "\n")

# ### 1.2.3 University of Augsburg specific fine tuning

# __this will be done using NER-models like Bert__

# Generate Table of Contents (ToC)

toc = [pages[1]]
for index, i in enumerate(pages[2:]):
    if "\n| Modul" in i[:15]:
        break
    toc.append(i)

toc = "\n\n".join(e.strip() for e in toc)
pages = pages[index + 2 :]

# alternatively load previously saved markdown
# with open("test-docling.md", "r") as f:
#     md_doc = f.read()

# Generate modules

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

# ## 2. Extracting important information using smolagents
# 1. Creating dataclasses, tools and a prompt
# 2. Executing smolagents with the previously created md-data

# ### 2.1.1 Create tools

import json
from ai.information_extraction.data_template import exam_info, time_info, ModuleInfo, ModuleHandbook
if printing:
    print(json.dumps(ModuleHandbook.model_json_schema(), indent=2))

# ### 2.1.2 Create prompt

from ai.information_extraction.smolagent import prompt

full_prompt = prompt.format(module_handbook=md_doc)

# ### 2.1.3 Create agent

from smolagents import CodeAgent, LiteLLMModel
from smolagents.default_tools import FinalAnswerTool # , PythonInterpreterTool
from ai.information_extraction.tools import ValidateOutput
from ai.information_extraction.prompts import system_prompt, instructions, prompt


# model = LiteLLMModel(model_id="ollama_chat/gemma4:31b")
# model_name = "qwen3.6:35b-a3b"
# model_name = "gemma4:31b"
model_name = "qwen3.5:4b"
context_window = 256000
# model = LiteLLMModel(model_id=f"ollama_chat/{model_name}")

# Create an agent with no tools
'''
agent = CodeAgent(
        tools=[FinalAnswerTool(), ValidateOutput()],
        additional_authorized_imports=["json", "pydantic", "typing", "ai.information_extraction.data_template", "ai.information_extraction.tools", "ai.information_extraction.tools.ValidateOutput"],
        instructions=instructions,
        max_steps=5,
        model=model)

agent.prompt_templates["system_prompt"] = agent.prompt_templates["system_prompt"] + "\n\nAdditional rules (German):\n" + system_prompt.format(module_break=module_break)
'''

# ### 2.1.4 Create inputs
# In order to use the size of the context window as best as possible, use the tokenizer from the used ai model for approximating the size a specific input would have in the context window

from tokenizers import Tokenizer

tokenizer = Tokenizer.from_file("gemma-4-31b-tokenizer.json")

mods = [(i, len(tokenizer.encode(i).ids)) for i in modules]
inputs = []
inp = []
inp_size = 0

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

if printing:
    print(f"Number of input chunks: {len(inputs)}")

# ### 2.2 Run agent

model = LiteLLMModel(model_id="ollama_chat/qwen3.5:9b")

from smolagents import VLLMModel

# model = VLLMModel(model_id="Qwen/Qwen3.5-9B")


results = []
for i in inputs:
    agent = CodeAgent(
            tools=[FinalAnswerTool(), ValidateOutput()],
            additional_authorized_imports=["json", "pydantic", "typing", "ai.information_extraction.data_template", "ai.information_extraction.tools"],
            instructions=instructions,
            max_steps=7,
            model=model)

    agent.prompt_templates["system_prompt"] = agent.prompt_templates["system_prompt"] + "\n\nAdditional rules (German):\n" + system_prompt.format(module_break="--- NEUES MODUL ---")


    # full_prompt = prompt.format(module_handbook=i)
    
    full_prompt = prompt.format(module_handbook=i)
    result = agent.run(full_prompt)
    results.append(result)

# Validate output and convert it to JSON

res = []
for r in results:
    try:
        result = ModuleHandbook.model_validate(r)
        if result.modules is None:
            raise ValueError("Modules are None, can't get much worse")
        res.append(result)
    except Exception as e:
        if isinstance(r, dict) and "data" in r:
            try:
                result = ModuleHandbook.model_validate(r["data"])
                res.append(result)
            except Exception as e2:
                print(f"Validation failed: {e}")
        elif isinstance(r, list):
            try:
                result = ModuleHandbook.model_validate(ModuleHandbook(modules=r))
                res.append(result)
            except Exception as e2:
                print(f"Validation failed: {e}")

data = [r.model_dump() for r in res]
modules = []
for d in data:
    modules.extend(mods if (mods := d.get("modules", None)) is not None else [])
if printing:
    print(f"Extracted {len(modules)} modules.")
    print(f"{len([i for i in data if i.get('modules') is not None])} of {len(results)} extractions were successful.")

import json

if printing:
    print(json.dumps(data, indent=4, ensure_ascii=False))

# ## 3. Create confidence-score using Regex and NER-models

pass

# ## 4. Save data to database (unia.modules_ai_extracted)

technique = f"agent-{model_name}"

print(len(md_doc.split(" ")))