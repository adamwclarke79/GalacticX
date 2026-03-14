/**
 * RetroDiffusion API client
 * https://retrodiffusion.ai
 *
 * Generates pixel art sprites, animations, tilesets, and edits.
 */

const API_BASE = 'https://api.retrodiffusion.ai/v1';

export class RetroDiffusion {
  constructor(apiKey) {
    this.apiKey = apiKey;
  }

  async _request(method, path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-RD-Token': this.apiKey
      },
      body: body ? JSON.stringify(body) : undefined
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`RetroDiffusion ${method} ${path} failed (${res.status}): ${text}`);
    }

    return res.json();
  }

  /**
   * Generate images via /v1/inferences.
   *
   * @param {object} opts
   * @param {string} opts.prompt - Description of image to generate
   * @param {number} [opts.width=96] - Width in pixels
   * @param {number} [opts.height=96] - Height in pixels
   * @param {number} [opts.numImages=1] - Number of images (animations: always 1)
   * @param {string} [opts.promptStyle='rd_pro__default'] - Style identifier
   * @param {number} [opts.seed] - Seed for reproducibility
   * @param {boolean} [opts.removeBg] - Remove background (transparent PNG)
   * @param {boolean} [opts.returnNonBgRemoved] - Also return pre-removal image
   * @param {boolean} [opts.tileX] - Seamless tile horizontally
   * @param {boolean} [opts.tileY] - Seamless tile vertically
   * @param {string[]} [opts.referenceImages] - Base64 reference images for RD_PRO (max 9, no data: prefix)
   * @param {string} [opts.inputImage] - Base64 input image (RGB, no transparency, no data: prefix)
   * @param {string} [opts.extraInputImage] - Second input for rd_tile__tileset_advanced (outside texture)
   * @param {string} [opts.extraPrompt] - Second prompt for rd_tile__tileset_advanced (outside texture)
   * @param {number} [opts.strength] - img2img strength 0-1
   * @param {string} [opts.inputPalette] - Base64 palette image to guide colors (no data: prefix)
   * @param {boolean} [opts.returnPrePalette] - Also return pre-palette image
   * @param {boolean} [opts.returnSpritesheet] - Return PNG spritesheet instead of GIF for animations
   * @param {boolean} [opts.bypassPromptExpansion] - Disable automatic prompt expansion
   * @param {boolean} [opts.includeDownloadableData] - Include structured asset data (e.g. inventory_items atlas)
   * @param {number} [opts.upscaleOutputFactor] - Set to 1 for native resolution, null for regular
   * @param {boolean} [opts.checkCost] - Estimate cost without generating
   * @returns {Promise<{base64_images: string[], balance_cost: number, remaining_balance: number, downloadable_data?: object}>}
   */
  async generate(opts) {
    const payload = {
      prompt: opts.prompt,
      width: opts.width ?? 96,
      height: opts.height ?? 96,
      num_images: opts.numImages ?? 1,
      prompt_style: opts.promptStyle ?? 'rd_pro__default'
    };

    if (opts.seed != null) payload.seed = opts.seed;
    if (opts.removeBg) payload.remove_bg = true;
    if (opts.returnNonBgRemoved) payload.return_non_bg_removed = true;
    if (opts.tileX) payload.tile_x = true;
    if (opts.tileY) payload.tile_y = true;
    if (opts.referenceImages) payload.reference_images = opts.referenceImages;
    if (opts.inputImage) payload.input_image = opts.inputImage;
    if (opts.extraInputImage) payload.extra_input_image = opts.extraInputImage;
    if (opts.extraPrompt) payload.extra_prompt = opts.extraPrompt;
    if (opts.strength != null) payload.strength = opts.strength;
    if (opts.inputPalette) payload.input_palette = opts.inputPalette;
    if (opts.returnPrePalette) payload.return_pre_palette = true;
    if (opts.returnSpritesheet) payload.return_spritesheet = true;
    if (opts.bypassPromptExpansion) payload.bypass_prompt_expansion = true;
    if (opts.includeDownloadableData) payload.include_downloadable_data = true;
    if (opts.upscaleOutputFactor != null) payload.upscale_output_factor = opts.upscaleOutputFactor;
    if (opts.checkCost) payload.check_cost = true;

    return this._request('POST', '/inferences', payload);
  }

  /** Check cost without generating. */
  async checkCost(opts) {
    return this.generate({ ...opts, checkCost: true });
  }

  /** Check remaining credit balance. */
  async getBalance() {
    return this._request('GET', '/inferences/credits');
  }

  /**
   * Edit an existing image via /v1/edit.
   * Cost: $0.06 per edit. Supports progressive editing (chain outputs as inputs).
   *
   * @param {string} prompt - Describe the edit (e.g. "add a hat")
   * @param {string} inputImageBase64 - Base64 encoded image (16x16 – 256x256, no data: prefix)
   * @returns {Promise<{outputImageBase64: string, remaining_credits: number}>}
   */
  async edit(prompt, inputImageBase64) {
    return this._request('POST', '/edit', {
      prompt,
      inputImageBase64
    });
  }

  // --- Style management ---

  async createStyle(opts) {
    return this._request('POST', '/styles', opts);
  }

  async updateStyle(styleId, opts) {
    return this._request('PATCH', `/styles/${styleId}`, opts);
  }

  async deleteStyle(styleId) {
    return this._request('DELETE', `/styles/${styleId}`);
  }
}

// ── Style constants ──

export const Styles = {
  // RD_PRO (96x96 – 256x256, $0.22/image)
  PRO_DEFAULT: 'rd_pro__default',
  PRO_PAINTERLY: 'rd_pro__painterly',
  PRO_FANTASY: 'rd_pro__fantasy',
  PRO_UI_PANEL: 'rd_pro__ui_panel',
  PRO_HORROR: 'rd_pro__horror',
  PRO_SCIFI: 'rd_pro__scifi',
  PRO_SIMPLE: 'rd_pro__simple',
  PRO_ISOMETRIC: 'rd_pro__isometric',
  PRO_TOPDOWN: 'rd_pro__topdown',
  PRO_PLATFORMER: 'rd_pro__platformer',
  PRO_DUNGEON_MAP: 'rd_pro__dungeon_map',
  PRO_EDIT: 'rd_pro__edit',
  PRO_PIXELATE: 'rd_pro__pixelate',
  PRO_SPRITESHEET: 'rd_pro__spritesheet',
  PRO_TYPOGRAPHY: 'rd_pro__typography',
  PRO_HEX_TILES: 'rd_pro__hexagonal_tiles',
  PRO_FPS_WEAPON: 'rd_pro__fps_weapon',
  PRO_INVENTORY: 'rd_pro__inventory_items',

  // RD_FAST (64x64 – 384x384)
  FAST_DEFAULT: 'rd_fast__default',
  FAST_RETRO: 'rd_fast__retro',
  FAST_SIMPLE: 'rd_fast__simple',
  FAST_DETAILED: 'rd_fast__detailed',
  FAST_ANIME: 'rd_fast__anime',
  FAST_GAME_ASSET: 'rd_fast__game_asset',
  FAST_PORTRAIT: 'rd_fast__portrait',
  FAST_TEXTURE: 'rd_fast__texture',
  FAST_UI: 'rd_fast__ui',
  FAST_ITEM_SHEET: 'rd_fast__item_sheet',
  FAST_TURNAROUND: 'rd_fast__character_turnaround',
  FAST_1BIT: 'rd_fast__1_bit',
  FAST_LOW_RES: 'rd_fast__low_res',
  FAST_MC_ITEM: 'rd_fast__mc_item',
  FAST_MC_TEXTURE: 'rd_fast__mc_texture',
  FAST_NO_STYLE: 'rd_fast__no_style',

  // RD_PLUS
  PLUS_DEFAULT: 'rd_plus__default',
  PLUS_RETRO: 'rd_plus__retro',
  PLUS_WATERCOLOR: 'rd_plus__watercolor',
  PLUS_TEXTURED: 'rd_plus__textured',
  PLUS_CARTOON: 'rd_plus__cartoon',
  PLUS_UI_ELEMENT: 'rd_plus__ui_element',
  PLUS_ITEM_SHEET: 'rd_plus__item_sheet',
  PLUS_TURNAROUND: 'rd_plus__character_turnaround',
  PLUS_ENVIRONMENT: 'rd_plus__environment',
  PLUS_TOPDOWN_MAP: 'rd_plus__topdown_map',
  PLUS_TOPDOWN_ASSET: 'rd_plus__topdown_asset',
  PLUS_ISOMETRIC: 'rd_plus__isometric',
  PLUS_ISOMETRIC_ASSET: 'rd_plus__isometric_asset',
  PLUS_CLASSIC: 'rd_plus__classic',
  PLUS_LOW_RES: 'rd_plus__low_res',
  PLUS_MC_ITEM: 'rd_plus__mc_item',
  PLUS_MC_TEXTURE: 'rd_plus__mc_texture',
  PLUS_TOPDOWN_ITEM: 'rd_plus__topdown_item',
  PLUS_SKILL_ICON: 'rd_plus__skill_icon',

  // Animations
  ANIM_4DIR_WALK: 'animation__four_angle_walking',       // 48x48 only, $0.07
  ANIM_WALK_IDLE: 'animation__walking_and_idle',          // 48x48 only, $0.07
  ANIM_SMALL_SPRITES: 'animation__small_sprites',         // 32x32 only, $0.07
  ANIM_VFX: 'animation__vfx',                             // 24x24–96x96 square, $0.07
  ANIM_8DIR_ROTATION: 'animation__8_dir_rotation',        // 80x80 only, $0.25
  ANIM_ANY: 'animation__any_animation',                   // 64x64 only, $0.25

  // Tilesets
  TILE_TILESET: 'rd_tile__tileset',                       // 16x16–32x32, $0.10
  TILE_TILESET_ADV: 'rd_tile__tileset_advanced',          // 16x16–32x32, $0.10
  TILE_SINGLE: 'rd_tile__single_tile',                    // 16x16–64x64
  TILE_VARIATION: 'rd_tile__tile_variation',               // 16x16–128x128
  TILE_OBJECT: 'rd_tile__tile_object',                    // 16x16–96x96
  TILE_SCENE_OBJECT: 'rd_tile__scene_object'              // 64x64–384x384
};
