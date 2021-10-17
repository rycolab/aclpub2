from pathlib import Path
from typing import List, Any

import jinja2

TEMPLATE_DIR = Path(Path(__file__).parent, "templates")


def load_file(*args: str):
    with open(Path(*args)) as f:
        return f.read()


def join(delimiter: str, items: List[Any]):
    return delimiter.join(items)


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
LATEX_JINJA_ENV.globals.update(load_file=load_file, join=join)


def load_template(template: str) -> jinja2.Template:
    return LATEX_JINJA_ENV.get_template(f"{template}.tex")
