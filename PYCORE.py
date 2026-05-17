import os
import sys
import time
import json
import math
import random
import datetime
import traceback
import inspect
import keyword
import platform
import threading
import queue
import subprocess
import pathlib
import shutil
import sqlite3
import logging
import code
import codeop
import ast
import tokenize
import ctypes
import io
import re
import copy
import types
import atexit
import collections
import urllib.request
import urllib.error
import urllib.parse
import signal

# ══════════════════════════════════════════════════════════════════════
#  RESOURCE PATH HELPER  (supports PyInstaller/Nuitka one-file builds)
# ══════════════════════════════════════════════════════════════════════

def resource_path(filename: str) -> pathlib.Path:
    try:
        base = pathlib.Path(sys._MEIPASS)  # type: ignore[attr-defined]
    except AttributeError:
        base = pathlib.Path(__file__).parent
    return base / filename


# ══════════════════════════════════════════════════════════════════════
#  ANSI COLOR / STYLE SYSTEM
# ══════════════════════════════════════════════════════════════════════

class Colors:
    RESET          = "\033[0m"
    BOLD           = "\033[1m"
    DIM            = "\033[2m"
    ITALIC         = "\033[3m"
    UNDERLINE      = "\033[4m"
    BLINK          = "\033[5m"
    REVERSE        = "\033[7m"

    BLACK          = "\033[30m"
    RED            = "\033[31m"
    GREEN          = "\033[32m"
    YELLOW         = "\033[33m"
    BLUE           = "\033[34m"
    MAGENTA        = "\033[35m"
    CYAN           = "\033[36m"
    WHITE          = "\033[37m"
    BRIGHT_BLACK   = "\033[90m"
    BRIGHT_RED     = "\033[91m"
    BRIGHT_GREEN   = "\033[92m"
    BRIGHT_YELLOW  = "\033[93m"
    BRIGHT_BLUE    = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN    = "\033[96m"
    BRIGHT_WHITE   = "\033[97m"

    BG_BLACK       = "\033[40m"
    BG_RED         = "\033[41m"
    BG_GREEN       = "\033[42m"
    BG_YELLOW      = "\033[43m"
    BG_BLUE        = "\033[44m"
    BG_MAGENTA     = "\033[45m"
    BG_CYAN        = "\033[46m"
    BG_WHITE       = "\033[47m"
    BG_BRIGHT_BLACK= "\033[100m"
    BG_BRIGHT_CYAN = "\033[106m"

    @staticmethod
    def fg256(n: int)        -> str: return f"\033[38;5;{n}m"
    @staticmethod
    def bg256(n: int)        -> str: return f"\033[48;5;{n}m"
    @staticmethod
    def rgb(r, g, b)         -> str: return f"\033[38;2;{r};{g};{b}m"
    @staticmethod
    def bgrgb(r, g, b)       -> str: return f"\033[48;2;{r};{g};{b}m"

C = Colors  # short alias


# ══════════════════════════════════════════════════════════════════════
#  BUILT-IN AI SYSTEM PROMPT  (replaces info.txt dependency entirely)
# ══════════════════════════════════════════════════════════════════════

BUILTIN_SYSTEM_PROMPT = """You are ARYAN AI, a friendly Python debugging assistant inside a futuristic cyberpunk Python shell called PyCore AI Shell.

Your job is to understand Python errors and explain them in a very simple way so a student can quickly understand:
1) error kya hai
2) error kyun aaya
3) usko kaise fix karna hai
4) correct code kya hoga

You must respond STRICTLY in this exact format only — nothing else:

ERROR:
[error type name only]

REASON:
[Explain in very simple Hinglish why this error happened. Write like you are teaching a beginner. Mention the main mistake clearly. Use 3-6 short lines.]

FIX:
[Explain in very simple Hinglish how to fix it step by step. Give practical solution, not vague advice. Use 3-6 short lines.]

CORRECT CODE:
[Provide only the corrected Python code. No explanation. No markdown fences. Only pure Python code.]

Important Rules:
- Always use simple Hinglish (mix of Hindi and English, easy to understand)
- Write like a teacher explaining to a beginner student
- Keep language easy, friendly, and beginner-friendly
- Avoid hard Hindi words and complicated grammar
- Explain the mistake clearly, not just the symptom
- If useful, mention the exact line or type of mistake
- In FIX, give direct solution steps
- In CORRECT CODE, give working code only — no ```python fences, no backticks
- No greetings, no closing lines, no emojis, no extra commentary
- Keep responses short, clear, and directly useful

Response style examples:
- "Ye variable pehle define nahi hua"
- "Tumne galat module import kiya"
- "Is line me type mismatch ho raha hai"
- "Pehle value set karo, fir use karo"
- "List ka index 0 se start hota hai, isliye last element -1 ya len-1 hoga"

CRITICAL: Always analyse the full traceback and runtime variable context provided. Give the most specific fix possible, not generic advice."""

PROMPT_VERSION = "3.0"


# ══════════════════════════════════════════════════════════════════════
#  CONFIG LOADER
# ══════════════════════════════════════════════════════════════════════

class ConfigLoader:
    """Loads and saves config.json next to the running script.
    Auto-repairs corrupted config files instead of silently ignoring them.
    """

    DEFAULT: dict = {
        "active_api_key"    : 0,
        "pycore_api_keys"   : [],
        "pycore_ai_enabled" : True,
        "pycore_model"      : "gemini-2.5-flash",
        "request_timeout"   : 18,
        "theme"             : "cyberpunk",
        "show_time"         : True,
    }

    def __init__(self):
        self.path = resource_path("config.json")
        self.data = dict(self.DEFAULT)
        self._lock = threading.Lock()
        self._load()

    def _load(self):
        try:
            if self.path.exists():
                raw = self.path.read_text(encoding="utf-8").strip()
                if raw:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        self.data.update(parsed)
                        return
            # file missing or empty → write defaults
            self.save()
        except (json.JSONDecodeError, ValueError):
            # corrupted → back up and reset
            try:
                bak = self.path.with_suffix(".json.bak")
                self.path.rename(bak)
            except Exception:
                pass
            self.save()
        except Exception:
            pass

    def save(self) -> bool:
        with self._lock:
            try:
                self.path.write_text(
                    json.dumps(self.data, indent=4, ensure_ascii=False),
                    encoding="utf-8"
                )
                return True
            except Exception:
                return False

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value) -> bool:
        self.data[key] = value
        return self.save()


# ══════════════════════════════════════════════════════════════════════
#  GEMINI API MANAGER
# ══════════════════════════════════════════════════════════════════════

_LRU_MAX = 64  # max cached responses

class PYCOREManager:
    """Handles all PYCORE API communication with retry, caching, and rotation."""

    BASE_URL = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        "/{model}:generateContent?key={key}"
    )

    def __init__(self, config: "ConfigLoader"):
        self.config      = config
        self._cache: "collections.OrderedDict[int, dict]" = collections.OrderedDict()
        self.enabled: bool = config.get("pycore_ai_enabled", True)
        self.last_status   = "unknown"
        self._lock         = threading.Lock()

    def is_ready(self) -> bool:
        keys = self.config.get("pycore_api_keys", [])
        return self.enabled and bool(keys)

    def analyze_error(
        self,
        code_src   : str,
        exc_name   : str,
        exc_msg    : str,
        traceback_s: str,
        history    : list,
        user_vars  : dict,
    ) -> "dict | None":
        if not self.is_ready():
            self.last_status = "no_key" if self.enabled else "disabled"
            return None

        prompt    = self._build_prompt(code_src, exc_name, exc_msg, traceback_s, history, user_vars)
        cache_key = hash(prompt)

        with self._lock:
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                self.last_status = "cached"
                return self._cache[cache_key]

        raw = self._call_api_with_retry(prompt)
        if raw is None:
            return None

        parsed = self._parse_response(raw)

        with self._lock:
            self._cache[cache_key] = parsed
            self._cache.move_to_end(cache_key)
            if len(self._cache) > _LRU_MAX:
                self._cache.popitem(last=False)  # evict oldest

        self.last_status = "ok"
        return parsed

    def test_connection(self) -> "tuple[bool, str]":
        if not self.config.get("pycore_api_keys", []):
            return False, "No API key set. Use :addkey to add one."
        result = self._call_api_with_retry("Say exactly: PYCORE AI ONLINE", timeout=10)
        if result:
            return True, "PYCORE connection successful ✔"
        return False, f"Connection failed — check key or internet. ({self.last_status})"

    # ── Prompt building ──────────────────────────────────────────────

    def _build_prompt(self, code_src, exc_name, exc_msg, tb, history, uv) -> str:
        hist_text = "\n".join(f"  {i+1}. {h}" for i, h in enumerate(history[-10:]))
        vars_text = "\n".join(
            f"  {k} ({type(v).__name__}) = {repr(v)[:100]}"
            for k, v in list(uv.items())[:20]
        )
        return (
            f"{BUILTIN_SYSTEM_PROMPT}\n\n"
            f"{'='*60}\n"
            f"=== ERROR CONTEXT (read carefully) ===\n"
            f"{'='*60}\n"
            f"Python Version : {platform.python_version()}\n"
            f"OS             : {platform.system()} {platform.release()}\n\n"
            f"--- Code That Was Executed ---\n{code_src}\n\n"
            f"--- Exception Type & Message ---\n{exc_name}: {exc_msg}\n\n"
            f"--- Full Traceback ---\n{tb or '(no traceback)'}\n\n"
            f"--- Last 10 Commands (most recent last) ---\n{hist_text or '(none yet)'}\n\n"
            f"--- Current Runtime Variables ---\n{vars_text or '(no user variables defined)'}\n"
            f"{'='*60}\n"
            f"Now respond ONLY in the required ERROR/REASON/FIX/CORRECT CODE format."
        )

    # ── API call with retry ──────────────────────────────────────────

    def _call_api_with_retry(self, prompt: str, timeout: "int | None" = None) -> "str | None":
        keys  = self.config.get("pycore_api_keys", [])
        if not keys:
            self.last_status = "no_key"
            return None

        active_idx = self.config.get("active_api_key", 0)
        tout = timeout if timeout is not None else self.config.get("request_timeout", 18)
        model = self.config.get("pycore_model", "gemini-2.5-flash")

        # Try active key first, then cycle through all others
        key_order = [active_idx] + [i for i in range(len(keys)) if i != active_idx]

        for idx in key_order:
            if idx < 0 or idx >= len(keys):
                continue
            api_key = keys[idx].strip()
            if not api_key:
                continue
            result = self._do_request(prompt, api_key, model, tout)
            if result is not None:
                # If we succeeded on a non-active key, rotate to it
                if idx != active_idx:
                    self.config.set("active_api_key", idx)
                return result
            # On rate-limit, stop trying more keys (wait needed)
            if self.last_status == "http_429":
                break

        return None

    def _do_request(self, prompt: str, api_key: str, model: str, tout: int) -> "str | None":
        url = self.BASE_URL.format(model=model, key=api_key)
        payload = json.dumps({
            "contents"       : [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 768,
                "temperature"    : 0.25,
                "topP"           : 0.9,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data   = payload,
            headers= {"Content-Type": "application/json"},
            method = "POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=tout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                # Navigate safely through response structure
                candidates = data.get("candidates", [])
                if not candidates:
                    self.last_status = "empty_response"
                    return None
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    self.last_status = "no_parts"
                    return None
                return parts[0].get("text", "")
        except urllib.error.HTTPError as e:
            self.last_status = f"http_{e.code}"
        except urllib.error.URLError:
            self.last_status = "offline"
        except TimeoutError:
            self.last_status = "timeout"
        except json.JSONDecodeError:
            self.last_status = "bad_json"
        except Exception as ex:
            self.last_status = f"error:{type(ex).__name__}"
        return None

    # ── Response parser ──────────────────────────────────────────────

    def _parse_response(self, raw: str) -> dict:
        """Extract ERROR/REASON/FIX/CORRECT CODE sections robustly."""
        raw = raw.strip()
        sections = {
            "error"       : "",
            "reason"      : "",
            "fix"         : "",
            "correct_code": "",
            "raw"         : raw,
        }
        # Strip any accidental markdown fences from CORRECT CODE
        raw_clean = re.sub(r"```(?:python)?", "", raw)
        raw_clean = re.sub(r"```", "", raw_clean)

        patterns = {
            "error"       : r"ERROR:\s*(.*?)(?=REASON:|FIX:|CORRECT CODE:|$)",
            "reason"      : r"REASON:\s*(.*?)(?=ERROR:|FIX:|CORRECT CODE:|$)",
            "fix"         : r"FIX:\s*(.*?)(?=ERROR:|REASON:|CORRECT CODE:|$)",
            "correct_code": r"CORRECT CODE:\s*(.*?)(?=ERROR:|REASON:|FIX:|$)",
        }
        for key, pat in patterns.items():
            m = re.search(pat, raw_clean, re.DOTALL | re.IGNORECASE)
            if m:
                sections[key] = m.group(1).strip()

        # Fallback: if nothing parsed, show raw
        if not any(sections[k] for k in ("error", "reason", "fix")):
            sections["reason"] = raw[:500] if raw else "(no response)"

        return sections


# ══════════════════════════════════════════════════════════════════════
#  GEMINI RESPONSE UI
# ══════════════════════════════════════════════════════════════════════

class PYCOREUI:
    """Renders PYCORE AI responses with full theme integration."""

    def __init__(self, theme: dict):
        self.theme = theme

    # ── Spinner ─────────────────────────────────────────────────────

    def spinner_start(self, message: str) -> threading.Event:
        """Start background spinner. Returns Event — call .set() to stop."""
        stop_event  = threading.Event()
        frames      = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        think_dots  = ["·  ","·· ","···","   "]
        a1          = self.theme["accent1"]
        a2          = self.theme["accent2"]
        start_t     = time.time()

        def _spin():
            i = 0
            while not stop_event.is_set():
                frame    = frames[i % len(frames)]
                dots     = think_dots[(i // 3) % len(think_dots)]
                elapsed  = time.time() - start_t
                line     = (
                    f"\r  {a1}{frame}{C.RESET} "
                    f"{a2}{message}{C.RESET} "
                    f"{C.DIM}{dots} {elapsed:.1f}s{C.RESET}   "
                )
                safe_print(line, end="", flush=True)
                time.sleep(0.08)
                i += 1
            safe_print(f"\r{' '*72}\r", end="", flush=True)

        t = threading.Thread(target=_spin, daemon=True)
        t.start()
        return stop_event

    # ── Main panel ──────────────────────────────────────────────────

    def print_gemini_panel(self, parsed: dict):
        t   = self.theme
        a1  = t["accent1"]
        a2  = t["accent2"]
        a3  = t["accent3"]
        err = t["error_color"]
        w, _ = get_terminal_size()
        w   = max(60, min(w, 140))  # clamp to sensible range
        bc  = t["border_char"]
        tl  = t["corner_tl"]
        tr  = t["corner_tr"]
        bl  = t["corner_bl"]
        br  = t["corner_br"]
        sid = t["side"]
        inner_w = w - 6  # account for "  ║  " prefix

        def _wrap_lines(text: str) -> list:
            """Word-wrap text to inner_w characters."""
            result = []
            for raw_ln in text.split("\n"):
                if len(raw_ln) <= inner_w:
                    result.append(raw_ln)
                else:
                    # simple char-wrap
                    while len(raw_ln) > inner_w:
                        result.append(raw_ln[:inner_w])
                        raw_ln = "  " + raw_ln[inner_w:]
                    result.append(raw_ln)
            return result

        def _section(label: str, content: str, label_c: str, text_c: str):
            if not content.strip():
                return
            safe_print(f"  {sid}  {label_c}{C.BOLD}{label}{C.RESET}", flush=True)
            for ln in _wrap_lines(content.strip()):
                safe_print(f"  {sid}    {text_c}{ln}{C.RESET}", flush=True)
            safe_print(f"  {sid}", flush=True)

        header_text = "🤖  PYCORE AI  —  ERROR ANALYSIS"
        h_plain_len = len(re.sub(r'\033\[[0-9;]*m', '', header_text)) + 4
        h_pad       = max(0, w - 4 - h_plain_len)

        safe_print()
        safe_print(f"  {a1}{tl}{bc*(w-4)}{tr}{C.RESET}", flush=True)
        safe_print(
            f"  {a1}{sid}{C.RESET}  {a2}{C.BOLD}{header_text}{C.RESET}"
            f"{' '*h_pad}{a1}{sid}{C.RESET}",
            flush=True
        )
        safe_print(f"  {a1}{sid}{bc*(w-4)}{sid}{C.RESET}", flush=True)

        _section("⚠  ERROR TYPE",     parsed.get("error",""),        err,  err)
        _section("📖 REASON (हिंदी)", parsed.get("reason",""),       a2,   a3)
        _section("🔧 FIX (हिंदी)",   parsed.get("fix",""),          a2,   a3)

        code_block = parsed.get("correct_code","").strip()
        if code_block:
            safe_print(f"  {sid}  {a1}{C.BOLD}✅ CORRECT CODE{C.RESET}", flush=True)
            for ln in _wrap_lines(code_block):
                safe_print(f"  {sid}    {C.BRIGHT_GREEN}{ln}{C.RESET}", flush=True)
            safe_print(f"  {sid}", flush=True)

        safe_print(f"  {a1}{bl}{bc*(w-4)}{br}{C.RESET}\n", flush=True)

    # ── Status notices ───────────────────────────────────────────────

    _REASON_MAP = {
        "http_429"      : "PYCORE rate limit hit — please wait a moment and retry",
        "http_401"      : "Invalid API key — check with :keys and :addkey",
        "http_403"      : "API key forbidden — check PYCORE console permissions",
        "http_400"      : "Bad request to PYCORE — check code context",
        "http_500"      : "PYCORE server error — try again shortly",
        "http_503"      : "PYCORE service unavailable — try again shortly",
        "offline"       : "No internet connection — running in offline mode",
        "timeout"       : "Request timed out — check internet speed",
        "no_key"        : "No API key set — use :addkey <key>",
        "disabled"      : "PYCORE AI is disabled — use :ai on to enable",
        "empty_response": "PYCORE returned an empty response",
        "bad_json"      : "Unexpected response format from PYCORE",
        "cached"        : "Response served from cache",
        "unknown"       : "Unknown PYCORE error",
    }

    def print_offline_notice(self, reason: str):
        t       = self.theme
        friendly= self._REASON_MAP.get(reason, f"PYCORE error: {reason}")
        safe_print(
            f"\n  {t['warn_color']}⚠  {friendly}.{C.RESET}\n"
            f"  {C.DIM}(PyCore built-in AI hint shown above){C.RESET}\n"
        )

    def print_no_key_notice(self):
        t = self.theme
        safe_print(
            f"\n  {t['warn_color']}[PYCORE AI: no API key configured. "
            f"Use :addkey <your_key> to enable full AI debugging.]{C.RESET}\n"
        )


# ══════════════════════════════════════════════════════════════════════
#  THEME SYSTEM
# ══════════════════════════════════════════════════════════════════════

THEMES: dict = {
    "cyberpunk": {
        "name"        : "CYBERPUNK",
        "prompt_color": C.BRIGHT_CYAN,
        "output_color": C.BRIGHT_WHITE,
        "error_color" : C.BRIGHT_RED,
        "warn_color"  : C.BRIGHT_YELLOW,
        "info_color"  : C.BRIGHT_MAGENTA,
        "accent1"     : C.BRIGHT_CYAN,
        "accent2"     : C.BRIGHT_MAGENTA,
        "accent3"     : C.BRIGHT_YELLOW,
        "dim_color"   : C.BRIGHT_BLACK,
        "border_char" : "═",
        "corner_tl"   : "╔", "corner_tr": "╗",
        "corner_bl"   : "╚", "corner_br": "╝",
        "side"        : "║",
        "logo_color"  : C.BRIGHT_CYAN,
    },
    "matrix": {
        "name"        : "MATRIX",
        "prompt_color": C.BRIGHT_GREEN,
        "output_color": C.GREEN,
        "error_color" : C.BRIGHT_RED,
        "warn_color"  : C.YELLOW,
        "info_color"  : C.BRIGHT_GREEN,
        "accent1"     : C.BRIGHT_GREEN,
        "accent2"     : C.GREEN,
        "accent3"     : C.BRIGHT_YELLOW,
        "dim_color"   : C.BRIGHT_BLACK,
        "border_char" : "─",
        "corner_tl"   : "┌", "corner_tr": "┐",
        "corner_bl"   : "└", "corner_br": "┘",
        "side"        : "│",
        "logo_color"  : C.BRIGHT_GREEN,
    },
    "midnight": {
        "name"        : "MIDNIGHT",
        "prompt_color": C.BRIGHT_BLUE,
        "output_color": C.WHITE,
        "error_color" : C.BRIGHT_RED,
        "warn_color"  : C.BRIGHT_YELLOW,
        "info_color"  : C.BRIGHT_BLUE,
        "accent1"     : C.BRIGHT_BLUE,
        "accent2"     : C.BRIGHT_MAGENTA,
        "accent3"     : C.CYAN,
        "dim_color"   : C.BRIGHT_BLACK,
        "border_char" : "▓",
        "corner_tl"   : "▛", "corner_tr": "▜",
        "corner_bl"   : "▙", "corner_br": "▟",
        "side"        : "▌",
        "logo_color"  : C.BRIGHT_BLUE,
    },
    "neon": {
        "name"        : "NEON",
        "prompt_color": C.BRIGHT_MAGENTA,
        "output_color": C.BRIGHT_WHITE,
        "error_color" : C.BRIGHT_RED,
        "warn_color"  : C.BRIGHT_YELLOW,
        "info_color"  : C.BRIGHT_MAGENTA,
        "accent1"     : C.BRIGHT_MAGENTA,
        "accent2"     : C.BRIGHT_CYAN,
        "accent3"     : C.BRIGHT_YELLOW,
        "dim_color"   : C.BRIGHT_BLACK,
        "border_char" : "═",
        "corner_tl"   : "╔", "corner_tr": "╗",
        "corner_bl"   : "╚", "corner_br": "╝",
        "side"        : "║",
        "logo_color"  : C.BRIGHT_MAGENTA,
    },
    "hacker": {
        "name"        : "HACKER",
        "prompt_color": C.BRIGHT_GREEN,
        "output_color": C.BRIGHT_GREEN,
        "error_color" : C.BRIGHT_RED,
        "warn_color"  : C.YELLOW,
        "info_color"  : C.GREEN,
        "accent1"     : C.BRIGHT_GREEN,
        "accent2"     : C.GREEN,
        "accent3"     : C.BRIGHT_YELLOW,
        "dim_color"   : C.BRIGHT_BLACK,
        "border_char" : "#",
        "corner_tl"   : "#", "corner_tr": "#",
        "corner_bl"   : "#", "corner_br": "#",
        "side"        : "|",
        "logo_color"  : C.BRIGHT_GREEN,
    },
    "aurora": {
        "name"        : "AURORA",
        "prompt_color": C.BRIGHT_CYAN,
        "output_color": C.BRIGHT_WHITE,
        "error_color" : C.BRIGHT_RED,
        "warn_color"  : C.BRIGHT_YELLOW,
        "info_color"  : C.BRIGHT_GREEN,
        "accent1"     : C.BRIGHT_CYAN,
        "accent2"     : C.BRIGHT_GREEN,
        "accent3"     : C.BRIGHT_WHITE,
        "dim_color"   : C.BRIGHT_BLACK,
        "border_char" : "·",
        "corner_tl"   : "╭", "corner_tr": "╮",
        "corner_bl"   : "╰", "corner_br": "╯",
        "side"        : "│",
        "logo_color"  : C.BRIGHT_GREEN,
    },
}


# ══════════════════════════════════════════════════════════════════════
#  TERMINAL UTILITIES
# ══════════════════════════════════════════════════════════════════════

def enable_ansi_windows():
    """Enable ANSI escape codes on Windows 10+."""
    if platform.system() == "Windows":
        try:
            kernel32 = ctypes.windll.kernel32   # type: ignore[attr-defined]
            # ENABLE_PROCESSED_OUTPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass

def get_terminal_size() -> "tuple[int,int]":
    try:
        cols, rows = shutil.get_terminal_size(fallback=(100, 30))
        return max(40, cols), max(10, rows)
    except Exception:
        return 100, 30

def clear_screen():
    os.system("cls" if platform.system() == "Windows" else "clear")

def move_cursor(row: int, col: int):
    safe_print(f"\033[{row};{col}H", end="", flush=True)

def hide_cursor():
    safe_print("\033[?25l", end="", flush=True)

def show_cursor():
    safe_print("\033[?25h", end="", flush=True)

def safe_print(*args, end="\n", flush=False, **kwargs):
    """Unicode-safe print wrapper — handles Windows encoding errors gracefully."""
    try:
        print(*args, end=end, flush=flush, **kwargs)
    except UnicodeEncodeError:
        # Fallback: replace unencodable chars
        text = " ".join(str(a) for a in args)
        text = text.encode(sys.stdout.encoding or "ascii", errors="replace").decode(
            sys.stdout.encoding or "ascii"
        )
        print(text, end=end, flush=flush)
    except Exception:
        pass

def print_colored(text: str, color: str = "", end: str = "\n", flush: bool = True):
    safe_print(f"{color}{text}{C.RESET}", end=end, flush=flush)

def typing_print(text: str, color: str = "", delay: float = 0.018, end: str = "\n"):
    """Print text character by character with a short delay."""
    for ch in text:
        safe_print(f"{color}{ch}{C.RESET}", end="", flush=True)
        time.sleep(delay)
    safe_print(end, end="", flush=True)

def center_text(text: str, width: int, fill: str = " ") -> str:
    plain = re.sub(r'\033\[[0-9;]*m', '', text)
    pad   = max(0, width - len(plain))
    left  = pad // 2
    right = pad - left
    return fill * left + text + fill * right

def strip_ansi(text: str) -> str:
    return re.sub(r'\033\[[0-9;]*m', '', text)

def clamp_line(text: str, max_len: int) -> str:
    """Truncate a string to max_len visible characters, preserving ANSI codes."""
    plain = strip_ansi(text)
    if len(plain) <= max_len:
        return text
    # Simple approach: truncate at character level
    return text[:max_len]

def box_line(text: str, width: int, theme: dict, padding: int = 1) -> str:
    plain  = strip_ansi(text)
    inner  = width - 2
    space  = inner - len(plain) - padding * 2
    return (
        theme["side"] +
        " " * padding +
        text +
        " " * max(0, space) +
        " " * padding +
        theme["side"]
    )

def draw_box(lines: list, theme: dict, width: "int | None" = None):
    if width is None:
        width, _ = get_terminal_size()
    w   = max(40, width)
    a1  = theme["accent1"]
    top = theme["corner_tl"] + theme["border_char"] * (w - 2) + theme["corner_tr"]
    bot = theme["corner_bl"] + theme["border_char"] * (w - 2) + theme["corner_br"]
    print_colored(top, a1)
    for ln in lines:
        print_colored(box_line(ln, w, theme), a1)
    print_colored(bot, a1)


# ══════════════════════════════════════════════════════════════════════
#  ASCII LOGO & BRANDING
# ══════════════════════════════════════════════════════════════════════

ASCII_LOGO = r"""
██████╗ ██╗   ██╗ ██████╗ ██████╗ ██████╗ ███████╗
██╔══██╗╚██╗ ██╔╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
██████╔╝ ╚████╔╝ ██║     ██║   ██║██████╔╝█████╗
██╔═══╝   ╚██╔╝  ██║     ██║   ██║██╔══██╗██╔══╝
██║        ██║   ╚██████╗╚██████╔╝██║  ██║███████╗
╚═╝        ╚═╝    ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝
       AI  SHELL  v3.0  ·  stdlib only
"""


# ══════════════════════════════════════════════════════════════════════
#  STARTUP ANIMATION  (cinematic 4-phase)
# ══════════════════════════════════════════════════════════════════════

class StartupAnimation:
    def __init__(self, theme: dict):
        self.theme = theme
        self.cols, self.rows = get_terminal_size()

    # ── Phase 1: matrix rain ─────────────────────────────────────────

    def _matrix_rain(self, duration: float = 1.2):
        chars = "01アイウエオカキクケコサシスセソタチツテトナニヌネノ!@#$%^&*░▒▓"
        a1    = self.theme["accent1"]
        dim   = self.theme["dim_color"]
        end_t = time.time() + duration
        while time.time() < end_t:
            row = random.randint(1, max(1, self.rows - 1))
            col = random.randint(1, max(1, self.cols - 1))
            ch  = random.choice(chars)
            move_cursor(row, col)
            color = a1 if random.random() > 0.65 else dim
            safe_print(f"{color}{ch}{C.RESET}", end="", flush=True)
            time.sleep(0.002)

    # ── Phase 2: scanlines ───────────────────────────────────────────

    def _scanlines(self):
        a1 = self.theme["accent1"]
        a2 = self.theme["accent2"]
        clear_screen()
        for row in range(1, self.rows + 1, 2):
            move_cursor(row, 1)
            safe_print(f"{a1}{'─' * self.cols}{C.RESET}", end="", flush=True)
            time.sleep(0.006)
        time.sleep(0.12)

    # ── Phase 3: logo with glitch ────────────────────────────────────

    def _glitch_text(self, text: str, color: str, iterations: int = 2):
        glitch_chars = "▓▒░█▄▀■□●○◆◇╬╫"
        for i in range(iterations):
            intensity = 0.18 - i * 0.06
            corrupted = "".join(
                random.choice(glitch_chars) if random.random() < intensity else c
                for c in text
            )
            safe_print(f"\r{color}{corrupted}{C.RESET}", end="", flush=True)
            time.sleep(0.055)
        safe_print(f"\r{color}{text}{C.RESET}", flush=True)

    def _show_logo(self):
        clear_screen()
        logo_color = self.theme["logo_color"]
        a2         = self.theme["accent2"]
        a3         = self.theme["accent3"]

        for line in ASCII_LOGO.split("\n"):
            centered = center_text(line, self.cols)
            self._glitch_text(centered, logo_color, iterations=1)
            time.sleep(0.035)

        safe_print()
        tagline = "◈  NEXT-GEN AI-POWERED PYTHON TERMINAL  •  BY ARYAN SINGH  ◈"
        self._glitch_text(center_text(tagline, self.cols), a2, iterations=2)
        safe_print()

    # ── Phase 4: boot bars ───────────────────────────────────────────

    def _animated_bar(self, label: str, color: str, bar_w: int = 38, delay: float = 0.010):
        a1 = self.theme["accent1"]
        a2 = self.theme["accent2"]
        a3 = self.theme["accent3"]
        safe_print(f"  {color}{label:<24}{C.RESET} [", end="", flush=True)
        for i in range(bar_w):
            frac = i / bar_w
            bar_c = a1 if frac < 0.33 else (a2 if frac < 0.66 else a3)
            safe_print(f"{bar_c}█{C.RESET}", end="", flush=True)
            time.sleep(delay)
        safe_print(f"] {C.BRIGHT_GREEN}OK{C.RESET}")

    def _boot_sequence(self):
        a1, a2, a3 = self.theme["accent1"], self.theme["accent2"], self.theme["accent3"]
        items = [
            ("Neural Core",          a1),
            ("Execution Engine",     a2),
            ("Memory Manager",       a3),
            ("History Database",     a2),
            ("PYCORE AI Interface",  a1),
            ("Theme System",         a3),
            ("Shell Interface",      a1),
        ]
        for label, color in items:
            self._animated_bar(label, color, bar_w=36, delay=0.009)

        safe_print()
        ready = "[ SYSTEM READY — PYCORE AI ONLINE ]"
        for _ in range(4):
            safe_print(f"\r  {a1}{C.BOLD}{ready}{C.RESET}", end="", flush=True)
            time.sleep(0.22)
            safe_print(f"\r  {a3}{C.BOLD}{ready}{C.RESET}", end="", flush=True)
            time.sleep(0.22)
        safe_print(f"\r  {a1}{C.BOLD}{ready}{C.RESET}")
        time.sleep(0.4)

    # ── Master play ──────────────────────────────────────────────────

    def play(self):
        hide_cursor()
        try:
            clear_screen()
            self._matrix_rain(duration=1.0)
            self._scanlines()
            self._show_logo()
            self._boot_sequence()
        except Exception:
            pass  # animation errors should never crash the shell
        finally:
            show_cursor()


# ══════════════════════════════════════════════════════════════════════
#  SQLITE HISTORY / SESSION DATABASE
# ══════════════════════════════════════════════════════════════════════

class SessionDatabase:
    """Thread-safe SQLite wrapper for session and command history."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock   = threading.Lock()
        self.conn    = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")   # better concurrent access
        self._init_tables()

    def _init_tables(self):
        with self._lock:
            cur = self.conn.cursor()
            cur.executescript("""
                CREATE TABLE IF NOT EXISTS history (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    session   TEXT    NOT NULL,
                    timestamp TEXT    NOT NULL,
                    code      TEXT    NOT NULL,
                    success   INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    name      TEXT    NOT NULL,
                    started   TEXT    NOT NULL,
                    ended     TEXT,
                    commands  INTEGER DEFAULT 0,
                    errors    INTEGER DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_history_session ON history(session);
            """)
            self.conn.commit()

    def new_session(self, name: str) -> int:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                "INSERT INTO sessions (name, started) VALUES (?, ?)",
                (name, datetime.datetime.now().isoformat())
            )
            self.conn.commit()
            return cur.lastrowid  # type: ignore[return-value]

    def end_session(self, session_id: int, commands: int, errors: int = 0):
        with self._lock:
            self.conn.execute(
                "UPDATE sessions SET ended=?, commands=?, errors=? WHERE id=?",
                (datetime.datetime.now().isoformat(), commands, errors, session_id)
            )
            self.conn.commit()

    def add_history(self, session_name: str, code_src: str, success: bool):
        with self._lock:
            self.conn.execute(
                "INSERT INTO history (session, timestamp, code, success) VALUES (?,?,?,?)",
                (session_name, datetime.datetime.now().isoformat(), code_src, int(success))
            )
            self.conn.commit()

    def get_history(self, limit: int = 50) -> list:
        with self._lock:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT timestamp, code, success FROM history ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return cur.fetchall()

    def close(self):
        try:
            with self._lock:
                self.conn.close()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════
#  PYCORE BUILT-IN AI ASSISTANT  (offline mode / local hints)
# ══════════════════════════════════════════════════════════════════════

class PYCOREAI:
    """Local AI-style coding assistant — works without API key."""

    ERROR_HINTS: dict = {
        "NameError": (
            "You used a variable or function that hasn't been defined yet.\n"
            "  ▸ Check spelling — Python is case-sensitive (myVar ≠ myvar).\n"
            "  ▸ Assign the variable before using it.\n"
            "  ▸ Use :vars to see what's currently in scope."
        ),
        "SyntaxError": (
            "Python can't understand your code structure.\n"
            "  ▸ Check for missing colons after if / for / def / class.\n"
            "  ▸ Count parentheses — every ( needs a matching ).\n"
            "  ▸ Look for mismatched quotes ' vs \".\n"
            "  ▸ Walrus operator := is Python 3.8+ only."
        ),
        "IndentationError": (
            "Your indentation is inconsistent.\n"
            "  ▸ Use 4 spaces per indent level throughout.\n"
            "  ▸ Never mix tabs and spaces.\n"
            "  ▸ Every block after : must be indented."
        ),
        "TabError": (
            "You mixed tabs and spaces.\n"
            "  ▸ Convert all tabs to 4 spaces.\n"
            "  ▸ Most editors have an 'untabify' or 'convert indentation' option."
        ),
        "TypeError": (
            "You mixed incompatible types or called something incorrectly.\n"
            "  ▸ Check if you're calling something that isn't a function.\n"
            "  ▸ Verify argument types (str vs int vs list, etc.).\n"
            "  ▸ Use type() to inspect objects: print(type(x))"
        ),
        "ValueError": (
            "A function received the right type but an invalid value.\n"
            "  ▸ int('abc') fails — only numeric strings work.\n"
            "  ▸ Check the expected value range for this function."
        ),
        "IndexError": (
            "You accessed a list/tuple index that doesn't exist.\n"
            "  ▸ Lists are 0-indexed: first item is [0], last is [-1].\n"
            "  ▸ Use len() to check the size before indexing.\n"
            "  ▸ Use a try/except IndexError to handle it safely."
        ),
        "KeyError": (
            "That key doesn't exist in your dictionary.\n"
            "  ▸ Use dict.get(key, default) for safe access.\n"
            "  ▸ Use 'key in mydict' to check before accessing.\n"
            "  ▸ Print dict.keys() to see available keys."
        ),
        "AttributeError": (
            "The object doesn't have that attribute or method.\n"
            "  ▸ Use dir(obj) to see all available attributes.\n"
            "  ▸ Check for typos in the method name.\n"
            "  ▸ Make sure the object is the type you think it is: type(obj)"
        ),
        "ZeroDivisionError": (
            "You divided by zero — not allowed in math.\n"
            "  ▸ Check the denominator before dividing.\n"
            "  ▸ Guard it: result = x / y if y != 0 else 0"
        ),
        "ImportError": (
            "Python can't find that module.\n"
            "  ▸ Check the module name for typos.\n"
            "  ▸ Only stdlib modules work here."
        ),
        "ModuleNotFoundError": (
            "That module is not installed or doesn't exist.\n"
            "  ▸ Third-party packages (pandas, numpy, requests…) are NOT\n"
            "    available here — this shell uses only Python stdlib.\n"
            "  ▸ Stdlib alternatives: csv/sqlite3 (pandas), math (numpy),\n"
            "    urllib.request (requests).\n"
            "  ▸ To use it, run your script in a normal terminal after pip install."
        ),
        "RecursionError": (
            "Your function called itself too many times (infinite recursion).\n"
            "  ▸ Add a base case that stops the recursion.\n"
            "  ▸ Example: if n <= 0: return 0\n"
            "  ▸ Trace the logic to see why the base case isn't reached."
        ),
        "FileNotFoundError": (
            "That file path doesn't exist.\n"
            "  ▸ Run: print(pathlib.Path('.').resolve()) to see current dir.\n"
            "  ▸ Verify the filename and path are spelled correctly.\n"
            "  ▸ Use pathlib.Path('file').exists() to check first."
        ),
        "PermissionError": (
            "You don't have permission to access that file or directory.\n"
            "  ▸ Check file permissions with os.stat().\n"
            "  ▸ On Windows, make sure the file isn't open in another program."
        ),
        "MemoryError": (
            "You ran out of memory.\n"
            "  ▸ Avoid generating huge lists — use generators (yield) instead.\n"
            "  ▸ Process data in chunks rather than loading it all at once."
        ),
        "StopIteration": (
            "An iterator ran out of items.\n"
            "  ▸ Use for loops instead of manual next() calls.\n"
            "  ▸ Use next(it, default) to supply a fallback value."
        ),
        "OverflowError": (
            "A numeric value is too large for Python to handle.\n"
            "  ▸ Python ints are unlimited; this is likely a float issue.\n"
            "  ▸ Use math.inf for infinity comparisons."
        ),
        "OSError": (
            "An operating system error occurred.\n"
            "  ▸ Check if the file/directory exists and you have access.\n"
            "  ▸ On Windows, check if the path uses forward slashes."
        ),
        "RuntimeError": (
            "A runtime error occurred that doesn't fit another category.\n"
            "  ▸ Read the message carefully — it usually tells you exactly what went wrong.\n"
            "  ▸ Check if you're calling code in the right order."
        ),
        "NotImplementedError": (
            "A method or function is not implemented yet.\n"
            "  ▸ If this is your code: fill in the method body.\n"
            "  ▸ If it's a library: check for a subclass that implements it."
        ),
        "AssertionError": (
            "An assert statement failed.\n"
            "  ▸ The condition after 'assert' evaluated to False.\n"
            "  ▸ Add a message: assert condition, 'What went wrong'"
        ),
        "UnicodeDecodeError": (
            "Failed to decode bytes as text.\n"
            "  ▸ When opening files use: open('file', encoding='utf-8')\n"
            "  ▸ For unknown encodings try: open('file', errors='replace')"
        ),
        "UnicodeEncodeError": (
            "Failed to encode text to bytes.\n"
            "  ▸ Use: text.encode('utf-8', errors='replace')\n"
            "  ▸ On Windows, set: sys.stdout.reconfigure(encoding='utf-8')"
        ),
    }

    TIPS: list = [
        "Use list comprehensions: [x**2 for x in range(10)]",
        "f-strings are fast and readable: f'Hello {name}, age {age}'",
        "enumerate() gives index + value: for i, v in enumerate(lst)",
        "zip() combines two lists: for a, b in zip(names, scores)",
        "dict.get(key, default) is safer than dict[key]",
        "*args and **kwargs let functions accept any arguments",
        "Use _ as a throwaway variable: for _ in range(5): ...",
        "any() and all() work on iterables: any(x > 0 for x in lst)",
        "collections.Counter is great for frequency counting",
        "lambda x: x*2 creates a quick inline function",
        "str.join() is much faster than += in loops",
        "Use 'with open(...)' to auto-close files safely",
        "sorted(lst, key=lambda x: x[1]) sorts by second element",
        "@dataclass auto-generates __init__, __repr__, __eq__",
        "Walrus operator: if (n := len(a)) > 10: print(n)",
        "Use pathlib.Path instead of os.path — much cleaner",
        "collections.defaultdict(list) avoids KeyError on new keys",
        "Use math.isclose(a, b) instead of a == b for floats",
        "Set comprehension: {x for x in lst if x > 0}",
        "functools.lru_cache caches function results automatically",
        "Use itertools.chain to flatten nested iterables",
        "textwrap.dedent() removes common leading whitespace",
        "sys.getsizeof() tells you the memory size of an object",
        "Use __slots__ in classes to reduce memory usage",
        "context managers (with) work with any __enter__/__exit__ object",
    ]

    _STDLIB_ALTERNATIVES: dict = {
        "pandas"     : "csv, sqlite3  (for tables/data)",
        "numpy"      : "math, array, statistics  (for numbers/math)",
        "requests"   : "urllib.request  (for HTTP requests)",
        "flask"      : "(web frameworks need pip — not available here)",
        "django"     : "(web frameworks need pip — not available here)",
        "scipy"      : "math, statistics  (limited alternative)",
        "matplotlib" : "(plot libs need pip — write CSV and plot elsewhere)",
        "PIL"        : "(image libs need pip — not available here)",
        "cv2"        : "(OpenCV needs pip — not available here)",
        "sklearn"    : "(ML libs need pip — not available here)",
        "tensorflow" : "(ML libs need pip — not available here)",
        "torch"      : "(ML libs need pip — not available here)",
        "sqlalchemy" : "sqlite3  (built-in SQL support)",
        "pymongo"    : "(use sqlite3 as a local alternative)",
        "aiohttp"    : "urllib.request + threading  (async-style HTTP)",
        "dotenv"     : "os.environ + json  (for config/env vars)",
        "pydantic"   : "dataclasses + typing  (built-in validation pattern)",
        "click"      : "argparse  (built-in CLI parsing)",
        "rich"       : "(ANSI colors available built-in here)",
        "tqdm"       : "(write a simple for-loop progress bar)",
        "yaml"       : "json  (use JSON format instead)",
        "toml"       : "json  (use JSON format instead)",
        "boto3"      : "urllib.request  (for basic AWS HTTP calls)",
        "paramiko"   : "(SSH libs need pip — not available here)",
        "cryptography": "hashlib, hmac, secrets  (built-in crypto)",
        "jwt"        : "hmac + hashlib + base64  (manual JWT)",
        "celery"     : "threading + queue  (for background tasks)",
        "redis"      : "(use sqlite3 for local caching)",
    }

    def __init__(self, theme: dict):
        self.theme = theme

    def get_error_hint(self, exc_type_name: str, exc_msg: str) -> str:
        hint = self.ERROR_HINTS.get(exc_type_name)
        if hint:
            return hint
        # Check if it's a subclass name we recognize partially
        for known, h in self.ERROR_HINTS.items():
            if known.lower() in exc_type_name.lower():
                return h
        return (
            f"Unexpected error: {exc_type_name}\n"
            "  ▸ Read the full traceback — it shows exactly where it broke.\n"
            "  ▸ Search Python docs for this error type.\n"
            "  ▸ Use :explain to analyse the last executed code."
        )

    def random_tip(self) -> str:
        return random.choice(self.TIPS)

    def explain_code(self, code_str: str) -> str:
        """Lightweight code explanation using AST analysis."""
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            return f"Can't parse code: {e}"

        findings = []
        counts   = collections.Counter()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                args_n = len(node.args.args)
                findings.append(f"✦ Defines function '{node.name}' with {args_n} argument(s)")
            elif isinstance(node, ast.AsyncFunctionDef):
                findings.append(f"✦ Defines async function '{node.name}'")
            elif isinstance(node, ast.ClassDef):
                bases = [getattr(b, 'id', '?') for b in node.bases]
                base_s = f" (inherits: {', '.join(bases)})" if bases else ""
                findings.append(f"✦ Defines class '{node.name}'{base_s}")
            elif isinstance(node, ast.For):
                counts["for_loops"] += 1
            elif isinstance(node, ast.While):
                counts["while_loops"] += 1
            elif isinstance(node, ast.If):
                counts["if_stmts"] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    mods = [a.name for a in node.names]
                else:
                    mods = [f"{node.module}.{a.name}" for a in node.names]
                findings.append(f"✦ Imports: {', '.join(mods)}")
            elif isinstance(node, ast.ListComp):
                counts["list_comps"] += 1
            elif isinstance(node, ast.DictComp):
                counts["dict_comps"] += 1
            elif isinstance(node, ast.SetComp):
                counts["set_comps"] += 1
            elif isinstance(node, ast.GeneratorExp):
                counts["generators"] += 1
            elif isinstance(node, ast.Lambda):
                counts["lambdas"] += 1
            elif isinstance(node, ast.Try):
                counts["try_blocks"] += 1

        for name, count in counts.items():
            label = name.replace("_", " ")
            if count:
                findings.append(f"✦ Contains {count} {label}")

        if not findings:
            findings = ["✦ Simple expression or statement"]

        return "\n  ".join(dict.fromkeys(findings))  # preserve order, remove dupes

    def suggest_fix(self, exc_type_name: str, exc_msg: str, code_str: str) -> str:
        if exc_type_name == "NameError":
            m = re.search(r"name '(.+?)' is not defined", exc_msg)
            if m:
                undef = m.group(1)
                builtins_dict = vars(__builtins__) if isinstance(__builtins__, dict) else vars(__builtins__)  # type: ignore
                if undef in builtins_dict:
                    return f"'{undef}' is a builtin — did you accidentally shadow it?"
                if keyword.iskeyword(undef):
                    return f"'{undef}' is a Python keyword — can't use it as a variable."
                return f"Try defining it first:  {undef} = <value>"

        if exc_type_name == "TypeError":
            if "NoneType" in exc_msg:
                return "A function returned None — check your return statement."
            if "takes" in exc_msg and "argument" in exc_msg:
                return "Wrong number of arguments passed to the function."

        if exc_type_name == "AttributeError":
            m = re.search(r"'(.+?)' object has no attribute '(.+?)'", exc_msg)
            if m:
                obj_t, attr = m.group(1), m.group(2)
                return f"'{obj_t}' has no '.{attr}' — check spelling or use dir() to inspect."

        if exc_type_name in ("ModuleNotFoundError", "ImportError"):
            m = re.search(r"No module named '([^']+)'", exc_msg)
            if m:
                pkg = m.group(1).split(".")[0]
                alt = self._STDLIB_ALTERNATIVES.get(pkg)
                if alt:
                    return f"stdlib alternative for '{pkg}': {alt}"
                return (
                    f"'{pkg}' needs pip. In a normal terminal run: "
                    f"pip install {pkg}"
                )

        if exc_type_name == "IndexError":
            return "Check the list length with len() before indexing."

        if exc_type_name == "KeyError":
            m = re.search(r"KeyError: (.+)", exc_msg)
            if m:
                key = m.group(1)
                return f"Key {key} not found. Use dict.get({key}, default) for safe access."

        if exc_type_name == "ZeroDivisionError":
            return "Guard the division: result = a / b if b != 0 else 0"

        return "Read the traceback line number and review your logic there."

    def print_error_report(self, exc_type, exc_val, tb):
        """Print a clean local error panel (no API needed)."""
        t  = self.theme
        a1, a2, a3 = t["accent1"], t["accent2"], t["accent3"]
        err = t["error_color"]
        w, _ = get_terminal_size()
        w    = max(60, min(w, 140))

        exc_name = type(exc_val).__name__
        exc_msg  = str(exc_val)

        tb_lines = traceback.format_tb(tb) if tb else []
        last_tb  = tb_lines[-1].strip() if tb_lines else ""

        border = "═" * (w - 4)
        inner_border = "─" * (w - 4)

        safe_print(f"\n  {err}╔{border}╗{C.RESET}")
        safe_print(f"  {err}║{C.RESET}  {C.BOLD}{err}⚡ PYCORE AI  —  LOCAL ERROR REPORT{C.RESET}{' '*(w-38)}{err}║{C.RESET}")
        safe_print(f"  {err}╠{border}╣{C.RESET}")

        # Error line
        msg_trunc = exc_msg[:w - 24]
        safe_print(f"  {err}║{C.RESET}  {C.BOLD}{err}{exc_name}:{C.RESET} {err}{msg_trunc}{C.RESET}")

        # Traceback snippet
        if last_tb:
            for part in last_tb.split("\n"):
                if part.strip():
                    trunc = part.strip()[:w - 12]
                    safe_print(f"  {err}║{C.RESET}  {C.DIM}  ↳ {trunc}{C.RESET}")

        safe_print(f"  {err}╠{inner_border}╣{C.RESET}")
        safe_print(f"  {err}║{C.RESET}  {a2}{C.BOLD}🤖 PYCORE AI Built-in Hint:{C.RESET}")

        hint = self.get_error_hint(exc_name, exc_msg)
        for line in hint.split("\n"):
            safe_print(f"  {err}║{C.RESET}  {a3}{line}{C.RESET}")

        fix = self.suggest_fix(exc_name, exc_msg, "")
        if fix:
            safe_print(f"  {err}║{C.RESET}")
            safe_print(f"  {err}║{C.RESET}  {a1}{C.BOLD}💡 Quick Fix:{C.RESET} {a1}{fix}{C.RESET}")

        safe_print(f"  {err}╚{border}╝{C.RESET}\n")


# ══════════════════════════════════════════════════════════════════════
#  PYTHON EXECUTION ENGINE
# ══════════════════════════════════════════════════════════════════════

class ExecutionEngine:
    """Executes Python code with persistent namespace and separate stdout/stderr capture."""

    _PRELOADED = {
        "math", "random", "datetime", "os", "sys",
        "json", "pathlib", "platform", "time", "re",
        "collections", "itertools", "functools",
    }

    def __init__(self):
        self.namespace: dict = {
            "__name__" : "__PYCORE_shell__",
            "__doc__"  : None,
        }
        # Pre-import commonly needed stdlib modules
        import collections as _c, itertools as _it, functools as _ft
        self.namespace.update({
            "math"       : math,
            "random"     : random,
            "datetime"   : datetime,
            "os"         : os,
            "sys"        : sys,
            "json"       : json,
            "pathlib"    : pathlib,
            "platform"   : platform,
            "time"       : time,
            "re"         : re,
            "collections": _c,
            "itertools"  : _it,
            "functools"  : _ft,
        })
        self.compiler  = codeop.CommandCompiler()
        self.exec_count: int = 0
        self.error_count: int = 0
        self.total_time: float = 0.0

    def get_user_vars(self) -> dict:
        skip = self._PRELOADED | {
            "__name__", "__doc__", "__builtins__", "__spec__",
        }
        return {k: v for k, v in self.namespace.items() if k not in skip}

    def compile_code(self, source: str):
        """Returns compiled code or None if incomplete; raises SyntaxError on bad syntax."""
        return self.compiler(source)

    def execute(self, source: str) -> "tuple[str, tuple|None, float]":
        """
        Execute source code in the persistent namespace.
        Returns (output_str, error_info, elapsed_seconds).
        error_info = None on success, (exc_type, exc_val, tb) on error.
        Stdout and stderr are captured separately; stderr is appended to output.
        """
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        cap_stdout = io.StringIO()
        cap_stderr = io.StringIO()
        sys.stdout = cap_stdout
        sys.stderr = cap_stderr

        error_info = None
        elapsed    = 0.0
        result_val = None

        try:
            t0 = time.perf_counter()
            # Try eval first (for expressions that produce displayable values)
            try:
                compiled_eval = compile(source, "<PYCORE>", "eval")
                result_val    = eval(compiled_eval, self.namespace)
            except SyntaxError:
                compiled_exec = compile(source, "<PYCORE>", "exec")
                exec(compiled_exec, self.namespace)
            elapsed = time.perf_counter() - t0
            self.exec_count += 1
            self.total_time += elapsed
        except KeyboardInterrupt:
            error_info = (KeyboardInterrupt, KeyboardInterrupt("Interrupted"), None)
            self.error_count += 1
        except SystemExit as e:
            error_info = (SystemExit, e, None)
        except Exception:
            error_info = sys.exc_info()
            self.error_count += 1
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        output = cap_stdout.getvalue()
        err_out= cap_stderr.getvalue()

        if err_out.strip():
            output += err_out  # append stderr to output so it's visible

        # If eval produced a value and nothing was printed, show repr
        if result_val is not None and not output.strip() and error_info is None:
            output = repr(result_val) + "\n"

        return output, error_info, elapsed

    @property
    def success_rate(self) -> float:
        total = self.exec_count + self.error_count
        return (self.exec_count / total * 100) if total else 100.0


# ══════════════════════════════════════════════════════════════════════
#  COMMAND HISTORY MANAGER  (O(1) operations via deque)
# ══════════════════════════════════════════════════════════════════════

class HistoryManager:
    def __init__(self, max_size: int = 2000):
        self._deque: "collections.deque[str]" = collections.deque(maxlen=max_size)
        self.pos   = 0

    @property
    def history(self) -> list:
        return list(self._deque)

    def add(self, line: str):
        if line.strip() and (not self._deque or self._deque[-1] != line):
            self._deque.append(line)
        self.pos = len(self._deque)

    def prev(self) -> str:
        if self._deque and self.pos > 0:
            self.pos -= 1
            return list(self._deque)[self.pos]
        return ""

    def next(self) -> str:
        if self.pos < len(self._deque) - 1:
            self.pos += 1
            return list(self._deque)[self.pos]
        self.pos = len(self._deque)
        return ""

    def save_to_file(self, path: str) -> bool:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(list(self._deque), f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def load_from_file(self, path: str) -> bool:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, str):
                        self._deque.append(item)
            self.pos = len(self._deque)
            return True
        except Exception:
            return False


# ══════════════════════════════════════════════════════════════════════
#  MAIN SHELL CLASS
# ══════════════════════════════════════════════════════════════════════

class PYCOREShell:
    """Main shell — orchestrates UI, execution engine, AI, and all commands."""

    VERSION   = "3.0.0"
    AUTHOR    = "Aryan Singh"

    GITHUB   = "https://github.com/aryansingh783"
    INSTAGRAM= "@aryan.singh.783"
    DB_FILE   = str(pathlib.Path.home() / ".pycore_shell_history.db")
    HIST_FILE = str(pathlib.Path.home() / ".pycore_shell_hist.json")

    COMMANDS: dict = {
        ":help"    : "Show this help screen",
        ":clear"   : "Clear the terminal  (alias: :cls)",
        ":cls"     : "Alias for :clear",
        ":exit"    : "Exit PyCore AI Shell  (alias: :quit)",
        ":quit"    : "Alias for :exit",
        ":vars"    : "Inspect runtime variables",
        ":history" : "Show command history (last 30)",
        ":about"   : "About PyCore AI Shell",
        ":theme"   : "Switch theme  e.g. :theme matrix",
        ":reset"   : "Reset the runtime namespace",
        ":save"    : "Save history to file",
        ":tip"     : "Get a random Python coding tip",
        ":explain" : "Explain last executed code (AST analysis)",
        ":stats"   : "Show session statistics",
        ":time"    : "Toggle execution time display",
        ":sys"     : "Show system information",
        ":run"     : "Run a Python file  e.g. :run script.py",
        ":reload"  : "Re-run the last :run file",
        ":cd"      : "Change working directory  e.g. :cd /path",
        ":addkey"  : "Add a PYCORE API key  e.g. :addkey AIza...",
        ":keys"    : "List all saved PYCORE API keys",
        ":usekey"  : "Switch active key by index  e.g. :usekey 1",
        ":delkey"  : "Delete a key by index  e.g. :delkey 0",
        ":ai"      : "Toggle/status PYCORE AI  :ai on | off | status",
        ":testai"  : "Test PYCORE API connection",
    }

    def __init__(self):
        enable_ansi_windows()

        self.cfg          = ConfigLoader()
        self.theme_name   = self.cfg.get("theme", "cyberpunk")
        if self.theme_name not in THEMES:
            self.theme_name = "cyberpunk"
        self.theme        = THEMES[self.theme_name]

        self.engine       = ExecutionEngine()
        self.history      = HistoryManager()
        self.ai           = PYCOREAI(self.theme)
        self.show_time    = self.cfg.get("show_time", True)
        self.session_name = datetime.datetime.now().strftime("session_%Y%m%d_%H%M%S")
        self.start_time   = datetime.datetime.now()
        self.last_code    = ""
        self.last_run_file: "str | None" = None

        # SQLite session DB
        try:
            self.db         = SessionDatabase(self.DB_FILE)
            self.session_id = self.db.new_session(self.session_name)
        except Exception:
            self.db         = None
            self.session_id = 0

        # Load saved history
        self.history.load_from_file(self.HIST_FILE)

        # PYCORE AI stack
        self.gemini    = PYCOREManager(self.cfg)
        self.gemini_ui = PYCOREUI(self.theme)

        # Register atexit cleanup so DB always closes on crash/exit
        atexit.register(self._atexit_cleanup)

    # ── Cleanup ──────────────────────────────────────────────────────

    def _atexit_cleanup(self):
        """Called automatically on any exit — saves state."""
        try:
            self.history.save_to_file(self.HIST_FILE)
        except Exception:
            pass
        try:
            if self.db:
                self.db.end_session(
                    self.session_id,
                    self.engine.exec_count,
                    self.engine.error_count
                )
                self.db.close()
        except Exception:
            pass

    # ── Header ───────────────────────────────────────────────────────

    def print_header(self):
        t   = self.theme
        a1, a2, a3 = t["accent1"], t["accent2"], t["accent3"]
        w, _ = get_terminal_size()
        w   = max(60, w)
        bc  = t["border_char"]
        now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        py_ver = platform.python_version()
        uptime = str(datetime.datetime.now() - self.start_time).split(".")[0]

        ai_icon = "🟢" if self.gemini.is_ready() else "🔴"

        top = t["corner_tl"] + bc * (w - 2) + t["corner_tr"]
        bot = t["corner_bl"] + bc * (w - 2) + t["corner_br"]

        # Title row
        plain_title = f" PYCORE AI SHELL  v{self.VERSION}  ·  Python {py_ver}  ·  {now}  ↑{uptime} "
        pad_title   = max(0, w - 2 - len(plain_title))
        title_row   = (
            f" {a1}{C.BOLD}PYCORE AI SHELL{C.RESET} "
            f"{a2}v{self.VERSION}  ·  Python {py_ver}{C.RESET}"
            f"{' ' * (pad_title // 2)}"
            f"{a3}{now}  ↑{uptime}{C.RESET} "
        )

        # Status row
        uv_count    = len(self.engine.get_user_vars())
        hist_count  = len(self.history.history)
        plain_status= (
            f" Theme:{self.theme_name.upper()}  "
            f"Cmds:{self.engine.exec_count}  "
            f"Errs:{self.engine.error_count}  "
            f"Vars:{uv_count}  "
            f"Hist:{hist_count}  "
            f"AI:{ai_icon}  "
            f"Type :help "
        )
        pad_status  = max(0, w - 2 - len(plain_status))
        status_row  = (
            f" {a1}Theme:{C.RESET}{a3}{self.theme_name.upper()}{C.RESET}  "
            f"{a1}Cmds:{C.RESET}{a2}{self.engine.exec_count}{C.RESET}  "
            f"{a1}Errs:{C.RESET}{t['error_color']}{self.engine.error_count}{C.RESET}  "
            f"{a1}Vars:{C.RESET}{a2}{uv_count}{C.RESET}  "
            f"{a1}Hist:{C.RESET}{a2}{hist_count}{C.RESET}  "
            f"{a1}AI:{C.RESET}{ai_icon}  "
            f"{a3}Type :help{C.RESET}"
            f"{' ' * pad_status}"
        )

        safe_print(f"{a1}{top}{C.RESET}")
        safe_print(f"{a1}{t['side']}{C.RESET}{title_row}{a1}{t['side']}{C.RESET}")
        safe_print(f"{a1}{t['side']}{C.RESET}{status_row}{a1}{t['side']}{C.RESET}")
        safe_print(f"{a1}{bot}{C.RESET}")

    # ── Prompt ───────────────────────────────────────────────────────

    def get_prompt(self, secondary: bool = False) -> str:
        t  = self.theme
        a1 = t["prompt_color"]
        a2 = t["accent2"]
        if secondary:
            return f"{a2}...{C.RESET} "
        return f"{a1}PyCore{C.RESET}{C.DIM}>{C.RESET}{a1}>{C.RESET}{C.DIM}>{C.RESET} "

    # ── Input ────────────────────────────────────────────────────────

    def read_input(self, prompt_str: str) -> str:
        try:
            return input(prompt_str)
        except EOFError:
            return ":exit"
        except KeyboardInterrupt:
            safe_print()
            return ""

    # ══════════════════════════════════════════════════════════════════
    #  COMMANDS
    # ══════════════════════════════════════════════════════════════════

    def cmd_help(self):
        t = self.theme
        a1, a2, a3 = t["accent1"], t["accent2"], t["accent3"]
        w, _ = get_terminal_size()
        w = max(60, min(w, 120))
        safe_print()
        safe_print(f"  {a1}{'═'*(w-4)}{C.RESET}")
        safe_print(f"  {a1}{C.BOLD}{'PYCORE AI SHELL  —  COMMAND REFERENCE':^{w-4}}{C.RESET}")
        safe_print(f"  {a1}{'═'*(w-4)}{C.RESET}")
        for cmd, desc in self.COMMANDS.items():
            safe_print(f"  {a1}{cmd:<12}{C.RESET}  {a2}{desc}{C.RESET}")
        safe_print(f"  {a1}{'─'*(w-4)}{C.RESET}")
        safe_print(f"  {a3}Any other input is executed as Python code.{C.RESET}")
        safe_print(f"  {a3}Multi-line: end a block with a blank line.{C.RESET}")
        safe_print(f"  {a1}{'═'*(w-4)}{C.RESET}\n")

    def cmd_vars(self):
        t = self.theme
        a1, a2, a3 = t["accent1"], t["accent2"], t["accent3"]
        uv = self.engine.get_user_vars()
        w, _ = get_terminal_size()
        col_w = min(w - 4, 80)

        # Type icons for common types
        _icons = {
            "int": "🔢", "float": "🔢", "str": "📝", "bool": "⚡",
            "list": "📋", "dict": "🗂", "tuple": "📦", "set": "🔵",
            "NoneType": "∅", "function": "λ", "type": "🔷",
        }

        safe_print()
        safe_print(f"  {a1}{'─'*col_w}{C.RESET}")
        safe_print(f"  {a1}{C.BOLD}{'RUNTIME VARIABLES':^{col_w}}{C.RESET}")
        safe_print(f"  {a1}{'─'*col_w}{C.RESET}")

        if not uv:
            safe_print(f"  {a3}(no user-defined variables yet){C.RESET}")
        else:
            safe_print(f"  {a1}{'Name':<20}{'Type':<14}{'Value'}{C.RESET}")
            safe_print(f"  {C.DIM}{'·'*col_w}{C.RESET}")
            for name, val in uv.items():
                typ  = type(val).__name__
                icon = _icons.get(typ, "·")
                rval = repr(val)
                if len(rval) > 45:
                    rval = rval[:42] + "..."
                safe_print(
                    f"  {a1}{name:<20}{C.RESET}"
                    f"{a2}{icon} {typ:<12}{C.RESET}"
                    f"{a3}{rval}{C.RESET}"
                )
        safe_print(f"  {a1}{'─'*col_w}{C.RESET}\n")

    def cmd_history(self):
        t  = self.theme
        a1, a2 = t["accent1"], t["accent2"]
        hist = self.history.history[-30:]
        safe_print()
        safe_print(f"  {a1}── COMMAND HISTORY (last {len(hist)}) ──{C.RESET}")
        if not hist:
            safe_print(f"  {a2}(no history yet){C.RESET}")
        else:
            for i, item in enumerate(hist, 1):
                first_line = item.split("\n")[0][:80]
                safe_print(f"  {a1}{i:>3}.{C.RESET} {a2}{first_line}{C.RESET}")
        safe_print()

    def cmd_about(self):
        t = self.theme
        a1, a2, a3 = t["accent1"], t["accent2"], t["accent3"]
        safe_print()
        for line in ASCII_LOGO.split("\n"):
            if line.strip():
                safe_print(f"  {a1}{line}{C.RESET}")
        safe_print()
        info = [
            ("Shell",       f"PyCore AI Shell v{self.VERSION}"),
            ("Python",      f"{platform.python_version()} ({platform.python_implementation()})"),
            ("Platform",    platform.platform()),
            ("Processor",   platform.processor() or "Unknown"),
            ("Author",      self.AUTHOR),
            ("AI Prompt",   f"Built-in v{PROMPT_VERSION} (no info.txt needed)"),
            ("Themes",      ", ".join(THEMES.keys())),
            ("Session",     self.session_name),
            ("DB",          self.DB_FILE),
        ]
        for label, val in info:
            safe_print(f"  {a1}{label:<14}{C.RESET}{a2}{val}{C.RESET}")
        safe_print()

    def cmd_theme(self, args: list):
        if not args:
            avail = ", ".join(THEMES.keys())
            safe_print(
                f"  Available themes: {avail}\n"
                f"  Usage: :theme <name>",
                end="\n"
            )
            return
        t_name = args[0].lower()
        if t_name not in THEMES:
            avail = ", ".join(THEMES.keys())
            print_colored(
                f"  Unknown theme '{t_name}'. Available: {avail}",
                self.theme["warn_color"]
            )
            return
        self.theme_name  = t_name
        self.theme       = THEMES[t_name]
        self.ai.theme    = self.theme
        self.gemini_ui   = PYCOREUI(self.theme)  # rebuild with new theme
        self.cfg.set("theme", t_name)
        print_colored(f"  ✔ Theme switched to {t_name.upper()}", self.theme["accent1"])

    def cmd_reset(self):
        self.engine = ExecutionEngine()
        self.ai     = PYCOREAI(self.theme)
        print_colored("  ✔ Runtime namespace reset. All variables cleared.", self.theme["accent1"])

    def cmd_save(self):
        ok = self.history.save_to_file(self.HIST_FILE)
        if ok:
            print_colored(f"  ✔ History saved → {self.HIST_FILE}", self.theme["accent1"])
        else:
            print_colored("  ✗ Failed to save history.", self.theme["error_color"])

    def cmd_tip(self):
        tip = self.ai.random_tip()
        safe_print(f"\n  💡 {self.theme['accent3']}{tip}{C.RESET}\n")

    def cmd_explain(self):
        t = self.theme
        if not self.last_code:
            print_colored(
                "  No code executed yet. Run some code first, then use :explain.",
                t["warn_color"]
            )
            return
        a1, a2 = t["accent1"], t["accent2"]
        safe_print()
        safe_print(f"  {a1}── CODE EXPLANATION ──{C.RESET}")
        safe_print(f"  {C.DIM}Code: {self.last_code.split(chr(10))[0][:60]}{C.RESET}")
        safe_print()
        explanation = self.ai.explain_code(self.last_code)
        for line in explanation.split("\n"):
            safe_print(f"  {a2}{line}{C.RESET}")
        safe_print()

    def cmd_stats(self):
        t = self.theme
        a1, a2, a3 = t["accent1"], t["accent2"], t["accent3"]
        uptime = str(datetime.datetime.now() - self.start_time).split(".")[0]
        total_ops = self.engine.exec_count + self.engine.error_count
        safe_print()
        rows = [
            ("Session",      self.session_name),
            ("Uptime",       uptime),
            ("Executions",   str(self.engine.exec_count)),
            ("Errors",       str(self.engine.error_count)),
            ("Success Rate", f"{self.engine.success_rate:.1f}%"),
            ("Total Time",   f"{self.engine.total_time:.4f}s"),
            ("Avg Time",     f"{self.engine.total_time/max(1,self.engine.exec_count)*1000:.2f}ms"),
            ("Variables",    str(len(self.engine.get_user_vars()))),
            ("History",      str(len(self.history.history))),
            ("AI Status",    "Online" if self.gemini.is_ready() else "Offline"),
            ("AI Cache",     f"{len(self.gemini._cache)} responses"),
            ("Theme",        self.theme_name.upper()),
        ]
        safe_print(f"  {a1}── SESSION STATISTICS ──{C.RESET}")
        for label, val in rows:
            safe_print(f"  {a1}{label:<18}{C.RESET}{a2}{val}{C.RESET}")
        safe_print()

    def cmd_toggle_time(self):
        self.show_time = not self.show_time
        self.cfg.set("show_time", self.show_time)
        state = "ON" if self.show_time else "OFF"
        print_colored(f"  ✔ Execution timer: {state}", self.theme["accent1"])

    def cmd_sys(self):
        t = self.theme
        a1, a2 = t["accent1"], t["accent2"]
        safe_print()
        rows = [
            ("OS",         platform.system()),
            ("Release",    platform.release()),
            ("Version",    platform.version()[:60]),
            ("Machine",    platform.machine()),
            ("Processor",  (platform.processor() or "N/A")[:50]),
            ("Python",     sys.version.split()[0]),
            ("Executable", sys.executable),
            ("CWD",        str(pathlib.Path.cwd())),
            ("Home",       str(pathlib.Path.home())),
        ]
        safe_print(f"  {a1}── SYSTEM INFORMATION ──{C.RESET}")
        for label, val in rows:
            safe_print(f"  {a1}{label:<14}{C.RESET}{a2}{val}{C.RESET}")
        safe_print()

    def cmd_run(self, args: list):
        if not args:
            print_colored("  Usage: :run <filename.py>", self.theme["warn_color"])
            return
        fpath = pathlib.Path(args[0]).expanduser()
        if not fpath.exists():
            print_colored(f"  ✗ File not found: {fpath}", self.theme["error_color"])
            return
        self.last_run_file = str(fpath)
        self._execute_file(fpath)

    def cmd_reload(self):
        if not self.last_run_file:
            print_colored("  No file has been run yet. Use :run <file> first.", self.theme["warn_color"])
            return
        fpath = pathlib.Path(self.last_run_file)
        if not fpath.exists():
            print_colored(f"  ✗ File no longer found: {fpath}", self.theme["error_color"])
            return
        self._execute_file(fpath)

    def _execute_file(self, fpath: pathlib.Path):
        t = self.theme
        try:
            source = fpath.read_text(encoding="utf-8")
            print_colored(f"  ▸ Running {fpath.name} …", t["accent2"])
            output, err_info, elapsed = self.engine.execute(source)
            if output.strip():
                print_colored(output.rstrip(), t["output_color"])
            if err_info:
                self.ai.print_error_report(*err_info)
                self._gemini_analyze(source, *err_info)
            else:
                print_colored(f"  ✔ Done in {elapsed*1000:.2f}ms", t["accent1"])
        except Exception as e:
            print_colored(f"  ✗ Error reading file: {e}", t["error_color"])

    def cmd_cd(self, args: list):
        if not args:
            safe_print(f"  {self.theme['accent2']}CWD: {pathlib.Path.cwd()}{C.RESET}")
            return
        target = pathlib.Path(args[0]).expanduser()
        try:
            os.chdir(target)
            print_colored(f"  ✔ Changed directory to: {pathlib.Path.cwd()}", self.theme["accent1"])
        except FileNotFoundError:
            print_colored(f"  ✗ Directory not found: {target}", self.theme["error_color"])
        except PermissionError:
            print_colored(f"  ✗ Permission denied: {target}", self.theme["error_color"])

    # ── PYCORE command handlers ──────────────────────────────────────

    def _cmd_addkey(self, args: list):
        t = self.theme
        if not args:
            print_colored("  Usage: :addkey <your_gemini_api_key>", t["warn_color"])
            return
        key  = args[0].strip()
        keys = self.cfg.get("pycore_api_keys", [])
        if key in keys:
            print_colored("  ⚠ Key already exists.", t["warn_color"])
            return
        keys.append(key)
        self.cfg.set("pycore_api_keys", keys)
        if len(keys) == 1:
            self.cfg.set("active_api_key", 0)
        self.gemini = PYCOREManager(self.cfg)
        print_colored(f"  ✔ API key added. Total keys: {len(keys)}", t["accent1"])

    def _cmd_keys(self):
        t      = self.theme
        keys   = self.cfg.get("pycore_api_keys", [])
        active = self.cfg.get("active_api_key", 0)
        if not keys:
            print_colored("  No API keys saved. Use :addkey to add one.", t["warn_color"])
            return
        safe_print()
        safe_print(f"  {t['accent1']}── SAVED GEMINI API KEYS ──{C.RESET}")
        for i, key in enumerate(keys):
            masked = (key[:8] + "..." + key[-4:]) if len(key) > 12 else key
            active_tag = f"  {C.BRIGHT_GREEN}← ACTIVE{C.RESET}" if i == active else ""
            safe_print(f"  {t['accent2']}[{i}] {masked}{C.RESET}{active_tag}")
        safe_print()

    def _cmd_usekey(self, args: list):
        t = self.theme
        if not args:
            print_colored("  Usage: :usekey <index>", t["warn_color"])
            return
        try:
            idx = int(args[0])
        except ValueError:
            print_colored("  Invalid index — must be a number.", t["error_color"])
            return
        keys = self.cfg.get("pycore_api_keys", [])
        if not (0 <= idx < len(keys)):
            print_colored(f"  Key index {idx} out of range (0–{len(keys)-1}).", t["error_color"])
            return
        self.cfg.set("active_api_key", idx)
        print_colored(f"  ✔ Active API key switched to index {idx}", t["accent1"])

    def _cmd_delkey(self, args: list):
        t = self.theme
        if not args:
            print_colored("  Usage: :delkey <index>", t["warn_color"])
            return
        try:
            idx = int(args[0])
        except ValueError:
            print_colored("  Invalid index — must be a number.", t["error_color"])
            return
        keys = self.cfg.get("pycore_api_keys", [])
        if not (0 <= idx < len(keys)):
            print_colored(f"  Key index {idx} out of range.", t["error_color"])
            return
        keys.pop(idx)
        self.cfg.set("pycore_api_keys", keys)
        active = self.cfg.get("active_api_key", 0)
        if keys and active >= len(keys):
            self.cfg.set("active_api_key", len(keys) - 1)
        print_colored("  ✔ API key deleted.", t["accent1"])

    def _cmd_ai(self, args: list):
        t   = self.theme
        sub = args[0].lower() if args else "status"
        a1, a2, a3 = t["accent1"], t["accent2"], t["accent3"]

        if sub == "on":
            self.gemini.enabled = True
            self.cfg.set("pycore_ai_enabled", True)
            print_colored("  ✔ PYCORE AI debugging: ON", a1)

        elif sub == "off":
            self.gemini.enabled = False
            self.cfg.set("pycore_ai_enabled", False)
            print_colored("  ✔ PYCORE AI debugging: OFF", t["warn_color"])

        elif sub == "status":
            keys    = self.cfg.get("pycore_api_keys", [])
            has_key = f"yes ({len(keys)} key(s))" if keys else "no (use :addkey)"
            state   = "ON" if self.gemini.enabled else "OFF"
            model   = self.cfg.get("pycore_model", "gemini-2.5-flash")
            status  = self.gemini.last_status
            active  = self.cfg.get("active_api_key", 0)
            safe_print()
            safe_print(f"  {a1}── GEMINI AI STATUS ──{C.RESET}")
            safe_print(f"  {a1}Enabled    {C.RESET}{a2}{state}{C.RESET}")
            safe_print(f"  {a1}API Keys   {C.RESET}{a2}{has_key}{C.RESET}")
            safe_print(f"  {a1}Active Key {C.RESET}{a2}index {active}{C.RESET}")
            safe_print(f"  {a1}Model      {C.RESET}{a2}{model}{C.RESET}")
            safe_print(f"  {a1}Last Call  {C.RESET}{a3}{status}{C.RESET}")
            safe_print(f"  {a1}Prompt Ver {C.RESET}{a2}{PROMPT_VERSION} (built-in){C.RESET}")
            safe_print(f"  {a1}Cache Size {C.RESET}{a2}{len(self.gemini._cache)} responses{C.RESET}")
            safe_print()

        else:
            print_colored("  Usage: :ai on | off | status", t["warn_color"])

    def _cmd_testai(self):
        t        = self.theme
        stop_ev  = self.gemini_ui.spinner_start("Testing PYCORE connection...")
        try:
            ok, msg = self.gemini.test_connection()
        finally:
            stop_ev.set()
            time.sleep(0.18)
        color = t["accent1"] if ok else t["error_color"]
        icon  = "✔" if ok else "✗"
        print_colored(f"  {icon} {msg}", color)

    # ── Command dispatcher ───────────────────────────────────────────

    def handle_command(self, line: str) -> bool:
        stripped = line.strip()
        if not stripped.startswith(":"):
            return False

        parts = stripped.split()
        cmd   = parts[0].lower()
        args  = parts[1:]

        dispatch = {
            ":exit"   : lambda: self._exit(),
            ":quit"   : lambda: self._exit(),
            ":help"   : lambda: self.cmd_help(),
            ":clear"  : lambda: (clear_screen(), self.print_header()),
            ":cls"    : lambda: (clear_screen(), self.print_header()),
            ":vars"   : lambda: self.cmd_vars(),
            ":history": lambda: self.cmd_history(),
            ":about"  : lambda: self.cmd_about(),
            ":theme"  : lambda: self.cmd_theme(args),
            ":reset"  : lambda: self.cmd_reset(),
            ":save"   : lambda: self.cmd_save(),
            ":tip"    : lambda: self.cmd_tip(),
            ":explain": lambda: self.cmd_explain(),
            ":stats"  : lambda: self.cmd_stats(),
            ":time"   : lambda: self.cmd_toggle_time(),
            ":sys"    : lambda: self.cmd_sys(),
            ":run"    : lambda: self.cmd_run(args),
            ":reload" : lambda: self.cmd_reload(),
            ":cd"     : lambda: self.cmd_cd(args),
            ":addkey" : lambda: self._cmd_addkey(args),
            ":keys"   : lambda: self._cmd_keys(),
            ":usekey" : lambda: self._cmd_usekey(args),
            ":delkey" : lambda: self._cmd_delkey(args),
            ":ai"     : lambda: self._cmd_ai(args),
            ":testai" : lambda: self._cmd_testai(),
        }

        handler = dispatch.get(cmd)
        if handler:
            handler()
        else:
            print_colored(
                f"  Unknown command: {cmd}  (type :help for all commands)",
                self.theme["warn_color"]
            )
        return True

    # ── Code execution ───────────────────────────────────────────────

    def should_continue_multiline(self, source: str) -> bool:
        """Return True if source is an incomplete Python block."""
        try:
            result = codeop.compile_command(source)
            return result is None
        except SyntaxError:
            return False

    def run_code(self, source: str):
        t = self.theme
        self.last_code = source

        # Record in history
        first_line = source.split("\n")[0]
        self.history.add(first_line)
        if self.db:
            try:
                self.db.add_history(self.session_name, source, True)
            except Exception:
                pass

        output, err_info, elapsed = self.engine.execute(source)

        if output.strip():
            print_colored(output.rstrip(), t["output_color"])

        if err_info:
            exc_type, exc_val, tb = err_info

            if exc_type is SystemExit:
                self._exit()

            # Update history as failure
            if self.db:
                try:
                    self.db.add_history(self.session_name, source, False)
                except Exception:
                    pass

            # Show built-in error report first
            self.ai.print_error_report(exc_type, exc_val, tb)

            # Then try PYCORE for deeper analysis
            self._gemini_analyze(source, exc_type, exc_val, tb)

        elif self.show_time and elapsed > 0.0001:
            print_colored(
                f"  {C.DIM}⏱  {elapsed*1000:.3f} ms{C.RESET}", ""
            )

    def _gemini_analyze(self, source: str, exc_type, exc_val, tb):
        """Send error to PYCORE and display AI response panel."""
        if not self.gemini.enabled:
            return
        if not self.gemini.is_ready():
            self.gemini_ui.print_no_key_notice()
            return

        exc_name = type(exc_val).__name__
        exc_msg  = str(exc_val)
        tb_str   = "".join(traceback.format_tb(tb)) if tb else ""

        stop_ev = self.gemini_ui.spinner_start("PYCORE AI analyzing error...")
        try:
            parsed = self.gemini.analyze_error(
                code_src   = source,
                exc_name   = exc_name,
                exc_msg    = exc_msg,
                traceback_s= tb_str,
                history    = self.history.history,
                user_vars  = self.engine.get_user_vars(),
            )
        finally:
            stop_ev.set()
            time.sleep(0.18)

        if parsed:
            self.gemini_ui.print_gemini_panel(parsed)
        else:
            self.gemini_ui.print_offline_notice(self.gemini.last_status)

    # ── Exit ─────────────────────────────────────────────────────────

    def _exit(self):
        t  = self.theme
        a1 = t["accent1"]
        a2 = t["accent2"]
        safe_print()
        typing_print("  Shutting down PyCore AI Shell…", a1, delay=0.016)
        time.sleep(0.2)
        typing_print(
            f"  Session stats: {self.engine.exec_count} commands, "
            f"{self.engine.error_count} errors, "
            f"{self.engine.success_rate:.0f}% success rate.",
            a2, delay=0.012
        )
        time.sleep(0.1)
        typing_print("  Session saved. Goodbye! ⚡", a1, delay=0.016)
        safe_print()
        sys.exit(0)

    # ── Main REPL loop ───────────────────────────────────────────────

    def run(self):
        # Boot animation
        try:
            anim = StartupAnimation(self.theme)
            anim.play()
        except Exception:
            pass

        time.sleep(0.2)
        clear_screen()
        self.print_header()

        # Welcome banner
        t = self.theme
        a1, a2, a3 = t["accent1"], t["accent2"], t["accent3"]
        safe_print()

        banner = [
            "╔════════════════════════════════════════════════════════════════╗",
            "║      PYCORE AI SHELL  —  ENHANCED PYTHON TERMINAL  v3.0        ║",
            "║                                                                ║",
            "║  Next-Gen Python REPL + IDLE Replacement + AI Debugger         ║",
            "║  Powered by PYCORE AI  ·  Built with Python stdlib only        ║",
            "║                                                                ║"
           f"║  Created by {self.AUTHOR:<51}║",
            "║  GitHub: github.com/aryansingh783                              ║",
            "║  Instagram: @aryan.singh.783                                   ║",
            "╚════════════════════════════════════════════════════════════════╝",
        ]
        for line in banner:
            typing_print(f"  {line}", a1, delay=0.0015)

        safe_print()
        typing_print(f"  ⚡ Welcome to PyCore AI Shell v{self.VERSION}", a1, delay=0.015)
        typing_print(f"  🤖 PYCORE Neural Debugging Engine is online and ready.", a2, delay=0.015)
        typing_print(f"  💡 Type :help for commands  ·  :tip for a Python tip", a3, delay=0.015)

        if not self.gemini.is_ready():
            typing_print(
                f"  🔴 PYCORE AI: no API key — use :addkey <key> to enable.",
                t["warn_color"], delay=0.013
            )
        else:
            typing_print(
                f"  🟢 PYCORE AI: connected and ready.",
                t["accent2"], delay=0.013
            )

        safe_print()

        # Main REPL
        pending_lines: list = []

        while True:
            try:
                prompt = self.get_prompt(secondary=bool(pending_lines))
                line   = self.read_input(prompt)

                # Empty input
                if line == "" and not pending_lines:
                    continue

                # Shell commands (only at top level)
                if not pending_lines and self.handle_command(line):
                    continue

                # Multiline accumulation
                if pending_lines:
                    if line.strip() == "":
                        # Blank line → execute accumulated block
                        source = "\n".join(pending_lines)
                        pending_lines.clear()
                        self.run_code(source)
                    else:
                        pending_lines.append(line)
                    continue

                # Single line — check if it starts an incomplete block
                if line.strip():
                    if self.should_continue_multiline(line + "\n"):
                        pending_lines.append(line)
                    else:
                        self.run_code(line)

            except KeyboardInterrupt:
                pending_lines.clear()
                print_colored(
                    "\n  KeyboardInterrupt — multiline cleared. "
                    "Press Ctrl+C again or type :exit to quit.\n",
                    t["warn_color"]
                )
            except Exception as e:
                print_colored(f"\n  Shell internal error: {e}\n", t["error_color"])


# ══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

def main():
    enable_ansi_windows()

    # Force UTF-8 output on Windows
    if platform.system() == "Windows":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    # Ignore SIGPIPE on Unix (pipe breakage shouldn't crash the shell)
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_IGN)  # type: ignore[attr-defined]

    shell = PYCOREShell()
    shell.run()


if __name__ == "__main__":
    main()





# ============================================================
# Creator Info
# ============================================================
# Creator  : Aryan Singh
# GitHub   : https://github.com/aryansingh783
# Instagram: @aryan.singh.783
# ============================================================
