<div align="center">

# PYCORE IDE

### The Python IDE that brings its own Python.

A fully portable Python IDE with a **bundled interpreter** and **working pip** — copy the folder to any Windows PC and write, run, and `pip install`, even on machines that have never had Python installed.

Built for students, school labs, and thin clients.

![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-58a6ff?style=flat-square)
![Python](https://img.shields.io/badge/python-bundled-3fb950?style=flat-square)
![pip](https://img.shields.io/badge/pip-works%20offline--install-bc8cff?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-orange?style=flat-square)

[Download](#download) · [Features](#features) · [Install](#installation) · [vs IDLE](#pycore-ide-vs-python-idle) · [Build from source](#build-from-source)

</div>

---

## Why PYCORE IDE?

Most Python IDEs assume Python is already installed and set up correctly. In a school lab, on a friend's laptop, or on a locked-down thin client, that assumption breaks — "Python is not recognized", missing PATH, no admin rights.

PYCORE IDE ships a **real Python interpreter inside the app**. Run the installer, and you're coding. `pip install` works from inside the app, so you can pull in `pandas`, `requests`, anything — and the packages stay in the app folder for next time.

---

## Download

> **Windows 10/11 (64-bit).** No Python required.

**[⬇ Download the latest release](../../releases/latest)** — grab `PYCORE_IDE_Setup.exe`, run it, and follow the wizard.

That's the whole installation. See [Installation](#installation) for the step-by-step.

---

## Features

| | Feature | What it does |
|---|---|---|
| 📦 | **Bundled Python** | A real interpreter ships inside the app. Runs on any Windows PC with nothing pre-installed. |
| 🔌 | **Working pip** | Install packages at runtime — `pip install pandas` — straight from the IDE. They persist in the app folder. |
| 🤖 | **AI error help** | Get the cause, fix, and corrected code in simple Hinglish. Works with **PYCORE AI (local), Gemini, ChatGPT, or Claude**. |
| 🎓 | **Tutor Mode** | AI gives hints and a guiding question instead of the answer — so students actually learn to debug. |
| ▶️ | **Interactive console** | A live Python REPL like IDLE's shell — variables persist, command history, run a file straight into it. |
| 🔎 | **Variables panel** | After every run, see each variable's name, type, and value at a glance. |
| 🟥 | **Error line highlight** | The exact line that failed turns red in the editor. |
| 📚 | **Ready examples** | Ten built-in starter programs — loops, lists, dictionaries, functions, file handling — one click to load. |
| ⌨️ | **input() support** | Programs that ask for input work, with a clear visual cue showing where to type. |
| 🎨 | **Modern dark UI** | Tabs, syntax highlighting, line numbers, auto-indent, animated splash screen. |

---

## Installation

No manual setup. Three steps:

1. **Download** `PYCORE_IDE_Setup.exe` from the [Releases page](../../releases/latest).
2. **Run** the installer and follow the wizard — pick an install location and whether to add a desktop shortcut.
3. **Launch** PYCORE IDE from your desktop or the Windows search bar.

> If Windows shows a blue **"Windows protected your PC"** box, click **More info → Run anyway**. The app is safe — it's just unsigned.
>
> **Tip:** to use `pip install` without admin rights, install to a user folder (e.g. `C:\PYCORE IDE`) instead of Program Files.

### Optional: turn on AI

Open **⚙ Settings**, pick an AI provider, paste your key (or PYCORE AI URL), and Save.

### Optional: install packages

Type a command in the bottom box, e.g. `pip install requests`, and hit **Run pip**. The package stays in the app folder for next time.

---

## System Requirements

| | |
|---|---|
| **Operating system** | Windows 10 / 11 (64-bit) |
| **Python pre-installed** | Not required |
| **RAM** | 2 GB minimum, 4 GB recommended |
| **Disk space** | ~300 MB (bundled Python + app) |
| **Internet** | Only for pip & AI features |
| **Admin rights** | Not needed — fully portable |

> On locked-down thin clients, running `.exe` files may be blocked by policy. Test from a USB drive first; if it's blocked, ask your lab admin.

---

## PYCORE IDE vs Python IDLE

IDLE is the trusted classic. PYCORE keeps what students need and adds portability and AI on top.

| Feature | PYCORE IDE | Python IDLE |
|---|:---:|:---:|
| Works without Python installed | ✅ Bundled | ❌ Needs Python |
| pip install inside the app | ✅ | ⚠️ Terminal only |
| AI error explanation | ✅ 4 providers | ❌ |
| Tutor mode (hints, not answers) | ✅ | ❌ |
| Interactive REPL / shell | ✅ | ✅ |
| Variables panel after run | ✅ | ❌ |
| Error line highlight | ✅ | ⚠️ Cursor jump only |
| Built-in example programs | ✅ 10 | ❌ |
| Runs from USB / shared folder | ✅ Portable | ❌ Needs install |
| Step debugger with breakpoints | ❌ Not yet | ✅ |
| Modern dark UI | ✅ | ⚠️ Basic |

> **Honest note:** IDLE still wins on the built-in step debugger. PYCORE is best when you need portability, AI help, and a student-friendly layout — pair the two if you want both.

---

## Optional: PYCORE AI (free local AI)

Want AI help with no API key? Run a local model on your own PC and point the IDE to it.

```bash
# on your PC, with Ollama installed
ollama serve

# expose it with a Cloudflare tunnel
cloudflared tunnel --url http://localhost:11434
```

Paste the resulting `https://…trycloudflare.com` URL into **Settings → PYCORE AI**. Keep your PC and tunnel running while you (or your students) use it.

> Note: a small local model on one PC is fine for a few users. For a whole class at once, a cloud provider (Gemini free tier) is more reliable.

---

## Build from source

Want to build the `.exe` yourself? You'll need a normal Python on your dev machine.

### Requirements
```bat
pip install pyqt6 pyinstaller
```

### Steps

```bat
:: 1. Download the embeddable Python and enable pip (run once)
setup_python.bat

:: 2. Build the exe (bundles python\ alongside it)
build_exe.bat
```

The result lands in `dist\PYCORE_IDE\` — a portable folder you can zip and share.

### How it works

PYCORE bundles the official **embeddable Python** package (from python.org) alongside the app. This is a *real, separate interpreter* — not PyInstaller's embedded Python — which is why `pip` works inside it. Your code runs in this bundled interpreter via `subprocess`, fully isolated.

> PyInstaller's own embedded Python has no `pip` or `site-packages` — it only runs the app. For live `pip install`, you need the embeddable package, so the two are bundled separately.

### Project structure

```
PYCORE-IDE/
├── app/
│   └── pycore_ide.py        # main IDE (PyQt6)
├── build_tools/
│   ├── setup_python.bat     # downloads embeddable Python + enables pip
│   └── build_exe.bat        # builds the exe + bundles python\
├── icon/
│   └── pycore.ico           # app icon
├── website/
│   └── index.html           # landing page
├── BUILD_NOTES.md           # detailed build notes (Hinglish)
├── TEST_GUIDE.md            # full feature test checklist
└── README.md
```

---

## Tech stack

- **UI:** PyQt6
- **Interpreter:** Python embeddable package (bundled)
- **Packaging:** PyInstaller (onedir)
- **AI:** PYCORE AI (Ollama) · Gemini · OpenAI · Anthropic

---

## Roadmap

- [ ] Step debugger with breakpoints
- [ ] Find & replace
- [ ] Code auto-completion
- [ ] Multiple themes

---

## License

Released under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

**PYCORE IDE** — standalone Python for everyone.

Created by **Aryan Singh**

</div>
