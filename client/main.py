import curses
import json
import os
from pathlib import Path
from typing import Optional, Tuple

import requests

DEFAULT_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TOKEN_PATH = Path.home() / ".insurance_cli_token"


def save_token(token: str, base_url: str) -> None:
    TOKEN_PATH.write_text(json.dumps({"token": token, "base_url": base_url}))


def load_token() -> Tuple[Optional[str], str]:
    if not TOKEN_PATH.exists():
        return None, DEFAULT_BASE_URL
    try:
        data = json.loads(TOKEN_PATH.read_text())
        return data.get("token"), data.get("base_url", DEFAULT_BASE_URL)
    except Exception:
        return None, DEFAULT_BASE_URL


def api_login(base_url: str, email: str, password: str) -> Tuple[bool, Optional[str]]:
    try:
        resp = requests.post(
            f"{base_url}/auth/login",
            headers={"Content-Type": "application/json"},
            json={"email": email, "password": password},
            timeout=10,
        )
    except Exception as exc:  # network or connection errors
        return False, f"Request failed: {exc}"

    if resp.status_code != 200:
        return False, f"Login failed {resp.status_code}: {resp.text}"

    token = resp.json().get("access_token")
    if not token:
        return False, "No token returned"
    return True, token


def api_me(base_url: str, token: str) -> Tuple[bool, str]:
    try:
        resp = requests.get(
            f"{base_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
    except Exception as exc:
        return False, f"Request failed: {exc}"

    if resp.status_code != 200:
        return False, f"Error {resp.status_code}: {resp.text}"
    return True, json.dumps(resp.json(), indent=2, ensure_ascii=False)


class App:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.token, self.base_url = load_token()
        self.message = "" if self.token else "Press L to login"
        self.status = "Logged in" if self.token else "Not logged in"

    def run(self) -> None:
        curses.curs_set(0)
        self.stdscr.nodelay(False)
        while True:
            self.draw()
            key = self.stdscr.getkey().lower()
            if key in ("q", "\x1b"):  # q or ESC
                break
            if key == "l":
                self.handle_login()
            elif key == "m":
                self.handle_me()
            elif key == "o":
                self.handle_logout()
            elif key == "b":
                self.handle_base_url()

    def draw(self) -> None:
        self.stdscr.clear()
        max_y, max_x = self.stdscr.getmaxyx()
        title = "Insurance CLI"
        subtitle = f"API: {self.base_url}"
        menu = [
            "[L] Login",
            "[M] Me",
            "[O] Logout",
            "[B] Base URL",
            "[Q] Quit",
        ]
        self.stdscr.addstr(1, 2, title, curses.A_BOLD)
        self.stdscr.addstr(2, 2, subtitle)
        self.stdscr.addstr(3, 2, f"Status: {self.status}")
        for idx, item in enumerate(menu, start=5):
            self.stdscr.addstr(idx, 4, item)
        if self.message:
            self._draw_message(max_y, max_x)
        self.stdscr.refresh()

    def prompt(self, prompt_text: str, hidden: bool = False) -> str:
        max_y, max_x = self.stdscr.getmaxyx()
        prompt_row = max_y - 4
        input_row = max_y - 3
        self.stdscr.move(prompt_row, 2)
        self.stdscr.clrtoeol()
        self.stdscr.addstr(prompt_row, 2, prompt_text)
        self.stdscr.move(input_row, 2)
        self.stdscr.clrtoeol()
        self.stdscr.refresh()

        curses.echo(False)
        curses.curs_set(1)
        buf: list[str] = []

        while True:
            try:
                ch = self.stdscr.get_wch()
            except curses.error:
                continue

            if isinstance(ch, str) and ch in ("\n", "\r"):
                break
            if ch in (curses.KEY_BACKSPACE, "\b", "\x7f"):
                if buf:
                    buf.pop()
            elif isinstance(ch, str) and ch.isprintable():
                buf.append(ch)

            display = "*" * len(buf) if hidden else "".join(buf)
            self.stdscr.move(input_row, 2)
            self.stdscr.clrtoeol()
            self.stdscr.addstr(input_row, 2, display[: max_x - 4])
            self.stdscr.refresh()

        curses.curs_set(0)
        return "".join(buf).strip()

    def handle_login(self) -> None:
        curses.echo(True)
        email = self.prompt("Email: ")
        password = self.prompt("Password: ", hidden=True)
        ok, result = api_login(self.base_url, email, password)
        if ok:
            self.token = result
            save_token(self.token, self.base_url)
            self.status = "Logged in"
            self.message = "Login successful"
        else:
            self.message = result

    def handle_me(self) -> None:
        if not self.token:
            self.message = "Not logged in. Press L to login."
            return
        ok, result = api_me(self.base_url, self.token)
        self.message = result

    def handle_logout(self) -> None:
        self.token = None
        if TOKEN_PATH.exists():
            TOKEN_PATH.unlink()
        self.status = "Not logged in"
        self.message = "Logged out"

    def handle_base_url(self) -> None:
        new_url = self.prompt(f"API base URL [{self.base_url}]: ") or self.base_url
        self.base_url = new_url
        self.message = f"Base URL set to {self.base_url}"

    @staticmethod
    def _truncate(text: str, width: int) -> str:
        return text if len(text) <= width else text[: width - 3] + "..."

    def _draw_message(self, max_y: int, max_x: int) -> None:
        lines = (self.message or "").splitlines() or [""]
        avail_lines = 3  # show up to 3 lines above footer area
        start_row = max_y - (avail_lines + 1)
        for i in range(min(len(lines), avail_lines)):
            row = start_row + i
            safe = "".join(ch if ch.isprintable() else "?" for ch in lines[i])
            self.stdscr.addstr(row, 2, self._truncate(safe, max_x - 4))


def main() -> None:
    curses.wrapper(lambda stdscr: App(stdscr).run())


if __name__ == "__main__":
    main()
