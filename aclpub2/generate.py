from collections import defaultdict
from pathlib import Path
from PyPDF2 import PdfFileReader
from aclpub2.templates import load_template, TEMPLATE_DIR

import subprocess
import yaml
import shutil

PARENT_DIR = Path(__file__).parent


def generate(*, path: str, proceedings: bool, handbook: bool, overwrite: bool):
    root = Path(path)
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)

    # Throw if the build directory isn't empty, and the user did not specify an overwrite.
    if len([build_dir.iterdir()]) > 0 and not overwrite:
        raise Exception(
            f"Build directory {build_dir} is not empty, and the overwrite flag is false."
        )

    # Load and preprocess the .yml configuration.
    (
        conference,
        papers,
        sponsors,
        prefaces,
        organizing_committee,
        program_committee,
        invited_talks,
        program,
    ) = load_configs(root)
    id_to_paper, alphabetized_author_index = process_papers(papers, root, proceedings)
    if proceedings:
        sessions_by_date = process_program_proceedings(program)
        template = load_template("proceedings")
        rendered_template = template.render(
            root=str(root),
            conference=conference,
            conference_dates=get_conference_dates(conference),
            sponsors=sponsors,
            prefaces=prefaces,
            organizing_committee=organizing_committee,
            program_committee=program_committee,
            invited_talks=invited_talks,
            papers=papers,
            id_to_paper=id_to_paper,
            program=sessions_by_date,
            alphabetized_author_index=alphabetized_author_index,
        )
        tex_file = Path(build_dir, "proceedings.tex")
        with open(tex_file, "w+") as f:
            f.write(rendered_template)
        subprocess.run(["pdflatex", f"-output-directory={build_dir}", str(tex_file)])

    if handbook:
        # Load and preprocess the .yml configuration.
        (
            conference,
            papers,
            sponsors,
            prefaces,
            organizing_committee,
            program_committee,
            harassment,
            meal,
            program_tutorial,
            tutorial_message,
            tutorials,
            welcome,
            invited_talks,
            program,
            awards,
            social_event,
            workshops,
            program_workshops,
            workshop_days,
            local_guide,
            venue_map
        ) = load_configs_handbook(root)

        template = load_template("handbook")
        program = process_program_handbook(program)
        program_tutorial = process_program_tutorial_handbook(program_tutorial, 350,3)
        rendered_template = template.render(
            root=str(root),
            conference=conference,
            conference_dates=get_conference_dates(conference),
            sponsors=sponsors,
            prefaces=prefaces,
            organizing_committee=organizing_committee,
            program_committee=program_committee,
            harassment=harassment,
            meal=meal,
            program_tutorial=program_tutorial,
            tutorial_message=tutorial_message,
            tutorials=tutorials,
            welcome=welcome,
            invited_talks=invited_talks,
            papers=papers,
            id_to_paper=id_to_paper,
            program=program,
            awards=awards,
            social_event=social_event,
            workshops=workshops,
            program_workshops=program_workshops,
            workshop_days=workshop_days,
            build_dir=str(build_dir),
            local_guide=local_guide,
            venue_map=venue_map
        )
        tex_file = Path(build_dir, "handbook.tex")
        with open(tex_file, "w+") as f:
            f.write(rendered_template)
        if not Path(build_dir, "content").exists():
            shutil.copytree(f"{TEMPLATE_DIR}/content", f"{build_dir}/content")
        subprocess.run(["pdflatex", f"-output-directory={build_dir}", str(tex_file)])
        subprocess.run(["makeindex", str(tex_file.with_suffix(".idx"))])
        subprocess.run(["pdflatex", f"-output-directory={build_dir}", str(tex_file)])
def get_conference_dates(conference) -> str:
    start_date = conference["start_date"]
    end_date = conference["end_date"]
    start_month = start_date.strftime("%B")
    end_month = end_date.strftime("%B")
    if start_month == end_month:
        return f"{start_month} {start_date.day}-{end_date.day}"
    return f"{start_month} {start_date.day} - {end_month} {end_date.day}"


def process_papers(papers, root: Path, pax: bool):
    """
    process_papers
    - uses PAX to extract PDF annotations from the paper files in preparation for
        re-insertion
    - maps paper ID to the contents of the paper in order to assist with program
        generation
    - alphabetizes and splits author names, and associates them with the start pages
        of papers they authored, in preparation for index generation
    """
    page = 1
    id_to_paper = {}
    author_to_pages = defaultdict(list)
    for paper in papers:
        pdf_path = Path(root, "papers", f"{paper['id']}.pdf")
        if pax:
            subprocess.run(
                [
                    "java",
                    "-cp",
                    f"{PARENT_DIR}/pax.jar:{PARENT_DIR}/pdfbox.jar",
                    "pax.PDFAnnotExtractor",
                    pdf_path,
                ]
            )
        pdf = PdfFileReader(str(pdf_path))
        paper["num_pages"] = pdf.getNumPages()
        paper["page_range"] = (page, page + pdf.getNumPages() - 1)
        id_to_paper[paper["id"]] = paper
        for author in paper["authors"]:
            name_parts = author.split(" ")
            index_name = f"{name_parts[-1]}, {' '.join(name_parts[:-1])}"
            author_to_pages[index_name].append(page)
        page += pdf.getNumPages()
    alphabetized_author_index = defaultdict(list)
    for author, pages in sorted(author_to_pages.items()):
        alphabetized_author_index[author[0].lower()].append((author, pages))
    return id_to_paper, sorted(alphabetized_author_index.items())

def process_program_handbook(program):
    sessions_by_date = defaultdict(list)
    for session in program:
        sessions_by_date[session["start_time"].date()].append(session)
    return sorted(sessions_by_date.items())


def process_program_proceedings(program):
    """
    process_program organizes program sessions by date, and manually cuts
    program entries in order to avoid page overflow. This is done by assuming
    a median paper entry line length of 3 lines (including title and authors),
    and that a maximum of 35 schedule lines will fit on one page.
    """
    max_lines = 35
    paper_median_lines = 3
    header_lines = 2
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
                for paper_id in session["papers"]:
                    table_entries.append(
                        {
                            "type": "paper",
                            "paper": paper_id,
                        }
                    )
            # Split the table lines so that no page overflows.
            for entry in table_entries:
                if entry["type"] == "header":
                    total_lines += header_lines
                elif entry["type"] == "paper":
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


def process_program_tutorial_handbook(program, max_lines = 35, paper_median_lines = 3, header_lines = 2):
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
                    "end_time": session["end_time"]
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

def process_program_workshop_handbook(program, max_lines = 35, paper_median_lines = 3, header_lines = 2):
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
                    "end_time": session["end_time"]
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




def normalize_latex_string(text: str) -> str:
    return text.replace("’", "'").replace("&", "\\&")


def load_configs(root: Path):
    """
    Loads all conference configuration files defined in the root directory.
    """
    conference = load_config("conference_details", root)
    papers = load_config("papers", root)
    for paper in papers:
        paper["title"] = normalize_latex_string(paper["title"])
    sponsors = load_config("sponsors", root)
    prefaces = load_config("prefaces", root)
    organizing_committee = load_config("organizing_committee", root)
    program_committee = load_config("program_committee", root)
    invited_talks = load_config("invited_talks", root, required=False)
    program = load_config("program", root)
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
    harassment = load_config("harassment", root)
    meal = load_config("meal", root)
    program_tutorial =load_config("program_tutorial", root)
    tutorial_message = load_config("tutorial_message", root)
    tutorials = load_config("tutorials", root)
    welcome_receiption= load_config("welcome_receiption", root)
    invited_talks = load_config("invited_talks", root, required=False)
    program = load_config("program", root)
    for entry in program:
        entry["title"] = normalize_latex_string(entry["title"])
    awards = load_config("awards", root)
    social_event = load_config("social_event", root)
    workshops = load_config("workshops", root)
    program_workshops = {}
    for workshop in workshops:
        program_workshops[workshop["id"]] = process_program_workshop_handbook(load_config("workshops/"+str(workshop["id"]), root),350)
    workshop_days=[]
    for workshop in workshops:
        wdate = workshop["date"]
        if wdate not in workshop_days:
            workshop_days.append(wdate)
    local_guide = load_config("local_guide", root)
    venue_map = load_config("venue_map", root)

    return (
        conference,
        papers,
        sponsors,
        prefaces,
        organizing_committee,
        program_committee,
        harassment,
        meal,
        program_tutorial,
        tutorial_message,
        tutorials,
        welcome_receiption,
        invited_talks,
        program,
        awards,
        social_event,
        workshops,
        program_workshops,
        workshop_days,
        local_guide,
        venue_map
    )

def load_config(config: str, root: Path, required=True):
    path = Path(root, f"{config}.yml")
    if not path.exists():
        if required:
            raise ValueError(
                f"{config} is a required configuration but {config}.yml was not found"
            )
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
