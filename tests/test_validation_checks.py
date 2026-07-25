from validation.checks import check_email, check_phone, corroboration_ok


def test_email_valid_with_mx():
    ok, detail = check_email("info@p1fo.com")
    assert ok, detail


def test_email_bad_syntax():
    ok, detail = check_email("not-an-email")
    assert not ok


def test_email_no_mx_domain():
    ok, detail = check_email("someone@this-domain-should-not-exist-zzz123.com")
    assert not ok


def test_phone_valid_us():
    ok, detail = check_phone("+1 310 737 2637")
    assert ok, detail


def test_phone_invalid():
    ok, detail = check_phone("123")
    assert not ok


def test_corroboration_two_domains():
    ok, _ = corroboration_ok(["https://a.com/x", "https://b.com/y"])
    assert ok


def test_corroboration_single_non_primary_domain_fails():
    ok, _ = corroboration_ok(["https://a.com/x"])
    assert not ok


def test_corroboration_single_sec_source_ok():
    ok, _ = corroboration_ok(["https://www.sec.gov/x"])
    assert ok
