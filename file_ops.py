# File and clipboard operations
import os
import glob
import pyperclip
from datetime import datetime
from config import get_text_folder, get_model_settings, get_prompt, PROCESSED_FOLDER
from openai_client import ask_chatgpt


def get_recent_texts(n=30):
    """Return up to *n* .txt files sorted by modification time (newest first)."""
    pattern = os.path.join(get_text_folder(), "*.txt")
    entries = []
    for f in glob.glob(pattern):
        try:
            mtime = os.path.getmtime(f)
            ctime = os.path.getctime(f)
            entries.append((f, mtime, ctime))
        except OSError:
            continue
    entries.sort(key=lambda x: x[1], reverse=True)
    return entries[:n]


def get_processed_path(original_path: str, extension: str = ".txt") -> str:
    """Map an original file path to its processed output path."""
    base = os.path.basename(original_path)
    name, _ = os.path.splitext(base)
    return os.path.join(PROCESSED_FOLDER, f"{name}{extension}")


def process_file(path, log_fn, model=None, prompt_id=None, prompt_text=None,
                 temperature=None, top_p=None, output_format=None):
    """Process a single file through ChatGPT and save the result.

    *log_fn* is a callable(str) that appends a message to the UI log.
    Returns True on success, False on failure.
    """
    settings = get_model_settings()
    model = model or settings["model"]
    temperature = temperature if temperature is not None else settings["temperature"]
    top_p = top_p if top_p is not None else settings["top_p"]
    output_format = output_format or settings.get("output_format", ".txt")

    if prompt_text is None:
        prompt_text = get_prompt(prompt_id).get("content", "")

    base = os.path.basename(path)
    name, _ = os.path.splitext(base)

    log_fn(f"\U0001f4c4 Selected file: {base}")
    log_fn("\U0001f4dd Reading transcript from text file\u2026")
    try:
        with open(path, "r", encoding="utf-8") as tf:
            transcript = tf.read()
    except Exception as e:
        log_fn(f"\u26a0\ufe0f Read error: {e}")
        return False

    log_fn(f"\u2705 Loaded transcript ({len(transcript):,} chars)")
    log_fn(f"\U0001f4ac Sending to {model} (temp={temperature}, top_p={top_p})\u2026")

    try:
        outline, stats = ask_chatgpt(
            transcript,
            model=model,
            system_prompt=prompt_text,
            temperature=temperature,
            top_p=top_p,
        )
    except Exception as e:
        log_fn(f"\u26a0\ufe0f ChatGPT error: {e}")
        return False

    # Copy to clipboard
    log_fn("\U0001f4e5 Copying outline to clipboard\u2026")
    try:
        pyperclip.copy(outline)
    except Exception:
        log_fn("\u26a0\ufe0f Clipboard copy failed (pyperclip issue).")

    # Save to processed folder
    outfile = os.path.join(PROCESSED_FOLDER, f"{name}{output_format}")
    try:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(outline)
        log_fn(f"\U0001f4be Saved outline to: {outfile}")
    except Exception as e:
        log_fn(f"\u26a0\ufe0f File save error: {e}")
        return False

    log_fn("\u2705 Done! Outline is now in your clipboard.")
    log_fn("")
    log_fn("\U0001f4ca Usage Details:")
    log_fn(f"   \u2022 Model: {stats['model']}")
    log_fn(f"   \u2022 Prompt tokens: {stats['prompt_tokens']:,}")
    log_fn(f"   \u2022 Completion tokens: {stats['completion_tokens']:,}")
    log_fn(f"   \u2022 Total tokens: {stats['total_tokens']:,}")
    log_fn(f"   \u2022 Response time: {stats['response_time']}s")
    log_fn("\u2014" * 40)
    return True


def open_file(path: str, log_fn) -> None:
    """Open a file with the OS default application."""
    try:
        if not os.path.exists(path):
            log_fn(f"\u26a0\ufe0f File not found: {path}")
            return
        os.startfile(path)
        log_fn(f"\U0001f4c2 Opened: {os.path.basename(path)}")
    except Exception as e:
        log_fn(f"\u26a0\ufe0f Could not open file: {e}")


def open_processed_for(original_path: str, log_fn, output_format: str = ".txt") -> None:
    processed = get_processed_path(original_path, output_format)
    open_file(processed, log_fn)


def copy_processed_for(original_path: str, log_fn, output_format: str = ".txt") -> None:
    processed = get_processed_path(original_path, output_format)
    try:
        if not os.path.exists(processed):
            log_fn(f"\u26a0\ufe0f Processed file not found: {processed}")
            return
        with open(processed, "r", encoding="utf-8") as f:
            content = f.read()
        if not content:
            log_fn(f"\u26a0\ufe0f Processed file is empty: {processed}")
            return
        pyperclip.copy(content)
        log_fn(f"\U0001f4cb Copied processed outline for: {os.path.basename(original_path)}")
    except Exception as e:
        log_fn(f"\u26a0\ufe0f Could not copy processed file: {e}")
