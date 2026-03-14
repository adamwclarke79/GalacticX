#!/usr/bin/env python3
"""
Downscale pixel art sprite with 6 detail-preserving methods.
Focuses on preserving fine features (head, eyes, outlines).

Usage: python3 scripts/downscale_compare.py <input.png> <target_size> <output_dir>
"""

import sys
import os
from collections import Counter
from PIL import Image, ImageFilter
import numpy as np


def extract_palette(img):
    """Extract unique non-transparent colors from an RGBA image."""
    arr = np.array(img)
    mask = arr[:, :, 3] > 128
    colors = arr[mask][:, :3]
    return np.unique(colors.reshape(-1, 3), axis=0)


def snap_to_palette(img, palette):
    """Snap every pixel to the nearest color in the palette, preserving alpha."""
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


def get_content_bbox(img):
    """Get bounding box of non-transparent content."""
    arr = np.array(img)
    alpha = arr[:, :, 3]
    rows = np.any(alpha > 128, axis=1)
    cols = np.any(alpha > 128, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]
    return cmin, rmin, cmax + 1, rmax + 1


def mode_vote(src_arr, target_size):
    """For each output pixel, pick most common color in source region."""
    sh, sw = src_arr.shape[:2]
    th, tw = target_size, target_size
    out = np.zeros((th, tw, 4), dtype=np.uint8)
    for ty in range(th):
        for tx in range(tw):
            sy0 = int(ty * sh / th)
            sy1 = max(sy0 + 1, int((ty + 1) * sh / th))
            sx0 = int(tx * sw / tw)
            sx1 = max(sx0 + 1, int((tx + 1) * sw / tw))
            block = src_arr[sy0:sy1, sx0:sx1].reshape(-1, 4)
            opaque = block[block[:, 3] > 128]
            if len(opaque) == 0:
                continue
            counter = Counter(tuple(p) for p in opaque)
            out[ty, tx] = counter.most_common(1)[0][0]
    return Image.fromarray(out)


def offset_nearest(src_img, target_size, ox=0.0, oy=0.0):
    """Nearest neighbor with sub-pixel offset to control which source pixel is chosen."""
    src = np.array(src_img)
    sh, sw = src.shape[:2]
    out = np.zeros((target_size, target_size, 4), dtype=np.uint8)
    for ty in range(target_size):
        for tx in range(target_size):
            sx = min(int((tx + 0.5 + ox) * sw / target_size), sw - 1)
            sy = min(int((ty + 0.5 + oy) * sh / target_size), sh - 1)
            out[ty, tx] = src[sy, sx]
    return Image.fromarray(out)


def crop_scale_pad(src_img, target_size, palette, resample=Image.NEAREST):
    """Crop to content bbox, scale content to fill more of target, then re-pad centered."""
    bbox = get_content_bbox(src_img)
    content = src_img.crop(bbox)
    cw, ch = content.size

    # Scale content to fit in target with 1px margin
    usable = target_size - 2
    scale = min(usable / cw, usable / ch)
    new_w = max(1, round(cw * scale))
    new_h = max(1, round(ch * scale))
    scaled = content.resize((new_w, new_h), resample)

    # Center on target canvas
    out = Image.new('RGBA', (target_size, target_size), (0, 0, 0, 0))
    ox = (target_size - new_w) // 2
    oy = (target_size - new_h) // 2
    out.paste(scaled, (ox, oy), scaled)
    return out


def twostep_nearest(src_img, target_size, mid_size):
    """Two-step downscale via intermediate size, both nearest neighbor."""
    mid = src_img.resize((mid_size, mid_size), Image.NEAREST)
    return mid.resize((target_size, target_size), Image.NEAREST)


def edge_preserve_downscale(src_img, target_size, palette):
    """Detect edges, use nearest at edge pixels, lanczos+snap elsewhere, then composite."""
    src_arr = np.array(src_img).astype(np.float32)

    # Edge detection on luminance
    lum = 0.299 * src_arr[:, :, 0] + 0.587 * src_arr[:, :, 1] + 0.114 * src_arr[:, :, 2]
    lum *= (src_arr[:, :, 3] / 255.0)

    # Sobel-like edge magnitude
    gy = np.abs(np.diff(lum, axis=0))
    gx = np.abs(np.diff(lum, axis=1))
    edge_map = np.zeros_like(lum)
    edge_map[:-1, :] += gy
    edge_map[:, :-1] += gx

    # Downscale edge map to target size
    edge_img = Image.fromarray((edge_map / edge_map.max() * 255).astype(np.uint8))
    edge_small = np.array(edge_img.resize((target_size, target_size), Image.BOX)).astype(np.float32) / 255.0

    # Two versions
    nearest = src_img.resize((target_size, target_size), Image.NEAREST)
    lanczos = snap_to_palette(src_img.resize((target_size, target_size), Image.LANCZOS), palette)

    # Blend: edges use nearest, smooth areas use lanczos+snap
    n_arr = np.array(nearest).astype(np.float32)
    l_arr = np.array(lanczos).astype(np.float32)

    # Threshold edge weights
    weight = np.clip(edge_small * 3, 0, 1)[:, :, None]
    blended = (n_arr * weight + l_arr * (1 - weight)).astype(np.uint8)

    return snap_to_palette(Image.fromarray(blended), palette)


def downscale_methods(src_img, target_size):
    """Return dict of {name: PIL.Image} for 6 downscale methods."""
    palette = extract_palette(src_img)
    results = {}

    # 1. Crop-to-content + nearest — maximizes pixel budget on the actual character
    results['1_crop_nearest'] = crop_scale_pad(src_img, target_size, palette, Image.NEAREST)

    # 2. Crop-to-content + Lanczos + palette snap
    cropped_lanczos = crop_scale_pad(src_img, target_size, palette, Image.LANCZOS)
    results['2_crop_lanczos_snap'] = snap_to_palette(cropped_lanczos, palette)

    # 3. Two-step nearest (104→80→64) — gentler reduction in two hops
    results['3_twostep_nearest'] = twostep_nearest(src_img, target_size, 80)

    # 4. Offset nearest — shifted sampling grid to better catch head features
    results['4_offset_nearest'] = offset_nearest(src_img, target_size, ox=0.3, oy=0.2)

    # 5. Edge-preserving hybrid — nearest at outlines/eyes, lanczos+snap in smooth areas
    results['5_edge_preserve'] = edge_preserve_downscale(src_img, target_size, palette)

    # 6. Mode vote on cropped content — most common color per region, no blending
    cropped_src = crop_scale_pad(src_img, target_size, palette, Image.NEAREST)  # just to get sizing
    # Actually do mode vote on the full image
    results['6_mode_vote'] = mode_vote(np.array(src_img), target_size)

    return results


def make_comparison_html(results, src_img, output_dir, target_size):
    """Also save the original for the HTML page."""
    src_path = os.path.join(output_dir, 'original.png')
    src_img.save(src_path)


def main():
    if len(sys.argv) < 4:
        print("Usage: python3 scripts/downscale_compare.py <input.png> <target_size> <output_dir>")
        sys.exit(1)

    input_path = sys.argv[1]
    target_size = int(sys.argv[2])
    output_dir = sys.argv[3]
    os.makedirs(output_dir, exist_ok=True)

    src = Image.open(input_path).convert('RGBA')
    bbox = get_content_bbox(src)
    content_w = bbox[2] - bbox[0]
    content_h = bbox[3] - bbox[1]
    print(f"Source: {src.size[0]}x{src.size[1]}")
    print(f"Content bbox: {content_w}x{content_h} (padding: {src.size[0]-content_w}px x {src.size[1]-content_h}px)")
    print(f"Palette: {len(extract_palette(src))} unique colors")
    print(f"Target: {target_size}x{target_size}")

    results = downscale_methods(src, target_size)

    for name, img in results.items():
        path = os.path.join(output_dir, f'{name}.png')
        img.save(path)
        print(f"Saved: {path}")

    # Save original too
    src.save(os.path.join(output_dir, 'original.png'))
    print("Done.")


if __name__ == '__main__':
    main()
