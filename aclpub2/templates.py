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
LATEX_JINJA_ENV.globals.update(load_file=load_file, join=join, group_by_last_name=group_by_last_name)


def load_template(template: str) -> jinja2.Template:
    return LATEX_JINJA_ENV.get_template(f"{template}.tex")
