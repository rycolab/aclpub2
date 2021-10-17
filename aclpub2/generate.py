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

    process_papers(papers, root)

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
    )

    # Write the resulting tex file.
    tex_file = Path(build_dir, "proceedings.tex")
    with open(tex_file, "w+") as f:
        f.write(rendered_template)

    # Build with latex.
    subprocess.run(["pdflatex", f"-output-directory={build_dir}", str(tex_file)])


def load_preface_text(root: Path):
    pass


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
        paper["title"] = paper["title"].replace("’", "'").replace("&", "\\&")
        paper["num_pages"] = pdf.getNumPages()
        paper["page_range"] = (page, page + pdf.getNumPages() - 1)
        page += pdf.getNumPages()


def get_program_sessions_by_date(program):
    dates = set()
    for session in program:
        dates.add(session["start_time"].date())
    sessions_by_date = defaultdict(list)
    for session in program:
        sessions_by_date[session["start_time"].date()].append(session)
    return sessions_by_date


def load_configs(root: Path):
    """
    Loads all conference configuration files defined in the root directory.
    """
    with open(Path(root, "conference_details.yml"), "r", encoding="utf-8") as f:
        conference = yaml.safe_load(f)
    with open(Path(root, "papers.yml"), "r", encoding="utf-8") as f:
        papers = yaml.safe_load(f)
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
