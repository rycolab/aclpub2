#!/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------
# Created By Rodrigo Wilkens
# Last update 02/April/2022
# version ='1.0'
# ---------------------------------------------------------------------------

import openreview
import os
import yaml
from tqdm import tqdm
import sys
from util import *

username = sys.argv[1]
password = sys.argv[2]

try:
    client_acl = openreview.Client(baseurl='https://api.openreview.net', username=username, password=password)
except:
    print("OpenReview connection refused")
    exit()

download_all = eval(sys.argv[4]) if len(sys.argv)>4 else True
download_pdf = eval(sys.argv[5]) if len(sys.argv)>5 else True

if not download_all or not download_pdf:
    print("The output of this run cannot be used at ACLPUB2")

acl_name = 'aclweb.org/ACL/2022/Conference' if len(sys.argv)>3 else sys.argv[3]
attachment_types = {"software":"software", "Data":"note"}

papers_folder = "papers"
attachments_folder = "attachments"
if not os.path.exists(papers_folder):
    os.mkdir(papers_folder)
if not os.path.exists(attachments_folder):
    os.mkdir(attachments_folder)



submissions=list(openreview.tools.iterget_notes(client_acl, invitation=acl_name+'/-/Blind_Submission', details='original'))
decision_by_forum={d.forum: d for d in list(openreview.tools.iterget_notes(client_acl, invitation=acl_name+'/Paper.*/-/Decision')) } 


papers = []
small_log = open("papers.log","w")
for submission in tqdm(submissions):
    if submission.id not in decision_by_forum:
        continue
    ######################
    #### main         
    authorsids = submission.details['original']['content']['authorids']
    authors = []
    for authorsid in authorsids:
        author, error = get_user(authorsid, client_acl)
        if error:
            small_log.write("Error at " + authorsid + " from (#" + str(submission.number) + "; openreview ID: " + submission.id + ") " + submission.content["title"] + "\n")
        if author:
            authors.append(author)
    assert len(authors)>0
    paper = { 
                "id": submission.number,# len(papers)+1, 
                "title":submission.content["title"],
                "authors":authors, 
                "abstract":submission.content["abstract"] if "abstract" in submission.content else "", 
                "file": str(submission.number) + ".pdf", #str(len(papers)+1) + ".pdf",             
                "pdf_file":submission.content["pdf"].split("/")[-1],
                'decision':decision_by_forum[submission.id].content['decision'],
                "openreview_id":submission.id
            }

    ######################
    #### attributes        
    submitted_area = submission.content["track"] if "track" in submission.content else None
    if 'paper_type' in submission.content:
        paper_type = " ".join(submission.content['paper_type'].split()[:2]).lower()
    else:
        paper_type = "N/A"
    presentation_type = "N/A"
    paper["attributes"] = {
                    "submitted_area":submitted_area,
                    "paper_type":paper_type,
                    "presentation_type":presentation_type,
            }
    ######################
    #### attachments        
    attachments = []
    for att_type in attachment_types:
        if att_type in submission.content and submission.content[att_type]:
            attachments.append({"type": attachment_types[att_type],
                            "file": "attachments/" + str(paper["id"]) + "_" + str(submission.content[att_type].split(".")[-1]),
                            "open_review_id": str(submission.content[att_type])
                            } )
            if download_all:
                file_tye = submission.content["software"].split(".")[-1]
                f = client_acl.get_attachment(submission.id, att_type)
                with open(os.path.join(attachments_folder, str(paper["id"]) + "." + file_tye),'wb') as op: op.write(f)
                
    if download_pdf:
        f = client_acl.get_pdf(id=paper['openreview_id'])
        with open(os.path.join(papers_folder, str(paper["id"]) + ".pdf"),'wb') as op: op.write(f)

    if len(attachments)>0:
        paper["attachments"] = attachments

    papers.append(paper)
    # if len(papers)>10:
    #     print(len(papers))
    #     break

small_log.close()
def get_paper_key(p):
    return p["id"]

papers.sort(key=get_paper_key)

yaml.dump(papers, open('papers.yml', 'w'))

