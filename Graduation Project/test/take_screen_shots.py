import pyautogui
import time
import os

def take_screenshots_sha256(interval=5, duration=60, save_folder="screenshots", sha_prefix=None):
    """
    Take screenshots every `interval` seconds for `duration` seconds,
    saving them with a given SHA-256 hash prefix.

    Example filename:
    <sha_prefix>_scr_0.png
    """
    if sha_prefix is None:
        raise ValueError("You must provide a SHA-256 hash as 'sha_prefix'")

    # Create folder if it doesn't exist
    os.makedirs(save_folder, exist_ok=True)

    start_time = time.time()
    count = 0

    while time.time() - start_time < duration:
        filename = os.path.join(save_folder, f"{sha_prefix}_scr_{count}.png")
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        print(f"[{count}] Screenshot saved as {filename}")
        count += 1
        time.sleep(interval)

    print("Finished taking screenshots.")

# Example usage:
my_sha = "563bcf7c914b868ddde73520e9e8d582275f00f57a7346353d34b9f378ec0fae"
take_screenshots_sha256(interval=10, duration=60, sha_prefix=my_sha)

