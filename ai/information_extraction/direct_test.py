from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, StoppingCriteriaList, StoppingCriteria
import torch
from smolagents import Model, TransformersModel


model_id = "Qwen/Qwen3.5-9B"

tokenizer = AutoTokenizer.from_pretrained(model_id)

bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
    bnb_8bit_compute_dtype=torch.float16,
)

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    dtype=torch.float16,
    device_map="auto",
    attn_implementation="flash_attention_2"
)
model.config.use_cache = True
model = torch.compile(model, mode="reduce-overhead")

"""class StopOnTokens(StoppingCriteria):
    def __init__(self, stop_token_ids: list):
        self.stop_token_ids = stop_token_ids

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        for stop_id in self.stop_token_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False


class LocalHFModel(Model):
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer

    def generate(self,
                 prompt: str,
                 stop_sequences: list[str] | None = None,
                 stop: str | None = None,
                 max_new_tokens: int | None= 128000,
                 temperature: float | None = 0.7,
                 top_p: float | None = 0.95,
                 top_k: float | None = 20,
                 presence_penalty: float | None = 1.5,
                 frequency_penalty: float | None = None):
        
        stop_ids = [tokenizer.encode(w, add_special_tokens=False)[0] for w in stop_sequences] if stop_sequences else []
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        params = {k: v for k, v in locals().items() if v is not None and k not in ["prompt", "stop"]}

        outputs = self.model.generate(
            **inputs,
            **params,
            do_sample=False, # use greedy for deterministic outputs
            stopping_criteria=StoppingCriteriaList([StopOnTokens(stop_ids)]) if stop_ids else None
        )

        text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        return text"""

wrapper = TransformersModel(
    model_id="Qwen/Qwen3.5-9B",
    device_map="auto",
    max_new_tokens=128000,
    )

wrapper.model = model
wrapper.tokenizer = tokenizer
wrapper.kwargs.update({
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 20,
        "repetition_penalty": 1.5,
    },)

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

from smolagents import CodeAgent
from smolagents.default_tools import FinalAnswerTool # , PythonInterpreterTool
from ai.information_extraction.tools import ValidateOutput
from ai.information_extraction.prompts import system_prompt, instructions, prompt


mods = [(i, len(tokenizer.encode(i))) for i in modules]
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

local_model = wrapper

agent = CodeAgent(
            tools=[FinalAnswerTool(), ValidateOutput()],
            additional_authorized_imports=["json", "pydantic", "typing", "ai.information_extraction.data_template", "ai.information_extraction.tools"],
            instructions=instructions,
            max_steps=7,
            model=local_model)

print(f"Number of input chunks: {len(inputs)}")
results = []
for i in inputs:
    agent.prompt_templates["system_prompt"] = agent.prompt_templates["system_prompt"] + "\n\nAdditional rules (German):\n" + system_prompt.format(module_break="--- NEUES MODUL ---")
    full_prompt = prompt.format(module_handbook=i)
    result = agent.run(full_prompt, reset=True)
    results.append(result)
print(results)
final_result = "\n\n".join(e.strip() for e in results)