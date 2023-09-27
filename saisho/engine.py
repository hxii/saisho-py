import shutil
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import ibis
import markdown
import minify_html
from colorama import Back, Fore, Style
from slugify import slugify


class PageTypes(Enum):
    ENTRY = "entry"  # Chronological page, i.e. blog post
    PAGE = "page"  # Static page, e.g. about
    PROJECT = "project"

    @classmethod
    def _missing_(cls, value: object) -> Any:
        return cls.ENTRY


@dataclass
class MessageType:
    decorator: str = "[ ]"
    decorator_color: str = Fore.BLACK
    message_color: str = Fore.BLACK


class MessageTypes(MessageType, Enum):
    HEADER = ("", Back.BLACK, Fore.LIGHTWHITE_EX)
    DEFAULT = ("[ ]", Back.BLACK, Fore.WHITE)
    ERROR = ("[X]", Back.RED, Fore.RED)
    OK = ("[V]", Back.GREEN, Fore.GREEN)
    INFO = ("[i]", Back.BLACK, Fore.LIGHTCYAN_EX)
    VERBOSE = ("[>]", Back.BLACK, Fore.LIGHTWHITE_EX)


class TerminalPrint:
    INDENT = 2

    @staticmethod
    def _print(message_type: MessageType, message: str):
        print(
            f"{Style.BRIGHT}{message_type.message_color}{message_type.decorator}"
            f"{Style.NORMAL}{TerminalPrint.INDENT * ' '}{message}{Fore.RESET}"
        )

    @staticmethod
    def header(message: str):
        if not saisho_engine.quiet:
            TerminalPrint._print(MessageTypes.HEADER, message)

    @staticmethod
    def error(message: str):
        TerminalPrint._print(MessageTypes.ERROR, message)

    @staticmethod
    def success(message: str):
        if not saisho_engine.quiet:
            TerminalPrint._print(MessageTypes.OK, message=message)

    @staticmethod
    def info(message: str):
        if not saisho_engine.quiet:
            TerminalPrint._print(MessageTypes.INFO, message)

    @staticmethod
    def verbose(message: str):
        if saisho_engine.verbose and not saisho_engine.quiet:
            TerminalPrint._print(MessageTypes.VERBOSE, message=message)


@dataclass
class Entry:
    title: str
    content: str
    tags: list
    date: datetime
    description: str
    display_date: str
    year: str
    uri: str
    file: Path
    type: PageTypes

    MARKDOWN_EXTENSIONS = [
        "meta",
        "wikilinks",
        "extra",
        "admonition",
        "fenced_code",
        "markdown_mark",
        "yafg",
        "markdown_del_ins",
        "toc",
    ]

    @classmethod
    def from_text(self, text: str, file: Path = None) -> "Entry":
        md = markdown.Markdown(extensions=self.MARKDOWN_EXTENSIONS)
        html = md.convert(text)
        meta: dict = md.Meta
        meta["type"] = "".join(meta.get("type", "entry"))
        meta["tags"] = [tag.strip() for tag in "".join(meta.get("tags", "")).split(",")]
        meta["title"] = "".join(meta.get("title", ""))
        date = "".join(meta.get("date", datetime.now().strftime("%Y-%m-%d")))
        meta["date"]: datetime = datetime.strptime(date, "%Y-%m-%d")
        meta["display_date"] = f"{meta['date'].strftime('%B')} {Tools.date_suffix(meta['date'].day)}"
        meta["description"] = "".join(meta.get("description", ""))
        meta["year"] = meta["date"].year
        return Entry(
            type=meta["type"],
            title=meta["title"],
            content=html,
            tags=meta["tags"],
            date=meta["date"],
            display_date=meta["display_date"],
            description=meta["description"],
            year=meta["year"],
            uri=slugify(file.stem),
            file=file,
        )

    @classmethod
    def from_file(self, file: Path) -> "Entry":
        return self.from_text(file.read_text("UTF-8"), file=file)


class Tools:
    @staticmethod
    def date_suffix(date: int) -> str:
        return str(date) + {
            1: "st",
            2: "nd",
            3: "rd",
            21: "st",
            22: "nd",
            23: "rd",
            31: "st",
        }.get(date, "th")

    @staticmethod
    def create_if_missing(filepath: Path) -> Path:
        if not filepath.exists():
            if filepath.suffix == "":
                filepath.mkdir()
            else:
                filepath.touch()
        return filepath

    @staticmethod
    def size(num, suffix="B"):
        for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
            if abs(num) < 1024.0:
                return f"{num:3.1f}{unit}{suffix}"
            num /= 1024.0
        return f"{num:.1f}Yi{suffix}"

    @staticmethod
    def colorize_bool(b, chars=["V", "X"], reverse_colors: bool = False) -> str:
        char = chars[0] if b else chars[1]
        e = bool(b) ^ reverse_colors
        return f"{Fore.GREEN if e else Fore.RED}{char}{Fore.RESET}"


class SaishoEngine:
    SOURCE_FOLDER: Path = Path("source")
    OUTPUT_FOLDER: Path = Path("html")
    TEMPLATE_FOLDER: Path = Path("template")

    def __init__(self) -> None:
        self.years: dict = {}
        self.entry_db: list[Entry] = []
        self._check_folders()
        Tools.create_if_missing(self.OUTPUT_FOLDER)
        ibis.loader = ibis.loaders.FileLoader(self.TEMPLATE_FOLDER)
        pass

    def _check_folders(self):
        for folder in [self.SOURCE_FOLDER, self.TEMPLATE_FOLDER]:
            if not folder.exists():
                TerminalPrint.error(f'Folder "{folder}" is missing!')
                exit(1)

    def _populate_entries(self, files: list[Path]) -> int:
        TerminalPrint.info("Populating entry DB")
        for file in files:
            self.entry_db.append(Entry.from_file(file))
        return len(self.entry_db)

    def _set_output_folder(self, output_folder: str = ""):
        self.OUTPUT_FOLDER = Tools.create_if_missing(Path(output_folder or "html"))

    @ibis.filters.register("date_suffix")
    def date_suffix(date: int):
        return Tools.date_suffix(date)

    @ibis.filters.register("timestamp_to_date")
    def ts_to_date(timestamp: int):
        return datetime.utcfromtimestamp(timestamp)

    def get_file(self, filename: str) -> Path:
        if not filename.endswith(".md"):
            filename += ".md"
        _filename = self.SOURCE_FOLDER / filename
        if _filename.is_file():
            return _filename.absolute()
        return False

    def get_all_files(self) -> list[Path]:
        markdown_files = [file.absolute() for file in self.SOURCE_FOLDER.iterdir() if file.suffix == ".md"]
        return markdown_files

    def _resolve_entries(self, filenames: list[str] | None) -> list[Path]:
        """
        Resolve filenames (strings) to entries (Path).
        Will return all available entries if filenames not provided.

        Arguments:
            filenames -- Optional. List of filenames to look for.

        Returns:
            List of resolved entry paths.
        """
        if not filenames:
            return self.get_all_files()
        else:
            paths: list[Path] = []
            for filename in filenames:
                if file := self.get_file(filename):
                    paths.append(file)
            return paths

    def read_file(self, filename: Path) -> str:
        return filename.read_text("UTF-8")

    def render_page(self, entry: Entry, print_instead: bool = False, compress: bool = False):
        page_template = ibis.loader("page.html")
        output_path = Tools.create_if_missing(self.OUTPUT_FOLDER / f"{entry.uri}.html")
        output = page_template.render(entry=entry)
        if compress:
            output = minify_html.minify(output, keep_comments=False)
        if not print_instead:
            result = output_path.write_text(output)
            TerminalPrint.verbose(f"Built {entry.file.name} - {Tools.size(result)}")
            return result
        print(output)

    def render_list(self, entries: dict, print_instead: bool = False, compress=False):
        TerminalPrint.info("Trying to build index")
        list_template = ibis.loader("list.html")
        output_path = Tools.create_if_missing(self.OUTPUT_FOLDER / "index.html")
        output = list_template.render(entries=entries)
        if compress:
            output = minify_html.minify(output, keep_comments=False)
        if not print_instead:
            TerminalPrint.info("Built index.html")
            return output_path.write_text(output)
        print(output)

    def build_single_page(self, file_names: list[str], **opts):
        TerminalPrint.info(f"Building {','.join(file_names)}")
        for file_name in file_names:
            file = self.get_file(file_name)
            if file:
                entry = Entry.from_file(file)
                saisho_engine.render_page(entry, **opts)
            else:
                TerminalPrint.error(f"{file_name} not found.")
        self.copy_stylesheets()

    def build_all_pages(self, **opts):
        # files = self.get_all_files()
        entry_count = self._populate_entries(self.get_all_files())
        TerminalPrint.info(f"Building {entry_count} pages...")
        years = {}
        for entry in self.entry_db:
            if not years.get(entry.year):
                years[entry.year] = []
            years[entry.year].append(entry)
            saisho_engine.render_page(entry, **opts)
        years = {k: years[k] for k in sorted(years, reverse=True)}  # Sort years descending
        for year in years:  # Sort entries by date descending
            years[year] = sorted(years[year], key=lambda entry: entry.date, reverse=True)
        saisho_engine.render_list(years, **opts)
        self.copy_stylesheets()

    def build_pages(self, filenames: list[str] | None, **opts):
        files = self._resolve_entries(filenames)
        entry_count = self._populate_entries(files)
        TerminalPrint.info(f"Building {entry_count} pages...")
        years = {}
        for entry in self.entry_db:
            if not years.get(entry.year):
                years[entry.year] = []
            years[entry.year].append(entry)
            saisho_engine.render_page(entry, **opts)
        # if filenames:
        years = {k: years[k] for k in sorted(years, reverse=True)}  # Sort years descending
        for year in years:  # Sort entries by date descending
            years[year] = sorted(years[year], key=lambda entry: entry.date, reverse=True)
        saisho_engine.render_list(years, **opts)
        self.copy_stylesheets()

    def copy_stylesheets(self):
        count = 0
        for stylesheet in self.TEMPLATE_FOLDER.rglob("*.css"):
            # shutil.copy2(stylesheet, self.OUTPUT_FOLDER / stylesheet.name)
            count += 1
            processed_stylesheet = minify_html.minify(stylesheet.read_text(), minify_css=True, keep_comments=False)
            (self.OUTPUT_FOLDER / stylesheet.name).write_text(processed_stylesheet)
        TerminalPrint.info(f"Copied {count} stylesheet(s).")


saisho_engine = SaishoEngine()
