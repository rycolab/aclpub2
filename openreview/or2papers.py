#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------------
# Created By Rodrigo Wilkens
# Last update 02/April/2022
# version ='1.0'
# ---------------------------------------------------------------------------

import argparse
import openreview
import os
import yaml
from tqdm import tqdm
import sys
from util import *


def main(username, password, venue, download_all, download_pdfs):
    try:
        client_acl = openreview.Client(
            baseurl="https://api.openreview.net", username=username, password=password
        )
        client_acl_v2 = openreview.Client(
            baseurl="https://api2.openreview.net", username=username, password=password
        )
    except:
        print("OpenReview connection refused")
        exit()

    try:
        venue_group = client_acl_v2.get_group(venue)
        in_v2 = venue_group.domain is not None and venue_group.domain == venue_group.id
    except:
        print(f"{venue} not found")
        exit()

    if not download_all or not download_pdfs:
        print("The output of this run cannot be used at ACLPUB2")

    attachment_types = {"software": "software", "Data": "note"}

    papers_folder = "papers"
    attachments_folder = "attachments"
    if not os.path.exists(papers_folder):
        os.mkdir(papers_folder)
    if not os.path.exists(attachments_folder):
        os.mkdir(attachments_folder)

    if not in_v2:
        submissions = list(
            openreview.tools.iterget_notes(
                client_acl, invitation=venue + "/-/Blind_Submission", details="original"
            )
        )
    else:
        submissions = client_acl_v2.get_all_notes(invitation=venue + "/-/Submission")

    decision_by_forum = {
        d.forum: d
        for d in list(
            openreview.tools.iterget_notes(
                client_acl, invitation=venue + "/Paper.*/-/Decision"
            )
        )
        if "accept" in d.content["decision"].lower()
    }

    papers = []
    small_log = open("papers.log", "w")
    for submission in tqdm(submissions):
        if submission.id not in decision_by_forum:
            continue
        authorsids = submission.details["original"]["content"]["authorids"]
        authors = []
        for authorsid in authorsids:
            author, error = get_user(authorsid, client_acl)
            if error:
                small_log.write(
                    "Error at "
                    + authorsid
                    + " from (#"
                    + str(submission.number)
                    + "; openreview ID: "
                    + submission.id
                    + ") "
                    + submission.content["title"]
                    + "\n"
                )
            if author:
                authors.append(author)
        assert len(authors) > 0
        paper = {
            "id": submission.number,  # len(papers)+1,
            "title": submission.content["title"],
            "authors": authors,
            "abstract": submission.content["abstract"]
            if "abstract" in submission.content
            else "",
            "file": str(submission.number) + ".pdf",  # str(len(papers)+1) + ".pdf",
            "pdf_file": submission.content["pdf"].split("/")[-1],
            "decision": decision_by_forum[submission.id].content["decision"],
            "openreview_id": submission.id,
        }

        # Fetch paper attributes and attachments.
        submitted_area = (
            submission.content["track"] if "track" in submission.content else None
        )
        if "paper_type" in submission.content:
            paper_type = " ".join(submission.content["paper_type"].split()[:2]).lower()
        else:
            paper_type = "N/A"
        presentation_type = "N/A"
        paper["attributes"] = {
            "submitted_area": submitted_area,
            "paper_type": paper_type,
            "presentation_type": presentation_type,
        }
        attachments = []
        for att_type in attachment_types:
            if att_type in submission.content and submission.content[att_type]:
                attachments.append(
                    {
                        "type": attachment_types[att_type],
                        "file": str(paper["id"])
                        + "."
                        + str(submission.content[att_type].split(".")[-1]),
                        "open_review_id": str(submission.content[att_type]),
                    }
                )
                if download_all:
                    file_tye = submission.content["software"].split(".")[-1]
                    f = client_acl.get_attachment(submission.id, att_type)
                    with open(
                        os.path.join(
                            attachments_folder, str(paper["id"]) + "." + file_tye
                        ),
                        "wb",
                    ) as op:
                        op.write(f)
        if download_pdfs:
            f = client_acl.get_pdf(id=paper["openreview_id"])
            with open(
                os.path.join(papers_folder, str(paper["id"]) + ".pdf"), "wb"
            ) as op:
                op.write(f)

        if len(attachments) > 0:
            paper["attachments"] = attachments

        papers.append(paper)

    small_log.close()

    papers.sort(key=lambda p: p["id"])
    yaml.dump(papers, open("papers.yml", "w"), allow_unicode=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch papers from an OpenReview venue."
    )
    parser.add_argument("username", type=str, help="OpenReview username.")
    parser.add_argument("password", type=str, help="OpenReview password.")
    parser.add_argument(
        "venue",
        type=str,
        help="OpenReview venue ID, found in the URL https://openreview.net/group?id=<VENUE ID>",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="If set, downloads all papers in the OpenReview venue.",
    )
    parser.add_argument(
        "--pdfs",
        action="store_true",
        help="If set, downloads PDFs.",
    )
    args = parser.parse_args()
    main(args.username, args.password, args.venue, args.all, args.pdfs)
