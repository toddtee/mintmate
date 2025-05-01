import pandas as pd
import random
import chess
import chess.pgn
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# === CONFIGURATION ===
CSV_FILE = 'lichess_db_puzzle.csv'  # Decompressed chess database
THEME = 'mateIn1'                      # Set the theme 'mateIn2', 'skewer', etc.
MIN_RATING = 600 
MAX_RATING = 700 

def uci_to_san(fen, uci_moves):
    board = chess.Board(fen)
    san_moves = []

    for uci in uci_moves.split():
        move = chess.Move.from_uci(uci)
        san = board.san(move)
        san_moves.append(san)
        board.push(move)

    return san_moves


# === LOAD DATA ===
print("Loading puzzle data...")
df = pd.read_csv(CSV_FILE)

# === FILTER DATA ===
filtered = df[
    df['Themes'].str.contains(THEME, case=False, na=False) &
    (df['Rating'] >= MIN_RATING) &
    (df['Rating'] <= MAX_RATING)
]

print(f"Found {len(filtered)} puzzles with theme '{THEME}' and rating between {MIN_RATING} and {MAX_RATING}.")

# === SELECT RANDOM PUZZLE ===
if not filtered.empty:
    puzzle = filtered.sample(1).iloc[0]
    print("\n✅ Puzzle Info:")
    print(f"ID: {puzzle['PuzzleId']}")
    print(f"Rating: {puzzle['Rating']}")
    print(f"Themes: {puzzle['Themes']}")
    print(f"FEN: {puzzle['FEN']}")
    print(f"Solution (UCI): {puzzle['Moves']}")
    print(f"Lichess Game Link: {puzzle['GameUrl']}")
else:
    print("❌ No puzzles found with those filters.")

fen = puzzle['FEN']  # from your filtered puzzle row
turn = fen.split(' ')[1]

if turn == 'w':
    print("White to move")
else:
    print("Black to move")
          
fen = puzzle['FEN']
uci_moves = puzzle['Moves']
print("UCI:", uci_moves)

san_moves = uci_to_san(fen, uci_moves)
print("SAN:", ' → '.join(san_moves))

# Split UCI solution into moves
uci_move_list = uci_moves.split()

def screenshot_puzzle(puzzle_id, output_path='puzzle.png'):
    url = f"https://lichess.org/training/{puzzle_id}?theme=blue&piece=kosal"

    options = Options()
    options.add_argument("--headless")  # run in background
    options.add_argument("--window-size=800,800")  # set size
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Wait for the board to load
    time.sleep(3)

    # Clear last move highlight (blue/yellow squares)
    driver.execute_script("""
    document.querySelectorAll('square.last-move').forEach(el => el.remove());
    """)

    try:
        board = driver.find_element("css selector", "cg-board")
        board.screenshot(output_path)
        print(f"🖼️ Screenshot saved to: {output_path}")
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
    finally:
        driver.quit()

# Only adjust if there are at least 2 moves
# if len(uci_move_list) >= 2:
#     # Start from the original FEN and apply the first move
#     board = chess.Board(fen)
#     first_move = chess.Move.from_uci(uci_move_list[0])
#     board.push(first_move)

#     # New FEN is after the first move has been made
#     updated_fen = board.fen()
#     second_move = uci_move_list[1]
    
#     # Convert the second move to SAN
#     san_mate_move = board.san(chess.Move.from_uci(second_move))

#     print("\n🎯 Adjusted Puzzle (Mate in 1):")
#     print(f"New FEN: {updated_fen}")
#     print(f"To move: {'White' if board.turn == chess.WHITE else 'Black'}")
#     print(f"Correct Move (UCI): {second_move}")
#     print(f"Correct Move (SAN): {san_mate_move}")
# else:
#     print("⚠️ Puzzle has only one move — already mate in 1 from the original FEN.")

# Get puzzle ID and define output image path
puzzle_id = puzzle['PuzzleId']
output_image = f"{puzzle_id}.png"

# Take screenshot
screenshot_puzzle(puzzle_id, output_image)