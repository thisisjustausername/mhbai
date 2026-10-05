import re
from pathlib import Path

PKG = "mhbai"
MODULES = [
    "ai", "api", "benchmark", "chatbot", "database", "datatypes",
    "documentation", "extract_info", "mapping", "modulecheck", "mongo_db",
    "pdf_reader", "playground", "public", "student_counselor", "uni_augsburg",
    "universities", "university_of_augsburg", "web_scraping", "website",
    "web_service", "xml_processing",
]
alt = "|".join(sorted(map(re.escape, MODULES), key=len, reverse=True))

# from mongo_db import x / from mongo_db.client import x
from_re = re.compile(rf"^([ \t]*)from[ \t]+({alt})\b([\w.]*)[ \t]+import\b", re.M)
# import mongo_db / import mongo_db.client / import mongo_db as m
imp_re = re.compile(rf"^([ \t]*)import[ \t]+({alt})\b([\w.]*)([ \t]+as[ \t]+\w+)?[ \t]*$", re.M)

def fix_from(m):
    return f"{m.group(1)}from {PKG}.{m.group(2)}{m.group(3)} import"

def fix_import(m):
    indent, mod, rest, alias = m.groups()
    full = f"{PKG}.{mod}{rest}"
    if alias:                      # import x as y -> import mhbai.x as y
        return f"{indent}import {full}{alias}"
    if rest:                       # import x.y -> needs manual usage fix
        print(f"  WARNING manual fix needed: import {mod}{rest}")
        return f"{indent}import {full}"
    return f"{indent}import {full} as {mod}"   # import x -> keeps name x

roots = [Path("src") / PKG, Path("tests")]
for root in roots:
    if not root.exists():
        continue
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        new = from_re.sub(fix_from, text)
        new = imp_re.sub(fix_import, new)
        if new != text:
            path.write_text(new, encoding="utf-8")
            print("fixed", path)
