#!/usr/bin/env python3
"""
Reference-guided pixel art upscale.

Upscales a low-res animation frame (e.g. 48x48) to match a high-res
reference sprite (e.g. 96x96), preserving original detail where possible.

Algorithm:
1. Downscale the reference to the frame's size (nearest neighbor)
2. For each pixel in the frame:
   - If it matches the downscaled reference (within threshold):
     → Copy the corresponding 2x2 block from the high-res reference
   - If it differs (limb moved, new area):
     → Fill the 2x2 block with the frame pixel, palette-snapped
3. Optional smoothing pass: blend boundary pixels between matched/unmatched regions

Usage:
  python3 scripts/reference_upscale.py <frame.png> <reference_96.png> <output.png> [--threshold 30] [--blend]
  python3 scripts/reference_upscale.py --batch <frames_dir> <reference_96.png> <output_dir> [--threshold 30]
"""

import sys
import os
import numpy as np
from PIL import Image


def extract_palette(img):
    """Extract unique non-transparent colors."""
    arr = np.array(img)
    mask = arr[:, :, 3] > 128
    colors = arr[mask][:, :3]
    if len(colors) == 0:
        return np.array([[0, 0, 0]])
    return np.unique(colors.reshape(-1, 3), axis=0)


def snap_pixel_to_palette(pixel_rgb, palette):
    """Snap a single RGB pixel to the nearest palette color."""
    diffs = palette.astype(np.float32) - pixel_rgb.astype(np.float32)
    dists = np.sum(diffs ** 2, axis=1)
    return palette[np.argmin(dists)]


def color_distance(c1, c2):
    """Euclidean RGB distance."""
    return np.sqrt(np.sum((c1.astype(np.float32) - c2.astype(np.float32)) ** 2))


def reference_upscale(frame_img, ref_img, threshold=30, blend=False):
    """
    Upscale frame using reference sprite to recover detail.

    Args:
        frame_img: Low-res animation frame (RGBA, e.g. 48x48)
        ref_img: High-res reference sprite (RGBA, e.g. 96x96)
        threshold: Color distance threshold for matching (0-255 scale)
        blend: Whether to smooth boundaries between matched/unmatched regions

    Returns:
        Upscaled RGBA image at reference resolution
    """
    frame = np.array(frame_img)
    ref = np.array(ref_img)

    fh, fw = frame.shape[:2]
    rh, rw = ref.shape[:2]

    # Calculate scale factor
    scale_x = rw // fw
    scale_y = rh // fh

    if scale_x != scale_y:
        raise ValueError(f"Non-uniform scale: {scale_x}x{scale_y}. Need square scaling.")

    scale = scale_x
    palette = extract_palette(ref_img)

    # Downscale reference to frame size for comparison
    ref_down = np.array(ref_img.resize((fw, fh), Image.NEAREST))

    # Build output at reference resolution
    out = np.zeros_like(ref)

    # Track which pixels were matched vs filled (for blend pass)
    match_map = np.zeros((fh, fw), dtype=bool)

    for fy in range(fh):
        for fx in range(fw):
            frame_px = frame[fy, fx]
            ref_down_px = ref_down[fy, fx]

            # Output block coordinates
            oy = fy * scale
            ox = fx * scale
            ref_block = ref[oy:oy+scale, ox:ox+scale]

            # Both transparent → keep transparent
            if frame_px[3] < 128 and ref_down_px[3] < 128:
                out[oy:oy+scale, ox:ox+scale] = 0
                continue

            # Frame transparent but ref isn't → transparent (character moved away)
            if frame_px[3] < 128:
                out[oy:oy+scale, ox:ox+scale] = 0
                continue

            # Frame opaque but ref transparent → new area (limb moved here)
            if ref_down_px[3] < 128:
                snapped = snap_pixel_to_palette(frame_px[:3], palette)
                for sy in range(scale):
                    for sx in range(scale):
                        out[oy+sy, ox+sx, :3] = snapped
                        out[oy+sy, ox+sx, 3] = frame_px[3]
                continue

            # Both opaque → compare colors
            dist = color_distance(frame_px[:3], ref_down_px[:3])

            if dist <= threshold:
                # Match → copy high-res detail from reference
                out[oy:oy+scale, ox:ox+scale] = ref_block
                match_map[fy, fx] = True
            else:
                # Different → fill with frame color, palette-snapped
                snapped = snap_pixel_to_palette(frame_px[:3], palette)
                for sy in range(scale):
                    for sx in range(scale):
                        out[oy+sy, ox+sx, :3] = snapped
                        out[oy+sy, ox+sx, 3] = frame_px[3]

    # Optional blend pass: at boundaries between matched/unmatched,
    # average the edge pixels for smoother transitions
    if blend:
        out = _blend_boundaries(out, match_map, scale, palette)

    return Image.fromarray(out)


def _blend_boundaries(out, match_map, scale, palette):
    """Smooth boundaries between reference-copied and filled regions."""
    result = out.copy()
    fh, fw = match_map.shape

    for fy in range(fh):
        for fx in range(fw):
            if match_map[fy, fx]:
                continue

            # Check if any neighbor is matched
            has_matched_neighbor = False
            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ny, nx = fy + dy, fx + dx
                if 0 <= ny < fh and 0 <= nx < fw and match_map[ny, nx]:
                    has_matched_neighbor = True
                    break

            if not has_matched_neighbor:
                continue

            # Blend the edge pixels of this block with neighbors
            oy, ox = fy * scale, fx * scale
            for sy in range(scale):
                for sx in range(scale):
                    py, px = oy + sy, ox + sx
                    if result[py, px, 3] < 128:
                        continue

                    # Average with adjacent pixels from matched blocks
                    samples = [result[py, px, :3].astype(np.float32)]
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = py + dy, px + dx
                        if 0 <= ny < out.shape[0] and 0 <= nx < out.shape[1]:
                            if out[ny, nx, 3] > 128:
                                samples.append(out[ny, nx, :3].astype(np.float32))

                    avg = np.mean(samples, axis=0)
                    snapped = snap_pixel_to_palette(avg.astype(np.uint8), palette)
                    result[py, px, :3] = snapped

    return result


def main():
    args = sys.argv[1:]

    if not args or args[0] in ['-h', '--help']:
        print(__doc__)
        sys.exit(0)

    threshold = 30
    blend = False
    batch = False

    # Parse flags
    filtered = []
    i = 0
    while i < len(args):
        if args[i] == '--threshold':
            threshold = int(args[i+1])
            i += 2
        elif args[i] == '--blend':
            blend = True
            i += 1
        elif args[i] == '--batch':
            batch = True
            i += 1
        else:
            filtered.append(args[i])
            i += 1

    if batch:
        if len(filtered) < 3:
            print("Batch usage: --batch <frames_dir> <reference.png> <output_dir>")
            sys.exit(1)
        frames_dir, ref_path, out_dir = filtered[0], filtered[1], filtered[2]
        os.makedirs(out_dir, exist_ok=True)
        ref = Image.open(ref_path).convert('RGBA')
        for fname in sorted(os.listdir(frames_dir)):
            if not fname.endswith('.png'):
                continue
            frame = Image.open(os.path.join(frames_dir, fname)).convert('RGBA')
            result = reference_upscale(frame, ref, threshold, blend)
            out_path = os.path.join(out_dir, fname)
            result.save(out_path)
            print(f"Upscaled: {fname}")
    else:
        if len(filtered) < 3:
            print("Usage: <frame.png> <reference.png> <output.png>")
            sys.exit(1)
        frame_path, ref_path, out_path = filtered[0], filtered[1], filtered[2]
        frame = Image.open(frame_path).convert('RGBA')
        ref = Image.open(ref_path).convert('RGBA')
        result = reference_upscale(frame, ref, threshold, blend)
        os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
        result.save(out_path)
        print(f"Saved: {out_path} ({result.size[0]}x{result.size[1]})")


if __name__ == '__main__':
    main()
