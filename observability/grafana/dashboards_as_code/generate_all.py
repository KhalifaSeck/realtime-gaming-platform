"""
Genere les JSON des dashboards Grafana depuis les fichiers Python.

Usage :
    cd observability/grafana/dashboards_as_code
    python generate_all.py

Chaque .py doit exposer une variable `dashboard` (Dashboard grafanalib).
"""
import importlib.util
import json
import sys
from pathlib import Path

from grafanalib._gen import DashboardEncoder

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE.parent / "dashboards"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_dashboard_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    py_files = [p for p in HERE.glob("*.py") if p.name != "generate_all.py"]
    if not py_files:
        print("No dashboard .py files found")
        return

    for py in py_files:
        try:
            module = load_dashboard_module(py)
            dashboard = getattr(module, "dashboard", None)
            if dashboard is None:
                print(f"[skip] {py.name} : no 'dashboard' variable")
                continue

            out_path = OUT_DIR / f"{py.stem}.json"
            payload = json.dumps(
                dashboard.to_json_data(),
                sort_keys=True,
                indent=2,
                cls=DashboardEncoder,
            )
            out_path.write_text(payload, encoding="utf-8")
            print(f"[ok]   {py.name} -> {out_path.relative_to(HERE.parent.parent.parent)}")
        except Exception as e:
            print(f"[fail] {py.name} : {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()