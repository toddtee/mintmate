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


def uci_to_san(fen, uci_moves):
    board = chess.Board(fen)
    san = []
    for u in uci_moves.split():
        move = chess.Move.from_uci(u)
        san.append(board.san(move))
        board.push(move)
    return san


def get_solution_san(original_fen, uci_moves):
    ucs = uci_moves.split()
    if len(ucs) <= 1:
        return uci_to_san(original_fen, uci_moves)
    board = chess.Board(original_fen)
    board.push(chess.Move.from_uci(ucs[0]))
    return [board.san(chess.Move.from_uci(u)) for u in ucs[1:]]


def get_to_move_color(fen, uci_moves):
    # determine side to move after the initial setup move
    board = chess.Board(fen)
    ucs = uci_moves.split()
    if ucs:
        # discard the first setup move
        board.push(chess.Move.from_uci(ucs[0]))
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
        driver.execute_script("""
            document.querySelectorAll('square.last-move').forEach(el => el.remove());
        """)
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

    # prepare workbook with hidden AnswerKey
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

    # generate puzzles
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
            p     = sub.sample(1).iloc[0]
            pid   = p["PuzzleId"]
            fen   = p["FEN"]
            moves = p["Moves"]
            url   = f"https://lichess.org/training/{pid}?theme={board_theme}&piece={piece_style}"
            shot  = os.path.join(output_dir, f"{pid}.png")

            sol_list = get_solution_san(fen, moves)
            sol_str  = ", ".join(sol_list)
            tm       = get_to_move_color(fen, moves)
            screenshot_puzzle(pid, shot, board_theme, piece_style)

            # record answer in AnswerKey
            answer_ws.append([pid, sol_str])

            # append to main sheet
            main_ws.append([pid, theme, p["Rating"], tm, url, "", "", ""])

            # embed screenshot in F
            row = main_ws.max_row
            with Image.open(shot) as img:
                w, h = img.size
            max_img_width = max(max_img_width, w)
            ximg = XLImage(shot)
            ximg.width, ximg.height = w, h
            cell = f"F{row}"
            main_ws.add_image(ximg, cell)
            main_ws.row_dimensions[row].height = h * 0.85
            screenshot_paths.append(shot)

            # add correctness formula in H
            main_ws.cell(row=row, column=8).value = f'=IF(G{row}=VLOOKUP(A{row},AnswerKey!$A:$B,2,FALSE),"✔ Correct","✘ Try again")'

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

    # save workbook
    file_path = os.path.join(output_dir, f"mintmate_puzzles_{ts}.xlsx")
    wb.save(file_path)
    print(f"\n📄 Workbook export: {file_path}")

    # purge screenshots
    for f in os.listdir(output_dir):
        if f.lower().endswith(".png"):
            os.remove(os.path.join(output_dir, f))
    print("🗑️ All screenshots removed from puzzle folder.")
