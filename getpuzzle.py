import tomli
import pandas as pd
import os
import re
import chess
from datetime import datetime
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# === Helpers ===

def load_config(path="mintmate_config.toml"):
    with open(path, "rb") as f:
        return tomli.load(f)


def get_solution_san(original_fen, uci_moves):
    board = chess.Board(original_fen)
    ucs = uci_moves.split()
    # discard opponent's setup move
    if ucs:
        first = chess.Move.from_uci(ucs[0])
        if first not in board.legal_moves:
            raise ValueError(f"Illegal setup move {ucs[0]} on FEN {original_fen}")
        board.push(first)
    san_list = []
    for u in ucs[1:]:
        move = chess.Move.from_uci(u)
        if move not in board.legal_moves:
            raise ValueError(f"Illegal puzzle move {u} in position {board.fen()}")
        san_text = board.san(move)
        san_list.append(san_text)
        board.push(move)
    return san_list


def get_to_move_color(original_fen, uci_moves):
    board = chess.Board(original_fen)
    ucs = uci_moves.split()
    if ucs:
        setup = chess.Move.from_uci(ucs[0])
        if setup in board.legal_moves:
            board.push(setup)
    return "White" if board.turn else "Black"


def screenshot_puzzle(puzzle_id, output_path, board_theme, piece_style):
    url = f"https://lichess.org/training/{puzzle_id}?theme={board_theme}&piece={piece_style}"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=800,800")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "cg-board"))
        )
        time.sleep(1)
        driver.execute_script(
            "document.querySelectorAll('square.last-move').forEach(el => el.remove());"
        )
        board = driver.find_element(By.CSS_SELECTOR, "cg-board")
        board.screenshot(output_path)
        print(f"📸 Saved screenshot to: {output_path}")
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
    finally:
        driver.quit()

# === Main ===

if __name__ == "__main__":
    cfg = load_config()
    csv_path = cfg["csv_path"]
    base_output = cfg["output_dir"]
    board_theme = cfg["board_theme"]
    piece_style = cfg["piece_style"]

    # naming & cleanup
    naming_cfg = cfg.get("file_naming", {})
    override_fn = naming_cfg.get("override_filename")
    term = naming_cfg.get("term", "")
    week = naming_cfg.get("week", "")
    template = naming_cfg.get("template", "mintmate_puzzles_{timestamp}.xlsx")
    cleanup = naming_cfg.get("cleanup_screenshots", False)

    # determine base directory & final filename
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    if override_fn:
        final_filename = override_fn
        dir_name = os.path.splitext(override_fn)[0]
    else:
        no_ts = re.sub(r"[\s_-]*\{timestamp\}", "", template)
        final_filename = no_ts.format(term=term, week=week, timestamp=ts)
        dir_name = os.path.splitext(final_filename)[0]
    dir_clean = dir_name.replace(" ", "")

    # create output folder
    os.makedirs(base_output, exist_ok=True)
    out_dir = os.path.join(base_output, dir_clean)
    os.makedirs(out_dir, exist_ok=True)

    # load puzzle data
    df = pd.read_csv(csv_path)

    # setup workbook & answer key
    wb = Workbook()
    answer_ws = wb.create_sheet(title="AnswerKey")
    answer_ws.append(["Puzzle ID","Answer"])
    answer_ws.sheet_state = "hidden"

    max_img_width = 0

    # iterate puzzle sets or default
    puzzle_sets = cfg.get("puzzle_sets")
    if puzzle_sets:
        sets = puzzle_sets
    else:
        sets = [{"sheet_name": "Puzzles", "puzzles": cfg.get("puzzles", [])}]

    for idx, pset in enumerate(sets):
        sheet_name = pset.get("sheet_name", f"Set{idx+1}")
        # create set-specific directory
        sheet_dir = os.path.join(out_dir, sheet_name.replace(" ", ""))
        os.makedirs(sheet_dir, exist_ok=True)

        ws = wb.active if idx == 0 else wb.create_sheet(title=sheet_name)
        ws.title = sheet_name
        ws.append(["Puzzle ID","Type","Rating","To Move","Lichess URL","Screenshot","Student Answer","Correct?"])

        for job in pset.get("puzzles", []):
            theme, lo, hi, cnt = job["type"], job["min_rating"], job["max_rating"], job["count"]
            for _ in range(cnt):
                sub = df[
                    df["Themes"].str.contains(theme, case=False, na=False) &
                    (df["Rating"] >= lo) &
                    (df["Rating"] <= hi)
                ]
                if sub.empty:
                    continue
                p = sub.sample(1).iloc[0]
                pid, fen, moves = p["PuzzleId"], p["FEN"], p["Moves"]
                url = f"https://lichess.org/training/{pid}?theme={board_theme}&piece={piece_style}"
                shot = os.path.join(sheet_dir, f"{pid}.png")

                sol = get_solution_san(fen, moves)
                answer_ws.append([pid, ", ".join(sol)])
                tm = get_to_move_color(fen, moves)
                screenshot_puzzle(pid, shot, board_theme, piece_style)

                ws.append([pid, theme, p["Rating"], tm, url, "", "", ""])
                r = ws.max_row
                with Image.open(shot) as img:
                    w, h = img.size
                max_img_width = max(max_img_width, w)
                ximg = XLImage(shot)
                ximg.width, ximg.height = w, h
                ws.add_image(ximg, f"F{r}")
                ws.row_dimensions[r].height = h * 0.85
                ws.cell(row=r, column=8).value = (
                    f'=IF(G{r}="","",'
                    f'IF(G{r}=VLOOKUP(A{r},AnswerKey!$A:$B,2,FALSE),"✅ Correct","❌ Try again"))'
                )

    # auto-fit columns
    for sheet in wb.worksheets:
        if sheet.title == "AnswerKey":
            continue
        col_lens = {}
        for row in sheet.iter_rows(min_row=1, max_row=sheet.max_row, min_col=1, max_col=sheet.max_column):
            for cell in row:
                val = cell.value if cell.value is not None else ""
                ln = len(str(val))
                col_lens[cell.column] = max(col_lens.get(cell.column, 0), ln)
        if max_img_width > 0:
            col_lens[6] = max(col_lens.get(6, 0), int(max_img_width * 0.13))
        for col, ln in col_lens.items():
            sheet.column_dimensions[get_column_letter(col)].width = ln + 2

    # save spreadsheet
    file_path = os.path.join(out_dir, final_filename)
    wb.save(file_path)
    print(f"📄 Workbook export: {file_path}")

    # optional cleanup screenshot files
    if cleanup:
        for root, dirs, files in os.walk(out_dir):
            for f in files:
                if f.lower().endswith(".png"):
                    os.remove(os.path.join(root, f))
        print("🗑️ Screenshots removed.")
    else:
        print("📸 Screenshots retained.")
