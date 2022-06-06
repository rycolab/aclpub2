from collections import defaultdict
from dataclasses import dataclass
import yaml
from typing import List, Optional
from pathlib import Path
import datetime


@dataclass
class Person(yaml.YAMLObject):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    institution: Optional[str] = None
    yaml_tag: str = "!Person"


@dataclass
class Conference(yaml.YAMLObject):
    book_title: str
    event_name: str
    cover_subtitle: str
    anthology_venue_id: str
    start_date: datetime.date
    end_date: datetime.date
    isbn: str
    location: str
    editors: Optional[List[Person]]
    yaml_tag: str = "!Conference"


@dataclass
class Paper(yaml.YAMLObject):
    title: str
    authors: List[Person]
    num_pages: Optional[int] = 0
    start_page: Optional[int] = 0
    end_page: Optional[int] = 0
    yaml_tag: str = "!Paper"


def load_configs(root: Path):
    """
    Loads all conference configuration files defined in the root directory.
    """
    conference = load_config("conference_details", root, required=True)
    # for item in conference:
    #     if isinstance(conference[item], str):
    #         conference[item] = normalize_latex_string(conference[item])
    papers = load_config("papers", root, required=True)
    # for paper in papers:
    #     paper["title"] = normalize_latex_string(paper["title"])
    sponsors = load_config("sponsors", root)
    prefaces = load_config("prefaces", root)
    organizing_committee = load_config("organizing_committee", root)
    program_committee = load_config("program_committee", root)
    for block in program_committee:
        for entry in block["entries"]:
            for k, v in entry.items():
                try:
                    entry[k] = normalize_latex_string(v)
                except:
                    print(
                        "Warning: the following entry from the program_committee.yml is ill-formed"
                    )
                    print("\t" + str(entry))
                    input("Press a key to continue...")

    invited_talks = load_config("invited_talks", root)
    additional_pages = load_config("additional_pages", root)
    program = load_config("program", root)
    if program is not None:
        for entry in program:
            entry["title"] = normalize_latex_string(entry["title"])

    return (
        conference,
        papers,
        sponsors,
        prefaces,
        organizing_committee,
        program_committee,
        invited_talks,
        additional_pages,
        program,
    )


def load_configs_handbook(root: Path):
    """
    Loads all conference configuration files defined in the root directory.
    """
    conference = load_config("conference_details", root)
    papers = load_config("papers", root)
    for paper in papers:
        paper["title"] = normalize_latex_string(paper["title"])
    sponsors = load_config("sponsors", root)
    prefaces = load_config("prefaces_handbook", root)
    organizing_committee = load_config("organizing_committee", root)
    program_committee = load_config("program_committee", root)
    for block in program_committee:
        for entry in block["entries"]:
            for k, v in entry.items():
                print(k, v)
                entry[k] = normalize_latex_string(v)
    tutorial_program = load_config("tutorial_program", root)
    tutorials = load_config("tutorials", root)
    invited_talks = load_config("invited_talks", root, required=False)
    additional_pages = load_config("additional_pages", root, required=False)
    program = load_config("program", root)
    for entry in program:
        entry["title"] = normalize_latex_string(entry["title"])
    workshops = load_config("workshops", root)
    program_workshops = {}
    for workshop in workshops:
        program_workshops[workshop["id"]] = process_program_workshop_handbook(
            load_config("workshops/" + str(workshop["id"]), root), max_lines=350
        )
    workshop_days = []
    for workshop in workshops:
        wdate = workshop["date"]
        if wdate not in workshop_days:
            workshop_days.append(wdate)

    return (
        conference,
        papers,
        sponsors,
        prefaces,
        organizing_committee,
        program_committee,
        tutorial_program,
        tutorials,
        invited_talks,
        additional_pages,
        program,
        workshops,
        program_workshops,
        workshop_days,
    )


def load_config(config: str, root: Path, required=False):
    path = Path(root, f"{config}.yml")
    if not path.exists():
        if required:
            raise ValueError(
                f"{config} is a required configuration but {config}.yml was not found"
            )
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.load(f, Loader=yaml.Loader)


def normalize_latex_string(text: str) -> str:
    return text.replace("’", "'").replace("&", "\\&").replace("_", "\\_")


def process_program_tutorial_handbook(
    program, max_lines=35, paper_median_lines=3, header_lines=2
):
    """
    process_program organizes program sessions by date, and manually cuts
    program entries in order to avoid page overflow. This is done by assuming
    a median paper entry line length of 3 lines (including title and authors),
    and that a maximum of 35 schedule lines will fit on one page.
    """
    sessions_by_date = defaultdict(list)
    for session in program:
        if "subsessions" in session:
            for session in session["subsessions"]:
                sessions_by_date[session["start_time"].date()].append(session)
        else:
            sessions_by_date[session["start_time"].date()].append(session)
    entries_by_date = {}
    for date, sessions in sessions_by_date.items():
        total_lines = 0
        pages = []
        current_page = []
        for session in sessions:
            table_entries = []
            table_entries.append(
                {
                    "type": "header",
                    "title": session["title"],
                    "start_time": session["start_time"],
                    "end_time": session["end_time"],
                }
            )
            if "tutorials" in session:
                for tutorial in session["tutorials"]:
                    table_entries.append(
                        {
                            "type": "tutorial",
                            "paper": tutorial,
                        }
                    )
            # Split the table lines so that no page overflows.
            for entry in table_entries:
                if entry["type"] == "header":
                    total_lines += header_lines
                elif entry["type"] == "tutorial":
                    total_lines += paper_median_lines
                current_page.append(entry)
                if total_lines >= max_lines:
                    pages.append(current_page)
                    current_page = []
                    total_lines = 0
        pages.append(current_page)
        entries_by_date[date] = pages
        current_page = []
        total_lines = 0
    return sorted(entries_by_date.items())


def process_program_workshop_handbook(
    program, max_lines=35, paper_median_lines=3, header_lines=2
):
    """
    process_program organizes program sessions by date, and manually cuts
    program entries in order to avoid page overflow. This is done by assuming
    a median paper entry line length of 3 lines (including title and authors),
    and that a maximum of 35 schedule lines will fit on one page.
    """
    sessions_by_date = defaultdict(list)
    for session in program:
        if "subsessions" in session:
            for session in session["subsessions"]:
                sessions_by_date[session["start_time"].date()].append(session)
        else:
            sessions_by_date[session["start_time"].date()].append(session)
    entries_by_date = {}
    for date, sessions in sessions_by_date.items():
        total_lines = 0
        pages = []
        current_page = []
        for session in sessions:
            table_entries = []
            table_entries.append(
                {
                    "type": "header",
                    "title": session["title"],
                    "start_time": session["start_time"],
                    "end_time": session["end_time"],
                }
            )
            if "papers" in session:
                for paper in session["papers"]:
                    table_entries.append(
                        {
                            "type": "paper",
                            "paper": paper,
                        }
                    )
            # Split the table lines so that no page overflows.
            for entry in table_entries:
                if entry["type"] == "header":
                    total_lines += header_lines
                elif entry["type"] == "tutorial":
                    total_lines += paper_median_lines
                current_page.append(entry)
                if total_lines >= max_lines:
                    pages.append(current_page)
                    current_page = []
                    total_lines = 0
        pages.append(current_page)
        entries_by_date[date] = pages
        current_page = []
        total_lines = 0
    return sorted(entries_by_date.items())
