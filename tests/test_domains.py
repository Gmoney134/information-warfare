import pytest

import app.domains as domains_module
from app.domains import extract_domain, is_known_disinfo_domain, load_domains


@pytest.fixture(autouse=True)
def clear_domains():
    domains_module._known_domains.clear()
    yield
    domains_module._known_domains.clear()


def test_load_domains(tmp_path):
    csv_file = tmp_path / "domains.csv"
    csv_file.write_text("Domain\nexample-disinfo.com\nbadnews.org\n")
    load_domains(str(csv_file))
    assert "example-disinfo.com" in domains_module._known_domains
    assert "badnews.org" in domains_module._known_domains


def test_load_domains_strips_whitespace(tmp_path):
    csv_file = tmp_path / "domains.csv"
    csv_file.write_text("Domain\n  spaced.com  \n")
    load_domains(str(csv_file))
    assert "spaced.com" in domains_module._known_domains


def test_is_known_disinfo_domain_match(tmp_path):
    csv_file = tmp_path / "domains.csv"
    csv_file.write_text("Domain\nbaddomain.com\n")
    load_domains(str(csv_file))
    assert is_known_disinfo_domain("https://baddomain.com/some/article") is True


def test_is_known_disinfo_domain_www_stripped(tmp_path):
    csv_file = tmp_path / "domains.csv"
    csv_file.write_text("Domain\nbaddomain.com\n")
    load_domains(str(csv_file))
    assert is_known_disinfo_domain("https://www.baddomain.com/article") is True


def test_is_known_disinfo_domain_no_match(tmp_path):
    csv_file = tmp_path / "domains.csv"
    csv_file.write_text("Domain\nbaddomain.com\n")
    load_domains(str(csv_file))
    assert is_known_disinfo_domain("https://legit.com/article") is False


def test_is_known_disinfo_domain_case_insensitive(tmp_path):
    csv_file = tmp_path / "domains.csv"
    csv_file.write_text("Domain\nBadDomain.com\n")
    load_domains(str(csv_file))
    assert is_known_disinfo_domain("https://BADDOMAIN.COM/article") is True


def test_extract_domain():
    assert extract_domain("https://www.example.com/path") == "example.com"
    assert extract_domain("https://sub.example.com/path") == "sub.example.com"
    assert extract_domain("https://example.com") == "example.com"
