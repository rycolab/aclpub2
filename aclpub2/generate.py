from collections import defaultdict
from pathlib import Path
from PyPDF2 import PdfFileReader
from aclpub2.templates import load_template

import subprocess
import yaml

PARENT_DIR = Path(__file__).parent


def generate(root: str):
    root = Path(root)
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)

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

    # Load the proceedings template.
    template = load_template("proceedings")

    id_to_paper, alphabetized_author_index = process_papers(papers, root)
    sessions_by_date = process_program(program)

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

    # Write the resulting tex file.
    tex_file = Path(build_dir, "proceedings.tex")
    with open(tex_file, "w+") as f:
        f.write(rendered_template)

    # Build with latex.
    subprocess.run(["pdflatex", f"-output-directory={build_dir}", str(tex_file)])


def get_conference_dates(conference) -> str:
    start_date = conference["start_date"]
    end_date = conference["end_date"]
    start_month = start_date.strftime("%B")
    end_month = end_date.strftime("%B")
    if start_month == end_month:
        return f"{start_month} {start_date.day}-{end_date.day}"
    return f"{start_month} {start_date.day} - {end_month} {end_date.day}"


def process_papers(papers, root: Path):
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


def process_program(program):
    """
    process_program organizes program sessions by date, and manually cuts
    program entries in order to avoid page overflow. This is done by assuming
    a median paper entry line length of 3 lines (including title and authors),
    and that a maximum of 35 schedule lines will fit on one page.
    """
    max_lines = 35
    paper_median_lines = 3
    header_lines = 2
    dates = set()
    for session in program:
        dates.add(session["start_time"].date())
    sessions_by_date = defaultdict(list)
    for session in program:
        sessions_by_date[session["start_time"].date()].append(session)
    entries_by_date = {}
    for date, sessions in sessions_by_date.items():
        total_lines = 0
        pages = []
        current_page = []
        for session in sessions:
            table_entries = []
            table_entries.append({
                "type": "header",
                "title": session["title"],
                "start_time": session["start_time"],
                "end_time": session["end_time"],
            })
            if "papers" in session:
                for paper_id in session["papers"]:
                    table_entries.append({
                        "type": "paper",
                        "paper": paper_id,
                    })
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


def load_config(config: str, root: Path, required=True):
    path = Path(root, f"{config}.yml")
    if not path.exists():
        if required:
            raise ValueError(f"{config} is a required configuration but {config}.yml was not found")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
