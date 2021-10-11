from pathlib import Path
from PyPDF2 import PdfFileReader

import subprocess
import yaml

CONFERENCE_CFG_FILE = "conference_details.yml"
PAPERS_CFG_FILE = "papers.yml"
PAPER_CMD = """
\\addcontentsline{toc}{section}{TEMPLATE_TITLE}
\pagestyle{fancy}
\cfoot{{\\thepage\\\\ \\footnotesize TEMPLATE_WATERMARK\\\\ \copyright TEMPLATE_YEAR Association for Computational Linguistics}}
\setcounter{ptmp}{\\value{page} + TEMPLATE_NUM_PAGES - 1}
\includepdf[pagecommand={\\thispagestyle{fancy}},pages=1]{TEMPLATE_PDF_PATH}
\includepdf[pagecommand={\\thispagestyle{plain}},pages=2-TEMPLATE_NUM_PAGES]{TEMPLATE_PDF_PATH}
"""


def generate(root: str):
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)

    conference, papers = load_configs(root)

    # Load the proceedings template.
    with open(
        Path(Path(__file__).parent, "proceedings_template.tex.txt"),
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
            .replace(
                "TEMPLATE_WATERMARK",
                f"Proceedings of the {conference['name']}, pages \\thepage -\\theptmp",
            )
            .replace("TEMPLATE_NUM_PAGES", str(pdf.getNumPages()))
            .replace("TEMPLATE_YEAR", str(conference["start-date"].year))
        )

    map(paper_cmd, papers)

    pdfs_str = list(map(paper_cmd, papers))
    template = template.replace("TEMPLATE_ABBREV", conference["abbreviation"])
    template = template.replace("TEMPLATE_CONFERENCE_NAME", conference["name"])
    template = template.replace("TEMPLATE_YEAR", str(conference["start-date"].year))
    template = template.replace("TEMPLATE_TITLE", "ACL Anthology")
    template = template.replace("TEMPLATE_PDFS_TO_INCLUDE", "\n".join(pdfs_str))

    tex_file = Path(build_dir, "proceedings.tex")
    with open(tex_file, "w+") as f:
        f.write(template)

    # Build with latex.
    print(f"-output-directory={build_dir}")
    subprocess.run(["pdflatex", f"-output-directory={build_dir}", str(tex_file)])


def load_configs(root: str):
    """
    Loads all conference configuration files defined in the root directory.
    """
    # Conference Details
    with open(Path(root, CONFERENCE_CFG_FILE), "r", encoding="utf-8") as f:
        conference = yaml.safe_load(f)
    # List of papers.
    with open(Path(root, PAPERS_CFG_FILE), "r", encoding="utf-8") as f:
        papers = yaml.safe_load(f)

    return conference, papers
