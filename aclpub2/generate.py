from pathlib import Path
from PyPDF2 import PdfFileReader

import subprocess
import yaml


def generate(root: str):
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)

    conference, papers, sponsors, prefaces, organizing_committee = load_configs(root)

    # Load the proceedings template.
    template = load_template("proceedings")
    paper_template = load_template("paper_entry")

    # Generate the templated proceedings.tex file.
    def paper_cmd(paper):
        pdf_path = str(Path(root, "papers", f"{paper['id']}.pdf"))
        pdf = PdfFileReader(pdf_path)
        title = paper["title"].replace("’", "'").replace("&", "\\&")
        return (
            paper_template.replace("TEMPLATE_TITLE", title)
            .replace("TEMPLATE_PDF_PATH", pdf_path)
            .replace("TEMPLATE_NUM_PAGES", str(pdf.getNumPages()))
        )

    map(paper_cmd, papers)

    # Replace the templated PDFs first, to allow othering templating to take effect.
    pdfs_str = list(map(paper_cmd, papers))
    template = template.replace("TEMPLATE_PDFS_TO_INCLUDE", "\n".join(pdfs_str))

    template = template.replace("TEMPLATE_ABBREV", conference["abbreviation"])
    template = template.replace("TEMPLATE_CONFERENCE_NAME", conference["name"])
    template = template.replace("TEMPLATE_ISBN", conference["isbn"])
    template = template.replace("TEMPLATE_YEAR", str(conference["start-date"].year))
    template = template.replace("TEMPLATE_TITLE", "ACL Anthology")
    template = template.replace(
        "TEMPLATE_CONFERENCE_DATES", get_conference_dates(conference)
    )
    template = template.replace("TEMPLATE_SPONSORS", generate_sponsors(sponsors, root))
    template = template.replace("TEMPLATE_PREFACES", generate_prefaces(prefaces, root))
    template = template.replace(
        "TEMPLATE_ORGANIZING_COMMITTEE",
        generate_organizing_committee(organizing_committee, root),
    )

    tex_file = Path(build_dir, "proceedings.tex")
    with open(tex_file, "w+") as f:
        f.write(template)

    # Build with latex.
    print(f"-output-directory={build_dir}")
    subprocess.run(["pdflatex", f"-output-directory={build_dir}", str(tex_file)])


def load_template(template: str) -> str:
    with open(
        Path(Path(__file__).parent, "templates", f"{template}.tex"),
        "r",
        encoding="utf-8",
    ) as f:
        return f.read()


def get_conference_dates(conference) -> str:
    start_date = conference["start-date"]
    end_date = conference["end-date"]
    start_month = start_date.strftime("%B")
    end_month = end_date.strftime("%B")
    if start_month == end_month:
        return f"{start_month} {start_date.day}-{end_date.day}"
    return f"{start_month} {start_date.day} - {end_month} {end_date.day}"


def generate_sponsors(sponsors, root: str) -> str:
    output = ""
    tier_template = load_template("sponsors_tier")
    logo_template = load_template("sponsors_logo")
    for level in sponsors:
        logos = ""
        for logo in level["logos"]:
            logos += logo_template.replace(
                "TEMPLATE_LOGO_FILE", str(Path(root, "sponsor-logos", logo))
            )
        output += tier_template.replace("TEMPLATE_TIER", level["tier"]).replace(
            "TEMPLATE_LOGOS", logos
        )
    return output


def generate_prefaces(prefaces, root: str) -> str:
    output = ""
    template = load_template("preface")
    for preface in prefaces:
        with open(Path(root, "prefaces", preface["file"])) as f:
            body = f.read()
            output += template.replace("TEMPLATE_ROLE", preface["role"]).replace(
                "TEMPLATE_BODY", body
            )
    return output


def generate_organizing_committee(organizing_committee, root: str) -> str:
    output = ""
    role_template = load_template("organizing_committee_role")
    entry_template = load_template("organizing_committee_entry")
    for entry in organizing_committee:
        entries = ""
        for member in entry["members"]:
            entries += entry_template.replace("TEMPLATE_NAME", member["name"]).replace(
                "TEMPLATE_INSTITUTION", member["institution"]
            )
        output += role_template.replace("TEMPLATE_ROLE", entry["role"]).replace(
            "TEMPLATE_ENTRIES", entries
        )
    return output


def load_configs(root: str):
    """
    Loads all conference configuration files defined in the root directory.
    """
    # Conference Details
    with open(Path(root, "conference-details.yml"), "r", encoding="utf-8") as f:
        conference = yaml.safe_load(f)
    # List of papers.
    with open(Path(root, "papers.yml"), "r", encoding="utf-8") as f:
        papers = yaml.safe_load(f)
    # Sponsors.
    with open(Path(root, "sponsors.yml"), "r", encoding="utf-8") as f:
        sponsors = yaml.safe_load(f)
    # Prefaces.
    with open(Path(root, "prefaces.yml"), "r", encoding="utf-8") as f:
        prefaces = yaml.safe_load(f)
    # Organizing Committee
    with open(Path(root, "organizing-committee.yml"), "r", encoding="utf-8") as f:
        organizing_committee = yaml.safe_load(f)

    return conference, papers, sponsors, prefaces, organizing_committee
