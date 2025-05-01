import tomli
import pandas as pd
import random
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

def get_to_move_color(fen):
    return "White" if fen.split()[1] == "w" else "Black"

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
    # load config + data
    cfg         = load_config()
    csv_path    = cfg["csv_path"]
    output_dir  = cfg["output_dir"]
    board_theme = cfg["board_theme"]
    piece_style = cfg["piece_style"]
    puzzle_jobs = cfg["puzzles"]

    df = pd.read_csv(csv_path)
    os.makedirs(output_dir, exist_ok=True)

    # prepare teacher workbook
    ts              = datetime.now().strftime("%Y-%m-%d_%H-%M")
    teacher_wb      = Workbook()
    teacher_ws      = teacher_wb.active
    teacher_ws.title= "Puzzles"
    headers         = ["Puzzle ID","Type","Rating","Answer","To Move","Lichess URL","Screenshot","FEN"]
    teacher_ws.append(headers)

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
            p = sub.sample(1).iloc[0]
            pid, fen, moves = p["PuzzleId"], p["FEN"], p["Moves"]
            url = f"https://lichess.org/training/{pid}?theme={board_theme}&piece={piece_style}"
            shot = os.path.join(output_dir, f"{pid}.png")

            sol = get_solution_san(fen, moves)
            tm  = get_to_move_color(fen)
            screenshot_puzzle(pid, shot, board_theme, piece_style)

            # append teacher row
            teacher_ws.append([
                pid, theme, p["Rating"],
                ", ".join(sol), tm,
                url, "", fen
            ])

            # embed teacher image
            with Image.open(shot) as img:
                w, h = img.size
            max_img_width = max(max_img_width, w)
            ximg = XLImage(shot)
            ximg.width, ximg.height = w, h
            cell = f"G{teacher_ws.max_row}"
            teacher_ws.add_image(ximg, cell)
            teacher_ws.row_dimensions[teacher_ws.max_row].height = h * 0.85

            screenshot_paths.append(shot)

    # auto-fit teacher columns
    col_lengths = {}
    for row in teacher_ws.iter_rows(min_row=1, max_row=teacher_ws.max_row, min_col=1, max_col=teacher_ws.max_column):
        for cell in row:
            ln = len(str(cell.value)) if cell.value is not None else 0
            col_lengths[cell.column] = max(col_lengths.get(cell.column, 0), ln)
    # screenshot col = pixel→excel units ~0.13
    if max_img_width:
        col_lengths[7] = max(col_lengths.get(7, 0), int(max_img_width * 0.13))
    for col, ln in col_lengths.items():
        teacher_ws.column_dimensions[get_column_letter(col)].width = ln + 2

    # save teacher file
    teacher_path = os.path.join(output_dir, f"mintmate_puzzles_{ts}_teacher.xlsx")
    teacher_wb.save(teacher_path)
    print(f"\n📄 Teacher export: {teacher_path}")

    # ——— student workbook ———
    student_wb       = Workbook()
    student_ws       = student_wb.active
    student_ws.title = "Puzzles"
    student_headers  = ["Puzzle ID","Type","Rating","To Move","Lichess URL","Screenshot"]
    student_ws.append(student_headers)

    # rebuild rows & embed images
    for i, shot in enumerate(screenshot_paths, start=2):
        pid  = teacher_ws.cell(row=i, column=1).value
        theme= teacher_ws.cell(row=i, column=2).value
        rat  = teacher_ws.cell(row=i, column=3).value
        tm   = teacher_ws.cell(row=i, column=5).value
        url  = teacher_ws.cell(row=i, column=6).value

        student_ws.append([pid, theme, rat, tm, url, ""])
        with Image.open(shot) as img:
            w, h = img.size
        simg = XLImage(shot)
        simg.width, simg.height = w, h
        loc = f"F{student_ws.max_row}"
        student_ws.add_image(simg, loc)
        student_ws.row_dimensions[student_ws.max_row].height = h * 0.85

    # auto-fit student columns
    stud_lengths = {}
    for row in student_ws.iter_rows(min_row=1, max_row=student_ws.max_row, min_col=1, max_col=student_ws.max_column):
        for cell in row:
            ln = len(str(cell.value)) if cell.value is not None else 0
            stud_lengths[cell.column] = max(stud_lengths.get(cell.column, 0), ln)
    if max_img_width:
        stud_lengths[6] = max(stud_lengths.get(6, 0), int(max_img_width * 0.13))
    for col, ln in stud_lengths.items():
        student_ws.column_dimensions[get_column_letter(col)].width = ln + 2

    # save student file
    student_path = os.path.join(output_dir, f"mintmate_puzzles_{ts}_student.xlsx")
    student_wb.save(student_path)
    print(f"🧑‍🎓 Student export: {student_path}")

    # ——— purge screenshots ———
    for f in os.listdir(output_dir):
        if f.lower().endswith(".png"):
            os.remove(os.path.join(output_dir, f))
    print("🗑️ All screenshots removed from puzzle folder.")
