"""Integer specification: newest-first FIR weights; no HDL dependencies."""
DEFAULT_PATTERN = [1, 1, -1, -1, 1, -1, 1, -1]
DEFAULT_WEIGHTS = DEFAULT_PATTERN[::-1]


def correlate(samples, weights):
    """Return dot products over zero-padded sliding windows."""
    assert len(weights) == 8 and all(-8 <= h <= 7 for h in weights)
    history = [0] * 8
    outputs = []
    for value in samples:
        assert -128 <= value <= 127
        history = [value] + history[:-1]
        outputs.append(sum(x * h for x, h in zip(history, weights)))
    return outputs
