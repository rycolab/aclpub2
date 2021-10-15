# aclpub2

## Setup

### Ubuntu/Debian
- Install `pdflatex` and associated dependencies.

```
sudo apt-get install texlive-latex-base
sudo apt-get install texlive-latex-recommended
sudo apt-get install texlive-latex-extra
sudo apt-get install texlive-fonts-recommended
```


### Development
Ensure that `PYTHONPATH` includes `.`, for example `export PYTHONPATH=.:$PYTHONPATH`.

Run the CLI on the example directory:
```
./bin/generate example/
```
