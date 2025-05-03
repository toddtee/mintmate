# src/mintmate/main.py

import os
import pandas as pd
from datetime import datetime
from .config_loader import load_config
from .excel_writer  import create_workbook

def main():
    cfg = load_config()
    os.makedirs(cfg["output_dir"], exist_ok=True)
    print(f"🐼 Loading Puzzle Database... {cfg["csv_path"]}")
    df = pd.read_csv(cfg["csv_path"])

    # 1) Build your file_naming dict with computed filename + dirname
    fn = cfg.get("file_naming", {})
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # Decide on the workbook filename
    if fn.get("override_filename"):
        workbook_name = fn["override_filename"]
    else:
        template = fn.get("template", "mintmate_puzzles_{timestamp}.xlsx")
        workbook_name = template.format(
            term=fn.get("term",""),
            week=fn.get("week",""),
            timestamp=ts
        )

    # Decide on the directory name (no spaces, strip any timestamp suffix)
    base = workbook_name.rsplit(".",1)[0].replace(f"_{ts}", "")
    dir_name = base.replace(" ", "")

    # Merge back into the dict
    fn.update({
        "filename": workbook_name,
        "dirname": dir_name,
        "timestamp": ts
    })

    # 2) Handle legacy single-sheet fallback
    puzzle_sets = cfg.get("puzzle_sets")
    if not puzzle_sets and "puzzles" in cfg:
        puzzle_sets = [{"sheet_name":"Puzzles","puzzles":cfg["puzzles"]}]

    # 3) Call the workbook builder
    out = create_workbook(
        puzzle_sets= puzzle_sets,
        df=          df,
        output_dir=  cfg["output_dir"],
        theme=       cfg["board_theme"],
        style=       cfg["piece_style"],
        file_naming= fn
    )

    print(f"📄 Workbook generated at {out}")

if __name__ == "__main__":
    main()
