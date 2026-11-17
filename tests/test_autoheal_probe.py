from sakthai.autoheal_probe import expected_answer


def test_expected_answer() -> None:
    assert expected_answer() == 42
