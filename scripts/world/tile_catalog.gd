class_name TileCatalog
extends RefCounted

var tile_size: int = 48
var root: String = ""
var sheets: Dictionary = {}
var regions: Dictionary = {}
var _texture_cache: Dictionary = {}


func load_from(path: String) -> bool:
	if not FileAccess.file_exists(path):
		push_warning("Tile catalog missing: %s" % path)
		return false

	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_warning("Unable to open tile catalog: %s" % path)
		return false

	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_warning("Tile catalog is not valid JSON object: %s" % path)
		return false

	var data: Dictionary = parsed as Dictionary
	tile_size = int(data.get("tile_size", tile_size))
	root = String(data.get("root", root))
	sheets = data.get("sheets", {}) as Dictionary
	regions = data.get("regions", {}) as Dictionary
	_texture_cache.clear()
	return root != "" and not sheets.is_empty() and not regions.is_empty()


func make_texture(region_id: String) -> Texture2D:
	if _texture_cache.has(region_id):
		return _texture_cache[region_id] as Texture2D
	if not regions.has(region_id):
		return null

	var region_data: Dictionary = regions[region_id] as Dictionary
	var sheet_id: String = String(region_data.get("sheet", ""))
	var sheet_path: String = _sheet_path(sheet_id)
	if sheet_path == "" or not ResourceLoader.exists(sheet_path):
		return null

	var source_texture: Texture2D = load(sheet_path) as Texture2D
	if source_texture == null:
		return null

	var atlas: AtlasTexture = AtlasTexture.new()
	atlas.atlas = source_texture
	atlas.region = Rect2(
		Vector2(float(region_data.get("x", 0)), float(region_data.get("y", 0))),
		Vector2(float(region_data.get("w", tile_size)), float(region_data.get("h", tile_size)))
	)
	_texture_cache[region_id] = atlas
	return atlas


func region_size(region_id: String) -> Vector2:
	if not regions.has(region_id):
		return Vector2(tile_size, tile_size)
	var region_data: Dictionary = regions[region_id] as Dictionary
	return Vector2(float(region_data.get("w", tile_size)), float(region_data.get("h", tile_size)))


func _sheet_path(sheet_id: String) -> String:
	if not sheets.has(sheet_id):
		return ""

	var relative_path := String(sheets[sheet_id])
	if relative_path == "":
		return ""
	if root.ends_with("/"):
		return root + relative_path
	return root + "/" + relative_path
