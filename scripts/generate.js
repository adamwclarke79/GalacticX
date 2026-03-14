#!/usr/bin/env node
/**
 * CLI tool for generating pixel art via RetroDiffusion API.
 *
 * Usage:
 *   node scripts/generate.js --prompt "stormtrooper" --out assets/sprites/test.png
 *   node scripts/generate.js --prompt "stormtrooper walking" --style animation__four_angle_walking --width 48 --height 48 --spritesheet --out walk.png
 *   node scripts/generate.js --prompt "desert sand" --style rd_tile__tileset --width 32 --height 32 --out tiles.png
 *   node scripts/generate.js --prompt "stormtrooper" --check-cost
 *   node scripts/generate.js --balance
 *
 * Run via: npm run generate -- <args>
 */

import fs from 'fs';
import path from 'path';

const API_BASE = 'https://api.retrodiffusion.ai/v1';
const API_KEY = process.env.RETRODIFFUSION_API_KEY;

if (!API_KEY) {
  console.error('Error: Set RETRODIFFUSION_API_KEY environment variable');
  process.exit(1);
}

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--prompt') args.prompt = argv[++i];
    else if (arg === '--style') args.promptStyle = argv[++i];
    else if (arg === '--width') args.width = parseInt(argv[++i]);
    else if (arg === '--height') args.height = parseInt(argv[++i]);
    else if (arg === '--num') args.numImages = parseInt(argv[++i]);
    else if (arg === '--seed') args.seed = parseInt(argv[++i]);
    else if (arg === '--out') args.out = argv[++i];
    else if (arg === '--remove-bg') args.removeBg = true;
    else if (arg === '--tile-x') args.tileX = true;
    else if (arg === '--tile-y') args.tileY = true;
    else if (arg === '--spritesheet') args.returnSpritesheet = true;
    else if (arg === '--check-cost') args.checkCost = true;
    else if (arg === '--balance') args.balanceOnly = true;
    else if (arg === '--input-image') args.inputImage = argv[++i];
    else if (arg === '--strength') args.strength = parseFloat(argv[++i]);
    else if (arg === '--extra-prompt') args.extraPrompt = argv[++i];
    else if (arg === '--extra-input') args.extraInputImage = argv[++i];
    else if (arg === '--palette') args.inputPalette = argv[++i];
    else if (arg === '--no-expand') args.bypassPromptExpansion = true;
    else if (arg === '--native') args.upscaleOutputFactor = 1;
    else if (arg === '--ref') {
      args.referenceImages = args.referenceImages || [];
      args.referenceImages.push(argv[++i]);
    }
  }
  return args;
}

async function apiRequest(method, apiPath, body) {
  const res = await fetch(`${API_BASE}${apiPath}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-RD-Token': API_KEY
    },
    body: body ? JSON.stringify(body) : undefined,
    signal: AbortSignal.timeout(300000) // 5 minute timeout for animations
  });
  if (!res.ok) {
    console.error(`API error (${res.status}):`, await res.text());
    process.exit(1);
  }
  return res.json();
}

function loadImageBase64(filePath) {
  const buf = fs.readFileSync(filePath);
  return buf.toString('base64');
}

async function checkBalance() {
  const data = await apiRequest('GET', '/inferences/credits');
  console.log(`Balance: $${data.balance}`);
}

async function generate(args) {
  const payload = {
    prompt: args.prompt,
    width: args.width ?? 96,
    height: args.height ?? 96,
    num_images: args.numImages ?? 1,
    prompt_style: args.promptStyle ?? 'rd_pro__default'
  };

  if (args.seed != null) payload.seed = args.seed;
  if (args.removeBg) payload.remove_bg = true;
  if (args.tileX) payload.tile_x = true;
  if (args.tileY) payload.tile_y = true;
  if (args.returnSpritesheet) payload.return_spritesheet = true;
  if (args.checkCost) payload.check_cost = true;
  if (args.bypassPromptExpansion) payload.bypass_prompt_expansion = true;
  if (args.upscaleOutputFactor != null) payload.upscale_output_factor = args.upscaleOutputFactor;
  if (args.strength != null) payload.strength = args.strength;
  if (args.extraPrompt) payload.extra_prompt = args.extraPrompt;

  // Load file-based inputs as base64
  if (args.inputImage) payload.input_image = loadImageBase64(args.inputImage);
  if (args.extraInputImage) payload.extra_input_image = loadImageBase64(args.extraInputImage);
  if (args.inputPalette) payload.input_palette = loadImageBase64(args.inputPalette);
  if (args.referenceImages) {
    payload.reference_images = args.referenceImages.map(loadImageBase64);
  }

  console.log('Request:', JSON.stringify({ ...payload, input_image: payload.input_image ? '[base64]' : undefined, reference_images: payload.reference_images ? `[${payload.reference_images.length} images]` : undefined }, null, 2));

  const data = await apiRequest('POST', '/inferences', payload);
  console.log(`Cost: $${data.balance_cost} | Remaining: $${data.remaining_balance}`);

  if (args.checkCost) return;

  if (!data.base64_images?.length) {
    console.log('No images returned.');
    return;
  }

  const outPath = args.out ?? 'output.png';
  const dir = path.dirname(outPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

  data.base64_images.forEach((b64, i) => {
    const filePath = data.base64_images.length > 1
      ? outPath.replace(/(\.\w+)$/, `-${i}$1`)
      : outPath;
    fs.writeFileSync(filePath, Buffer.from(b64, 'base64'));
    console.log(`Saved: ${filePath}`);
  });
}

const args = parseArgs(process.argv);

if (args.balanceOnly) {
  checkBalance();
} else if (!args.prompt) {
  console.log(`RetroDiffusion CLI

Usage: npm run generate -- [options]

Options:
  --prompt TEXT        Image description (required)
  --style STYLE        Style ID (default: rd_pro__default)
  --width N            Width in px (default: 96)
  --height N           Height in px (default: 96)
  --num N              Number of images (default: 1)
  --seed N             Reproducibility seed
  --out PATH           Output file path (default: output.png)
  --remove-bg          Transparent background
  --tile-x / --tile-y  Seamless tiling
  --spritesheet        PNG spritesheet (for animations)
  --input-image FILE   Input image for img2img / animations
  --strength N         img2img strength 0-1
  --ref FILE           Reference image (repeatable, max 9)
  --extra-prompt TEXT  Second prompt (tileset_advanced)
  --extra-input FILE   Second input image (tileset_advanced)
  --palette FILE       Palette reference image
  --no-expand          Disable prompt expansion
  --native             Native resolution output
  --check-cost         Estimate cost only
  --balance            Show credit balance`);
} else {
  generate(args);
}
