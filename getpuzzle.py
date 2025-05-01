import pandas as pd
import random
import chess
import chess.pgn
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import tomli
import os

def load_config(path="mintmate_config.toml"):
    with open(path, "rb") as f:
        return tomli.load(f)

config = load_config()

# Global config values
csv_path = config["csv_path"]
output_dir = config["output_dir"]
board_theme = config["board_theme"]
piece_style = config["piece_style"]
puzzle_jobs = config["puzzles"]

# === Helpers ===
def uci_to_san(fen, uci_moves):
    board = chess.Board(fen)
    san_moves = []
    for uci in uci_moves.split():
        move = chess.Move.from_uci(uci)
        san = board.san(move)
        san_moves.append(san)
        board.push(move)
    return san_moves

def adjust_fen_one_move(fen, uci_moves):
    moves = uci_moves.split()
    if len(moves) < 2:
        return fen, moves[0]  # already mate-in-1
    board = chess.Board(fen)
    first_move = chess.Move.from_uci(moves[0])
    board.push(first_move)
    return board.fen(), moves[1]

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
        # Wait for board to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "cg-board"))
        )
        time.sleep(1)  # Just in case

        # Remove move highlights (yellow/blue)
        driver.execute_script("""
            document.querySelectorAll('square.last-move').forEach(el => el.remove());
        """)

        # Screenshot just the board
        board = driver.find_element(By.CSS_SELECTOR, "cg-board")
        board.screenshot(output_path)
        print(f"📸 Saved screenshot to: {output_path}")

    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
    finally:
        driver.quit()


# === LOAD DATA ===
print("📂 Loading puzzle data...")
df = pd.read_csv(csv_path)

for job in puzzle_jobs:
    theme=job["type"]
    min_rating = job["min_rating"]
    max_rating = job["max_rating"]
    count = job["count"]

    print(f"\n🔧 Generating {count} puzzle(s) for '{theme}' [{min_rating}–{max_rating}]")
 

    # === FILTER DATA ===
    filtered = df[
        df['Themes'].str.contains(theme, case=False, na=False) &
        (df['Rating'] >= min_rating) &
        (df['Rating'] <= max_rating)
    ]

    if filtered.empty:
        print("⚠️ No matching puzzles found.")
        continue

    os.makedirs(output_dir, exist_ok=True)

    
    for _ in range(count):
        puzzle = filtered.sample(1).iloc[0]
        puzzle_id = puzzle["PuzzleId"]
        original_fen = puzzle["FEN"]
        uci_moves = puzzle["Moves"]
        lichess_url = f"https://lichess.org/training/{puzzle_id}?theme={board_theme}&piece={piece_style}"

        updated_fen, solving_move = adjust_fen_one_move(original_fen, uci_moves)
        san = uci_to_san(updated_fen, solving_move)[0]

        # Output info
        print(f"✅ Puzzle ID: {puzzle_id}")
        print(f"   Lichess:  {lichess_url}")
        print(f"   FEN:      {updated_fen}")
        print(f"   Move:     {san} ({solving_move})")

        screenshot_path = os.path.join(output_dir, f"{puzzle_id}.png")
        screenshot_puzzle(puzzle_id, screenshot_path, board_theme, piece_style)




# print(f"Found {len(filtered)} puzzles with theme '{THEME}' and rating between {MIN_RATING} and {MAX_RATING}.")

# # === SELECT RANDOM PUZZLE ===
# if not filtered.empty:
#     puzzle = filtered.sample(1).iloc[0]
#     print("\n✅ Puzzle Info:")
#     print(f"ID: {puzzle['PuzzleId']}")
#     print(f"Rating: {puzzle['Rating']}")
#     print(f"Themes: {puzzle['Themes']}")
#     print(f"FEN: {puzzle['FEN']}")
#     print(f"Solution (UCI): {puzzle['Moves']}")
#     print(f"Lichess Game Link: {puzzle['GameUrl']}")
# else:
#     print("❌ No puzzles found with those filters.")

# fen = puzzle['FEN']  # from your filtered puzzle row
# turn = fen.split(' ')[1]

# if turn == 'w':
#     print("White to move")
# else:
#     print("Black to move")
          
# fen = puzzle['FEN']
# uci_moves = puzzle['Moves']
# print("UCI:", uci_moves)

# san_moves = uci_to_san(fen, uci_moves)
# print("SAN:", ' → '.join(san_moves))

# # Split UCI solution into moves
# uci_move_list = uci_moves.split()

# def screenshot_puzzle(puzzle_id, output_path='puzzle.png'):
#     url = f"https://lichess.org/training/{puzzle_id}?theme=blue&piece=kosal"

#     options = Options()
#     options.add_argument("--headless")  # run in background
#     options.add_argument("--window-size=800,800")  # set size
#     options.add_argument("--disable-gpu")
#     options.add_argument("--no-sandbox")

#     driver = webdriver.Chrome(options=options)
#     driver.get(url)

#     # Wait for the board to load
#     time.sleep(3)

#     # Clear last move highlight (blue/yellow squares)
#     driver.execute_script("""
#     document.querySelectorAll('square.last-move').forEach(el => el.remove());
#     """)

#     try:
#         board = driver.find_element("css selector", "cg-board")
#         board.screenshot(output_path)
#         print(f"🖼️ Screenshot saved to: {output_path}")
#     except Exception as e:
#         print(f"❌ Screenshot failed: {e}")
#     finally:
#         driver.quit()

# # Only adjust if there are at least 2 moves
# # if len(uci_move_list) >= 2:
# #     # Start from the original FEN and apply the first move
# #     board = chess.Board(fen)
# #     first_move = chess.Move.from_uci(uci_move_list[0])
# #     board.push(first_move)

# #     # New FEN is after the first move has been made
# #     updated_fen = board.fen()
# #     second_move = uci_move_list[1]
    
# #     # Convert the second move to SAN
# #     san_mate_move = board.san(chess.Move.from_uci(second_move))

# #     print("\n🎯 Adjusted Puzzle (Mate in 1):")
# #     print(f"New FEN: {updated_fen}")
# #     print(f"To move: {'White' if board.turn == chess.WHITE else 'Black'}")
# #     print(f"Correct Move (UCI): {second_move}")
# #     print(f"Correct Move (SAN): {san_mate_move}")
# # else:
# #     print("⚠️ Puzzle has only one move — already mate in 1 from the original FEN.")

# # Get puzzle ID and define output image path
# puzzle_id = puzzle['PuzzleId']
# output_image = f"{puzzle_id}.png"

# # Take screenshot
# screenshot_puzzle(puzzle_id, output_image)