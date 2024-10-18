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
import openreview.api


def main(username, password, venue, download_all, download_pdfs):
    try:
        client_acl_v2 = openreview.api.OpenReviewClient(
            baseurl="https://api2.openreview.net", username=username, password=password
        )
    except Exception as e:
        print(f"OpenReview connection refused\n{e}")
        exit()

    try:
        client_acl_v2.get_group(venue)
    except Exception as e:
        print(f"Unable to get group for: {venue}\nSee below for the OpenReview API error")
        print(f"Exception: {e}")
        exit()

    if not download_all or not download_pdfs:
        print("The output of this run cannot be used at ACLPUB2")

    attachment_types = {"software": "software", "data": "data", "copyright_PDF": "copyright"}

    papers_folder = "papers"
    attachments_folder = "attachments"
    if not os.path.exists(papers_folder):
        os.mkdir(papers_folder)
    if not os.path.exists(attachments_folder):
        os.mkdir(attachments_folder)

    submissions = client_acl_v2.get_all_notes(content={ 'venueid': venue}, details='replies')
    if len(submissions) <= 0:
        print("No submissions found. Please double check your venue ID and/or permissions to view the submissions")

    ## Publication chairs do not have access to the forum replies - use venueid instead
    if len(submissions[0].details["replies"]) <= 0:
        decision_by_forum = {
            s.forum: s
            for s in submissions if s.content["venueid"]["value"] == venue
        }
    else:
        decision_by_forum = {
            r["forum"]: r
            for s in submissions for r in s.details["replies"] if any(i.endswith("Decision") for i in r["invitations"])
            if "accept" in r["content"]["decision"]["value"].lower()
        }

    papers = []
    abstract_flag, paper_type_flag, track_flag = False, False, False
    small_log = open("papers.log", "w")
    for submission in tqdm(submissions):
        if submission.id not in decision_by_forum:
            continue
        authorsids = get_content_from(submission, "authorids")
        authors = []
        for authorsid in authorsids:
            author, error = get_user(authorsid, client_acl_v2)
            if error:
                small_log.write(
                    "Error at "
                    + authorsid
                    + " from (#"
                    + str(submission.number)
                    + "; openreview ID: "
                    + submission.id
                    + ") "
                    + get_content_from(submission, "title")
                    + "\n"
                )
            if author:
                authors.append(author)
        assert len(authors) > 0

        if "abstract" in submission.content:
            abstract = get_content_from(submission, "abstract")
        else:
            abstract = ""
            if not abstract_flag:
                abstract_flag = True
                print(f"Paper {submission.id} abstract field is not present. Contact info@openreview.net if you need this information migrated from ARR")

        paper = {
            "id": submission.number,  # len(papers)+1,
            "title": get_content_from(submission, "title"),
            "authors": authors,
            "abstract": abstract,
            "file": str(submission.number) + ".pdf",  # str(len(papers)+1) + ".pdf",
            "pdf_file": get_content_from(submission, "pdf").split("/")[-1],
            "decision": get_decision_from_venueid(submission),
            "openreview_id": submission.id,
        }

        # Fetch paper attributes and attachments.
        submitted_area = (
            get_content_from(submission, "track")
        )
        if "track" not in submission.content and not track_flag:
            track_flag = True
            print(f"Paper {submission.id} track field is not present. Contact info@openreview.net if you need this information migrated from ARR")

        if "paper_type" in submission.content:
            paper_type = " ".join(get_content_from(submission, "paper_type").split()[:2]).lower()
        else:
            paper_type = "N/A"
            if not paper_type_flag:
                paper_type_flag = True
                print("paper_type field (long or short) is not present. Contact info@openreview.net if you need this information migrated from ARR")
        presentation_type = "N/A"
        paper["attributes"] = {
            "submitted_area": submitted_area,
            "paper_type": paper_type,
            "presentation_type": presentation_type,
        }
        attachments = []

        attachments_count = 0
        suffix = ""

        for att_type in attachment_types:
            if att_type in submission.content and submission.content[att_type]:
                if attachments_count == 0:
                    suffix = ""
                else:
                    suffix = "_" + str(attachments_count)

                attachments.append(
                    {
                        "type": attachment_types[att_type],
                        "file": str(paper["id"]) + suffix
                        + "."
                        + str(get_content_from(submission, att_type).split(".")[-1]),
                        "open_review_id": str(get_content_from(submission, att_type)),
                    }
                )
                if download_all:
                    file_tye = get_content_from(submission, att_type).split(".")[-1]
                    f = client_acl_v2.get_attachment(submission.id, att_type)
                    with open(
                        os.path.join(
                            attachments_folder, str(paper["id"]) + suffix + "." + file_tye
                        ),
                        "wb",
                    ) as op:
                        op.write(f)
                attachments_count = attachments_count + 1
        if download_pdfs:
            try:
                f = client_acl_v2.get_pdf(id=paper["openreview_id"])
                with open(
                    os.path.join(papers_folder, str(paper["id"]) + ".pdf"), "wb"
                ) as op:
                    op.write(f)
            except:
                print(f"Unable to download PDF for {paper['openreview_id']}")

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
