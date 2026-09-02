import os

import openreview.api
import yaml
from tqdm import tqdm

# This is a heavily vibe-coded and to some extent manually improved update of o2papers.py
# which I couldn't make work our workshop hosted on OpenReview in May 2026.
#
# This *does* produce the papers.yaml file required for compiling the workshop proceedings
# but hasn't been tested for anything beyond.

def get_val(note, field, default=None):
    """Helper to safely get values from API v2 note content."""
    return note.content.get(field, {}).get('value', default)


def get_user(or_id: str, client_acl, force_institution=False):
    """
    Updated for OpenReview API v2
    """
    profile = None
    try:
        # In V2, get_profile works for both ~ID and email
        profile = client_acl.get_profile(or_id)
    except openreview.OpenReviewException:
        print(f"\nERROR: or_id not found: {or_id}")
        first_name, second_name = or_id.strip('~').split('_')
        return {
            "first_name": first_name, "last_name": second_name, "name": f'{first_name} {second_name}',
            "username": or_id, "emails": or_id, "institution": "NA"
        }

    # Get content dictionary
    # In V2, content fields often look like: {'names': {'value': [...]}}
    content = profile.content
    print(content)

    # 1. Handle Names
    names_list = content.get('names', [])
    if isinstance(names_list, dict):  # Handle cases where it's wrapped in 'value'
        names_list = names_list.get('value', [])

    name_preferred = next((n for n in names_list if n.get('preferred')), names_list[0] if names_list else {})

    # Logic for extracting parts of the name
    first_name = name_preferred.get('first', '')
    middle_name = name_preferred.get('middle', '') or ""
    last_name = name_preferred.get('last', '')
    fullname = name_preferred.get('fullname', '')

    if not first_name and fullname:
        # Fallback parsing for fullnames (carrying over your custom logic)
        parts = fullname.split(" ")
        first_name = parts[0] if len(parts) > 0 else ""
        last_name = parts[-1] if len(parts) > 1 else ""
        middle_name = " ".join(parts[1:-1])

        # Surname prefix handling (your specific list)
        prefixes = (
            "al", "da", "de", "de la", "del", "dela", "della", "dos", "di", "el", "van", "van den", "van der", "von",
            "von der")
        if middle_name.lower() in prefixes:
            last_name = f"{middle_name} {last_name}"
            middle_name = ""

    # 1. Handle Emails (Check top-level attribute first, then content)
    email_addr = content.get('preferredEmail', 'no-email')
    # if hasattr(profile, 'emails') and profile.emails:
    #     email_addr = profile.emails[0]
    # else:
    #     pass
    email_addr = email_addr.replace("_", "\\_")

    # 3. Handle Institution (History)
    institution_names = []
    history = content.get('history', [])
    if isinstance(history, dict):
        history = history.get('value', [])

    for entry in history:
        # Only get current institutions (where 'end' is null/empty)
        if not entry.get('end'):
            inst = entry.get('institution', {})
            inst_name = inst.get('name') if isinstance(inst, dict) else inst
            if inst_name:
                institution_names.append(inst_name)

    # 4. Construct Return Object
    result = {
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "name": fullname or f"{first_name} {last_name}".strip(),
        "username": name_preferred.get('username', '').strip(),
        "emails": email_addr
    }

    if middle_name:
        result["middle_name"] = middle_name.strip()

    inst_string = ", ".join(institution_names)

    if inst_string:
        result["institution"] = inst_string
    elif force_institution:
        result["institution"] = "NA"

    # Additional Identifiers (V2 style)
    fields = {
        "gscholar": "google_scholar_id",
        "dblp": "dblp_id",
        "homepage": "homepage",
        "orcid": "orcid",
        "semanticScholar": "semantic_scholar_id"
    }

    for or_key, ret_key in fields.items():
        val = content.get(or_key, {})
        if isinstance(val, dict):
            val = val.get('value')
        if val:
            result[ret_key] = val

    return result


# print(profiles)


if __name__ == '__main__':

    # --- Configuration & Initialization ---
    venue_id = 'aclweb.org/ACL/2026/Workshop/FancyWorkshopName'
    username = 'john.doe@gmail.com'
    password = 'S3CRET'
    download_all = True
    download_pdfs = True

    client_acl_v2 = openreview.api.OpenReviewClient(
        baseurl='https://api2.openreview.net', username=username, password=password
    )

    # https://docs.openreview.net/how-to-guides/communication/how-to-get-email-addresses
    client_acl_v2.impersonate(venue_id)  # didn't do anything special, though :/

    all_submissions = client_acl_v2.get_all_notes(invitation=f"{venue_id}/-/Submission", details='replies')

    attachment_types = {"software": "software", "data": "data"}
    papers_folder = "papers"
    attachments_folder = "attachments"
    if not os.path.exists(papers_folder):
        os.mkdir(papers_folder)
    if not os.path.exists(attachments_folder):
        os.mkdir(attachments_folder)

    # Fetch submissions with replies (for decisions)
    # Note: details='replies' is still used in v2
    submissions = client_acl_v2.get_all_notes(
        invitation=f"{venue_id}/-/Submission",  # Or Blind_Submission
        details='replies'
    )

    print(len(submissions))

    # we have 24 papers submitted overall
    assert 24 == len(submissions)

    # 2. Rebuild Decision Mapping
    decision_by_forum = {}

    for s in submissions:
        for reply in s.details.get('replies', []):
            # In v2, invitations is a list of strings
            if any('Decision' in inv for inv in reply.get('invitations', [])):
                decision = reply.get('content', {}).get('decision', {}).get('value', '').lower()
                if 'accept' in decision:
                    decision_by_forum[s.forum] = reply
                    break

    # we accepted 14 direct submissions
    assert 14 == len(decision_by_forum)

    # 3. Optimize Author Lookup (Safely chunked to avoid 400 Bad Request)
    all_author_ids = set()
    for s in submissions:
        if s.id in decision_by_forum:
            # get_val returns a list of author IDs
            author_ids = get_val(s, 'authorids', [])
            # print(author_ids)
            all_author_ids.update(author_ids)

    # Clean the IDs (remove any empty strings or non-strings)
    valid_ids = [aid for aid in all_author_ids if aid and isinstance(aid, str)]

    # print(valid_ids)

    profiles = {}
    if valid_ids:
        print(f"Fetching {len(valid_ids)} author profiles individually...")

        for aid in tqdm(valid_ids, desc="Downloading Profiles"):
            try:
                # get_profiles always returns a list, even for one ID
                p_list = client_acl_v2.get_profiles([aid])
                if p_list:
                    p = p_list[0]
                    profiles[p.id] = p
            except Exception as e:
                # This logs the specific ID that failed so you can check it manually
                print(f"\nWarning: Could not fetch profile for {aid}. Error: {e}")

    # 4. Process Papers
    papers = []
    small_log = open("papers.log", "w")

    for submission in tqdm(submissions):
        if submission.id not in decision_by_forum:
            continue

        # Extract Authors
        author_ids = get_val(submission, 'authorids', [])
        authors_data = [get_user(aid, client_acl_v2) for aid in author_ids]
        print("++*----")
        print(authors_data)
        print("++**-----")

        # Extract Content
        title = get_val(submission, 'title', 'No Title')
        abstract = get_val(submission, 'abstract', '')
        pdf_path = get_val(submission, 'pdf', '')
        track = get_val(submission, 'track', 'N/A')

        # Paper Type Logic
        pt_raw = get_val(submission, 'paper_type', 'N/A')
        paper_type = " ".join(pt_raw.split()[:2]).lower() if pt_raw != 'N/A' else 'N/A'

        paper = {
            "id": submission.number,
            "title": title,
            "authors": authors_data,
            "abstract": abstract,
            "file": f"{submission.number}.pdf",
            "pdf_file": pdf_path.split("/")[-1] if pdf_path else "",
            "decision": "Accepted",  # Since we filtered for accepted only
            "openreview_id": submission.id,
            "attributes": {
                "submitted_area": track,
                "paper_type": paper_type,
                "presentation_type": "N/A",
            }
        }

        # 5. Handle Attachments
        paper_attachments = []
        for att_field, att_label in attachment_types.items():
            att_value = get_val(submission, att_field)
            if att_value:
                ext = att_value.split('.')[-1]
                filename = f"{submission.number}_{att_field}.{ext}"

                paper_attachments.append({
                    "type": att_label,
                    "file": filename,
                    "open_review_id": att_value
                })

                if download_all:
                    try:
                        f_content = client_acl_v2.get_attachment(submission.id, att_field)
                        with open(os.path.join(attachments_folder, filename), "wb") as f:
                            f.write(f_content)
                    except Exception as e:
                        small_log.write(f"Attach Error {submission.id} ({att_field}): {str(e)}\n")

        if paper_attachments:
            paper["attachments"] = paper_attachments

        # 6. Download PDF
        if download_pdfs and pdf_path:
            try:
                pdf_content = client_acl_v2.get_pdf(id=submission.id)
                with open(os.path.join(papers_folder, f"{submission.number}.pdf"), "wb") as f:
                    f.write(pdf_content)
            except:
                print(f"Unable to download PDF for {submission.id}")

        papers.append(paper)

    small_log.close()
    papers.sort(key=lambda p: p["id"])
    with open("papers.yml", "w", encoding="utf-8") as f:
        yaml.dump(papers, f, allow_unicode=True)
