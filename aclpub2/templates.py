from collections import defaultdict
from pathlib import Path
from typing import List, Any

import jinja2

TEMPLATE_DIR = Path(Path(__file__).parent, "templates")


def load_file(*args: str):
    with open(Path(*args)) as f:
        return f.read()


def join(delimiter: str, items: List[Any], delimiter_last=None):
    if delimiter_last:
        output = delimiter.join(items[:-1])
        output = output + delimiter_last + items[-1]
        return output
    return delimiter.join(items)


def join_page_numbers(page_numbers):
    linked = map(lambda x: "\hyperlink{page." + str(x) + "}{" + str(x) + "}", page_numbers)
    return ", ".join(linked)


def group_by_last_name(names: List[str]) -> List[List[str]]:
    alphabetized_names = defaultdict(list)
    for name in names:
        last_name = name.split(" ")[-1]
        alphabetized_names[last_name[0].lower()].append(name)
    output = []
    letters = list(alphabetized_names.keys())
    letters.sort()
    for letter in letters:
        output.append(alphabetized_names[letter])
    return output


def program_date(date) -> str:
    return date.strftime("%A, %B %-d, %Y")


def session_times(session) -> str:
    start = session["start_time"].strftime("%H:%M")
    end = session["end_time"].strftime("%H:%M")
    return f"{start} - {end}"


LATEX_JINJA_ENV = jinja2.Environment(
    block_start_string='\BLOCK{',
    block_end_string='}',
    variable_start_string='\VAR{',
    variable_end_string='}',
    comment_start_string='\#{',
    comment_end_string='}',
    trim_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR))
)
LATEX_JINJA_ENV.globals.update(load_file=load_file, join=join,
                               group_by_last_name=group_by_last_name,
                               program_date=program_date, session_times=session_times,
                               join_page_numbers=join_page_numbers)


def load_template(template: str) -> jinja2.Template:
    return LATEX_JINJA_ENV.get_template(f"{template}.tex")
