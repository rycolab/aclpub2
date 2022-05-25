
required_conference_fields = ["book_title", "event_name", "cover_subtitle",
                                "anthology_venue_id", "start_date", "end_date",
                                "isbn", "location", "editors", "publisher",
                                "volume_name"]

def check_required_conference_fields(conference):
    is_ok = True
    for required_conference_field in required_conference_fields:
        if required_conference_field not in conference:
            print("[WARNING] The input file conference_details.yml does not contain the '" + required_conference_field + "' field.")
            is_ok = False

    if "editors" in conference:
        if type(conference["editors"]) is not list:
            print("[WARNING] In the file conference_details.yml, please add at least one editor to the editors field.")
            is_ok = False
        else:
            editors = conference["editors"]
            for editor in editors:
                if "first_name" not in editor or "last_name" not in editor:
                    print("[WARNING] In the file conference_details.yml, the editor ")
                    print(editor)
                    print("is malformed. Each editor should have both first_name and last_name.")
                    is_ok = False

    return is_ok

def avoid_latex_in_conference_field(conference):
    is_ok = True
    for required_conference_field in required_conference_fields:
        value = conference[required_conference_field]
        if isinstance(value, str) and "\\" in value:
            print("[WARNING] The input file conference_details.yml contains a LaTeX escape in '" + required_conference_field +
                "': '" + value + "'. Please avoid to use these escape characters.")
            is_ok = False

    return is_ok
