from aclpub2.generate import get_conference_dates
import yaml


def test_get_conference_dates():
    conference = yaml.safe_load(
        """
start_date: 2020-01-01
end_date: 2020-01-01
    """
    )
    assert get_conference_dates(conference) == "January 1"

    conference = yaml.safe_load(
        """
start_date: 2020-01-01
end_date: 2020-01-02
    """
    )
    assert get_conference_dates(conference) == "January 1-2"

    conference = yaml.safe_load(
        """
start_date: 2020-01-01
end_date: 2020-02-02
    """
    )
    assert get_conference_dates(conference) == "January 1 - February 2"
