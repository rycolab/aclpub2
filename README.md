# How to generate proceedings for \*CL Conferences and Workshops in aclpub2 format

This guide has been created to provide \*CL Conferences (ACL, NAACL, EMNLP, ... ) and Workshops organisers with the instructions to follow to generate proceedings in aclpub2 format. 

The provided Python tool to generate the proceedings takes as input a set of files containing all information on the event (in the `.yml` format) and generates a `.tex` file containing the conference details, sponsors, prefaces, organizing and program committees, as well as the concatenation of all the watermarked accepted papers and the author index. Such `.tex` file is then compiled to generate the `pdf` file of the proceedings (to be sent to ACL Anthology following [these instructions](https://aclanthology.org/info/contrib/)).


## Before starting

###  Which reviewing platform is you conference/workshop using?
- OpenReview. This guide is for you, we will explain you how to use the provided tool to generate the proceedings (and the handbook) automatically from OpenReview. 
- EasyChair (or any other reviewing platform). This guide is for you, we will explain you how to generate the proceedings starting from manually edited files.
- SoftConf. You can either follow the istructions provided by this guide to generate the proceedings starting from manually edited files (this is the suggested option for small-medium size events) or follow the [ACLPUB instructions](https://github.com/acl-org/acl-pub/blob/gh-pages/aclpub-start.md).


## Table of Contents
1. [Proceedings input format and structure](#Proceedings-input-format-and-structure)

2. [Expected output](#Expected-output)

3. [Manually editing yml input files](#Manually-editing-yml-input-files)

4. [How to export yml files from OpenReview](#How-to-export-yml-files-from-OpenReview)

5. [Testing the tool to generate your proceedings](#Testing-the-tool-to-generate-your-proceedings)


## Proceedings input format and structure
The scripts to generate the proceedings accept as input a set of `.yml` files and directories. A YML file is a text document that contains data formatted using YAML (YAML Ain't Markup Language), a human-readable data format used for data serialization. You can open a YML file in any text editor (or source code editor).
Examples and usage of YAML syntax can be found [here](https://www.w3schools.io/file/yaml-arrays/).

The following `.yml` files should be provided to the generation scripts. Files 1, 2, 3, 4 and 6 should be manually edited with information concerning your conference/workshops, while files 5 and 7 can be automatically exported from OpenReview (or manually edited if you are not using OpenReview).

1. `conference_details.yml`
2. `sponsors.yml` (optional)
3. `prefaces.yml`
4. `organizing_committee.yml`
5. `program_committee.yml`
6. `invited_talks.yml` (optional)
7. `papers.yml`

We strongly suggest taking a look at this [link](https://github.com/rycolab/aclpub2/tree/main/examples/sigdial), where you can find **examples** of all the above files initialized for a past conference.

In addition, for the handbook, a file `program.yml` should be created [Jump to Handbook generation instructions](#Handbook-generation-instructions). 

## Expected output
The generated proceedings should be sent to the ACL Anthology [(instructions)](https://aclanthology.org/info/contrib/) as a `.zip` or `.tgz` file containing a repository named with the conference/workshop acronym. Such repository should contain:
1. A folder named `input` containing all the input files (i.e., the `*.yml` and `*.tex` files used to generate the proceedings)
2. A folder named `watermarked_pdf` containing all the pdfs of the watermarked camera ready papers AND the attacments 
3. A folder name `attachments` containinng all files associated with the paper. Notice that these file must be correctly referred in the `papers.yml` file.
4. A PDF file named `proceedings.pdf` containing the whole conference/workshop proceedings (i.e., the introduction and all the watermarked PDFs of the camera ready papers).

Upload the resulting file (<conference>_data.tgz) to a file server or cloud storage (e.g. Google Drive) and email the link to it to the Anthology Director. Please do not send the file as an email attachment.

**Important:** Before generating the final proceedings, please carefully check the input pdfs of the camera ready papers with the ACLPUBCHECK tool, a Python tool that automatically detects author formatting errors, margin violations as well as many other common formatting errors in papers that are using the LaTeX sty file associated with ACL venues. The tool and instructions to use it can be found [here](https://github.com/acl-org/aclpubcheck). We *strongly suggest* to share with the authors this tool before the sumbission of their final camera ready, in order to reduce the effort of controlling possibly hundreds of papers. 

## Manually editing yml input files
Below you can find instructions (and examples) on how you should edit the `.yml` files with information on your conference/workshop.

#### conference_details.yml
This file should contain the key information about the conference, as its name, abbreviation and so on. It is used to build the cover of the proceedings, watermarks, and other items.

Note that the ISBN of your conference/workshop will be provided by ACL.

```yaml
book_title: name of the book; it should be in the form "Proceedings of ..." and it will be used in the bib file to name the event
event_name: name of the Conference or Workshop and it will be used in the frontmatter of the proceedeings and in the watermark over the single papers
cover_subtitle: the subtitle used in the cover of the proceedings, it can be in the form "Proceedings of the Conference, Vol. 1  (Long Papers)" or "Proceedings of the Workshop"
anthology_venue_id: conference/workshop abbreviation or acronym, e.g. EMNLP
start_date: Conference start date YYYY-MM-dd
end_date: Conference end date YYYY-MM-dd
isbn: ISBN number of the proceeding (assigned by the ACL)
location: location of the conference
editors: list of the editors of the volume, in the form 
  - first_name: name of the editor (e.g., John)
    middle_name: middle nanme of the editor (e.g., D.)
    last_name: surname of the editor (e.g., Walker)
publisher: published of the conference, generally "Association for Computational Linguistics"
```

Here some example, first for a conference:

```yaml
book_title: Proceedings of the 60th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)
event_name: The 60th Annual Meeting of the Association for Computational Linguistics
cover_subtitle: Proceedings of the Conference (Volume 1: Long Papers)
anthology_venue_id: ACL
start_date: 2022-05-22
end_date: 2022-05-27
isbn: XXX-X-XXXXXX-XX-X (you should replace this with the real ISBN)
location: Dublin, Ireland
editors:
  - first_name: Smaranda
    last_name: Muresan
  - first_name: Preslav
    last_name: Nakov
  - first_name: Aline
    last_name: Villavicencio
publisher: Association for Computational Linguistics
```

and for a workshop

```yaml
book_title: Proceedings of the 2nd Workshop on Human Evaluation of NLP Systems (HumEval 2021)
event_name: The 2nd Workshop on Human Evaluation of NLP Systems
cover_subtitle: Proceedings of the Workshop
anthology_venue_id: HumEval
start_date: 2022-05-27
end_date: 2022-05-27
isbn: XXX-X-XXXXXX-XX-X (you should replace this with the real ISBN)
location: Dublin, Ireland
editors:
  - first_name: Belz
    last_name: Anya
  - first_name: Popović
    last_name: Maja
  - first_name: Reiter
    last_name: Ehud
  - first_name: Shimorina
    last_name: Anastasia
publisher: Association for Computational Linguistics
```


#### sponsors.yml
This file should list the sponsors (if any). A directory containing the related logos should be created in the same directory of the `.yml` files (named sponsor_logos/).

```yaml
- tier: Name of the tier, e.g. Diamond Level or In Collaboration With
  logos:
    - Path to a logo file relative to the sponsor_logos/ directory, e.g. facebook.png
```

#### prefaces.yml
This file should list the prefaces that will be included in the proceedings. A directory containing the `.tex` files that provide the text of the prefaces should be created in the same directory of the `.yml` files (named prefaces/).

```yaml
- title: Title of the preface, e.g. "Preface by the General Chair"
  file: Name of the file relative to the prefaces/ directory containing the preface text, e.g. general_chair.tex
```

The contents of the `.tex` files should not include usual headers and footers found within LaTeX files.
Instead, they should only contain the contents between the `\begin{document}` and `\end{document}` directives.
Frequently, this will simply be plaintext, with a few formulas, figures, or tables.

#### organizing_committee.yml
This file should list the members of the organizaing committee. You should edit this file manually.
```yaml
- role: Name of role, e.g. General Chair
  members:
    - name: Committee member name as it should appear, e.g. John Doe
      institution: Committee member's institution name as it should appear, e.g. University of California Berkeley, USA
```

#### program_committee.yml
This file should list the members of the program committee. You can edit this file manually, or export it from OpenReview [Jump to How to export yml files from OpenReview](#How-to-export-yml-files-from-OpenReview).

```yaml
- role: Name of role, e.g. General Chair
  members:
    - name: Committee member name as it should appear, e.g. John Doe
      institution: Committee member's institution name as it should appear, e.g. University of California Berkeley, USA
- role: Reviewers
  type: name_block  # By adding the name_block type in the role, names will be output in alphabetized blocks.
  entries:
    - Committee Member Name
```

#### invited_talks.yml
This optional file should list the invited talks and associated abstracts and bios. A directory containing the `.tex` files that provide the text of the abstract and the bios should be created in the same directory of the `.yml` files (named invited_talks/).
As with the prefaces, the contents of the `.tex` files should not include usual headers and footers found within LaTeX files,
and only what is usually found between the `\begin{document}` and `\end{document}` directives.

```yaml
- speaker_name: Speaker name as it should appear, e.g. Jane Doe
  institution: Speaker's institution name as it should appear, e.g. University of California Berkeley, USA
  title: The title of the talk.
  abstract_file: Path to abstract LaTeX file relative to the invited_talks/ directory.
  bio_file: Path to bio LaTeX file relative to the invited_talks/ directory.
```

#### papers.yml

This file should list the accepted papers, along with a directory (named papers/) containing the associated PDFs.
Each of the listed papers must have a unique ID so that they may be referred to by ID within the `program.yml` file later on. You can edit this file manually, or export it from OpenReview [Jump to How to export yml files from OpenReview](#How-to-export-yml-files-from-OpenReview).


```yaml
- id: Unique ID for the paper.
  authors:  # List of authors, structure detailed below.
    - first_name: First name e.g. Jane
      middle_name: (opt) Middle name e.g. Emily
      last_name: Last name e.g. Doe
      preferred_name: (opt) Prefered name, if not the same as first_name.
      institution: Name of the author's institution.
      email: Author's email.
      openreview: (opt) Author's OpenReview username.
      google_scholar: (opt) Author's Google Scholar ID.
      orcid: (opt) Author's ORCID ID.
      dblp: (opt) Author's DBLP ID.
      semantic_scholar: (opt) Author's Semantic Scholar ID.
  attributes: 
    # Key-value pairs used to manage other aspects of
    # the publication process. Below are examples of possible
    # attributes.
    paper_type: long | short
    presentation_type: oral | poster
    submitted_area: Semantics | Machine Learning | ...
  file: File name relative to the papers/ directory, e.g. 1.pdf
  attachments:
    # A list of additional files associated with the paper.
    # The type, along with one of file or url must be specified.
    - type: Dataset | Note | Poster | Presentation | Software | Attachment
      file: Local file path, e.g. attachments/5.zip
      url: URL pointing to the file, e.g. https://openreview.net/attachment?id=abcdefg
  title: Title of the paper.
  abstract: Abstract of the paper, usually a LaTeX fragment.
```

## How to export yml files from OpenReview
When running your workshop on OpenReview, it is possible to use their API for automatically extracting the `papers.yml` and `program_committee.yml` files. For this purpose, we provide two Python3 scripts for facilitating your work.
  
1. `or2papers.py`: it creates the `papers.yml` file by extracting the papers marked as "accepted" as "Decision"; 

2. `or2program_committee.py`: it creates the `program_committee.yml` file by retrieving the *Senior Area Chairs* list registered at workshop spate on OpenReview and the list of reviewers;
  
Those scripts are designed to be used by the workshop's Program Chairs due to access permission required during the queries to OpenReview. To use these scripts, you will need **username** (the e-mails used for login onto OpenReview), **password** (the password associated with the user's account), and the **workshop_ID** (the OpenReview identifier linked to the workshop).

**Workshop ID**: you can find out the workshop's identifier by following one of the two approaches below:
1. Workshop ID is identified as "venue ID" on the setup website.

2. Workshop ID is present at the workshop's URL. It is the ID field. For example, the ID of the ACL conference (https://openreview.net/group?id=aclweb.org/ACL/2022/Conference) is "aclweb.org/ACL/2022/Conference". Note that & is a separator in the URL. Therefore anything after it is not part of the workshop ID.

### Before running the scripts

#### Requirements
Those scripts require Python3 and OpenReview API installed on your machine. For installing OpenReview API, please go to https://openreview-py.readthedocs.io/en/latest/how_to_setup.html

#### Updated data
The scripts based on OpenReview API retrieve all information directly from OpenReview. In other words, all SACs, reviewers and authors must have their OpenReview profiles updated (mainly name and affiliation).
  
### or2papers.py
This script will find the intersection of all blind submissions and the submissions with a decision set as accepted. Those papers' information will be stored in the `paper.yml` file and downloaded at the "papers" and "attachments" folders. The download includes the PDF and additional attachments provided during the submission. Note that papers are randomly sorted, and different runs of the `or2papers.py` will return the papers sorted differently. 
For running `or2papers.py` type:

```
python or2papers.py USER PASSWORD WORKSHOP_ID
```
For example: 

```
python or2papers.py myuser@acl.com 123456 aclweb.org/ACL/2022/Conference
```

### or2program_committee.py
This script searches all Senior_Area_Chairs and Program_Chairs under your conference and saves their information in the `program_committee.yml` file.

For running `or2papers.py` type:
  
```
python or2program_committee.py USER PASSWORD WORKSHOP_ID
```
For example: 
```
python or2program_committee.py myuser@acl.com 123456 aclweb.org/ACL/2022/Conference
```
### :warning: Warnings
1. The workshops that accepts the ARR commitment should be aware that the `or2program_committee.py` script only extracts data of submitted/committed papers.

2. During the script execution, you may see a message such as "ERROR: or_id not found". It means that the script could not retrieve the profile's information from OpenReview. Therefore, you must insert manually the data in the `paper.yml` or `program_committee.yml`. You can identify the problematic OpenReview ID and their papers in `paper.log` and `program_committee.log`

  

## Testing the tool to generate your proceedings
Now that you know the expected structure of the proceedings and you know how to edit/export the required `.yml` input files, you are ready to test the tool to automatically generate the proceedings. First of all, follow the Setup procedures. 

Then, as a training example, we made at your disposal in the examples/sigdial repository all the files you would need to correctly generate the proceedings. 

Could you compile the sigdial proceedings? :confetti_ball:

Excellent, you are now ready to run the generation scripts on the files you have just edited/exported for your conference/workshop.

### Setup: Install python dependencies.

```
python -m pip install -r requirements.txt
```

### Setup: Install Java

Java is required to use the [pax](https://ctan.org/pkg/pax?lang=en) latex library,
which is responsible for extracting and reinserting PDF links.
Visit the [Java website](https://www.java.com/) for instructions on how to install.

### Setup: Install `pdflatex` and associated dependencies.

#### Ubuntu/Debian

```
sudo apt-get install texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra texlive-bibtex-extra
```

#### OSX

Install `mactex`.

One way this is to install [Homebrew](https://brew.sh) first and then:

```
brew install mactex
```

### Test Run

Ensure that `PYTHONPATH` includes `.`, for example `export PYTHONPATH=.:$PYTHONPATH`.

Run the CLI on the SIGDIAL example directory:

```
./bin/generate examples/sigdial --proceedings --handbook
```

The generated results, along with intermediate files and links, can then be found in
the `build` directory in the directory in which you ran the command.

## Usage

As said before, the generation scripts accepts as input the path to a directory, containing a set of `.yml` files and directories.
This expected input directory structure and the CLI are detailed below.

### CLI

```bash
# Generates the proceedings.
./bin/generate examples/sigdial --proceedings

# Generates the handbook.
./bin/generate examples/sigdial --handbook

# Generates both.
./bin/generate examples/sigdial --proceedings --handbook

# Generates both and overwrites the existing contents of the build directory.
./bin/generate examples/sigdial --proceedings --handbook --overwrite
```

Users may wish to make modifications to the output `.tex` files.
Though we recommend first copying the `.tex` files to a new working directory,
the `--overwrite` flag helps ensure that local modifications are not accidentally erased.


## Development

The above describe a reasonable default usage of this package, but the behavior can easily be extended or modified by adjusting the contents of the `aclpub2/` directory.
The main files to keep in mind are `aclpub2/templates/proceedings.tex` which contains the core Jinja template file, and `aclpub2/generate.py` which is responsible for rendering the template.

#### Jinja

This project makes extensive use of Jinja to produce readable Latex templates.
Before contributing or forking, it is generally helpful to familiarize yourself with
the Jinja library. Documentation can be found [here](https://jinja.palletsprojects.com/en/2.11.x/templates/https://jinja.palletsprojects.com/en/2.11.x/templates/).

Additional configuration for Jinja can be found in the `aclpub2/templates.py` file.
The purpose of this file are to set up the Jinja environment with LaTeX-like block delimiters so that the `proceedings.tex` file can be syntax highlighted and otherwise interacted with in a fashion that is more natural for LaTeX users.
In addition, it is also responsible for configuring some convenience functions that allow us to create some LaTeX structures in the final output `.tex` file that are easier to write in native Python than either the Jinja base syntax, or LaTeX alone.

## Handbook generation instructions

** Work in progress **

#### program.yml

Describes the conference program.
This file is organized in blocks, each with a title, start, and end time, followed by a list of papers IDs.
Instead of defining presentations, sessions may define subsessions, which have the same structure as the top-level session.

```yaml
- title: Title of the conference session, e.g. Opening Remarks
  start_time: Start time of the session as an ISO datestring.
  end_time: End time of the session as an ISO datestring.
  location: Location that the session is taking place in, e.g. Main Hall or Online
  chair: (opt) Name of the chair of the session, e.g. Jane Doe.
  url: (opt) URL to join or view the session, if applicable.
  papers:
  - id: Paper ID
    start_time: Optional start time of the paper slot as an ISO datestring.
    end_time: Optional start time of the paper slot as an ISO datestring.
# Or, if this is a session that is broken into subsessions:
- title: Title of the conference session, e.g. Opening Remarks
  start_time: Start time of the session as an ISO datestring.
  end_time: End time of the session as an ISO datestring.
  subsessions:
    - title: Title of the conference session, e.g. Opening Remarks
    start_time: Start time of the session as an ISO datestring.
    end_time: End time of the session as an ISO datestring.
    chair: (opt) Name of the chair of the session, e.g. Jane Doe.
    location: Location that the session is taking place in.
    papers:
    - id: Paper ID
      start_time: Optional start time of the paper slot as an ISO datestring.
      end_time: Optional start time of the paper slot as an ISO datestring.
```
