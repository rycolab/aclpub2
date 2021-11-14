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
sudo apt-get install texlive-latex-base
sudo apt-get install texlive-latex-recommended
sudo apt-get install texlive-latex-extra
sudo apt-get install texlive-fonts-recommended
```

#### OSX
Install `mactex`.

One way this is to install [Homebrew](https://brew.sh) first and then:
```
brew install mactex
```

### Development
Ensure that `PYTHONPATH` includes `.`, for example `export PYTHONPATH=.:$PYTHONPATH`.

Run the CLI on the example directory:
```
./bin/generate example/
```

The generated results, along with intermediate files and links, can then be found in
the `build` directory in the directory in which you ran the command.

#### Jinja
This project makes extensive use of Jinja to produce readable Latex templates.
Before contributing or forking, it is generally helpful to familiarize yourself with
the Jinja library. Documentation can be found [here](ttps://jinja.palletsprojects.com/en/2.11.x/templates/https://jinja.palletsprojects.com/en/2.11.x/templates/)

