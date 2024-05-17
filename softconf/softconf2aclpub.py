#!/usr/bin/env python

import mechanize
from pprint import pprint
import json
from getpass import getpass
from bs4 import BeautifulSoup
import yaml
import wget
import csv
import zipfile
from glob import glob
import os
import shutil
import re

with open("config.json") as f:
    config = json.load(f)

if config["username"] == "" or config["password"] == "":
    config["username"] = input("Insert your SOFTCONF username: ")
    config["password"] = getpass("Insert your SOFTCONF password: ")

SOFTCONF_URL = "https://www.softconf.com/"
CONF_URL = f"{SOFTCONF_URL}{config['conf']}/{config['track']}/"


def capitalize_name(name):
    """
        :param name: a string containing a name
        :return: the string where the first letter of every token is capitalized
    """
    tokens = name.split(" ")
    if '-' in tokens[0]:
        count = tokens[0].count('-')
        if count == 1:
            toks = [tok[0].upper()+tok[1:].lower() for tok in tokens[0].split('-')]
        elif count > 1:
            names = tokens[0].split('-')
            toks = []
            for i, n in enumerate(names):
                if i != 1:
                    toks += [n[0].upper()+n[1:].lower()]
                else:
                    if n[0] == n[0].lower():
                        toks += [n]
                    else:
                        toks += [n[0].upper()+n[1:].lower()]
        tokens_capitalized = "-".join(toks)
    else:
        tokens_capitalized = [token[0].upper()+token[1:].lower() for token in tokens]
    return " ".join(tokens_capitalized)

def full_name(first_name, last_name, middle_name=None):
    """
        :param first_name: a string containing a first name
        :param last_name: a string containing a last name
        :param middle_name: a string containing a middle name
        :return: a string containing the full name with corret capitalization
    """
    first_name = capitalize_name(first_name)
    last_name = capitalize_name(last_name)
    if not middle_name is None and len(middle_name)>0:
        middle_name = capitalize_name(middle_name)
        full_name = " ".join([first_name, middle_name, last_name])
    else:
        full_name = " ".join([first_name, last_name])

    full_name = full_name.replace("  ", " ")
    return full_name

def tex_escape(text):
    """
        :param text: a plain text message
        :return: the message escaped to appear correctly in LaTeX
    """
    conv = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
        '<': r'\textless{}',
        '>': r'\textgreater{}',
    }
    regex = re.compile('|'.join(re.escape(str(key)) for key in sorted(conv.keys(), key = lambda item: - len(item))))
    return regex.sub(lambda match: conv[match.group()], text)

# helper function for SOFTCONF scraping
def follow_link_by_text(br, text):
    """
        :param br: a Browser object
        :param text: the text of a link in a page
        :return: the response of the browser after following the link
    """
    for link in br.links():
        if link.text == text:
            response = br.follow_link(link)
            return response
    return None

def get_conference_details():
    br = mechanize.Browser()
    cj = mechanize.LWPCookieJar()
    opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(cj))
    mechanize.install_opener(opener)

    br.set_handle_robots(False)   # ignore robots
    br.set_handle_refresh(False)  # can sometimes hang without this
    br.addheaders = [('User-agent', 'Firefox')]

    # open login page
    response = br.open(CONF_URL)

    # select login form
    br.form = list(br.forms())[0]

    # login as manager
    br.form.controls[0].value = config["username"]
    br.form.controls[1].value = config["password"]
    response = br.submit()

    # navigate to the setup page
    response = follow_link_by_text(br, "Manager Console")
    response = follow_link_by_text(br, "Conference Setup Tool")

    # select configuration form
    br.form = list(br.forms())[2]

    metadata = dict()
    for control in br.form.controls:
        if control.type == "text":
            metadata[control.name] = control.value

    # read the conference metadata        
    conference_details = dict()
    conference_details["book_title"] = f"Proceedings of the {metadata['CONF_NAME']} (XXX)"
    conference_details["event_name"] = metadata['CONF_NAME']
    conference_details["cover_subtitle"] = f"Proceedings of the Conference (XXX)"
    conference_details["anthology_venue_id"] = "ACL"
    conference_details["start_date"] = "XXXX-XX-XX"
    conference_details["end_date"] = "XXXX-XX-XX"
    conference_details["isbn"] = "XXX-X-XXXXXX-XX-X"
    conference_details["location"] = metadata["CONF_LOCATION"]
    conference_details["publisher"] = "Association for Computational Linguistics"

    # open the admin accounts page
    response = br.back()
    response = follow_link_by_text(br, "Manager Console")
    response = follow_link_by_text(br, "Manage Administration Accounts")

    # read the names of the chairs
    conference_details["editors"] = []
    html = response.read()
    soup = BeautifulSoup(html, features="html5lib")
    table = soup.find(id="t2")
    for row in table.findAll('tr')[1:-1]:
        col = row.findAll('td')
        conference_details["editors"].append({
            "first_name": capitalize_name(col[3].string.strip()),
            "last_name": capitalize_name(col[4].string.strip())
        })

    # write the YAML
    with open("conference_details.yml", "w") as fo:
        yaml.dump(conference_details, fo, allow_unicode=True)

def get_program_committee():
    program_committee = [
        {
            "role": "Chairs",
            "entries":[]
        },
        {
            "role": "Program Committee",
            "entries":[]
        }
        ]
    filename = wget.download(config["service_program_committee"])
    with open(filename, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            person = {
                "first_name": capitalize_name(row["First Name"]),
                "last_name": capitalize_name(row["Last Name"]),
                "name": full_name(row["First Name"], row["Last Name"]),
                "emails": row["Email"],
                "homepage": "",
                "dblp_id": "",
                "google_scholar_id": row["Google Scholar ID"],
                "semantic_scholar_id": row["Semantic Scholar ID"],
                "orcid": row["ORCID"],
                "institution": tex_escape(row["Affiliation"]),
                "username": row["Username"]
            }
            roles = row["Roles"].split(":")
            if "manager" in roles:
                program_committee[0]["entries"].append(person)
            elif "committee" in roles:
                program_committee[1]["entries"].append(person)

    # write the YAML
    with open("program_committee.yml", "w") as fo:
        yaml.dump(program_committee, fo, allow_unicode=True)

def get_files():
    br = mechanize.Browser()
    cj = mechanize.LWPCookieJar()
    opener = mechanize.build_opener(mechanize.HTTPCookieProcessor(cj))
    mechanize.install_opener(opener)

    br.set_handle_robots(False)   # ignore robots
    br.set_handle_refresh(False)  # can sometimes hang without this
    br.addheaders = [('User-agent', 'Firefox')]

    # open login page
    response = br.open(CONF_URL)

    # select login form
    br.form = list(br.forms())[0]

    # login as manager
    br.form.controls[0].value = config["username"]
    br.form.controls[1].value = config["password"]
    response = br.submit()

    # navigate to the setup page
    response = follow_link_by_text(br, "Manager Console")
    response = follow_link_by_text(br, "Monitor Final Submissions")

    # select download form
    br.form = list(br.forms())[2]
    response = br.submit()
    archive = response.read()
    with open("files.zip", "wb") as fo:
        fo.write(archive)
    with zipfile.ZipFile("files.zip", 'r') as zip_ref:
        zip_ref.extractall(".")

    os.makedirs("papers", exist_ok=True)
    for filename in glob("final/*/*.pdf"):
        paper_id = os.path.basename(filename).split("_")[0]
        os.rename(filename, os.path.join("papers", paper_id+".pdf"))

    os.makedirs("attachments", exist_ok=True)
    for filename in glob("final/*/*"):
        os.rename(filename, os.path.join("attachments", os.path.basename(filename)))

    shutil.rmtree("final")
    os.remove("files.zip")

def get_papers():
    papers = []
    filename = wget.download(config["service_papers"])
    with open(filename, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            authors = []
            if row["Acceptance Status"].startswith("Accept"):
                author_col = re.compile(r'(\d+): Last Name')
                authors_i = sorted([
                    int(author_col.match(key).group(1))
                    for key in row if author_col.match(key)
                ])
                for i in authors_i:
                    if row[f"{i}: Last Name"] != "":
                        authors.append({
                            "emails": row[f"{i}: Email"],
                            "first_name": capitalize_name(row[f"{i}: First Name"]),
                            "last_name": capitalize_name(row[f"{i}: Last Name"]),
                            "name": full_name(row[f"{i}: First Name"], row[f"{i}: Last Name"], middle_name=row[f"{i}: Middle Name"]),
                            "username": row[f"{i}: Username"],
                            "institution": tex_escape(row[f"{i}: Affiliation"])
                        })
                sub_type = "Submission Type" if "Submission Type" in row else "Paper type"
                paper = {
                    "abstract": tex_escape(row["Abstract"]),
                    "attributes": {
                        "paper_type": row[sub_type],
                        "presentation_type": "N/A",
                        "submitted_area": row["Track"] if "Track" in row else "",
                    },
                    "authors": authors,
                    "decision": "Accept to main conference",
                    "file": row["Submission ID"]+".pdf",
                    "id": row["Submission ID"],
                    "title": tex_escape(row["Title"]),
                }

                attachments = []
                for filename in glob(os.path.join("attachments", f"{row['Submission ID']}_*")):
                    attachments.append({
                        "file": os.path.basename(filename),
                        "type": "Supplementary Material"
                    })
                if len(attachments) > 0:
                    paper["attachments"] = attachments

                papers.append(paper)

    # write the YAML
    with open("papers.yml", "w") as fo:
        yaml.dump(papers, fo, width=4096, allow_unicode=True)

# main
get_conference_details()
get_program_committee()
get_files()
get_papers()


