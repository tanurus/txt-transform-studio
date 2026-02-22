# --------------------------------------------------------------------------- #
#  gui.py — Modern Transform GUI with customization panel                      #
# --------------------------------------------------------------------------- #
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from tkinter.scrolledtext import ScrolledText
import threading
from datetime import datetime
import os

from file_ops import (
    get_recent_texts,
    process_file,
    open_file,
    open_processed_for,
    copy_processed_for,
    get_processed_path,
)
from config import (
    get_text_folder,
    set_text_folder,
    get_model_catalog,
    get_model_settings,
    set_model_settings,
    get_prompt_presets,
    get_prompt,
    get_default_prompt_id,
    set_default_prompt_id,
    upsert_prompt,
    SUPPORTED_MODELS,
    get_theme,
    set_theme,
)
from openai_client import is_configured

# -- Theme palettes --------------------------------------------------------- #
THEMES = {
    "dark": {
        "bg":           "#1e1e2e",
        "bg_alt":       "#181825",
        "surface":      "#313244",
        "surface_hl":   "#45475a",
        "text":         "#cdd6f4",
        "text_dim":     "#a6adc8",
        "accent":       "#89b4fa",
        "accent_hover": "#74c7ec",
        "accent_press": "#b4befe",
        "green":        "#a6e3a1",
        "red":          "#f38ba8",
        "yellow":       "#f9e2af",
        "border":       "#585b70",
        "tree_bg":      "#1e1e2e",
        "tree_fg":      "#cdd6f4",
        "tree_sel_bg":  "#45475a",
        "tree_sel_fg":  "#cdd6f4",
        "log_bg":       "#11111b",
        "log_fg":       "#a6adc8",
        "entry_bg":     "#313244",
        "entry_fg":     "#cdd6f4",
        "btn_fg":       "#1e1e2e",
    },
    "light": {
        "bg":           "#eff1f5",
        "bg_alt":       "#e6e9ef",
        "surface":      "#ccd0da",
        "surface_hl":   "#bcc0cc",
        "text":         "#4c4f69",
        "text_dim":     "#6c6f85",
        "accent":       "#1e66f5",
        "accent_hover": "#2a6ef5",
        "accent_press": "#0550d4",
        "green":        "#40a02b",
        "red":          "#d20f39",
        "yellow":       "#df8e1d",
        "border":       "#9ca0b0",
        "tree_bg":      "#eff1f5",
        "tree_fg":      "#4c4f69",
        "tree_sel_bg":  "#bcc0cc",
        "tree_sel_fg":  "#4c4f69",
        "log_bg":       "#e6e9ef",
        "log_fg":       "#5c5f77",
        "entry_bg":     "#ccd0da",
        "entry_fg":     "#4c4f69",
        "btn_fg":       "#ffffff",
    },
}

FONT_FAMILY = "Segoe UI"
MONO_FAMILY = "Cascadia Code"


# -- Helpers ----------------------------------------------------------------- #

def _apply_theme(root, style, theme_name):
    """Apply the full colour palette to the root window and ttk styles."""
    t = THEMES[theme_name]

    root.configure(bg=t["bg"])

    # --- ttk styles ---
    style.configure(".", background=t["bg"], foreground=t["text"],
                     font=(FONT_FAMILY, 10))

    # Treeview
    style.configure("Treeview",
                     background=t["tree_bg"], foreground=t["tree_fg"],
                     fieldbackground=t["tree_bg"],
                     rowheight=28, font=(FONT_FAMILY, 10),
                     borderwidth=0)
    style.map("Treeview",
              background=[("selected", t["tree_sel_bg"])],
              foreground=[("selected", t["tree_sel_fg"])])
    style.configure("Treeview.Heading",
                     background=t["surface"], foreground=t["text"],
                     font=(FONT_FAMILY, 10, "bold"), relief="flat")
    style.map("Treeview.Heading",
              background=[("active", t["surface_hl"])])

    # Buttons
    style.configure("App.TButton",
                     font=(FONT_FAMILY, 9, "bold"), padding=(12, 5),
                     background=t["surface"], foreground=t["text"])
    style.map("App.TButton",
              background=[("active", t["surface_hl"]), ("pressed", t["border"])],
              foreground=[("disabled", t["text_dim"])])

    style.configure("Accent.TButton",
                     font=(FONT_FAMILY, 9, "bold"), padding=(14, 5),
                     background=t["accent"], foreground=t["btn_fg"])
    style.map("Accent.TButton",
              background=[("active", t["accent_hover"]), ("pressed", t["accent_press"])],
              foreground=[("disabled", t["text_dim"])])

    # Labels, Frames, Notebooks
    style.configure("TLabel", background=t["bg"], foreground=t["text"],
                     font=(FONT_FAMILY, 10))
    style.configure("TFrame", background=t["bg"])
    style.configure("TLabelframe", background=t["bg"], foreground=t["text"],
                     font=(FONT_FAMILY, 10, "bold"))
    style.configure("TLabelframe.Label", background=t["bg"], foreground=t["accent"],
                     font=(FONT_FAMILY, 10, "bold"))
    style.configure("TNotebook", background=t["bg"])
    style.configure("TNotebook.Tab", background=t["surface"], foreground=t["text"],
                     padding=(12, 4), font=(FONT_FAMILY, 9))
    style.map("TNotebook.Tab",
              background=[("selected", t["accent"])],
              foreground=[("selected", t["btn_fg"])])

    # Combobox
    style.configure("TCombobox",
                     fieldbackground=t["entry_bg"], foreground=t["entry_fg"],
                     background=t["surface"], arrowcolor=t["accent"],
                     font=(FONT_FAMILY, 10))
    style.map("TCombobox",
              fieldbackground=[("readonly", t["entry_bg"])],
              foreground=[("readonly", t["entry_fg"])])

    # Scale
    style.configure("TScale", background=t["bg"], troughcolor=t["surface"],
                     sliderthickness=18)

    # Progressbar
    style.configure("Horizontal.TProgressbar",
                     background=t["accent"], troughcolor=t["surface"],
                     thickness=6)

    # Scrollbar
    style.configure("Vertical.TScrollbar",
                     background=t["surface"], troughcolor=t["bg"],
                     arrowcolor=t["text_dim"])

    return t


# =========================================================================== #
#  create_gui                                                                  #
# =========================================================================== #

def create_gui():
    root = tk.Tk()
    root.title("TXT Transform Studio")
    root.geometry("1060x780")
    root.minsize(860, 600)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    current_theme = get_theme()
    t = _apply_theme(root, style, current_theme)

    # -- Shared state ------------------------------------------------------- #
    recent_files: list = []
    processing_count = tk.IntVar(value=0)
    model_settings = get_model_settings()

    # -- Theme toggle ------------------------------------------------------- #
    def toggle_theme():
        nonlocal current_theme, t
        current_theme = "light" if current_theme == "dark" else "dark"
        set_theme(current_theme)
        t = _apply_theme(root, style, current_theme)
        for w in (log_box, prompt_editor):
            w.configure(bg=t["log_bg"], fg=t["log_fg"],
                        insertbackground=t["accent"],
                        selectbackground=t["accent"], selectforeground=t["btn_fg"])
        status_bar.configure(bg=t["bg_alt"], fg=t["text_dim"])
        for child in _all_tk_frames:
            child.configure(bg=t["bg"])
        theme_btn.configure(text="Light" if current_theme == "dark" else "Dark")

    # -- Top bar ------------------------------------------------------------ #
    top_bar = tk.Frame(root, bg=t["bg"])
    top_bar.pack(fill="x", padx=12, pady=(10, 0))

    title_lbl = tk.Label(top_bar, text="TXT Transform Studio",
                          font=(FONT_FAMILY, 16, "bold"),
                          bg=t["bg"], fg=t["accent"])
    title_lbl.pack(side="left")

    theme_btn = ttk.Button(
        top_bar,
        text="Light" if current_theme == "dark" else "Dark",
        command=toggle_theme,
        style="App.TButton",
    )
    theme_btn.pack(side="right")

    # -- Main paned window (left: files+log  |  right: settings) ------------ #
    paned = ttk.PanedWindow(root, orient="horizontal")
    paned.pack(fill="both", expand=True, padx=12, pady=8)

    left_frame = ttk.Frame(paned)
    right_frame = ttk.Frame(paned)
    paned.add(left_frame, weight=3)
    paned.add(right_frame, weight=1)

    # ===================================================================== #
    #  LEFT PANEL                                                            #
    # ===================================================================== #

    # Folder row
    folder_frame = ttk.Frame(left_frame)
    folder_frame.pack(fill="x", pady=(0, 4))
    folder_var = tk.StringVar(value=get_text_folder())
    ttk.Label(folder_frame, text="Folder:", font=(FONT_FAMILY, 10, "bold")).pack(side="left")
    folder_lbl = ttk.Label(folder_frame, textvariable=folder_var, font=(FONT_FAMILY, 9))
    folder_lbl.pack(side="left", padx=(6, 0), fill="x", expand=True)
    ttk.Button(folder_frame, text="Change...", command=lambda: choose_folder(),
               style="App.TButton").pack(side="right")

    # Treeview
    tree_frame = ttk.Frame(left_frame)
    tree_frame.pack(fill="both", expand=True)
    cols = ("Filename", "Modified", "Created", "Processed")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=14)
    for col in cols:
        tree.heading(col, text=col)
        if col == "Filename":
            tree.column(col, width=240, anchor="w")
        elif col == "Processed":
            tree.column(col, width=80, anchor="center")
        else:
            tree.column(col, width=140, anchor="w")
    tree.pack(side="left", fill="both", expand=True)
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    vsb.pack(side="right", fill="y")
    tree.configure(yscrollcommand=vsb.set)

    # Action buttons
    btn_bar = ttk.Frame(left_frame)
    btn_bar.pack(fill="x", pady=6)
    ttk.Button(btn_bar, text="Refresh", command=lambda: refresh_list(),
               style="App.TButton").pack(side="left", padx=(0, 4))
    ttk.Button(btn_bar, text="Add File", command=lambda: add_file(),
               style="App.TButton").pack(side="left", padx=(0, 4))
    ttk.Button(btn_bar, text="Select All", command=lambda: select_all(),
               style="App.TButton").pack(side="left", padx=(0, 4))
    ttk.Button(btn_bar, text="Open Original", command=lambda: open_selected_original(),
               style="App.TButton").pack(side="left", padx=(0, 4))
    ttk.Button(btn_bar, text="Copy Processed", command=lambda: copy_selected_processed(),
               style="App.TButton").pack(side="left", padx=(0, 4))

    process_btn = ttk.Button(btn_bar, text="Process Selected",
                              command=lambda: process_selected(),
                              style="Accent.TButton")
    process_btn.pack(side="right")

    # Progress bar
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(left_frame, variable=progress_var,
                                    maximum=100, mode="indeterminate",
                                    style="Horizontal.TProgressbar")

    # Log area
    log_label = ttk.Label(left_frame, text="Activity Log",
                           font=(FONT_FAMILY, 10, "bold"))
    log_label.pack(anchor="w", pady=(4, 2))

    log_box = ScrolledText(left_frame, wrap=tk.WORD,
                            font=(MONO_FAMILY, 9),
                            bg=t["log_bg"], fg=t["log_fg"],
                            insertbackground=t["accent"],
                            selectbackground=t["accent"],
                            selectforeground=t["btn_fg"],
                            relief="flat", bd=0, padx=8, pady=6,
                            height=10)
    log_box.pack(fill="both", expand=True)

    # ===================================================================== #
    #  RIGHT PANEL                                                           #
    # ===================================================================== #

    # Model settings
    model_frame = ttk.LabelFrame(right_frame, text="  Model Settings  ", padding=8)
    model_frame.pack(fill="x", pady=(0, 8))

    ttk.Label(model_frame, text="Model").pack(anchor="w")
    model_ids = list(SUPPORTED_MODELS)
    model_names = {m["id"]: m["name"] for m in get_model_catalog()}
    model_display = [f"{model_names.get(mid, mid)}" for mid in model_ids]
    model_var = tk.StringVar(value=model_display[model_ids.index(model_settings["model"])]
                              if model_settings["model"] in model_ids else model_display[0])
    model_combo = ttk.Combobox(model_frame, textvariable=model_var,
                                values=model_display, state="readonly", width=22)
    model_combo.pack(fill="x", pady=(2, 8))

    # Temperature
    ttk.Label(model_frame, text="Temperature").pack(anchor="w")
    temp_var = tk.DoubleVar(value=model_settings["temperature"])
    temp_label = ttk.Label(model_frame, text=f"{temp_var.get():.2f}")
    temp_label.pack(anchor="e")
    temp_scale = ttk.Scale(model_frame, from_=0.0, to=2.0, variable=temp_var,
                            orient="horizontal",
                            command=lambda v: temp_label.configure(text=f"{float(v):.2f}"))
    temp_scale.pack(fill="x", pady=(0, 8))

    # Top P
    ttk.Label(model_frame, text="Top P").pack(anchor="w")
    top_p_var = tk.DoubleVar(value=model_settings["top_p"])
    top_p_label = ttk.Label(model_frame, text=f"{top_p_var.get():.2f}")
    top_p_label.pack(anchor="e")
    top_p_scale = ttk.Scale(model_frame, from_=0.0, to=1.0, variable=top_p_var,
                             orient="horizontal",
                             command=lambda v: top_p_label.configure(text=f"{float(v):.2f}"))
    top_p_scale.pack(fill="x", pady=(0, 8))

    # Output format
    ttk.Label(model_frame, text="Output Format").pack(anchor="w")
    fmt_var = tk.StringVar(value=model_settings.get("output_format", ".txt"))
    fmt_combo = ttk.Combobox(model_frame, textvariable=fmt_var,
                              values=[".txt", ".md"], state="readonly", width=8)
    fmt_combo.pack(anchor="w", pady=(2, 4))

    # Save settings button
    def save_settings():
        idx = model_display.index(model_var.get()) if model_var.get() in model_display else 0
        try:
            set_model_settings(
                model=model_ids[idx],
                temperature=round(temp_var.get(), 2),
                top_p=round(top_p_var.get(), 2),
                output_format=fmt_var.get(),
            )
            log("Settings saved.")
        except Exception as exc:
            log(f"Could not save settings: {exc}")

    ttk.Button(model_frame, text="Save Settings", command=save_settings,
               style="App.TButton").pack(fill="x", pady=(4, 0))

    # Prompt editor
    prompt_frame = ttk.LabelFrame(right_frame, text="  Prompt  ", padding=8)
    prompt_frame.pack(fill="both", expand=True)

    # Preset selector
    presets = get_prompt_presets()
    preset_names = [p["name"] for p in presets]
    preset_ids = [p["id"] for p in presets]
    default_pid = get_default_prompt_id()
    preset_var = tk.StringVar(
        value=next((p["name"] for p in presets if p["id"] == default_pid), preset_names[0])
    )

    preset_row = ttk.Frame(prompt_frame)
    preset_row.pack(fill="x", pady=(0, 4))
    ttk.Label(preset_row, text="Preset").pack(side="left")
    preset_combo = ttk.Combobox(preset_row, textvariable=preset_var,
                                 values=preset_names, state="readonly", width=20)
    preset_combo.pack(side="right", fill="x", expand=True, padx=(6, 0))

    prompt_editor = ScrolledText(prompt_frame, wrap=tk.WORD,
                                  font=(MONO_FAMILY, 9),
                                  bg=t["log_bg"], fg=t["log_fg"],
                                  insertbackground=t["accent"],
                                  selectbackground=t["accent"],
                                  selectforeground=t["btn_fg"],
                                  relief="flat", bd=0, padx=6, pady=6,
                                  height=8)
    prompt_editor.pack(fill="both", expand=True, pady=(0, 6))

    def load_preset(*_args):
        name = preset_var.get()
        idx = preset_names.index(name) if name in preset_names else 0
        prompt_data = get_prompt(preset_ids[idx])
        prompt_editor.delete("1.0", tk.END)
        prompt_editor.insert("1.0", prompt_data.get("content", ""))

    preset_combo.bind("<<ComboboxSelected>>", load_preset)
    # initial load
    active_prompt = get_prompt(default_pid)
    prompt_editor.insert("1.0", active_prompt.get("content", ""))

    # Prompt action buttons
    prompt_btn_row = ttk.Frame(prompt_frame)
    prompt_btn_row.pack(fill="x")

    def save_prompt():
        name = preset_var.get().strip()
        content = prompt_editor.get("1.0", tk.END).strip()
        if not name or not content:
            messagebox.showwarning("Empty", "Prompt name and content cannot be empty.")
            return
        idx = preset_names.index(name) if name in preset_names else None
        pid = preset_ids[idx] if idx is not None else None
        try:
            result = upsert_prompt(pid, name, content, set_default=True)
            set_default_prompt_id(result["id"])
            log(f"Prompt '{name}' saved and set as active.")
            _refresh_presets()
        except Exception as exc:
            log(f"Prompt save error: {exc}")

    def new_prompt():
        name = f"Custom {len(preset_names) + 1}"
        prompt_editor.delete("1.0", tk.END)
        prompt_editor.insert("1.0", "Enter your system prompt here...")
        preset_var.set(name)
        preset_names.append(name)
        preset_ids.append("")
        preset_combo.configure(values=preset_names)

    def _refresh_presets():
        nonlocal presets, preset_names, preset_ids
        presets = get_prompt_presets()
        preset_names.clear()
        preset_ids.clear()
        for p in presets:
            preset_names.append(p["name"])
            preset_ids.append(p["id"])
        preset_combo.configure(values=preset_names)

    ttk.Button(prompt_btn_row, text="Save", command=save_prompt,
               style="App.TButton").pack(side="left", padx=(0, 4))
    ttk.Button(prompt_btn_row, text="New", command=new_prompt,
               style="App.TButton").pack(side="left")

    # Status bar
    status_bar = tk.Label(
        root, anchor="w",
        font=(FONT_FAMILY, 9),
        bg=t["bg_alt"], fg=t["text_dim"],
        padx=12, pady=4,
    )
    status_bar.pack(fill="x", side="bottom")

    def update_status():
        api_status = "API Key Set" if is_configured() else "No API Key"
        ms = get_model_settings()
        n_files = len(tree.get_children())
        active = processing_count.get()
        active_txt = f" | Processing {active}" if active else ""
        status_bar.configure(
            text=f"{api_status}  |  {ms['model']}  |  {n_files} files{active_txt}"
        )
        root.after(2000, update_status)

    # Collect all tk.Frames for theme toggling
    _all_tk_frames = [top_bar]

    # ===================================================================== #
    #  Callbacks                                                             #
    # ===================================================================== #

    def log(msg):
        log_box.insert(tk.END, msg + "\n")
        log_box.see(tk.END)

    def processed_status(path: str) -> str:
        ext = fmt_var.get()
        return "Yes" if os.path.exists(get_processed_path(path, ext)) else "-"

    def update_processed_status(path: str) -> None:
        if not tree.exists(path):
            return
        tree.set(path, "Processed", processed_status(path))

    def refresh_list():
        nonlocal recent_files
        entries = get_recent_texts(50)
        recent_files = [path for path, _, _ in entries]
        tree.delete(*tree.get_children())
        if not entries:
            log("No .txt files found.")
        else:
            for path, mtime, ctime in entries:
                fname = os.path.basename(path)
                mod = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                cre = datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M")
                tree.insert("", "end", iid=path,
                            values=(fname, mod, cre, processed_status(path)))
            log(f"Refreshed - {len(entries)} file(s) at {datetime.now().strftime('%H:%M:%S')}")
        update_status()

    def choose_folder():
        selected = filedialog.askdirectory(
            title="Select folder with TXT files",
            initialdir=get_text_folder(),
        )
        if not selected:
            return
        try:
            set_text_folder(selected)
            folder_var.set(get_text_folder())
            log(f"Folder set to: {selected}")
            refresh_list()
        except Exception as exc:
            messagebox.showerror("Folder Error", f"Could not set folder:\n{exc}")

    def add_file():
        file_path = filedialog.askopenfilename(
            title="Select a TXT file to add",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*")],
        )
        if not file_path:
            return
        try:
            mtime = os.path.getmtime(file_path)
            ctime = os.path.getctime(file_path)
        except OSError:
            messagebox.showerror("File Error", "Could not access file metadata.")
            return
        fname = os.path.basename(file_path)
        mod = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        cre = datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M")
        recent_files.insert(0, file_path)
        tree.insert("", 0, iid=file_path,
                    values=(fname, mod, cre, processed_status(file_path)))
        tree.selection_set(file_path)
        log(f"Added: {fname}")

    def select_all():
        tree.selection_set(tree.get_children())

    def open_selected_original():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select at least one file.")
            return
        for chosen in sel:
            threading.Thread(target=open_file, args=(chosen, log), daemon=True).start()

    def copy_selected_processed():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select at least one file.")
            return
        ext = fmt_var.get()
        for chosen in sel:
            threading.Thread(target=copy_processed_for,
                             args=(chosen, log, ext), daemon=True).start()

    def process_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Select at least one file to process.")
            return

        # Gather current settings
        idx = model_display.index(model_var.get()) if model_var.get() in model_display else 0
        cur_model = model_ids[idx]
        cur_temp = round(temp_var.get(), 2)
        cur_top_p = round(top_p_var.get(), 2)
        cur_fmt = fmt_var.get()
        cur_prompt = prompt_editor.get("1.0", tk.END).strip()

        progress_bar.pack(fill="x", pady=(4, 0), before=log_label)
        progress_bar.start(12)
        processing_count.set(processing_count.get() + len(sel))
        update_status()

        for chosen in sel:
            def _run(path=chosen):
                try:
                    process_file(
                        path, log,
                        model=cur_model,
                        prompt_text=cur_prompt,
                        temperature=cur_temp,
                        top_p=cur_top_p,
                        output_format=cur_fmt,
                    )
                finally:
                    root.after(0, lambda p=path: update_processed_status(p))
                    new_count = processing_count.get() - 1
                    processing_count.set(max(0, new_count))
                    if new_count <= 0:
                        root.after(0, lambda: (progress_bar.stop(),
                                               progress_bar.pack_forget()))
                    root.after(0, update_status)

            threading.Thread(target=_run, daemon=True).start()

    # -- Initial load ------------------------------------------------------- #
    refresh_list()
    update_status()
    root.mainloop()
