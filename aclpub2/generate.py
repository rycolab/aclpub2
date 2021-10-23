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
    sessions_by_date = get_program_sessions_by_date(program)

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


def get_program_sessions_by_date(program):
    dates = set()
    for session in program:
        dates.add(session["start_time"].date())
    sessions_by_date = defaultdict(list)
    for session in program:
        sessions_by_date[session["start_time"].date()].append(session)
    return sessions_by_date


def normalize_latex_string(text: str) -> str:
    return text.replace("’", "'").replace("&", "\\&")


def load_configs(root: Path):
    """
    Loads all conference configuration files defined in the root directory.
    """
    with open(Path(root, "conference_details.yml"), "r", encoding="utf-8") as f:
        conference = yaml.safe_load(f)
    with open(Path(root, "papers.yml"), "r", encoding="utf-8") as f:
        papers = yaml.safe_load(f)
        for paper in papers:
            paper["title"] = normalize_latex_string(paper["title"])
    with open(Path(root, "sponsors.yml"), "r", encoding="utf-8") as f:
        sponsors = yaml.safe_load(f)
    with open(Path(root, "prefaces.yml"), "r", encoding="utf-8") as f:
        prefaces = yaml.safe_load(f)
    with open(Path(root, "organizing_committee.yml"), "r", encoding="utf-8") as f:
        organizing_committee = yaml.safe_load(f)
    with open(Path(root, "program_committee.yml"), "r", encoding="utf-8") as f:
        program_committee = yaml.safe_load(f)
    with open(Path(root, "invited_talks.yml"), "r", encoding="utf-8") as f:
        invited_talks = yaml.safe_load(f)
    with open(Path(root, "program.yml"), "r", encoding="utf-8") as f:
        program = yaml.safe_load(f)
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
