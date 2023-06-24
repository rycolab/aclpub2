from pathlib import Path
from datetime import datetime

import yaml


def normalize_latex_string(text: str) -> str:
    return (
        text.replace("’", "'")
        .replace("&", "\\&")
        .replace("_", "\\_")
        .replace("%", "\\%")
    )


def load_configs(root: Path):
    """
    Loads all conference configuration files defined in the root directory.
    """
    conference = load_config("conference_details", root, required=True)
    for item in conference:
        if isinstance(conference[item], str):
            conference[item] = normalize_latex_string(conference[item])

    papers = load_config("papers", root)
    if papers is not None:
        for paper in papers:
            paper["title"] = normalize_latex_string(paper["title"])
            paper["abstract"] = normalize_latex_string(paper["abstract"])

            # force strings into data-time objects
            if isinstance(paper["start_time"], str):
                paper["start_time"] = datetime.strptime(paper["start_time"], '%Y-%m-%d %H:%M:%S')
            if isinstance(paper["end_time"], str):
                paper["end_time"] = datetime.strptime(paper["end_time"], '%Y-%m-%d %H:%M:%S')
            
            
    sponsors = load_config("sponsors", root)
    prefaces = load_config("prefaces", root)
    organizing_committee = load_config("organizing_committee", root)
    program_committee = load_config("program_committee", root)
    if program_committee is not None:
        for block in program_committee:
            for entry in block["entries"]:
                for k, v in entry.items():
                    try:
                        entry[k] = normalize_latex_string(v)
                    except:
                        print(
                            "Warning: the following entry from the program_committee.yml is ill-formed"
                        )
                        print("\t" + str(entry))
                        input("Press a key to continue...")

    invited_talks = load_config("invited_talks", root)
    panels = load_config("panels", root)
    additional_pages = load_config("additional_pages", root)
    program = load_config("program", root)
    if program is not None:
        for entry in program:
            entry["title"] = normalize_latex_string(entry["title"])
            if "abstract" in entry:
                entry["abstract"] = normalize_latex_string(entry["abstract"])
            else:
                entry["abstract"] = ""

            # force strings into data-time objects
            if isinstance(entry["start_time"], str):
                entry["start_time"] = datetime.strptime(entry["start_time"], '%Y-%m-%d %H:%M:%S')
            if isinstance(entry["end_time"], str):
                entry["end_time"] = datetime.strptime(entry["end_time"], '%Y-%m-%d %H:%M:%S')
            

            if "subsessions" in entry:
                for subentry in entry["subsessions"]:
                    subentry["title"] = normalize_latex_string(subentry["title"])

                    if isinstance(subentry["start_time"], str):
                        subentry["start_time"] = datetime.strptime(subentry["start_time"], '%Y-%m-%d %H:%M:%S')
                    if isinstance(subentry["end_time"], str):
                        subentry["end_time"] = datetime.strptime(subentry["end_time"], '%Y-%m-%d %H:%M:%S')


    # Consistency check of input material
    is_ok = True
    is_ok = is_ok and check_required_conference_fields(conference)
    is_ok = is_ok and avoid_latex_in_conference_field(conference)

    if not is_ok:
        print(
            "\nAt least one of your input files contains an error, please solve all issues to be compliant with the submission to the ACL Anthology."
        )
        print(
            "Please take a look at: https://github.com/rycolab/aclpub2/blob/main/README.md"
        )
        input("\nPress Enter to continue anyway or Ctrl+C to quit.\n")

    return (
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
    )


def normalize_program(program):
    for entry in program:
        entry["title"] = normalize_latex_string(entry["title"])
        
        
        # force strings into data-time objects
        if isinstance(entry["start_time"], str):
            entry["start_time"] = datetime.strptime(entry["start_time"], '%Y-%m-%d %H:%M:%S')
        if isinstance(entry["end_time"], str):
            entry["end_time"] = datetime.strptime(entry["end_time"], '%Y-%m-%d %H:%M:%S')

            
        if "subsessions" in entry:
            for subentry in entry["subsessions"]:
                subentry["title"] = normalize_latex_string(subentry["title"])
         
                if isinstance(subentry["start_time"], str):
                    subentry["start_time"] = datetime.strptime(subentry["start_time"], '%Y-%m-%d %H:%M:%S')
                if isinstance(subentry["end_time"], str):
                    subentry["end_time"] = datetime.strptime(subentry["end_time"], '%Y-%m-%d %H:%M:%S')
        
                if "papers" in subentry:
                    for paper_slot in subentry["papers"]:
                        if isinstance(paper_slot["start_time"], str):
                            paper_slot["start_time"] = datetime.strptime(paper_slot["start_time"], '%Y-%m-%d %H:%M:%S')
                        if isinstance(paper_slot["end_time"], str):
                            paper_slot["end_time"] = datetime.strptime(paper_slot["end_time"], '%Y-%m-%d %H:%M:%S')
             
     
        if "papers" in entry:
            for paper_slot in entry["papers"]:

                if isinstance(paper_slot["start_time"], str):
                    paper_slot["start_time"] = datetime.strptime(paper_slot["start_time"], '%Y-%m-%d %H:%M:%S')
                if isinstance(paper_slot["end_time"], str):
                    paper_slot["end_time"] = datetime.strptime(paper_slot["end_time"], '%Y-%m-%d %H:%M:%S')


def load_configs_handbook(root: Path):
    """
    Loads all conference configuration files defined in the root directory.
    """
    conference = load_config("conference_details", root)
    papers = load_config("papers", root)
    for paper in papers:
        paper["title"] = normalize_latex_string(paper["title"])
        if "abstract" in paper:
            paper["abstract"] = paper["abstract"] #normalize_latex_string(paper["abstract"])
        else:
            paper["abstract"] = ""
        
    sponsors = load_config("sponsors", root)
    prefaces = load_config("prefaces", root)
    organizing_committee = load_config("organizing_committee", root)
    program_committee = load_config("program_committee", root)
    for block in program_committee:
        for entry in block["entries"]:
            for k, v in entry.items():
                entry[k] = normalize_latex_string(v)
    tutorial_program = load_config("tutorial_program", root)
    normalize_program(tutorial_program)
    tutorials = load_config("tutorials", root)
    invited_talks = load_config("invited_talks", root, required=False)
    panels = load_config("panels", root, required=False)
    additional_pages = load_config("additional_pages", root, required=False)
    program = load_config("program", root)
    normalize_program(program)
    workshops = load_config("workshops", root)
    workshop_programs = {}
    for workshop in workshops:
        workshop_programs[workshop["id"]] = load_config(
            "workshops/program_" + str(workshop["id"]), root, required=True
        )
    workshop_papers = {}
    for workshop in workshops:
        workshop_papers[workshop["id"]] = load_config(
            "workshops/papers_" + str(workshop["id"]), root, required=True
        )
    program_overview = load_config("program_overview", root)

    return (
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
    )


def load_config(config: str, root: Path, required=False):
    path = Path(root, f"{config}.yml")
    if not path.exists():
        if required:
            raise ValueError(
                f"{config} is a required configuration but {config}.yml was not found"
            )
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


required_conference_fields = [
    "book_title",
    "event_name",
    "cover_subtitle",
    "anthology_venue_id",
    "start_date",
    "end_date",
    "isbn",
    "location",
    "editors",
    "publisher",
    "volume_name",
]


def check_required_conference_fields(conference):
    is_ok = True
    for required_conference_field in required_conference_fields:
        if required_conference_field not in conference:
            print(
                "[WARNING] The input file conference_details.yml does not contain the '"
                + required_conference_field
                + "' field."
            )
            is_ok = False

    if "editors" in conference:
        if type(conference["editors"]) is not list:
            print(
                "[WARNING] In the file conference_details.yml, please add at least one editor to the editors field."
            )
            is_ok = False
        else:
            editors = conference["editors"]
            for editor in editors:
                if "first_name" not in editor or "last_name" not in editor:
                    print("[WARNING] In the file conference_details.yml, the editor ")
                    print(editor)
                    print(
                        "is malformed. Each editor should have both first_name and last_name."
                    )
                    is_ok = False

    return is_ok


def avoid_latex_in_conference_field(conference):
    is_ok = True
    for required_conference_field in required_conference_fields:
        value = conference[required_conference_field]
        if isinstance(value, str) and "\\" in value:
            print(
                "[WARNING] The input file conference_details.yml contains a LaTeX escape in '"
                + required_conference_field
                + "': '"
                + value
                + "'. Please avoid to use these escape characters."
            )
            is_ok = False

    return is_ok
