from pathlib import Path

import subprocess
import yaml

PAPERS_CFG_FILE = "papers.yml"
PAPER_CMD = """
\\addcontentsline{toc}{section}{TEMPLATE_TITLE}
\includepdf[pagecommand={\\thispagestyle{plain}},pages=-]{TEMPLATE_PDF_PATH}
"""


def generate(root: str):
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)

    # Load the proceedings template.
    with open(
        Path(Path(__file__).parent, "proceedings_template.tex.txt"),
        "r",
        encoding="utf-8",
    ) as f:
        template = f.read()

    # Load the config file listing all papers.
    with open(Path(root, PAPERS_CFG_FILE), "r", encoding="utf-8") as f:
        papers = yaml.safe_load(f)

    # Generate the templated proceedings.tex file.
    def paper_cmd(paper):
        title = paper["title"].replace("’", "'").replace("&", "\\&")
        return PAPER_CMD.replace("TEMPLATE_TITLE", title).replace(
            "TEMPLATE_PDF_PATH", str(Path(root, "papers", f"{paper['id']}.pdf"))
        )

    map(paper_cmd, papers)

    pdfs_str = list(map(paper_cmd, papers))
    template = template.replace("TEMPLATE_TITLE", "ACL Anthology")
    template = template.replace("TEMPLATE_PDFS_TO_INCLUDE", "\n".join(pdfs_str))

    tex_file = Path(build_dir, "proceedings.tex")
    with open(tex_file, "w+") as f:
        f.write(template)

    # Build with latex.

    print(f"-output-directory={build_dir}")
    subprocess.run(["pdflatex", f"-output-directory={build_dir}", str(tex_file)])
