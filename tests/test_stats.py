"""The numbers shown after each answer, the /context bar, and the overflow warnings."""
from stats import (TurnStats, context_bar, context_report, context_used, context_warning,
                   cut_warning, tokens_per_second, usage_line)


def turn(read, wrote=10, first=0.5, writing=2.0):
    return TurnStats(read=read, wrote=wrote, first_token_s=first, writing_s=writing)


def test_tokens_per_second():
    assert tokens_per_second(turn(100, wrote=20, writing=4.0)) == 5.0


def test_tokens_per_second_no_time_is_zero_not_a_crash():
    assert tokens_per_second(turn(100, wrote=1, writing=0.0)) == 0.0


def test_context_used_is_read_plus_wrote():
    assert context_used(turn(300, wrote=50)) == 350


def test_usage_line():
    line = usage_line(turn(300, wrote=100, first=1.24, writing=4.0), 4096)
    assert line == "[read 300 · wrote 100 · 25.0 tok/s · first token 1.2 s · context 400/4096 (10%)]"


def test_context_bar_empty_half_full():
    assert context_bar(0.0, width=10) == "[░░░░░░░░░░]"
    assert context_bar(0.5, width=10) == "[█████░░░░░]"
    assert context_bar(1.0, width=10) == "[██████████]"


def test_context_bar_stays_inside_its_box():
    assert context_bar(1.7, width=10) == "[██████████]"  # overflowed: still 10 wide
    assert context_bar(-0.2, width=10) == "[░░░░░░░░░░]"


def test_context_report_before_any_request():
    assert context_report(None, 4096, []) == "No request yet: ask something first."


def test_context_report_counts_messages():
    messages = [{"role": "system", "content": "s"},
                {"role": "user", "content": "q"},
                {"role": "assistant", "content": "a"}]
    report = context_report(turn(1000, wrote=24), 4096, messages)
    assert "1024 / 4096 tokens (25%)" in report
    assert "free                3072 tokens" in report
    assert "3 (1 system, 1 user, 1 assistant)" in report


def test_context_warning_only_above_80_percent():
    assert context_warning(turn(3000, wrote=0), 4096) is None   # 73%
    assert context_warning(turn(3300, wrote=0), 4096) is not None  # 81%


def test_no_cut_when_the_history_grows():
    assert cut_warning(turn(100), turn(200), 4096) is None


def test_no_cut_on_the_first_turn():
    assert cut_warning(None, turn(200), 4096) is None


def test_cut_when_read_goes_down():
    # Our history only grows, so reading fewer tokens means the server dropped some
    warning = cut_warning(turn(3000), turn(1500), 4096)
    assert warning.startswith("✂ the server cut the conversation")


def test_cut_when_writing_overflows_the_window():
    warning = cut_warning(turn(3000), turn(4000, wrote=200), 4096)
    assert warning.startswith("✂ the window overflowed while writing")


def test_once_cut_always_cut():
    warning = cut_warning(turn(1500), turn(1600), 4096, already_cut=True)
    assert warning.startswith("✂ still cut")
