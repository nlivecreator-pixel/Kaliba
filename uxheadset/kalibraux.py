import os
import sys
import threading
import time
from typing import Optional

from rich.color import Color
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.style import Style
from rich.text import Text

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

USE_UNICODE = os.environ.get("TERM") != "dumb" and sys.stdout.encoding.lower() in ("utf-8", "utf8")
SEP = "─" if USE_UNICODE else "-"

console = Console(highlight=False)


class Colors:
    LOGO_START = "#5B8FFF"
    LOGO_END = "#8322CD"
    
    PURPLE = "#8322CD"
    CYAN = "cyan"
    GREEN = "green"
    RED = "red"
    YELLOW = "yellow"
    DIM = "dim"
    BOLD = "bold"
    
    LOGO_GRADIENT = [LOGO_START, "#6379F5", "#6B63EB", "#734EE1", "#7B38D7", LOGO_END]
    
    INFO = CYAN
    SUCCESS = GREEN
    DANGER = RED
    WARNING = YELLOW
    PROGRESS = PURPLE
    ACCENT = CYAN
    HIGHLIGHT = YELLOW
    ERROR = RED
    OK = GREEN
    HEADER = BOLD
    SEPARATOR = DIM
    LABEL = BOLD


LOGO_LINES = [
    "██╗  ██╗ █████╗ ██╗     ██╗██████╗ █████╗ ",
    "██║ ██╔╝██╔══██╗██║     ██║██╔══██╗██╔══██╗",
    "█████╔╝ ███████║██║     ██║██████╔╝███████║",
    "██╔═██╗ ██╔══██║██║     ██║██╔══██╗██╔══██║",
    "██║  ██╗██║  ██║███████╗██║██████╔╝██║  ██║",
    "╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝╚═════╝ ╚═╝  ╚═╝",
]

LOGO_GRADIENT = Colors.LOGO_GRADIENT


def _parse_hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def print_logo():
    for i, line in enumerate(LOGO_LINES):
        t = i / max(len(LOGO_LINES) - 1, 1)
        idx = int(t * (len(LOGO_GRADIENT) - 1))
        c1 = LOGO_GRADIENT[min(idx, len(LOGO_GRADIENT) - 1)]
        c2 = LOGO_GRADIENT[min(idx + 1, len(LOGO_GRADIENT) - 1)]
        sc = _parse_hex(c1)
        ec = _parse_hex(c2)
        out = Text()
        length = len(line)
        for j, ch in enumerate(line):
            tt = j / max(length - 1, 1)
            r = int(sc[0] + (ec[0] - sc[0]) * tt)
            g = int(sc[1] + (ec[1] - sc[1]) * tt)
            b = int(sc[2] + (ec[2] - sc[2]) * tt)
            out.append(ch, Style(color=Color.from_rgb(r, g, b), bold=True))
        console.print("  ", out)


def clear_screen():
    console.clear()


def banner(cls: bool = True, subtitle: str = "KalibraUX"):
    if cls:
        clear_screen()
    console.print()
    console.print()
    print_logo()
    console.print(f"  [dim]{subtitle}[/]")
    console.print(f"  [dim]{'=' * 60}[/]\n")


def farewell():
    clear_screen()
    console.print()
    console.print()
    print_logo()
    console.print()
    console.print("  До скорых встреч!")
    console.print()


def color(text: str, code: str) -> str:
    mapping = {
        "red": "red", "green": "green", "yellow": "yellow",
        "blue": "blue", "magenta": "magenta", "cyan": "cyan",
        "white": "white", "bold": "bold", "dim": "dim",
        "purple": Colors.PURPLE,
    }
    c = mapping.get(code, "")
    if c:
        return f"[{c}]{text}[/]"
    return text


def danger(msg: str):
    console.print(f" [bold red][!][/] {msg}")


def info(msg: str):
    console.print(f" [bold cyan][*][/] {msg}")


def success(msg: str):
    console.print(f" [bold green][+][/] {msg}")


def warning(msg: str):
    console.print(f" [bold yellow][?][/] {msg}")


def section(title: str):
    console.print()
    console.print(f"  [bold]{title}[/]")
    console.print(f"  [dim]{SEP * 40}[/]")


def field(label: str, value: str = "", value_color: str = ""):
    label_part = f"  [bold]{label}:[/]"
    if value and value_color:
        value_part = f" [{value_color}]{value}[/]"
        console.print(f"{label_part}{value_part}")
    elif value:
        console.print(f"{label_part} {value}")
    else:
        console.print(label_part)


def menu_item(index: str, text: str):
    console.print(f"    [cyan]{index}[/]  {text}")


def separator(length: int = 40):
    console.print(f"  [dim]{SEP * length}[/]")


class ProgressBar:
    def __init__(self, total: int, prefix: str = "Загрузка..."):
        self.total = total
        self.prefix = prefix
        self.progress = Progress(
            TextColumn(f"[bold {Colors.PROGRESS}]{{task.description}}[/]"),
            BarColumn(bar_width=20, complete_style=Colors.PROGRESS, finished_style=Colors.SUCCESS),
            TextColumn("[progress]{task.completed}/{task.total}[/]"),
            console=console,
        )
        self.task = self.progress.add_task(f"  [*] {prefix}", total=total)

    def __enter__(self):
        self.progress.__enter__()
        return self

    def __exit__(self, *args):
        self.progress.__exit__(*args)

    def update(self, n: int = 1):
        self.progress.advance(self.task, n)

    def set_current(self, n: int):
        self.progress.update(self.task, completed=n)

    def finish(self):
        self.progress.update(self.task, completed=self.total)


class Spinner:
    def __init__(self, text: str = ""):
        self.text = text

    def spin(self):
        pass

    def done(self, msg: Optional[str] = None):
        line = f"[bold green][+][/] {self.text}"
        if msg:
            line += f" — {msg}"
        console.print(line)

    def fail(self, msg: Optional[str] = None):
        line = f"[bold red][-][/] {self.text}"
        if msg:
            line += f" — {msg}"
        console.print(line)


def print_result_header(title: str = "РЕЗУЛЬТАТЫ"):
    console.print()
    console.print(f"  [bold]{title}[/]")
    console.print(f"  [dim]{SEP * 40}[/]")
    console.print()


def format_accent(text: str) -> str:
    return f"[{Colors.ACCENT}]{text}[/]"


def format_highlight(text: str) -> str:
    return f"[{Colors.HIGHLIGHT}]{text}[/]"


def format_error(text: str) -> str:
    return f"[{Colors.ERROR}]{text}[/]"


def format_ok(text: str) -> str:
    return f"[{Colors.OK}]{text}[/]"


def format_dim(text: str) -> str:
    return f"[{Colors.DIM}]{text}[/]"


class LoadingAnimations:
    DOTS = ["[.]", "[*]", '["]']
    SLASHES = ["[<]", "[/]", "[>]"]
    BARS = ["[=]", "[-]", "[+]"]
    CIRCLES = ["[o]", "[O]", "[0]"]


class PingPongLoader:
    def __init__(self, text: str = "Загрузка...", frames: list = None, interval: float = 0.2, color: str = Colors.ACCENT):
        self.text = text
        self.frames = frames if frames is not None else LoadingAnimations.DOTS
        self.interval = interval
        self.color = color
        self._running = False
        self._thread = None

    def _ping_pong_sequence(self):
        n = len(self.frames)
        if n == 0:
            return
        while True:
            for i in range(n):
                yield i
            for i in range(n - 2, 0, -1):
                yield i

    def _animate(self):
        seq = self._ping_pong_sequence()
        with console.status("", spinner=None):
            while self._running:
                frame_idx = next(seq)
                frame = self.frames[frame_idx]
                console.print(f"\r  [{self.color}]{frame}[/] {self.text}", end="")
                time.sleep(self.interval)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self, msg: str = None):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        console.print("\r  ", end="")
        if msg:
            success(f"{self.text} — {msg}")
        else:
            success(self.text)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


class MessageStyle:
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    ERROR = "error"
    
    @staticmethod
    def format(role: str, content: str, prefix: str = None) -> str:
        if role == MessageStyle.USER:
            p = prefix or "U"
            return f"  [bold green]┌── {p} ──┐[/]\n  {content}"
        elif role == MessageStyle.ASSISTANT:
            p = prefix or "A"
            return f"  [bold cyan]┌── {p} ──┐[/]\n  {content}"
        elif role == MessageStyle.SYSTEM:
            return f"  [dim]● {content}[/]"
        elif role == MessageStyle.TOOL:
            p = prefix or "T"
            return f"  [bold yellow]┌── {p} ──┐[/]\n  [dim]{content}[/]"
        elif role == MessageStyle.ERROR:
            return f"  [bold red]✗ {content}[/]"
        return content


class PromptInput:
    @staticmethod
    def render(placeholder: str = "Введите сообщение...", show_hints: bool = True):
        console.print(f"\n  [dim]┌────────────────────────────────────────────────────┐[/]")
        console.print(f"  [dim]│[/]  [bold]>[/] {placeholder}{' ' * (40 - len(placeholder))}  [dim]│[/]")
        if show_hints:
            console.print(f"  [dim]│[/]  [yellow]@[/][dim]файл[/]  [red]![/][dim]команда[/]  [cyan]/[/][dim]справка[/]  [dim]────────────│[/]")
        console.print(f"  [dim]└────────────────────────────────────────────────────┘[/]\n")
    
    @staticmethod
    def render_compact(placeholder: str = "> "):
        console.print(f"\n  [bold]{placeholder}[/]", end=" ")


class Dialog:
    @staticmethod
    def select(title: str, items: list, selected_index: int = 0):
        console.print(f"\n  [bold]┌── {title} ──┐[/]")
        console.print(f"  [dim]│[/]{' ' * 44}[dim]│[/]")
        for i, item in enumerate(items):
            marker = "[cyan]●[/]" if i == selected_index else "[dim]○[/]"
            padding = " " * (36 - len(str(item)))
            console.print(f"  [dim]│[/]  {marker} {item}{padding}[dim]│[/]")
        console.print(f"  [dim]│[/]{' ' * 44}[dim]│[/]")
        console.print(f"  [dim]│[/]  [green][ Enter ][/][dim]  [red][ Отмена ][/][dim]{' ' * 18}│[/]")
        console.print(f"  [bold]└────────────────────────────────────────────────────┘[/]\n")
        return selected_index
    
    @staticmethod
    def confirm(title: str, message: str, default_yes: bool = True):
        yes_style = "[green]" if default_yes else "[dim]"
        no_style = "[dim]" if default_yes else "[red]"
        console.print(f"\n  [bold]┌── {title} ──┐[/]")
        console.print(f"  [dim]│[/]{' ' * 44}[dim]│[/]")
        console.print(f"  [dim]│[/]  {message}{' ' * (42 - len(message))}[dim]│[/]")
        console.print(f"  [dim]│[/]{' ' * 44}[dim]│[/]")
        console.print(f"  [dim]│[/]  {yes_style}[ Да (Y) ][/][dim]  {no_style}[ Нет (N) ][/][dim]{' ' * 16}│[/]")
        console.print(f"  [bold]└────────────────────────────────────────────────────┘[/]\n")


class StatusBar:
    @staticmethod
    def render(model_name: str = None, tokens_used: int = None, tokens_total: int = None, 
               context_name: str = None, extra: str = None):
        parts = []
        if context_name:
            parts.append(f"[cyan]{context_name}[/]")
        if model_name:
            parts.append(f"[green]● {model_name}[/]")
        if tokens_used is not None and tokens_total:
            parts.append(f"[yellow]{tokens_used}K / {tokens_total}K tokens[/]")
        if extra:
            parts.append(f"[dim]{extra}[/]")
        
        mid = "  [dim]│[/]  ".join(parts)
        console.print(f"  [dim]╔════════════════════════════════════════════════════════════════╗[/]")
        console.print(f"  [dim]║[/]  {mid}{' ' * 20}  [dim]║[/]")
        console.print(f"  [dim]╚════════════════════════════════════════════════════════════════╝[/]\n")
    
    @staticmethod
    def render_minimal(left: str = "", center: str = "", right: str = ""):
        console.print(f"  [dim]┌────────────────────────────────────────────────────────────────┐[/]")
        if left or center or right:
            console.print(f"  [dim]│[/]  [cyan]{left}[/]{' ' * 20}[dim]│[/]{center}{' ' * 20}[dim]│[/][dim]{right}[/]  [dim]│[/]")
        console.print(f"  [dim]└────────────────────────────────────────────────────────────────┘[/]\n")


class ModelInfo:
    @staticmethod
    def list(models: list, current_index: int = None):
        section("ДОСТУПНЫЕ МОДЕЛИ")
        for i, model in enumerate(models):
            name = model.get("name", "Unknown")
            provider = model.get("provider", "")
            context = model.get("context_window", "")
            current = "[cyan]●[/]" if (current_index is not None and i == current_index) else " "
            console.print(f"    {current} [bold]{name}[/]")
            if provider or context:
                details = []
                if provider:
                    details.append(f"[dim]{provider}[/]")
                if context:
                    details.append(f"[yellow]ctx: {context}[/]")
                console.print(f"       {' '.join(details)}")
        console.print()
    
    @staticmethod
    def current(name: str, provider: str = None, context_window: str = None):
        parts = [f"[green]●[/] [bold]{name}[/]"]
        if provider:
            parts.append(f"[dim]({provider})[/]")
        if context_window:
            parts.append(f"[yellow]context: {context_window}[/]")
        console.print(f"  {' '.join(parts)}\n")


class CommandList:
    COMMANDS = [
        {"name": "/help", "desc": "показать справку"},
        {"name": "/models", "desc": "список доступных моделей"},
        {"name": "/connect", "desc": "добавить провайдер API"},
        {"name": "/editor", "desc": "открыть внешний редактор"},
        {"name": "/export", "desc": "экспорт сессии в Markdown"},
        {"name": "/compact", "desc": "сжать текущую сессию"},
        {"name": "/details", "desc": "показать детали выполнения"},
        {"name": "/exit", "desc": "выйти (синонимы: /quit, /q)"},
    ]
    
    @staticmethod
    def show():
        section("SLASH-КОМАНДЫ (/)")
        for cmd in CommandList.COMMANDS:
            console.print(f"    [cyan]{cmd['name']:<12}[/] — [dim]{cmd['desc']}[/]")
        console.print()
    
    @staticmethod
    def render_compact():
        names = "  ".join([f"[cyan]{c['name']}[/]" for c in CommandList.COMMANDS[:4]])
        console.print(f"  [dim]Команды:[/] {names}  [dim]...[/]\n")


class FileReference:
    @staticmethod
    def format(path: str, line_start: int = None, line_end: int = None) -> str:
        base = f"[yellow]@[/][cyan]{path}[/]"
        if line_start is not None:
            if line_end and line_end != line_start:
                return f"{base}[yellow]:{line_start}-{line_end}[/]"
            return f"{base}[yellow]:{line_start}[/]"
        return base
    
    @staticmethod
    def list_refs(files: list):
        if not files:
            return
        console.print("  [dim]Файлы в контексте:[/]")
        for f in files:
            console.print(f"    {FileReference.format(f)}")
        console.print()
    
    @staticmethod
    def render_picker_hint():
        console.print("  [dim]Введите[/] [yellow]@[/][dim] для поиска файла,[/] [cyan]@/[/][dim] для выбора из дерева[/]")
        console.print("  [dim]Пример:[/] [cyan]@src/main.py[/][dim] или[/] [cyan]@src/main.py:10-25[/]\n")


class ToolResult:
    @staticmethod
    def start(tool_name: str, command: str = None):
        console.print(f"  [bold yellow]┌──[/] [green]{tool_name}[/] [bold yellow]──┐[/]")
        if command:
            console.print(f"  [dim]│[/]  [cyan]$ {command}[/]{' ' * 30}[dim]│[/]")
    
    @staticmethod
    def output(line: str):
        console.print(f"  [dim]│[/]  {line}{' ' * (40 - len(str(line)))}[dim]│[/]")
    
    @staticmethod
    def end(exit_code: int = 0):
        status = "[green]0[/]" if exit_code == 0 else f"[red]{exit_code}[/]"
        console.print(f"  [dim]│[/]  [dim]exit code:[/] {status}{' ' * 20}[dim]│[/]")
        console.print(f"  [bold yellow]└────────────────────────────────────────────┘[/]\n")
    
    @staticmethod
    def render_block(tool_name: str, content: str, command: str = None, exit_code: int = 0):
        ToolResult.start(tool_name, command)
        lines = str(content).split("\n")
        for line in lines[:15]:
            if len(line) > 50:
                line = line[:47] + "..."
            ToolResult.output(line)
        if len(lines) > 15:
            ToolResult.output(f"... (+{len(lines) - 15} строк)")
        ToolResult.end(exit_code)


class Keybindings:
    LEADER = "Ctrl+X"
    
    BINDINGS = [
        ("M", "модели", "/models"),
        ("E", "редактор", "/editor"),
        ("C", "сжать", "/compact"),
        ("X", "экспорт", "/export"),
        ("Q", "выход", "/exit"),
        ("H", "справка", "/help"),
    ]
    
    @staticmethod
    def show():
        section("ШОРТКАТЫ (ЛИДЕР-КЛЮЧ: Ctrl+X)")
        for key, desc, cmd in Keybindings.BINDINGS:
            console.print(f"    [dim]{Keybindings.LEADER}[/] + [dim]{key}[/]  — {desc}  [dim]({cmd})[/]")
        console.print()
    
    @staticmethod
    def render_statusline_hint():
        short = " ".join([f"[dim]{Keybindings.LEADER}+{k}[/]" for k, _, _ in Keybindings.BINDINGS[:3]])
        console.print(f"  [dim]{short} ...[/]")


class LoadingAnimations:
    DOTS = ["[.]", "[*]", '["]']
    SLASHES = ["[<]", "[/]", "[>]"]
    BARS = ["[=]", "[-]", "[+]"]
    CIRCLES = ["[o]", "[O]", "[0]"]


class PingPongLoader:
    def __init__(self, text: str = "Загрузка...", frames: list = None, interval: float = 0.2, color: str = Colors.ACCENT):
        self.text = text
        self.frames = frames if frames is not None else LoadingAnimations.DOTS
        self.interval = interval
        self.color = color
        self._running = False
        self._thread = None

    def _ping_pong_sequence(self):
        n = len(self.frames)
        if n == 0:
            return
        while True:
            for i in range(n):
                yield i
            for i in range(n - 2, 0, -1):
                yield i

    def _animate(self):
        seq = self._ping_pong_sequence()
        with console.status("", spinner=None):
            while self._running:
                frame_idx = next(seq)
                frame = self.frames[frame_idx]
                console.print(f"\r  [{self.color}]{frame}[/] {self.text}", end="")
                time.sleep(self.interval)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self, msg: str = None):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        console.print("\r  ", end="")
        if msg:
            success(f"{self.text} — {msg}")
        else:
            success(self.text)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

