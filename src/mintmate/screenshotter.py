# src/mintmate/screenshotter.py

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def screenshot_puzzle(
    puzzle_id: str,
    output_path: str,
    board_theme: str,
    piece_style: str,
    log  # new parameter
):
    """
    Capture a screenshot of a Lichess training puzzle board and save it to output_path.
    Uses the provided `log` callable for feedback.
    """
    log(f"📸 Capturing screenshot for puzzle {puzzle_id}")
    url = (
        f"https://lichess.org/training/{puzzle_id}"
        f"?theme={board_theme}&piece={piece_style}"
    )
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=800,800")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "cg-board"))
        )
        time.sleep(1)
        driver.execute_script(
            "document.querySelectorAll('square.last-move').forEach(el => el.remove());"
        )
        board = driver.find_element(By.CSS_SELECTOR, "cg-board")
        board.screenshot(output_path)
        log(f"✅ Screenshot saved to: {output_path}")
    except Exception as e:
        log(f"❌ Failed to capture puzzle {puzzle_id}: {e}")
        raise
    finally:
        driver.quit()
