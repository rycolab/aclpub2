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
        if "first" in namePrefered:
            name = ' '.join(filter(None, [
                    namePrefered.get('first', ''),
                    namePrefered.get('middle', ''),
                    namePrefered.get('last', '')
                ])).replace("  ", " ")
            first_name = namePrefered.get('first', '')
            middle_name = namePrefered.get('middle', '')
            if middle_name is None:
                middle_name = ""
            last_name = namePrefered.get('last', '')
        else: ## first, middle, and last may not be present - OR switched to requiring only fullnames but this may change later for inclusivity
            name = namePrefered['fullname']
            try:
                assert "@" not in name,name
            except AssertionError:
                print("\nERROR: name looks like email address:", name, "for OR user", or_id)

            # if full name has no spaces, try to insert some based on capitalization/periods
            if " " not in name:
                name2 = ""
                for c in name:
                    if c.isupper() and name2 and (name2[-1].islower() or name2[-1]=="."):
                        name2 += " "    # insert a space
                    name2 += c
                name = name2
            first_name = name.split(" ")[0] if " " in name else ""
            last_name = name.split(" ")[-1]
            middle_name = " ".join(name.split(" ")[1:-1])

            # move common surname prefixes from the middle name to the last name
            if middle_name.lower() in ("al", "da", "de", "de la", "del", "dela", "della", "dos", "di", "el", "van", "van den", "van der", "von", "von der"):
                last_name = middle_name + " " + last_name
                middle_name = ""
            elif middle_name.lower().endswith((" van den", " van der", " von der")):
                last_name = middle_name[-7:] + " " + last_name
                middle_name = middle_name[:-8]
            elif middle_name.lower().endswith((" de la", " della")):
                last_name = middle_name[-5:] + " " + last_name
                middle_name = middle_name[:-6]
            elif middle_name.lower().endswith((" dela",)):
                last_name = middle_name[-4:] + " " + last_name
                middle_name = middle_name[:-5]
            elif middle_name.lower().endswith((" del", " dos", " van", " von")):
                last_name = middle_name[-3:] + " " + last_name
                middle_name = middle_name[:-4]
            elif middle_name.lower().endswith((" al", " da", " de", " di", " el")):
                last_name = middle_name[-2:] + " " + last_name
                middle_name = middle_name[:-3]

        username = namePrefered['username'].strip()
        if len(first_name)>2:
            first_name = " ".join([n[0].upper() + n[1:].lower() if (n==n.upper() or n==n.lower()) else n for n in first_name.split(" ")])
        if len(middle_name)>2:
            middle_name = " ".join([n[0].upper() + n[1:].lower() if (n==n.upper() or n==n.lower()) else n for n in middle_name.split(" ")])
        if len(last_name)>2:
            if all(n.isupper() or n.islower() for n in last_name.split(" ")):   # name does not contain any words with both uppercase and lowercase characters; impose initial-only capitalization for each word
                last_name = " ".join([n[0].upper() + n[1:].lower() for n in last_name.split(" ")])

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

def get_content_from (submission, content_field):
    # Given a paper from OpenReview (either openreview.Note or openreview.api.Note) and a field,
    # get its value or None if value does not exist 
    try:
        if isinstance(submission, dict):
            content = submission['content']
        else:
            content = submission.content
    except:
        raise Exception(f"submission must either be a dict, openreview.Note or openreview.api.Note, got type={type(submission)}")
    ret = content.get(content_field, '')
    if isinstance(ret, dict):
        return ret['value']
    else:
        return ret

def get_decision_from_venueid (submission):
    # Return the decision from venue id
    return submission.content.get('venue', {}).get('value').split(' ')[-1]
