# TXT Transform Studio

A clean, standalone desktop app for transforming TXT transcript files into organized outlines using ChatGPT.

## Features

- **Modern Tkinter GUI** with dark/light theme toggle (Catppuccin palette)
- **Model selection** — GPT-4.1, GPT-4.1 Mini, GPT-4.1 Nano
- **Temperature & Top-P sliders** for fine-tuning output creativity
- **Inline prompt editor** with preset management
- **Output format** — save as `.txt` or `.md`
- **Progress bar** during processing
- **Status bar** showing API key status, current model, and file count
- **Clipboard integration** — processed output is auto-copied

## Setup

```bash
# Clone the repo
git clone https://github.com/tanurus/txt-transform-studio.git
cd txt-transform-studio

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env with your API key
copy .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Launch
python main.py
```

## How It Works

1. Select a folder containing `.txt` transcript files
2. Choose files from the list
3. Configure model, temperature, top-p, and prompt
4. Click **Process Selected** — the app sends each file to ChatGPT
5. The organized outline is saved to `Processed Database/` and copied to clipboard

## Project Structure

```
main.py           — Entry point
gui.py            — Modern Tkinter GUI with customization panel
config.py         — Settings, model catalog, prompt presets
file_ops.py       — File listing, processing, clipboard operations
openai_client.py  — OpenAI API wrapper
SYSTEM_PROMPT.txt — Default transformation prompt
```
