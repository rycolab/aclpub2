from collections import defaultdict
from pathlib import Path
from typing import List, Any

import jinja2

TEMPLATE_DIR = Path(Path(__file__).parent, "templates")

HOMOGLYPHS = {"Ø": "o", "Ö": "o", "Ç": "c", "Ş": "s", "Š": "s", "Á": "a", "\c{S}": "s", "Ü": "u"}


def load_file(*args: str):
    with open(Path(*args)) as f:
        return f.read()


def render_name(user):
    name = user["first_name"] + " "
    if "middle_name" in user:
        name += user["middle_name"] + " "
    name += user["last_name"] + "\index{" + user["last_name"] + "}"
    return name


def join_names(delimiter: str, items: List[Any], delimiter_last: str = None):
    items = list(map(render_name, items))
    if len(items) == 1:
        return items[0]
    if delimiter_last:
        front = delimiter.join(items[:-1])
        return delimiter_last.join((front, items[-1]))
    return delimiter.join(items)


def index_author(author: str):
    n = author.split(" ")
    return "\index{" + n[-1] + ", " + " ".join(n[:-1]) + "}"


def index_speakers(author: str):
    n = author.split(",")
    s = ""
    for aut in n:
        sur = aut.split(" ")[-1]
        s += "\index{" + sur + "}"
    return s


def join_page_numbers(page_numbers):
    linked = map(
        lambda x: "\hyperlink{page." + str(x) + "}{" + str(x) + "}", page_numbers
    )
    return ", ".join(linked)


def group_by_last_name(entries) -> List[List[str]]:
    alphabetized_names = defaultdict(list)
    for entry in entries:
        last_name = entry["last_name"]
        alphabetized_names[homoglyph(last_name)].append(entry)
    output = []
    letters = list(alphabetized_names.keys())
    letters.sort()
    for letter in letters:
        alphabetized_names[letter].sort(key=lambda x: (x["last_name"], x["first_name"]))
        output.append(alphabetized_names[letter])
    return output


def to_string_sorting_by_last_name(entries) -> str:
    res = []
    groups = group_by_last_name(entries)
    for group in groups:
        res.append(join_names(", ", group))
    return ", ".join(res)


def homoglyph(name: str) -> str:
    for s, h in HOMOGLYPHS.items():
        if name.startswith(s):
            return h
    return name[0].lower()


def program_date(date) -> str:
    return date.strftime("%A, %B %-d, %Y")


def session_times(session) -> str:
    start = session["start_time"].strftime("%H:%M")
    end = session["end_time"].strftime("%H:%M")
    return f"{start} - {end}"


LATEX_JINJA_ENV = jinja2.Environment(
    block_start_string="\BLOCK{",
    block_end_string="}",
    variable_start_string="\VAR{",
    variable_end_string="}",
    comment_start_string="\#{",
    comment_end_string="}",
    trim_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
)
LATEX_JINJA_ENV.globals.update(
    load_file=load_file,
    join_names=join_names,
    group_by_last_name=group_by_last_name,
    to_string_sorting_by_last_name=to_string_sorting_by_last_name,
    program_date=program_date,
    session_times=session_times,
    join_page_numbers=join_page_numbers,
    index_author=index_author,
    index_speakers=index_speakers,
)


def load_template(template: str) -> jinja2.Template:
    return LATEX_JINJA_ENV.get_template(f"{template}.tex")
