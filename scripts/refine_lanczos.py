#!/usr/bin/env python3
"""
Refine Direct Lanczos + Snap downscale with 6 variations.

Usage: python3 scripts/refine_lanczos.py <input.png> <target_size> <output_dir>
"""

import sys
import os
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


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


def method_lanczos_snap(src, target, palette):
    """Baseline — same as round 2 winner."""
    return snap_to_palette(src.resize((target, target), Image.LANCZOS), palette)


def method_lanczos_sharpen_snap(src, target, palette):
    """Lanczos → light sharpen → snap. Crisps up edges before palette lock."""
    lanczos = src.resize((target, target), Image.LANCZOS)
    sharpened = lanczos.filter(ImageFilter.UnsharpMask(radius=0.5, percent=100, threshold=0))
    return snap_to_palette(sharpened, palette)


def method_lanczos_heavy_sharpen_snap(src, target, palette):
    """Lanczos → heavier sharpen → snap. More aggressive edge enhancement."""
    lanczos = src.resize((target, target), Image.LANCZOS)
    sharpened = lanczos.filter(ImageFilter.UnsharpMask(radius=1.0, percent=200, threshold=0))
    return snap_to_palette(sharpened, palette)


def method_lanczos_contrast_snap(src, target, palette):
    """Lanczos → boost contrast → snap. Helps separate similar tones before snapping."""
    lanczos = src.resize((target, target), Image.LANCZOS)
    # Split alpha, enhance RGB, recombine
    arr = np.array(lanczos)
    alpha = arr[:, :, 3]
    rgb_img = Image.fromarray(arr[:, :, :3])
    enhanced = ImageEnhance.Contrast(rgb_img).enhance(1.3)
    result = np.dstack([np.array(enhanced), alpha])
    return snap_to_palette(Image.fromarray(result), palette)


def method_lanczos_sharpen_contrast_snap(src, target, palette):
    """Lanczos → sharpen → contrast boost → snap. Combined refinement."""
    lanczos = src.resize((target, target), Image.LANCZOS)
    sharpened = lanczos.filter(ImageFilter.UnsharpMask(radius=0.5, percent=150, threshold=0))
    arr = np.array(sharpened)
    alpha = arr[:, :, 3]
    rgb_img = Image.fromarray(arr[:, :, :3])
    enhanced = ImageEnhance.Contrast(rgb_img).enhance(1.2)
    result = np.dstack([np.array(enhanced), alpha])
    return snap_to_palette(Image.fromarray(result), palette)


def method_lanczos_edge_enhance_snap(src, target, palette):
    """Lanczos → PIL edge enhance filter → snap. Different approach to edge preservation."""
    lanczos = src.resize((target, target), Image.LANCZOS)
    enhanced = lanczos.filter(ImageFilter.EDGE_ENHANCE)
    return snap_to_palette(enhanced, palette)


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 scripts/refine_lanczos.py <input.png> <target_size> <output_dir>")
        sys.exit(1)

    input_path = sys.argv[1]
    target_size = int(sys.argv[2])
    output_dir = sys.argv[3]
    os.makedirs(output_dir, exist_ok=True)

    src = Image.open(input_path).convert('RGBA')
    palette = extract_palette(src)

    print(f"Source: {src.size[0]}x{src.size[1]} → {target_size}x{target_size}")
    print(f"Palette: {len(palette)} unique colors")

    results = {
        '1_lanczos_snap': method_lanczos_snap(src, target_size, palette),
        '2_lanczos_light_sharpen': method_lanczos_sharpen_snap(src, target_size, palette),
        '3_lanczos_heavy_sharpen': method_lanczos_heavy_sharpen_snap(src, target_size, palette),
        '4_lanczos_contrast': method_lanczos_contrast_snap(src, target_size, palette),
        '5_lanczos_sharpen_contrast': method_lanczos_sharpen_contrast_snap(src, target_size, palette),
        '6_lanczos_edge_enhance': method_lanczos_edge_enhance_snap(src, target_size, palette),
    }

    for name, img in results.items():
        path = os.path.join(output_dir, f'{name}.png')
        img.save(path)
        print(f"Saved: {path}")

    src.save(os.path.join(output_dir, 'original.png'))
    print("Done.")


if __name__ == '__main__':
    main()
