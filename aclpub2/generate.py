from pathlib import Path
from PyPDF2 import PdfFileReader

import subprocess
import yaml

PAPERS_CFG_FILE = "papers.yml"
SPONSORS_CFG_FILE = "sponsors.yml"
PREFACES_CFG_FILE = "prefaces.yml"


PAPER_CMD = """
\\addcontentsline{toc}{section}{TEMPLATE_TITLE}
\pagestyle{fancy}
\cfoot{{\\thepage\\\\
    \\footnotesize\\emph{Prooceedings of the TEMPLATE_CONFERENCE_NAME},
    pages \\thepage -\\theptmp\\\\
    TEMPLATE_CONFERENCE_DATES, TEMPLATE_YEAR
    \\textcopyright TEMPLATE_YEAR Association for Computational Linguistics}}
\setcounter{ptmp}{\\value{page} + TEMPLATE_NUM_PAGES - 1}
\includepdf[pagecommand={\\thispagestyle{fancy}},pages=1]{TEMPLATE_PDF_PATH}
\includepdf[pagecommand={\\thispagestyle{plain}},pages=2-TEMPLATE_NUM_PAGES]{TEMPLATE_PDF_PATH}
"""


def generate(root: str):
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)

    conference, papers, sponsors, prefaces, organizing_committee = load_configs(root)

    # Load the proceedings template.
    with open(
        Path(Path(__file__).parent, "proceedings_template.tex"),
        "r",
        encoding="utf-8",
    ) as f:
        template = f.read()

    # Generate the templated proceedings.tex file.
    def paper_cmd(paper):
        pdf_path = str(Path(root, "papers", f"{paper['id']}.pdf"))
        pdf = PdfFileReader(pdf_path)
        title = paper["title"].replace("’", "'").replace("&", "\\&")
        return (
            PAPER_CMD.replace("TEMPLATE_TITLE", title)
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
    for level in sponsors:
        output += "\\textbf{" + level["tier"] + "}\n\n\\bigskip"
        for logo in level["logos"]:
            output += (
                "\includegraphics[width=2cm]{"
                + str(Path(root, "sponsor-logos", logo))
                + "}"
            )
        output += "\n\n\\bigskip "
    return output


def generate_prefaces(prefaces, root: str) -> str:
    output = ""
    for preface in prefaces:
        output += "\\textbf{Preface by the " + preface["role"] + "}\\\\"
        with open(Path(root, "prefaces", preface["file"])) as f:
            body = f.read()
            output += body
        output += "\\newpage"
    return output


def generate_organizing_committee(organizing_committee, root: str) -> str:
    output = ""
    for entry in organizing_committee:
        output += "\\textbf{" + entry["role"] + "}\\\\ "
        for member in entry["members"]:
            output += f"{member['name']}, {member['institution']}\\\\ "
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
