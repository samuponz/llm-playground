"""The colour scale from 4f and the entropy of a probability list."""
import pytest

from confidence import SCALE, colour, entropy


def background(p):
    """The (red, green, blue) background colour that probability p gets."""
    return next(rgb for lowest, _, rgb in SCALE if p >= lowest)


GREEN, YELLOW, ORANGE, RED = (rgb for _, _, rgb in SCALE)


@pytest.mark.parametrize("p, expected", [
    (1.0, GREEN), (0.90, GREEN),     # exactly 90% is still "sure"
    (0.899, YELLOW), (0.50, YELLOW),
    (0.499, ORANGE), (0.20, ORANGE),
    (0.199, RED), (0.0, RED),
])
def test_colour_scale_boundaries(p, expected):
    assert background(p) == expected
    r, g, b = expected
    assert f"\033[48;2;{r};{g};{b}m" in colour(p)


def test_entropy_of_one_sure_choice_is_zero():
    assert entropy([("a", 1.0)]) == 0


def test_entropy_of_a_coin_flip_is_one_bit():
    assert entropy([("a", 0.5), ("b", 0.5)]) == pytest.approx(1.0)


def test_entropy_of_four_equal_choices_is_two_bits():
    assert entropy([(t, 0.25) for t in "abcd"]) == pytest.approx(2.0)


def test_entropy_ignores_zero_probabilities():
    assert entropy([("a", 1.0), ("b", 0.0)]) == 0  # log(0) would crash
