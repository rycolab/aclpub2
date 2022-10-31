import csv
import yaml
import collections
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--csv_path", 
        type=str, 
        help="Path to input csv."
)
parser.add_argument(
        "--out_path",
        type=str,
        default="output.yaml",
        help="Name of YAML file to write to.",
)
parser.add_argument("--author_field_name", 
        type=str, 
        default="Authors_Full"
)
args = parser.parse_args()


all_entries = []
with open(args.csv_path, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        row_out = collections.OrderedDict()
        authors = collections.defaultdict(dict)
        for k, v in row.items():
            if k.split(':')[0].isnumeric():
                if not v:
                    continue
                number, attribute = k.split(': ')
                authors[int(number)][attribute] = v
            else:
                row_out[k] = v
        row_out[args.author_field_name] = [authors[key] for key in sorted(authors.keys(), reverse=True)]
        all_entries.append(dict(row_out))

with open(args.out_path, 'w') as outfile:
    yaml.dump(
        all_entries,
        outfile,
        sort_keys=False)
