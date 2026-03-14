#!/usr/bin/env python3
"""
Detail-focused downscale for pixel art.
Optimized for perfect 2x integer ratios (e.g. 96→48).

Usage: python3 scripts/downscale_detail.py <input.png> <target_size> <output_dir>
"""

import sys
import os
import numpy as np
from collections import Counter
from PIL import Image, ImageFilter


def extract_palette(img):
    arr = np.array(img)
    mask = arr[:, :, 3] > 128
    colors = arr[mask][:, :3]
    return np.unique(colors.reshape(-1, 3), axis=0)


def snap_to_palette(img, palette):
    arr = np.array(img).astype(np.float32)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]
    h, w = rgb.shape[:2]
    flat = rgb.reshape(-1, 3)
    pal = palette.astype(np.float32)
    diffs = flat[:, None, :] - pal[None, :, :]
    dists = np.sum(diffs ** 2, axis=2)
    nearest_idx = np.argmin(dists, axis=1)
    snapped = pal[nearest_idx].reshape(h, w, 3).astype(np.uint8)
    result = np.dstack([snapped, alpha.astype(np.uint8)])
    return Image.fromarray(result)


def detect_outlines(img):
    """Detect outline/edge pixels (high contrast neighbors)."""
    arr = np.array(img).astype(np.float32)
    rgb = arr[:, :, :3]
    alpha = arr[:, :, 3]
    lum = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    lum *= (alpha / 255.0)

    h, w = lum.shape
    edge = np.zeros((h, w), dtype=np.float32)
    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        shifted = np.zeros_like(lum)
        sy = slice(max(0, dy), min(h, h + dy) or None)
        dy_src = slice(max(0, -dy), min(h, h - dy) or None)
        sx = slice(max(0, dx), min(w, w + dx) or None)
        dx_src = slice(max(0, -dx), min(w, w - dx) or None)
        shifted[sy, sx] = lum[dy_src, dx_src]
        edge += np.abs(lum - shifted)

    return edge / edge.max() if edge.max() > 0 else edge


def method_direct_nearest(src, target):
    """Perfect 2x nearest neighbor — no crop, preserves positioning."""
    return src.resize((target, target), Image.NEAREST)


def method_direct_box_snap(src, target, palette):
    """Box filter (averages each 2x2 block) then palette snap."""
    box = src.resize((target, target), Image.BOX)
    return snap_to_palette(box, palette)


def method_direct_lanczos_snap(src, target, palette):
    """Lanczos on full frame then palette snap."""
    lanczos = src.resize((target, target), Image.LANCZOS)
    return snap_to_palette(lanczos, palette)


def method_direct_nearest_sharpen(src, target, palette):
    """Nearest neighbor then unsharp mask to enhance edges, palette snap."""
    nearest = src.resize((target, target), Image.NEAREST)
    sharpened = nearest.filter(ImageFilter.UnsharpMask(radius=0.5, percent=200, threshold=0))
    return snap_to_palette(sharpened, palette)


def method_outline_preserve(src, target, palette):
    """Detect outlines at source res, downscale both, prioritize outline pixels."""
    arr = np.array(src)
    edge = detect_outlines(src)

    sh, sw = arr.shape[:2]
    scale = sh // target

    out = np.zeros((target, target, 4), dtype=np.uint8)

    for ty in range(target):
        for tx in range(target):
            sy, sx = ty * scale, tx * scale
            block = arr[sy:sy+scale, sx:sx+scale]
            edge_block = edge[sy:sy+scale, sx:sx+scale]

            pixels = block.reshape(-1, 4)
            opaque = pixels[pixels[:, 3] > 128]

            if len(opaque) == 0:
                continue

            # If any pixel in block is an outline pixel, prefer it
            edge_vals = edge_block.flatten()
            opaque_mask = block[:, :, 3].flatten() > 128
            edge_opaque = edge_vals[opaque_mask]

            if edge_opaque.max() > 0.3:
                # Pick the pixel with highest edge value (the outline)
                idx = np.argmax(edge_opaque)
                out[ty, tx] = opaque[idx]
            else:
                # No strong edge — average then snap
                avg = np.mean(opaque[:, :3].astype(np.float32), axis=0)
                snapped = palette[np.argmin(np.sum((palette.astype(np.float32) - avg) ** 2, axis=1))]
                out[ty, tx, :3] = snapped
                out[ty, tx, 3] = 255

    return Image.fromarray(out)


def method_darkest_outline(src, target, palette):
    """Like outline preserve but specifically keeps darkest pixel per block (outlines are usually dark)."""
    arr = np.array(src)
    sh, sw = arr.shape[:2]
    scale = sh // target

    out = np.zeros((target, target, 4), dtype=np.uint8)

    for ty in range(target):
        for tx in range(target):
            sy, sx = ty * scale, tx * scale
            block = arr[sy:sy+scale, sx:sx+scale]
            pixels = block.reshape(-1, 4)
            opaque = pixels[pixels[:, 3] > 128]

            if len(opaque) == 0:
                continue

            # Check if block has both dark (outline) and light pixels
            lums = 0.299 * opaque[:, 0] + 0.587 * opaque[:, 1] + 0.114 * opaque[:, 2]
            lum_range = lums.max() - lums.min()

            if lum_range > 40:
                # High contrast block — pick darkest (preserve outline)
                darkest = opaque[np.argmin(lums)]
                snapped = palette[np.argmin(np.sum((palette.astype(np.float32) - darkest[:3].astype(np.float32)) ** 2, axis=1))]
                out[ty, tx, :3] = snapped
                out[ty, tx, 3] = 255
            else:
                # Uniform block — average then snap
                avg = np.mean(opaque[:, :3].astype(np.float32), axis=0)
                snapped = palette[np.argmin(np.sum((palette.astype(np.float32) - avg) ** 2, axis=1))]
                out[ty, tx, :3] = snapped
                out[ty, tx, 3] = 255

    return Image.fromarray(out)


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 scripts/downscale_detail.py <input.png> <target_size> <output_dir>")
        sys.exit(1)

    input_path = sys.argv[1]
    target_size = int(sys.argv[2])
    output_dir = sys.argv[3]
    os.makedirs(output_dir, exist_ok=True)

    src = Image.open(input_path).convert('RGBA')
    palette = extract_palette(src)
    sh, sw = src.size
    scale = sw // target_size

    print(f"Source: {sw}x{sh} → {target_size}x{target_size} (perfect {scale}x ratio)")
    print(f"Palette: {len(palette)} unique colors")

    results = {}
    results['1_direct_nearest'] = method_direct_nearest(src, target_size)
    results['2_direct_box_snap'] = method_direct_box_snap(src, target_size, palette)
    results['3_direct_lanczos_snap'] = method_direct_lanczos_snap(src, target_size, palette)
    results['4_nearest_sharpen'] = method_direct_nearest_sharpen(src, target_size, palette)
    results['5_outline_preserve'] = method_outline_preserve(src, target_size, palette)
    results['6_darkest_outline'] = method_darkest_outline(src, target_size, palette)

    for name, img in results.items():
        path = os.path.join(output_dir, f'{name}.png')
        img.save(path)
        print(f"Saved: {path}")

    # Save original for comparison
    src.save(os.path.join(output_dir, 'original.png'))
    print("Done.")


if __name__ == '__main__':
    main()
