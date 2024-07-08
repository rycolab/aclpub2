from collections import defaultdict
from pathlib import Path
from PyPDF2 import PdfFileReader

from aclpub2.templates import load_template, homoglyph, TEMPLATE_DIR
from aclpub2.config import load_configs, load_configs_handbook

import multiprocessing
import subprocess
import roman
import shutil
import os
import glob
import traceback
import yaml

PARENT_DIR = Path(__file__).parent


def generate_proceedings(path: str, overwrite: bool, outdir: str, nopax: bool, frontmatter: bool):
    root = Path(path)
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)

    # Throw if the build directory isn't empty, and the user did not specify an overwrite.
    if len([_ for _ in build_dir.iterdir()]) > 0 and not overwrite:
        raise Exception(
            f"Build directory {build_dir} is not empty, and the overwrite flag is false."
        )
    if overwrite:
        shutil.rmtree(str(build_dir), ignore_errors=True)
        build_dir.mkdir()

    # Load and preprocess the .yml configuration.
    (
        conference,
        papers,
        sponsors,
        prefaces,
        organizing_committee,
        program_committee,
        invited_talks,
        panels,
        additional_pages,
        program,
    ) = load_configs(root)

    sessions_by_date = None
    if program is not None:
        try:
            sessions_by_date = process_program(program)
        except:
            print("Sorry. Your program.yml file seems malformed. It will be skipped.")
            traceback.print_exc()
            sessions_by_date = None

    id_to_paper, alphabetized_author_index, archival_papers = process_papers(papers, root)

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
        panels=panels,
        additional_pages=additional_pages,
        archival_papers=archival_papers,
        id_to_paper=id_to_paper,
        program=sessions_by_date,
        alphabetized_author_index=alphabetized_author_index,
        include_papers=False,
        nopax=nopax,
    )
    tex_file = Path(build_dir, "front_matter.tex")
    with open(tex_file, "w+") as f:
        f.write(rendered_template)
    subprocess.run(
        [
            "pdflatex",
            f"-output-directory={build_dir}",
            "-save-size=40000",
            str(tex_file),
        ]
    )

    # Regenerate the output directory.
    output_dir = Path(outdir)
    shutil.rmtree(str(output_dir), ignore_errors=True)
    output_dir.mkdir()

    # Copy the inputs yaml.
    input_copy_dir = Path(output_dir, "inputs")
    input_copy_dir.mkdir()
    files = glob.iglob(os.path.join(root, "*.y*ml"))
    for file in files:
        if os.path.isfile(file):
            shutil.copy2(file, input_copy_dir)

    # If there are no papers, treat the front_matter as the proceedings and exit.
    if papers is None:
        shutil.copy2(
            Path(build_dir, "front_matter.pdf"), Path(output_dir, "proceedings.pdf")
        )
        return

    # If frontmatter is set, output the front matter and exit.
    if frontmatter:
        shutil.copy2(
            Path(build_dir, "front_matter.pdf"), Path(output_dir, "front_matter.pdf")
        )
        return

    generate_watermarked_pdfs(id_to_paper.values(), conference, root)
    rendered_template = template.render(
        root=str(root),
        conference=conference,
        conference_dates=get_conference_dates(conference),
        sponsors=sponsors,
        prefaces=prefaces,
        organizing_committee=organizing_committee,
        program_committee=program_committee,
        invited_talks=invited_talks,
        panels=panels,
        additional_pages=additional_pages,
        archival_papers=archival_papers,
        id_to_paper=id_to_paper,
        program=sessions_by_date,
        alphabetized_author_index=alphabetized_author_index,
        include_papers=True,
        nopax=nopax,
    )
    tex_file = Path(build_dir, "proceedings.tex")
    with open(tex_file, "w+") as f:
        f.write(rendered_template)
    subprocess.run(
        [
            "pdflatex",
            f"-output-directory={build_dir}",
            "-save-size=40000",
            str(tex_file),
        ]
    )
    # Must run the latex compilation twice to include internal links.
    subprocess.run(
        [
            "pdflatex",
            f"-output-directory={build_dir}",
            "-save-size=40000",
            str(tex_file),
        ]
    )

    # Copy proceedings
    shutil.copy2(
        Path(build_dir, "proceedings.pdf"), Path(output_dir, "proceedings.pdf")
    )
    # Copy watermarked PDFs.
    output_watermarked = Path(output_dir, "watermarked_pdfs")
    output_watermarked.mkdir()
    for file in Path(build_dir, "watermarked_pdfs").glob("*.pdf"):
        shutil.copy2(file, output_watermarked)
    # Copy the front matter as 0.pdf.
    shutil.copy2(Path(build_dir, "front_matter.pdf"), Path(output_watermarked, "0.pdf"))
    # Overwrite the papers.yml with information that contains page ranges
    with open(Path(input_copy_dir, "papers.yml"), "w") as new_papers_yml:
        yaml.dump(papers, new_papers_yml)
    # Copy other input folders.
    for folder_to_copy in [
        "papers",
        "invited_talks",
        "panels",
        "additional_pages",
        "prefaces",
        "sponsor_logos",
    ]:
        copy_folder(
            Path(root, folder_to_copy), Path(input_copy_dir, folder_to_copy)
        )

    copy_folder(Path(root, "attachments"), Path(output_dir, "attachments"))


def copy_folder(input_path: Path, output_dir: Path):
    if os.path.isdir(input_path):
        shutil.copytree(input_path, output_dir)


def find_page_offset(proceedings_pdf):
    offset = None
    last_roman = None
    last_page = None
    for i in range(proceedings_pdf.getNumPages()):
        page_line = proceedings_pdf.getPage(i).extractText().split("\n")[-2]
        try:  # Make sure the roman numbered front-matter is correct.
            rn = roman.fromRoman(page_line)
            if last_roman is None:
                last_roman = rn
            elif rn != last_roman + 1:
                raise ValueError("Failed to detect consecutive page numbers.")
            last_roman = rn
        except roman.InvalidRomanNumeralError as e:
            try:
                pn = int(page_line)
                if pn == 1:
                    offset = i - 1
                if last_page is not None and pn != last_page + 1:
                    raise ValueError("Failed to detect consecutive page numbers.")
                last_page = pn
            except ValueError as e:
                if last_roman is not None:
                    raise ValueError(f"Failed to parse page numbers: {e}")
    return offset


def generate_handbook(path: str, overwrite: bool):
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
        tutorial_program,
        tutorials,
        invited_talks,
        panels,
        additional_pages,
        program,
        program_overview,
        workshops,
        workshop_programs,
        workshop_papers,
    ) = load_configs_handbook(root)
    program_workshops = {}
    for id, workshop_program in workshop_programs.items():
        if workshop_program is not None:
            program_workshops[id] = process_program(workshop_program)
    workshop_days = []
    for workshop in workshops:
        wdate = workshop["date"]
        if wdate not in workshop_days:
            workshop_days.append(wdate)

    id_to_paper = {}
    for paper in papers:
        id_to_paper[str(paper["id"])] = paper

    template = load_template("handbook")
    program = process_program_handbook(program)
    tutorial_program = process_program(tutorial_program, max_lines=350)
    rendered_template = template.render(
        root=str(root),
        conference=conference,
        conference_dates=get_conference_dates(conference),
        sponsors=sponsors,
        prefaces=prefaces,
        organizing_committee=organizing_committee,
        program_committee=program_committee,
        tutorial_program=tutorial_program,
        tutorials=tutorials,
        invited_talks=invited_talks,
        panels=panels,
        additional_pages=additional_pages,
        papers=papers,
        id_to_paper=id_to_paper,
        program=program,
        program_overview=program_overview,
        workshops=workshops,
        program_workshops=program_workshops,
        workshop_days=workshop_days,
        workshop_papers=workshop_papers,
        build_dir=str(build_dir),
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
        if start_date.day == end_date.day:
            return f"{start_month} {start_date.day}"
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
    if papers is None:
        return None, None, None
    page = 1
    id_to_paper = {}
    author_to_pages = defaultdict(list)
    archival_papers = []
    for paper in papers:
        # Always add the paper to the id-to-paper map.
        if "id" not in paper:
            raise ValueError(f"missing 'id' in paper: {paper}")
        id_to_paper[paper["id"]] = paper
        # If the paper is not archival, skip the rest of the processing.
        if "archival" in paper and not paper["archival"]:
            continue
        if "file" not in paper:
            raise ValueError(f"missing 'file' in paper {paper['id']}")
        pdf_path = Path(root, "papers", paper["file"])
        pdf = PdfFileReader(str(pdf_path))
        paper["num_pages"] = pdf.getNumPages()
        paper["start_page"] = page
        paper["end_page"] = page + pdf.getNumPages() - 1
        if "authors" not in paper:
            raise ValueError(f"missing 'authors' in paper {paper['id']}")
        for author in paper["authors"]:
            if "first_name" not in author:
                raise ValueError(f"missing 'first_name' in author of paper {paper['id']}")
            given_names = author["first_name"]
            if "middle_name" in author:
                given_names += f" {author['middle_name']}"
            if "last_name" not in author:
                raise ValueError(f"missing 'last_name' in author of paper {paper['id']}")
            index_name = f"{author['last_name']}, {given_names}"
            author_to_pages[index_name].append(page)
        page += pdf.getNumPages()
        archival_papers.append(paper)
    alphabetized_author_index = defaultdict(list)
    for author, pages in sorted(author_to_pages.items()):
        alphabetized_author_index[homoglyph(author[0]).lower()].append((author, pages))
    for author_pages in alphabetized_author_index.values():
        author_pages.sort(key=lambda entry: entry[0].lower())
    return id_to_paper, sorted(alphabetized_author_index.items()), archival_papers


def error_handler(e):
    print(traceback.print_exception(type(e), e, e.__traceback__))
    input(
        "\nSorry. I have problems compiling the watermarked papers. Press Enter to process another paper or Ctrl+C to quit.\n"
    )


def generate_watermarked_pdfs(papers_with_pages, conference, root: Path):
    build_dir = Path("build")
    watermarked_pdfs = Path(build_dir, "watermarked_pdfs")
    watermarked_pdfs.mkdir(exist_ok=True)
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        for paper in papers_with_pages:
            if "archival" in paper and not paper["archival"]:
                continue
            pool.apply_async(
                create_watermarked_pdf,
                args=(paper, conference, root),
                error_callback=error_handler,
            )
        pool.close()
        pool.join()


def create_watermarked_pdf(paper, conference, root: Path):
    build_dir = Path("build")
    watermarked_pdfs = Path(build_dir, "watermarked_pdfs")
    template = load_template("watermarked_pdf")
    rendered_template = template.render(
        root=root,
        paper=paper,
        conference=conference,
        conference_dates=get_conference_dates(conference),
    )
    tex_file = Path(watermarked_pdfs, f"{paper['id']}.tex")
    with open(tex_file, "w+") as f:
        f.write(rendered_template)
    pdf_path = Path(root, "papers", paper["file"])
    pax_path = pdf_path.with_suffix(".pax")
    if not pax_path.exists():
        subprocess.call(
            [
                "java",
                "-cp",
                f"{PARENT_DIR}/pax.jar:{PARENT_DIR}/pdfbox.jar",
                "pax.PDFAnnotExtractor",
                pdf_path,
            ]
        )
    print(f"Compiling {paper['id']}")
    returncode = subprocess.call(
        [
            "pdflatex",
            "-halt-on-error",
            f"-output-directory={watermarked_pdfs}",
            str(tex_file),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
    )
    returncode = subprocess.call(
        [
            "pdflatex",
            "-halt-on-error",
            f"-output-directory={watermarked_pdfs}",
            str(tex_file),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
    )
    if returncode != 0:
        # Some PAX errors can be handled by trying a second time.
        returncode = subprocess.call(
            [
                "pdflatex",
                "-halt-on-error",
                f"-output-directory={watermarked_pdfs}",
                str(tex_file),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )

    if returncode > 0:
        raise Exception(
            "Sorry but it seems I cannot compile paper "
            + str(paper["file"])
            + " and it will not be added to the output folder!"
            + "\nIt is generally due to a PDF with a problematic internal links."
            '\nA "possible" solution is to open the PDF with any preview system and export it again.'
        )


def process_program_handbook(program):
    sessions_by_date = defaultdict(list)
    for session in program:
        sessions_by_date[session["start_time"].date()].append(session)
    return sorted(sessions_by_date.items())


def process_program(program, max_lines=32, paper_median_lines=3, header_lines=2):
    """
    process_program organizes program sessions by date, and manually cuts
    program entries in order to avoid page overflow. This is done by assuming
    a median paper entry line length of 3 lines (including title and authors),
    and that a maximum of 32 schedule lines will fit on one page.
    """
    max_lines = 32
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
