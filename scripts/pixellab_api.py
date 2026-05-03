#!/usr/bin/env python3
"""
PixelLab v2 API helper for GalacticX asset generation.

Examples:
  python3 scripts/pixellab_api.py balance
  python3 scripts/pixellab_api.py generate-image-v2 \
    --description "small sci-fi data core, transparent background" \
    --width 64 \
    --height 64 \
    --output-dir assets/sprites/api_generated/data_core \
    --image-prefix data_core
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import struct
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://api.pixellab.ai/v2"
TOKEN_ENV_VAR = "PIXELLAB_API_TOKEN"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOTENV = PROJECT_ROOT / ".env"
TERMINAL_JOB_STATUSES = {"completed", "failed"}


class PixelLabError(RuntimeError):
    """Raised when the PixelLab API returns an error or unusable response."""


def load_dotenv(path: Path = DEFAULT_DOTENV) -> None:
    """Load simple KEY=VALUE pairs from .env without overwriting the shell."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip().strip("'\"")
        os.environ[key] = value


def require_token() -> str:
    token = os.environ.get(TOKEN_ENV_VAR, "").strip()
    if not token:
        raise PixelLabError(
            f"Missing {TOKEN_ENV_VAR}. Add it to .env or export it before running."
        )
    return token


def api_request(
    method: str,
    path: str,
    *,
    token: str,
    body: dict[str, Any] | None = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 120,
) -> dict[str, Any]:
    url = path if path.startswith("http") else f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    data = None
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }

    if body is not None:
        data = json.dumps(body, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        raw_error = error.read().decode("utf-8", errors="replace")
        detail = _extract_error_detail(raw_error)
        raise PixelLabError(f"PixelLab HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise PixelLabError(f"PixelLab request failed: {error.reason}") from error

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise PixelLabError(f"PixelLab returned non-JSON response: {raw[:300]}") from error

    if not isinstance(parsed, dict):
        raise PixelLabError("PixelLab returned an unexpected non-object JSON response.")
    return parsed


def _extract_error_detail(raw_error: str) -> str:
    try:
        parsed = json.loads(raw_error)
    except json.JSONDecodeError:
        return raw_error[:500] or "empty error response"
    return json.dumps(parsed, ensure_ascii=True)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def summarize_for_disk(value: Any) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, child in value.items():
            if key == "base64" and isinstance(child, str):
                result[key] = f"<base64 {len(child)} chars>"
            else:
                result[key] = summarize_for_disk(child)
        return result
    if isinstance(value, list):
        return [summarize_for_disk(item) for item in value]
    return value


def parse_image_size(path: Path) -> tuple[int, int, str]:
    data = path.read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return width, height, "png"
    if data.startswith(b"\xff\xd8"):
        return parse_jpeg_size(data)
    raise PixelLabError(f"Unsupported reference image format: {path}")


def parse_jpeg_size(data: bytes) -> tuple[int, int, str]:
    index = 2
    while index < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(data):
            break
        segment_length = struct.unpack(">H", data[index : index + 2])[0]
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            height, width = struct.unpack(">HH", data[index + 3 : index + 7])
            return width, height, "jpeg"
        index += segment_length
    raise PixelLabError("Could not read JPEG dimensions.")


def reference_image_payload(path: Path, usage_description: str | None = None) -> dict[str, Any]:
    width, height, image_format = parse_image_size(path)
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    payload: dict[str, Any] = {
        "image": {
            "type": "base64",
            "base64": encoded,
            "format": image_format,
        },
        "size": {
            "width": width,
            "height": height,
        },
    }
    if usage_description:
        payload["usage_description"] = usage_description
    return payload


def decode_base64_image(image: dict[str, Any]) -> bytes:
    data = image.get("base64")
    if not isinstance(data, str) or not data:
        raise PixelLabError("Image response did not include base64 data.")
    if "," in data and data.lstrip().startswith("data:"):
        data = data.split(",", 1)[1]
    return base64.b64decode(data)


def collect_response_images(
    job_result: dict[str, Any], image_field: str
) -> list[tuple[str, dict[str, Any]]]:
    last_response = job_result.get("last_response")
    response = last_response if isinstance(last_response, dict) else job_result

    if image_field == "all":
        images: list[tuple[str, dict[str, Any]]] = []
        for field in ("images", "quantized_images"):
            values = response.get(field)
            if isinstance(values, list):
                images.extend((field, item) for item in values if isinstance(item, dict))
        single = response.get("image")
        if isinstance(single, dict):
            images.append(("image", single))
        return images

    values = response.get(image_field)
    if isinstance(values, list):
        return [(image_field, item) for item in values if isinstance(item, dict)]
    if image_field == "image" and isinstance(values, dict):
        return [("image", values)]
    if image_field != "images":
        return []

    single = response.get("image")
    if isinstance(single, dict):
        return [("image", single)]
    return []


def save_response_images(
    job_result: dict[str, Any],
    *,
    output_dir: Path,
    image_prefix: str,
    image_field: str,
) -> list[Path]:
    images = collect_response_images(job_result, image_field)
    if not images:
        raise PixelLabError(f"No images found in response field {image_field!r}.")

    output_dir.mkdir(parents=True, exist_ok=True)
    include_field_name = image_field == "all"
    saved_paths: list[Path] = []

    for index, (field_name, image) in enumerate(images):
        field_part = f"_{slugify(field_name)}" if include_field_name else ""
        path = output_dir / f"{image_prefix}{field_part}_{index:02d}.png"
        path.write_bytes(decode_base64_image(image))
        saved_paths.append(path)

    return saved_paths


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("_")
    return slug or "pixellab_asset"


def command_balance(args: argparse.Namespace) -> int:
    token = require_token()
    result = api_request(
        "GET",
        "/balance",
        token=token,
        base_url=args.base_url,
        timeout=args.request_timeout,
    )
    credits = result.get("credits", {})
    subscription = result.get("subscription", {})
    print(f"Credits USD: {credits.get('usd')}")
    print(
        "Generations: "
        f"{subscription.get('generations')} / {subscription.get('total')}"
    )
    return 0


def command_generate_image_v2(args: argparse.Namespace) -> int:
    token = require_token()
    output_dir = Path(args.output_dir)
    image_prefix = slugify(args.image_prefix)
    artifact_prefix = slugify(args.artifact_prefix)

    payload: dict[str, Any] = {
        "description": args.description,
        "image_size": {
            "width": args.width,
            "height": args.height,
        },
        "no_background": args.no_background,
    }
    if args.seed is not None:
        payload["seed"] = args.seed
    if args.style_image:
        payload["style_image"] = reference_image_payload(
            Path(args.style_image), args.style_usage
        )
    if args.reference_image:
        payload["reference_images"] = [
            reference_image_payload(Path(path)) for path in args.reference_image
        ]

    write_json(output_dir / f"{artifact_prefix}_request.summary.json", summarize_for_disk(payload))

    submit_result = api_request(
        "POST",
        "/generate-image-v2",
        token=token,
        body=payload,
        base_url=args.base_url,
        timeout=args.request_timeout,
    )
    write_json(output_dir / f"{artifact_prefix}_submit.json", submit_result)

    job_id = submit_result.get("background_job_id")
    if not isinstance(job_id, str) or not job_id:
        raise PixelLabError("PixelLab response did not include background_job_id.")

    if args.no_poll:
        print(f"Submitted PixelLab job: {job_id}")
        return 0

    job_result = poll_background_job(
        job_id,
        token=token,
        base_url=args.base_url,
        interval=args.poll_interval,
        timeout_seconds=args.poll_timeout,
        request_timeout=args.request_timeout,
    )
    write_json(output_dir / f"{artifact_prefix}_job_result.json", job_result)

    if job_result.get("status") != "completed":
        raise PixelLabError(f"PixelLab job ended with status: {job_result.get('status')}")

    saved_paths = save_response_images(
        job_result,
        output_dir=output_dir,
        image_prefix=image_prefix,
        image_field=args.image_field,
    )

    print(f"Completed PixelLab job: {job_id}")
    for path in saved_paths:
        print(f"Saved: {path}")
    return 0


def poll_background_job(
    job_id: str,
    *,
    token: str,
    base_url: str,
    interval: float,
    timeout_seconds: float,
    request_timeout: int,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_result: dict[str, Any] | None = None

    while time.monotonic() <= deadline:
        last_result = api_request(
            "GET",
            f"/background-jobs/{job_id}",
            token=token,
            base_url=base_url,
            timeout=request_timeout,
        )
        status = str(last_result.get("status", "")).lower()
        print(f"Job {job_id}: {status or 'unknown'}")
        if status in TERMINAL_JOB_STATUSES:
            return last_result
        time.sleep(interval)

    raise PixelLabError(
        f"Timed out waiting for PixelLab job {job_id}. Last response: {last_result}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PixelLab v2 API helper")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--request-timeout", type=int, default=120)

    subparsers = parser.add_subparsers(dest="command", required=True)

    balance = subparsers.add_parser("balance", help="Check PixelLab account balance")
    balance.set_defaults(func=command_balance)

    generate = subparsers.add_parser(
        "generate-image-v2",
        help="Submit /generate-image-v2, poll the job, and save images",
    )
    generate.add_argument("--description", required=True)
    generate.add_argument("--width", type=int, required=True)
    generate.add_argument("--height", type=int, required=True)
    generate.add_argument("--output-dir", required=True)
    generate.add_argument("--image-prefix", default="pixellab_asset")
    generate.add_argument("--artifact-prefix", default="generate_image_v2")
    generate.add_argument("--seed", type=int)
    generate.add_argument(
        "--style-image",
        help="Optional PNG/JPEG style reference image for PixelLab to match",
    )
    generate.add_argument(
        "--style-usage",
        help="Optional instruction for how PixelLab should use the style image",
    )
    generate.add_argument(
        "--reference-image",
        action="append",
        help="Optional PNG/JPEG subject reference image. Repeat up to four times.",
    )
    generate.add_argument(
        "--image-field",
        choices=("images", "quantized_images", "image", "all"),
        default="images",
        help="Response image field to save after the job completes.",
    )
    generate.add_argument("--poll-interval", type=float, default=5.0)
    generate.add_argument("--poll-timeout", type=float, default=600.0)
    generate.add_argument("--no-poll", action="store_true")
    background = generate.add_mutually_exclusive_group()
    background.add_argument(
        "--no-background",
        dest="no_background",
        action="store_true",
        default=True,
    )
    background.add_argument(
        "--keep-background",
        dest="no_background",
        action="store_false",
    )
    generate.set_defaults(func=command_generate_image_v2)

    return parser


def main() -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except PixelLabError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
