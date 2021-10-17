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

    # Fill templates.
    # paper_id_to_page = process_papers(
    #     papers, Path(build_dir, "papers")
    # )

    rendered_template = template.render(
        root=str(root),
        conference=conference,
        conference_dates=get_conference_dates(conference), sponsors=sponsors, prefaces=prefaces,
        organizing_committee=organizing_committee,
        program_committee=program_committee,
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
    paper_template = load_template("paper_entry")
    toc_template = load_template("toc_entry")
    templated_papers = ""
    templated_toc = ""
    page_ranges = {}
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
        title = paper["title"].replace("’", "'").replace("&", "\\&")
        templated_papers += (
            paper_template.replace("TEMPLATE_TITLE", title)
            .replace("TEMPLATE_PDF_PATH", str(pdf_path))
            .replace("TEMPLATE_NUM_PAGES", str(pdf.getNumPages()))
        )
        author_string = ""
        for i, author in enumerate(paper["authors"]):
            if i == len(paper["authors"]) - 1:  # Last author
                author_string += " and "
            author_string += author
            if i < len(paper["authors"]) - 1:
                author_string += ", "
        templated_toc += (
            toc_template.replace("TEMPLATE_TITLE", title)
            .replace("TEMPLATE_AUTHORS", author_string)
            .replace("TEMPLATE_PAGE", str(page))
        )
        page_ranges[paper["id"]] = (page, page + pdf.getNumPages() - 1)
        page += pdf.getNumPages()
    return page_ranges


def generate_organizing_committee(organizing_committee) -> str:
    output = ""
    role_template = load_template("committee_role")
    for entry in organizing_committee:
        entries = ""
        for member in entry["members"]:
            entries += generate_committee_entry(member)
        output += role_template.replace("TEMPLATE_ROLE", entry["role"]).replace(
            "TEMPLATE_ENTRIES", entries
        )
    return output


def generate_committee_entry(member) -> str:
    entry_template = load_template("committee_entry")
    return entry_template.replace("TEMPLATE_NAME", member["name"]).replace(
        "TEMPLATE_INSTITUTION", member["institution"]
    )


def generate_program_committee(program_committee) -> str:
    output = ""
    program_committee_template = load_template("program_committee")

    # First add program commitee members
    program_committee_entries = ""
    for member in program_committee["program_committee"]:
        program_committee_entries += generate_committee_entry(member)

    area_chair_role_template = load_template("area_chair_role")
    senior_area_chairs = ""
    for area in program_committee["senior_area_chairs"]:
        entries = ""
        for member in area["members"]:
            entries += generate_committee_entry(member)
        senior_area_chairs += area_chair_role_template.replace("TEMPLATE_AREA",
                                                               area["area"]).replace("TEMPLATE_ENTRIES", entries)
    area_chairs = ""
    for area in program_committee["area_chairs"]:
        entries = ", ".join(area["members"])
        area_chairs += area_chair_role_template.replace("TEMPLATE_AREA",
                                                        area["area"]).replace("TEMPLATE_ENTRIES", entries)

    output = program_committee_template.replace(
        "TEMPLATE_PROGRAM_COMMITTEE_ENTRIES", program_committee_entries
    ).replace("TEMPLATE_SENIOR_AREA_CHAIRS", senior_area_chairs).replace("TEMPLATE_AREA_CHAIRS", area_chairs).replace("TEMPLATE_REVIEWERS", ", ".join(program_committee["reviewers"]))
    return output


def generate_invited_talks(invited_talks, root: Path) -> str:
    output = ""
    invited_talk_template = load_template("invited_talk")
    for talk in invited_talks:
        id = talk["id"]
        with open(Path(root, "invited_talks", f"{id}_abstract.tex")) as f:
            abstract = f.read()
        with open(Path(root, "invited_talks", f"{id}_bio.tex")) as f:
            bio = f.read()
        output += (
            invited_talk_template.replace("TEMPLATE_NAME", talk["speaker_name"])
            .replace("TEMPLATE_INSTITUTION", talk["institution"])
            .replace("TEMPLATE_TITLE", talk["title"])
            .replace("TEMPLATE_ABSTRACT", abstract)
            .replace("TEMPLATE_BIO", bio)
        )
    return output


def generate_program(program) -> str:
    program = get_program_sessions_by_date(program)
    return "PLACEHOLDER"


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
