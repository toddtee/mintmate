import tomli
import pandas as pd
import os
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
    """
    Discard the first UCI setup move, then convert the remaining UCI moves into SAN.
    Raises an exception if any move is illegal.
    """
    board = chess.Board(original_fen)
    ucs = uci_moves.split()
    # play the opponent's setup move
    if ucs:
        first = chess.Move.from_uci(ucs[0])
        if first not in board.legal_moves:
            raise ValueError(f"Illegal setup move {ucs[0]} on FEN {original_fen}")
        board.push(first)
    san_list = []
    # convert and play the solver moves
    for u in ucs[1:]:
        move = chess.Move.from_uci(u)
        if move not in board.legal_moves:
            raise ValueError(f"Illegal puzzle move {u} in position {board.fen()}")
        san_text = board.san(move)
        san_list.append(san_text)
        board.push(move)
    return san_list


def get_to_move_color(original_fen, uci_moves):
    """
    Return 'White' or 'Black' for the solver's turn: after discarding the setup move.
    """
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
    cfg         = load_config()
    csv_path    = cfg["csv_path"]
    output_dir  = cfg["output_dir"]
    board_theme = cfg["board_theme"]
    piece_style = cfg["piece_style"]
    puzzle_jobs = cfg["puzzles"]

    df = pd.read_csv(csv_path)
    os.makedirs(output_dir, exist_ok=True)

    ts        = datetime.now().strftime("%Y-%m-%d_%H-%M")
    wb        = Workbook()
    main_ws   = wb.active
    main_ws.title = "Puzzles"
    headers   = ["Puzzle ID","Type","Rating","To Move","Lichess URL","Screenshot","Student Answer","Correct?"]
    main_ws.append(headers)

    answer_ws = wb.create_sheet(title="AnswerKey")
    answer_ws.append(["Puzzle ID","Answer"])
    answer_ws.sheet_state = "hidden"

    screenshot_paths = []
    max_img_width    = 0

    for job in puzzle_jobs:
        theme, lo, hi, cnt = job["type"], job["min_rating"], job["max_rating"], job["count"]
        print(f"\n🎯 Generating {cnt} '{theme}' puzzles [{lo}–{hi}]")
        sub = df[
            df["Themes"].str.contains(theme, case=False, na=False) &
            (df["Rating"] >= lo) &
            (df["Rating"] <= hi)
        ]
        if sub.empty:
            print("⚠️ No puzzles for this config.")
            continue

        for _ in range(cnt):
            p       = sub.sample(1).iloc[0]
            pid     = p["PuzzleId"]
            fen     = p["FEN"]
            moves   = p["Moves"]
            url     = f"https://lichess.org/training/{pid}?theme={board_theme}&piece={piece_style}"
            shot    = os.path.join(output_dir, f"{pid}.png")

            sol_list = get_solution_san(fen, moves)
            sol_str  = ", ".join(sol_list)
            tm       = get_to_move_color(fen, moves)
            screenshot_puzzle(pid, shot, board_theme, piece_style)

            answer_ws.append([pid, sol_str])
            main_ws.append([pid, theme, p["Rating"], tm, url, "", "", ""])

            row = main_ws.max_row
            with Image.open(shot) as img:
                w, h = img.size
            max_img_width = max(max_img_width, w)
            ximg = XLImage(shot)
            ximg.width, ximg.height = w, h
            main_ws.add_image(ximg, f"F{row}")
            main_ws.row_dimensions[row].height = h * 0.85
            screenshot_paths.append(shot)

            main_ws.cell(row=row, column=8).value = (
                f'=IF(G{row}="","",'
                f'IF(G{row}=VLOOKUP(A{row},AnswerKey!$A:$B,2,FALSE),"✅ Correct","❌ Try again"))'
            )

    # auto-fit columns
    col_lengths = {}
    for row in main_ws.iter_rows(min_row=1, max_row=main_ws.max_row, min_col=1, max_col=main_ws.max_column):
        for cell in row:
            ln = len(str(cell.value)) if cell.value is not None else 0
            col_lengths[cell.column] = max(col_lengths.get(cell.column, 0), ln)
    if max_img_width:
        col_lengths[6] = max(col_lengths.get(6, 0), int(max_img_width * 0.13))
    for col, ln in col_lengths.items():
        main_ws.column_dimensions[get_column_letter(col)].width = ln + 2

    file_path = os.path.join(output_dir, f"mintmate_puzzles_{ts}.xlsx")
    wb.save(file_path)
    print(f"\n📄 Workbook export: {file_path}")

    for f in os.listdir(output_dir):
        if f.lower().endswith(".png"):
            os.remove(os.path.join(output_dir, f))
    print("🗑️ All screenshots removed from puzzle folder.")
