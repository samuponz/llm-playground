"""Look at a model's weights: the numbers it is made of.

    docker compose run --rm app python weights.py                       # the whole file
    docker compose run --rm app python weights.py blk.0.attn_q.weight   # one matrix
    docker compose run --rm app python weights.py blk.0.attn_q.weight --model qwen3:4b-q4_K_M

The model file is read straight from Ollama's storage (mounted read-only at /ollama).
It is a GGUF file: a list of named matrices ("tensors"), each stored in its own format
(Q4_K, Q6_K, F16...). The `gguf` package, from the llama.cpp project, reads it and turns
the stored integers back into numbers (integer x scale + offset).

For one matrix it prints statistics and saves two pictures in docs/images/:
a histogram (how the values are spread) and an image (one pixel per weight).
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")  # draw to files, no screen needed
import matplotlib.pyplot as plt
import numpy as np
from gguf import GGUFReader
from gguf.quants import dequantize

OLLAMA_MODELS = "/ollama/models"
IMAGES = "docs/images"


def model_file(model):
    """Find the GGUF file of an Ollama model, e.g. "qwen3:1.7b".

    Ollama keeps a small manifest per model; its "model" layer names the big file
    (a "blob", named after its sha256 checksum).
    """
    name, tag = model.split(":") if ":" in model else (model, "latest")
    manifest = f"{OLLAMA_MODELS}/manifests/registry.ollama.ai/library/{name}/{tag}"
    with open(manifest) as f:
        layers = json.load(f)["layers"]
    digest = next(l["digest"] for l in layers if l["mediaType"].endswith(".model"))
    return f"{OLLAMA_MODELS}/blobs/{digest.replace(':', '-')}"


def summary(reader):
    """How many weights are stored in each format, and the average bits per weight."""
    by_type = {}
    for t in reader.tensors:
        count, weights, size = by_type.get(t.tensor_type.name, (0, 0, 0))
        by_type[t.tensor_type.name] = (count + 1, weights + int(t.n_elements),
                                       size + int(t.n_bytes))

    total_weights = sum(w for _, w, _ in by_type.values())
    total_bytes = sum(b for _, _, b in by_type.values())
    print(f"{'format':<7} {'matrices':>8} {'weights':>14} {'share':>6} {'MB':>8} {'bits/weight':>12}")
    for name, (count, weights, size) in sorted(by_type.items(), key=lambda x: -x[1][1]):
        print(f"{name:<7} {count:>8} {weights:>14,} {weights / total_weights:>6.1%} "
              f"{size / 1e6:>8.1f} {size * 8 / weights:>12.2f}")
    print(f"{'total':<7} {len(reader.tensors):>8} {total_weights:>14,} {'':>6} "
          f"{total_bytes / 1e6:>8.1f} {total_bytes * 8 / total_weights:>12.2f}")


def stats(w):
    """Print how the values of one matrix are spread."""
    std = w.std()
    beyond = np.mean(np.abs(w - w.mean()) > 3 * std)
    print(f"shape {w.shape[0]} rows x {w.shape[1]} columns = {w.size:,} weights")
    print(f"mean {w.mean():+.4f}   std {std:.4f}   min {w.min():+.4f}   max {w.max():+.4f}")
    print(f"biggest value = {np.abs(w).max() / std:.0f} x std")
    # A perfect bell curve (normal distribution) has 0.27% of values beyond 3 std.
    # More than that = "heavy tails": more outliers than a bell curve.
    print(f"beyond 3 std: {beyond:.2%}  (a perfect bell curve: 0.27%)")

    # Outlier rows and columns: lines whose typical size is far from the others.
    # In the image they show up as stripes (rows: horizontal, columns: vertical).
    for axis, name in ((1, "rows"), (0, "columns")):
        size = np.abs(w).mean(axis=axis)
        ratio = size / np.median(size)
        big, small = np.argsort(ratio)[::-1][:5], np.argsort(ratio)[:5]
        print(f"{name}, biggest (x the typical one):",
              ", ".join(f"{i} ({ratio[i]:.1f}x)" for i in big))
        print(f"{name}, smallest:", ", ".join(f"{i} ({ratio[i]:.2f}x)" for i in small))


def pictures(w, title, prefix):
    """Save a histogram and an image of the matrix."""
    os.makedirs(IMAGES, exist_ok=True)
    std = w.std()

    # Histogram, twice: normal scale (the bell) and log scale (the tails become visible)
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 4))
    for ax, log in ((a, False), (b, True)):
        ax.hist(w.ravel(), bins=200, color="#4c72b0", log=log)
        ax.set_xlabel("weight value")
        ax.set_ylabel("how many weights" + (" (log scale)" if log else ""))
    a.set_title("normal scale: the bell")
    b.set_title("log scale: the tails")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(f"{prefix}-hist.png", dpi=110)
    plt.close(fig)

    # Image: blue = negative, white = 0, red = positive. Colours are capped at 3 std,
    # otherwise a few outliers would set the scale and everything else would look white
    # (the same dynamic-range problem quantization has).
    fig, (a, b) = plt.subplots(1, 2, figsize=(12, 6), gridspec_kw={"width_ratios": [2, 1]})
    a.imshow(w, cmap="RdBu_r", vmin=-3 * std, vmax=3 * std, interpolation="nearest",
             aspect="auto")
    a.set_title(f"whole matrix ({w.shape[0]} x {w.shape[1]})")
    a.set_xlabel("column (input dimension)")
    a.set_ylabel("row (output dimension)")
    zoom = w[:64, :64]
    im = b.imshow(zoom, cmap="RdBu_r", vmin=-3 * std, vmax=3 * std, interpolation="nearest")
    b.set_title("zoom: top-left 64 x 64")
    fig.colorbar(im, ax=b, fraction=0.046, label="weight value")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(f"{prefix}-image.png", dpi=110)
    plt.close(fig)
    print(f"saved {prefix}-hist.png and {prefix}-image.png")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("tensor", nargs="?", help="name of one matrix, e.g. blk.0.attn_q.weight")
    parser.add_argument("--model", default="qwen3:1.7b")
    args = parser.parse_args()

    path = model_file(args.model)
    reader = GGUFReader(path)
    print(f"{args.model}: {path} ({os.path.getsize(path) / 1e9:.2f} GB)\n")

    if not args.tensor:
        summary(reader)
        return

    t = next((t for t in reader.tensors if t.name == args.tensor), None)
    if t is None:
        print(f"no matrix named {args.tensor}. Some names:",
              ", ".join(t.name for t in reader.tensors[:12]))
        return
    # Stored integers + scales -> the numbers the model computes with
    w = dequantize(t.data, t.tensor_type).astype(np.float32)
    print(f"{t.name}, stored as {t.tensor_type.name}")
    stats(w)
    prefix = f"{IMAGES}/{args.model.replace(':', '-')}-{t.name}"
    pictures(w, f"{args.model}  {t.name}  ({t.tensor_type.name})", prefix)


if __name__ == "__main__":
    main()
