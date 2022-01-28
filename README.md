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

Run the CLI on the example directory:

```
./bin/generate example/ --proceedings --handbook
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
./bin/generate example/ --proceedings

# Generates the handbook.
./bin/generate example/ --handbook

# Generates both.
./bin/generate example/ --proceedings --handbook

# Generates both and overwrites the existing contents of the build directory.
./bin/generate example/ --proceedings --handbook --overwrite
```

Users may wish to make modifications to the output `.tex` files.
Though we recommend first copying the `.tex` files to a new working directory,
the `--overwrite` flag helps ensure that local modifications are not accidentally erased.

### Input Format

#### conference_details.yml

List key information about the conference that builds the cover, watermarks, and other items.

```
name: [str] Name of the Conference
abbreviation: [str] Conference abbreviation or acronym, i.e. EMNLP
start_date: [str] Conference start date YYYY-MM-dd
end_date: [str] Conference end date YYYY-MM-dd
isbn: [str] ISBN number of the proceeding.
```

#### organizing_committee.yml

Lists the members of organizaing committee.

```
- role: Name of role, i.e. General Chair
  members:
    - name: Committe member name as it should appear, i.e. John Doe
      institution: Committee member's institution name as it should appear, i.e. University of California Berkeley, USA
```

#### program_committee.yml

Lists the members of program committee.

```
- role: Name of role, i.e. General Chair
  members:
    - name: [str] Committe member name as it should appear, i.e. John Doe
      institution: [str] Committee member's institution name as it should appear, i.e. University of California Berkeley, USA
    # OR
    - [str] Committee member name as it should appear, if institution should not be included.
- role: Reviewers
  type: name_block  # By adding the name_block type in the role, names will be output in alphabetized blocks.
  entries:
    - [str] Committee Member Name
```

#### papers.yml + papers/

Lists the accepted papers, along with a directory containing the associated PDFs.
The listed papers much each have a unique ID so that they may be referred to by ID within the `program.yml` file later on.

```
- id: [str] Unique ID for the paper.
  authors:
    - [str] Author1 Name
    - [str] Author2 Name
  file: [str] File name relative to the papers/ directory, i.e. 1.pdf
  title: [str] Title of the paper.
  abstract: [str] Abstract of the paper, usually a LaTeX fragment.
```

#### program.yml

Describes the conference program.
This file is organized in blocks, each with a title, start, and end time, followed by a list of papers IDs.

```
- title: [str] Title of the conference session, i.e. Opening Remarks
  start_time: [str] Start time of the session as an ISO datestring.
  end_time: [str] End time of the session as an ISO datestring.
  papers:
  - id: [str] Paper ID
    start_time: [str] Optional start time of the paper slot as an ISO datestring.
    end_time: [str] Optional start time of the paper slot as an ISO datestring.
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
