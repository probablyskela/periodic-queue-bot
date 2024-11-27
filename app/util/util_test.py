from app.util import RelativeDelta


def test_RelativeDelta() -> None:
    assert RelativeDelta(minutes=2) > RelativeDelta(minutes=1)
    assert RelativeDelta(hours=25) > RelativeDelta(days=1)
    assert RelativeDelta(hours=24) == RelativeDelta(days=1)

    assert RelativeDelta(minutes=10).s == RelativeDelta(minutes=10).s
    assert RelativeDelta(minutes=10).s == 10 * 60
    assert RelativeDelta(hours=1, minutes=10, seconds=12).s == 1 * 60 * 60 + 10 * 60 + 12
