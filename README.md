# aclpub2

## Setup

### Install python dependencies.

```
python -m pip install -r requirements.txt
```

### Install Java

Java is required to use the [pax](https://ctan.org/pkg/pax?lang=en) latex library,
which is responsible for extracting and reinserting PDF links.
Visit the [Java website](https://www.java.com/) for instructions on how to install.

### Install `pdflatex` and associated dependencies.

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

The generation scripts accepts as input the path to a directory, containing a set of `.yml` files and directories.
Examples and usage of YAML syntax can be found [here](https://www.w3schools.io/file/yaml-arrays/)
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

### Input Format

#### conference_details.yml

List key information about the conference that builds the cover, watermarks, and other items.

```yaml
name: Name of the Conference
abbreviation: Conference abbreviation or acronym, e.g. EMNLP
volume: Volume name, e.g. "Proceedings of the Conference, Vol. 1  (Long Papers)"
start_date: Conference start date YYYY-MM-dd
end_date: Conference end date YYYY-MM-dd
isbn: ISBN number of the proceeding.
```

#### sponsors.yml + sponsor_logos/

List of sponsor tiers along with a directory containing the related logos.

```yaml
- tier: Name of the tier, e.g. Diamond Level or In Collaboration With
  logos:
    - Path to a logo file relative to the sponsor_logos/ directory, e.g. facebook.png
```

#### prefaces.yml + prefaces/

List of prefaces along with a directory containing `.tex` files that provide the text of the prefaces.

```yaml
- title: Title of the preface, e.g. "Preface by the General Chair"
  file: Name of the file relative to the prefaces/ directory containing the preface text, e.g. general_chair.tex
```

The contents of the `.tex` files should not include usual headers and footers found within LaTeX files.
Instead, they should only contain the contents between the `\begin{document}` and `\end{document}` directives.
Frequently, this will simply be plaintext, with a few formulas, figures, or tables.

#### organizing_committee.yml

Lists the members of organizaing committee.

```yaml
- role: Name of role, e.g. General Chair
  members:
    - name: Committe member name as it should appear, e.g. John Doe
      institution: Committee member's institution name as it should appear, e.g. University of California Berkeley, USA
```

#### program_committee.yml

Lists the members of program committee.

```yaml
- role: Name of role, e.g. General Chair
  members:
    - name: Committe member name as it should appear, e.g. John Doe
      institution: Committee member's institution name as it should appear, e.g. University of California Berkeley, USA
- role: Reviewers
  type: name_block  # By adding the name_block type in the role, names will be output in alphabetized blocks.
  entries:
    - Committee Member Name
```

#### invited_talks.yml + invited_talks/

List of invited talks and associated abstracts and bios.
As with the prefaces, the contents of the `.tex` files should not include usual headers and footers found within LaTeX files,
and only what is usually found between the `\begin{document}` and `\end{document}` directives.

```yaml
- speaker_name: Speaker name as it should appear, e.g. Jane Doe
  institution: Speaker's institution name as it should appear, e.g. University of California Berkeley, USA
  title: The title of the talk.
  abstract_file: Path to abstract LaTeX file relative to the invited_talks/ directory.
  bio_file: Path to bio LaTeX file relative to the invited_talks/ directory.
```

#### papers.yml + papers/

Lists the accepted papers, along with a directory containing the associated PDFs.
The listed papers much each have a unique ID so that they may be referred to by ID within the `program.yml` file later on.

```yaml
- id: Unique ID for the paper.
  authors:  # List of authors, structure detailed below.
    - first_name: First name e.g. Jane
    - middle_name: (opt) Middle name e.g. Emily
    - last_name: Last name e.g. Doe
    - prefered_name: (opt) Prefered name, if not the same as first_name.
    - institution: Name of the author's institution.
    - email: Author's email.
    - openreview: (opt) Author's OpenReview username.
    - google_scholar: (opt) Author's Google Scholar ID.
    - orcid: (opt) Author's ORCID ID.
    - dblp: (opt) Author's DBLP ID.
    - semantic_scholar: (opt) Author's Semantic Scholar ID.
  attributes: 
    # A list of key-value pairs used to manage other aspects of
    # the publication process. Below are examples of possible
    # attributes.
    - name: Paper Type
      value: long | short
    - name: Presentation Type
      value: oral | poster
    - name: Submitted Area
      value: Semantics | Machine Learning | ...
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

#### program.yml

Describes the conference program.
This file is organized in blocks, each with a title, start, and end time, followed by a list of papers IDs.

```yaml
- title: Title of the conference session, e.g. Opening Remarks
  start_time: Start time of the session as an ISO datestring.
  end_time: End time of the session as an ISO datestring.
  papers:
  - id: Paper ID
    start_time: Optional start time of the paper slot as an ISO datestring.
    end_time: Optional start time of the paper slot as an ISO datestring.
```

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
