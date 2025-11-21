import runpy
import sys
from pathlib import Path

def run_target(arg: str):
    p = Path(arg).resolve()
    # if user passed an explicit module name, run it directly
    if not p.exists() and "." in arg and not arg.endswith(".py"):
        runpy.run_module(arg, run_name="__main__", alter_sys=True)
        return

    # compute module name relative to cwd (workspace root)
    try:
        rel = p.relative_to(Path.cwd().resolve())
        module = ".".join(rel.with_suffix("").parts)
        runpy.run_module(module, run_name="__main__", alter_sys=True)
    except Exception:
        # fallback: execute file directly
        runpy.run_path(str(p), run_name="__main__")

def main():
    if len(sys.argv) < 2:
        print("Usage: run_from_root.py <file.py | package.module>")
        sys.exit(2)
    run_target(sys.argv[1])

if __name__ == "__main__":
    main()