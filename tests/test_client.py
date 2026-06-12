from client import make_session, DEFAULT_HEADERS


def test_make_session_sets_user_agent_and_referer():
    s = make_session()
    assert "User-Agent" in s.headers
    assert "komiku" in s.headers["Referer"]


def test_default_headers_has_realistic_user_agent():
    assert "Mozilla" in DEFAULT_HEADERS["User-Agent"]
