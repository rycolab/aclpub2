#!/usr/bin/env python
# -*- coding: utf-8 -*-

#----------------------------------------------------------------------------
# Created By Rodrigo Wilkens
# Last update 27/March/2022
# version ='1.0'
# ---------------------------------------------------------------------------

def join_institution(institution):
    if len(institution)==0:
        return None
    if len(institution)==1:
        return institution[0]
    res = ", ".join(institution[:-1])
    res += " and " + institution[-1]
    return res


def get_user(or_id,client_acl, force_institution=False):
    c = None
    try:
        c = client_acl.get_profile(or_id)
    except:
        print("\nERROR: or_id not found", or_id)
        return {"first_name":or_id, "last_name":or_id,"name":or_id, "username":or_id, "emails":or_id, "institution":"NA"}, True
    try:
        if or_id[0] == "~":
            emails = client_acl.search_profiles(ids=[or_id])
            assert len(emails) >= 1
        else:
            emails = client_acl.search_profiles(ids=[c.id])
            assert len(emails) >= 1
            # emails = [or_id]
    except:
        print("\nERROR: or_id not associated to an email", or_id)
        return {"first_name":or_id, "last_name":or_id,"name":or_id, "username":or_id, "emails":or_id, "institution":"NA"}, True
    # try:
    if True:
        c = c.content
        namePrefered = None
        for name in c["names"]:
            if namePrefered==None or ('preferred' in name and name['preferred']):
                namePrefered = name
        name = " ".join([namePrefered['first'] if type(namePrefered['first'])==str else '', 
                         namePrefered['middle'] if namePrefered['middle']!=None else '', 
                         namePrefered['last'] if namePrefered['last']!=None else '' ]).replace("  ", " ")
        first_name = namePrefered['first'].strip() if type(namePrefered['first'])==str else ''
        middle_name = namePrefered['middle'].strip() if namePrefered['middle']!=None else ''
        last_name = namePrefered['last'].strip() if namePrefered['last']!=None else ''
        username = namePrefered['username'].strip()
        if len(first_name)>2:
            first_name = " ".join([n[0].upper() + n[1:].lower() if (n==n.upper() or n==n.lower()) else n for n in first_name.split(" ")])
        if len(middle_name)>2:
            middle_name = " ".join([n[0].upper() + n[1:].lower() if (n==n.upper() or n==n.lower()) else n for n in middle_name.split(" ")])
        if len(last_name)>2:
            last_name = " ".join([n[0].upper() + n[1:].lower() if (n==n.upper() or n==n.lower()) else n for n in last_name.split(" ")])
            

        if 'preferredEmail' in emails[0].content:
            emails = emails[0].content['preferredEmail']
        else:
            emails = emails[0].content['emails'][0]
        emails = emails.replace("_","\\_")

        institution = []
        if 'history' in c:
            for h in c['history']:
                if 'end' not in h or h['end'] == None:
                    institution.append(h['institution']["name"])
        ret = {"first_name":first_name, "last_name":last_name,"name":name, "username":username, "emails":emails}
        institution = join_institution(institution)
        if institution:
            ret["institution"] = institution
        else:
            if force_institution:
                ret["institution"] = "NA"
        if len(middle_name)>0:
            ret["middle_name"]=middle_name
        if "gscholar" in c:
            ret["google_scholar_id"] = c["gscholar"]
        if 'dblp' in c:
            ret['dblp_id'] = c['dblp']
        if 'homepage' in c:
            ret['homepage'] = c['homepage']
        if 'orcid'in c:
            ret['orcid'] = c['orcid']
        if 'semanticScholar' in c:
            ret["semantic_scholar_id"] = c['semanticScholar']
        return ret, False
