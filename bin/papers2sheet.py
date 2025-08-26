# Converts papers.xml (extracted from OpenReview) into a tab-separated file to be copy-pasted
# to a Google sheet for workshop chairs (use Ctrl+Shift+V)
#
# Ivan Habernal, July 2024
# MIT License

from pathlib import Path
from typing import List
import yaml


def generate_sheet_tsv(input_file_yml: Path, output_file_tsv: Path) -> None:
    yaml_load: List[dict] = yaml.safe_load(input_file_yml.read_text('utf-8'))

    with open(output_file_tsv, 'wt', encoding='utf-8') as output_f:
        # Iterate over papers
        for entry in yaml_load:
            # print(entry.keys())
            # -> abstract', 'attributes', 'authors', 'file', 'id', 'openreview_id', 'pdf_file', 'title

            # Single paper output container
            single_output_line_list: List[str] = []

            # Paper ID
            single_output_line_list.append(entry.get('id'))
            # Title
            single_output_line_list.append(entry.get('title'))
            # Abstract to a single line
            single_output_line_list.append(entry.get('abstract').replace('\n', ' '))

            # Collect authors
            authors: List[dict] = entry.get('authors')
            for author in authors:
                # keys: ['emails', 'first_name', 'google_scholar_id', 'homepage', 'last_name', 'name', 'username'])
                # We need: author X first name; author X last name; author X email
                single_output_line_list.append(author.get('first_name'))
                single_output_line_list.append(author.get('last_name'))
                single_output_line_list.append(author.get('emails'))

            # explicitly re-type to string ... because yaml and Python
            output_line = '\t'.join([str(_) for _ in single_output_line_list])
            print(output_line)

            output_f.write(output_line + '\n')


if __name__ == '__main__':
    # example usage
    generate_sheet_tsv(Path('examples/privatenlp24ws/papers.yml'),
                       Path('examples/privatenlp24ws/papers.tsv'))
