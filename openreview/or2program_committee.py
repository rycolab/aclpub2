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

use_tracks = True

try:
    client_acl = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net', username=username, password=password)
except:
    print("OpenReview connection refused")
    exit()

acl_name = 'aclweb.org/ACL/2022/Conference' if len(sys.argv)<=3 else sys.argv[3]
acl_name = acl_name.strip('/')

try:
    venue_group = client_acl.get_group(acl_name)
    in_v2 = venue_group.domain is not None and venue_group.domain == venue_group.id
except:
    print(f"{acl_name} not found")
    exit()

def sort_role(t):
    return t["role"]
def sort_user(t):
    return t["last_name"]

def extract_or_data(client_acl, all_groups, role="Senior_Area_Chairs", or2acl={}):
    lst = []
    ## Groups will either look like venue_id/role or venue_id/track/role
    for i, group in enumerate([g for g in all_groups if any(role == entry for entry in g.id.split('/'))]):
        # print(i, group.id)
        track = group.id.replace(acl_name, '').replace(role, '').strip('/')
        if len(track) > 0:
            or_track_name = f"{track}_{role}"
        else:
            or_track_name = role
        if or_track_name in or2acl:
            or_track_name = or2acl[or_track_name]
        t = { "role": or_track_name.replace("_"," "), "entries":[] }
        # print(t)
        

        lst.append(t)
        for member in group.members:
                # print(member)
                # if member[0] == "~":
                user, error = get_user(member, client_acl) #get_user(member.content['reviewer_id'], client_acl)
                # else:
                #     user = get_user_by_email(member, client_acl)
                if not error:
                    t["entries"].append(user)
        t["entries"].sort(key=sort_user)
        t = None
    lst.sort(key=sort_role)
    return lst

def get_committee(acl_name):
    if acl_name[-1] != "/":
        acl_name += "/"
    committees = []
    for i, group in enumerate(openreview.tools.iterget_groups(client_acl, regex=acl_name)):
        if acl_name + "Paper" in group.id or "Program_Chairs" in group.id or "Conflicts" in group.id:
            continue
        name = group.id.replace(acl_name,"") 
        if name.startswith("Authors"):
            continue
        if len(name.split("/"))>1:
            continue
        # print(group.id,group)
        # print(group.id)
        committees.append(group.id)
    return committees


if use_tracks:
    use_tracks = ".*/"
else:
    use_tracks = ""

## for debug
# committees = get_committee(acl_name)
# print(committees)

# Fetch all groups and filter out the paper/submission groups
all_groups = client_acl.get_all_groups(prefix = f"{acl_name}/.*")
if not in_v2:
    all_groups = [g for g in all_groups if 'Paper' not in g.id]
else:
    all_groups = [g for g in all_groups if 'Submission' not in g.id]

program_committee = []

# get PCs
program_committee = extract_or_data(client_acl, all_groups, role="Program_Chairs")

# get SACs
or2acl = {} # You can use this dictionary to replace OpenReview field names with others you want to use in the proceedings
program_committee.extend(extract_or_data(client_acl, all_groups, role="Senior_Area_Chairs", or2acl=or2acl))

# get ACs
program_committee.extend(extract_or_data(client_acl, all_groups, role="Area_Chairs", or2acl=or2acl))

# get reviewers
aux = extract_or_data(client_acl, all_groups, role="Reviewers", or2acl=or2acl)
for reviewer in aux:
    reviewer["type"]="name_block"
program_committee.extend(aux)


yaml.dump(program_committee, open('program_committee.yml', 'w'), allow_unicode=True)
