# swisstopo-mcp — Design Specification

**Date:** 2026-04-02
**Status:** Approved
**Author:** Claude + User

## Overview

A Model Context Protocol (MCP) server providing AI-native access to Swiss federal geodata via Swisstopo APIs. Focused on broad geodata access with a school infrastructure planning emphasis. Built with the same stack and patterns as the existing zurich-opendata-mcp and swiss-transport-mcp servers.

## Goals

- Provide 13 tools covering 6 Swisstopo API families
- WGS84 (lat/lon) as default coordinate input for LLM-friendly usage
- German tool descriptions and output, English code
- 11 tools work without any API key; 2 ÖREB tools with configurable canton registry
- Modular architecture by API family

## Non-Goals

- Full 26-canton ÖREB coverage (start with ZH, extensible)
- Caching/rate-limiting (Swisstopo APIs are generous)
- National school layer (doesn't exist at Swisstopo; zurich-opendata-mcp covers Zurich schools)

---

## Project Structure

```
swisstopo-mcp/
├── src/swisstopo_mcp/
│   ├── __init__.py                 # Version info
│   ├── server.py                   # FastMCP instance, tool registration, entry point
│   ├── api_client.py               # Shared HTTP client, error handler, coordinate helpers
│   ├── rest_api.py                 # api3.geo.admin.ch: layer search, identify, find
│   ├── geocoding.py                # SearchServer: address/location search
│   ├── height.py                   # Height queries & elevation profile
│   ├── stac.py                     # STAC catalog: collections, items, search
│   ├── wmts.py                     # Map tile URL generation
│   └── oereb.py                    # ÖREB cadastre (optional, canton ZH)
├── tests/
│   └── test_server.py
├── .github/workflows/
│   ├── ci.yml                      # Ruff lint + unit tests (Python 3.11-3.13)
│   └── publish.yml                 # PyPI publish on GitHub release
├── pyproject.toml
├── claude_desktop_config.json
├── README.md / README.de.md
├── CHANGELOG.md
├── CONTRIBUTING.md
└── LICENSE (MIT)
```

**Registration pattern:** Each module (e.g., `rest_api.py`) defines Pydantic input models and plain `async def` handler functions. `server.py` imports these functions and wraps them with `@mcp.tool()` decorators — the `mcp` instance lives only in `server.py` to avoid circular imports. This matches the swiss-transport-mcp pattern.

---

## API Endpoints & Constants

```python
GEO_ADMIN_BASE = "https://api3.geo.admin.ch"
STAC_BASE = "https://data.geo.admin.ch/api/stac/v0.9"  # Verify at implementation: may need update to v1.0
WMTS_BASE = "https://wmts.geo.admin.ch/1.0.0"

REQUEST_TIMEOUT = 30.0
USER_AGENT = "SwisstopoMCP/0.1 (MCP Server)"

# Swiss bounding box (WGS84) for input validation
CH_LAT_MIN, CH_LAT_MAX = 45.8, 47.9
CH_LON_MIN, CH_LON_MAX = 5.9, 10.5
```

> **Implementation note:** The STAC API version (v0.9) must be verified at implementation time. Swisstopo may have migrated to v1.0. The base URL is a single constant, easy to update.

### Supported Coordinate Systems

| Code | Name | Usage |
|------|------|-------|
| 4326 | WGS84 | **Default for all inputs** (lat/lon, intuitive for LLMs) |
| 2056 | LV95 | Current Swiss standard, used internally |
| 21781 | LV03 | Legacy Swiss system |
| 3857 | Web Mercator | Web mapping |

---

## FastMCP Initialization

```python
mcp = FastMCP(
    "swisstopo_mcp",
    instructions=(
        "Swiss federal geodata server with 13 tools across 6 API families. "
        "Use swisstopo_search_layers to discover layer IDs, then use "
        "swisstopo_identify_features or swisstopo_find_features to query them. "
        "swisstopo_geocode converts addresses to coordinates. "
        "swisstopo_get_height returns elevation. "
        "swisstopo_search_geodata finds downloadable datasets (orthophotos, 3D models, etc.). "
        "swisstopo_map_url generates shareable map links. "
        "ÖREB tools (swisstopo_get_egrid, swisstopo_get_oereb_extract) require a canton parameter."
    ),
)
```

## Entry Point

```python
def main():
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    if transport in ("sse", "streamable-http"):
        port = int(os.environ.get("MCP_PORT", "8000"))
        mcp.run(transport=transport, port=port)
    else:
        mcp.run()

if __name__ == "__main__":
    main()
```

Entry point in pyproject.toml: `swisstopo-mcp = "swisstopo_mcp.server:main"`

## Tool Annotations

All tools use consistent MCP annotations:

```python
annotations={
    "title": "German title",
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}
```

All 13 tools are read-only and non-destructive.

---

## Tools (13 total)

### REST API (`rest_api.py`) — 4 Tools

#### `swisstopo_search_layers`
- **Purpose:** Search the Swisstopo layer catalog (500+ layers)
- **Endpoint:** `GET /rest/services/ech/MapServer` or `SearchServer?type=layers`
- **Parameters:** `query` (str, required), `lang` (str, default "de"), `limit` (int, default 10, max 30)
- **Returns:** Markdown table with layer ID, name, description, queryable status

#### `swisstopo_identify_features`
- **Purpose:** Find features at a coordinate/geometry (spatial query)
- **Endpoint:** `GET /rest/services/ech/MapServer/identify`
- **Parameters:** `layers` (str, required — comma-separated layer IDs), `lat` (float, ge=45.8, le=47.9), `lon` (float, ge=5.9, le=10.5), `tolerance` (int, default 0, ge=0, le=200), `sr` (int, default 4326)
- **Internal:** Converts WGS84 to required format, sets `geometryType=esriGeometryPoint`
- **Returns:** Feature attributes as key-value list grouped by layer

#### `swisstopo_find_features`
- **Purpose:** Attribute search within a single layer (e.g., find building by EGID)
- **Endpoint:** `GET /rest/services/ech/MapServer/find`
- **Parameters:** `layer` (str, required), `search_text` (str, required), `search_field` (str, required), `contains` (bool, default true)
- **Returns:** Matching features with attributes

#### `swisstopo_get_feature`
- **Purpose:** Retrieve a specific feature by ID
- **Endpoint:** `GET /rest/services/ech/MapServer/{layer}/{feature_id}`
- **Parameters:** `layer` (str, required), `feature_id` (str, required), `sr` (int, default 4326)
- **Returns:** Full feature attributes and geometry summary

### Geocoding (`geocoding.py`) — 2 Tools

#### `swisstopo_geocode`
- **Purpose:** Address/location → coordinates
- **Endpoint:** `GET /rest/services/ech/SearchServer?type=locations`
- **Parameters:** `search_text` (str, required, min 2, max 200), `origins` (str|None — "address", "zipcode", "gg25", "district", "kantone", "gazetteer", "parcel"), `sr` (int, default 4326), `limit` (int, default 10, max 50)
- **Returns:** Markdown table with label, coordinates, type, relevance

#### `swisstopo_reverse_geocode`
- **Purpose:** Coordinates → nearest address/location
- **Implementation:** Uses SearchServer with `type=locations&origins=address` and the coordinate as bbox center point (small bbox around the point). This is simpler and more reliable than the Identify endpoint which requires `mapExtent` and `imageDisplay` parameters.
- **Parameters:** `lat` (float, required, ge=45.8, le=47.9), `lon` (float, required, ge=5.9, le=10.5), `limit` (int, default 5, max 10), `sr` (int, default 4326)
- **Returns:** Nearest address(es) with coordinates

### Height (`height.py`) — 2 Tools

#### `swisstopo_get_height`
- **Purpose:** Elevation at a coordinate
- **Endpoint:** `GET /rest/services/height`
- **Parameters:** `lat` (float, required), `lon` (float, required), `sr` (int, default 4326)
- **Returns:** "Die Höhe bei (47.38, 8.54) beträgt 408.3 m ü. M."

#### `swisstopo_elevation_profile`
- **Purpose:** Elevation profile along a line
- **Endpoint:** `GET /rest/services/profile.json`
- **Parameters:** `coordinates` (str, required — simplified format: "lat1,lon1;lat2,lon2;..." — the tool constructs the GeoJSON LineString internally), `nb_points` (int, default 200), `sr` (int, default 4326)
- **Returns:** Compact table with distance, elevation, gradient
- **Note:** Accepts a simple coordinate string instead of raw GeoJSON, which is more LLM-friendly. Internally converts to `{"type":"LineString","coordinates":[[lon1,lat1],[lon2,lat2]]}`.

### STAC Catalog (`stac.py`) — 2 Tools

#### `swisstopo_search_geodata`
- **Purpose:** Search STAC collections (orthophotos, elevation models, 3D buildings, historical maps)
- **Endpoint:** `GET /api/stac/v0.9/collections` with text filtering
- **Parameters:** `query` (str, required), `limit` (int, default 10)
- **Returns:** Collection cards with title, description, temporal extent, asset formats

#### `swisstopo_get_collection`
- **Purpose:** Full details + download assets for a collection
- **Endpoint:** `GET /api/stac/v0.9/collections/{collection_id}`
- **Parameters:** `collection_id` (str, required)
- **Returns:** Detailed metadata with asset download links, spatial/temporal extent, license

### WMTS Maps (`wmts.py`) — 1 Tool

#### `swisstopo_map_url`
- **Purpose:** Generate a map.geo.admin.ch viewer URL for a specific location and layer(s)
- **Endpoint:** URL construction (no API call needed)
- **Parameters:** `lat` (float, required), `lon` (float, required), `zoom` (int, default 8, description="Zoomstufe 1-13"), `layers` (str|None, default None — comma-separated layer IDs to overlay), `lang` (str, default "de")
- **Returns:** Direct `map.geo.admin.ch` URL that can be opened in a browser, e.g. `https://map.geo.admin.ch/?lang=de&E=2683000&N=1248000&zoom=8&layers=ch.swisstopo.pixelkarte-farbe`
- **Notable layers:** `ch.swisstopo.pixelkarte-farbe` (national map), `ch.swisstopo.swissimage` (aerial), `ch.are.bauzonen` (zoning)
- **Note:** Generates a viewer URL instead of raw WMTS tile URLs. This is far more useful for LLM users — they can share the link or open it directly. The Swiss tile matrix uses LV95 coordinates, not standard Web Mercator, making raw tile URL construction non-trivial.

### ÖREB Cadastre (`oereb.py`) — 2 Tools (optional)

#### `swisstopo_get_egrid`
- **Purpose:** Get property ID (EGRID) from coordinates
- **Endpoint:** `GET {canton_base}/getegrid/json/?EN={easting},{northing}`
- **Parameters:** `lat` (float, required), `lon` (float, required), `canton` (str, **required** — e.g. "ZH", "BE")
- **Graceful degradation:** Returns helpful error if canton not in registry, with link to https://oereb.cadastre.ch
- **Note:** Canton is required (no auto-detection — YAGNI). The LLM can ask the user or infer from context.

#### `swisstopo_get_oereb_extract`
- **Purpose:** Get public-law restrictions on a property
- **Endpoint:** `GET {canton_base}/extract/json/?EGRID={egrid}`
- **Parameters:** `egrid` (str, required), `canton` (str, **required** — e.g. "ZH", "BE"), `topics` (str|None), `lang` (str, default "de")
- **Returns:** Structured list of restrictions with topic, description, authority

### ÖREB Canton Registry

```python
OEREB_ENDPOINTS = {
    "ZH": "https://oereb.geo.zh.ch",
    "BE": "https://www.oereb2.apps.be.ch",
    # Extensible
}
```

Configurable via `SWISSTOPO_OEREB_CANTONS` environment variable (default: "ZH").

---

## Shared Infrastructure (`api_client.py`)

### HTTP Client

```python
async def _get_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    )

async def geo_admin_request(path: str, params: dict) -> dict:
    """GET on api3.geo.admin.ch → JSON"""

async def stac_request(path: str, params: dict) -> dict:
    """GET on data.geo.admin.ch/api/stac → JSON"""
```

### Error Handler

```python
def handle_api_error(e: Exception, context: str = "") -> str:
    """Translates HTTP errors to German user-friendly messages."""
    # 404 → "Ressource nicht gefunden"
    # 429 → "Zu viele Anfragen"
    # Timeout → "Zeitüberschreitung"
    # ConnectionError → "Verbindungsfehler"
```

### Coordinate Helpers

```python
def wgs84_to_lv95(lat: float, lon: float) -> tuple[float, float]:
    """WGS84 → LV95 conversion using Swisstopo polynomial approximation (~1m accuracy).
    Reference: Swisstopo 'Formeln und Konstanten' document, section 4.1."""

def validate_sr(sr: int) -> int:
    """Validate spatial reference, raise ValueError if unsupported."""

def format_coordinates(x: float, y: float, sr: int) -> str:
    """Format coordinates with SR label."""
```

---

## Pydantic Patterns

All input models follow the established convention:

```python
class ExampleInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    field: str = Field(
        ...,
        description="German description for LLM users",
        min_length=2,
        max_length=200,
    )
```

- `from __future__ import annotations` at the top of every module
- `extra="forbid"` rejects unknown parameters
- `str_strip_whitespace=True` auto-trims whitespace
- German descriptions on all fields
- WGS84 (4326) as default SR everywhere
- Swiss bounding box validation on all lat/lon fields (45.8-47.9 / 5.9-10.5)
- Sensible defaults for all optional fields

---

## Output Format

All tools return **Markdown strings** (not JSON), consistent with existing servers:

- Tables for multi-result queries
- Key-value lists for single features
- Inline tips and hints for next steps
- Error messages with actionable suggestions

---

## Environment Variables

```bash
# Optional — only for ÖREB extension
SWISSTOPO_OEREB_CANTONS="ZH,BE"    # Activated cantons (default: ZH)

# Transport mode
MCP_TRANSPORT="stdio"               # "stdio" (default) or "sse" / "streamable-http"
MCP_PORT="8000"                      # Port for HTTP transport
```

---

## Packaging & Deployment

### pyproject.toml

- Build system: Hatchling
- Dependencies: `mcp[cli]>=1.0.0`, `httpx>=0.27.0`, `pydantic>=2.0.0`
- Entry point: `swisstopo-mcp = "swisstopo_mcp.server:main"`
- Python: 3.11, 3.12, 3.13

### Claude Desktop Config

```json
{
  "mcpServers": {
    "swisstopo": {
      "command": "swisstopo-mcp",
      "env": {
        "SWISSTOPO_OEREB_CANTONS": "ZH"
      }
    }
  }
}
```

### Installation

```bash
pip install swisstopo-mcp          # From PyPI
swisstopo-mcp                      # Run via console script
python -m swisstopo_mcp.server     # Run as module
```

---

## Testing Strategy

- **Unit tests** (no API): Pydantic validation, coordinate conversion, Markdown formatting, error handling
- **Live tests** (`@pytest.mark.live`): Real API calls against Swisstopo
- **CI:** Ruff lint + unit tests on push/PR, live tests skipped
- **Frameworks:** pytest, pytest-asyncio, respx (HTTP mocking)

---

## Key Swisstopo Layers for School Planning

| Layer ID | Name | Use Case |
|----------|------|----------|
| `ch.bfs.gebaeude_wohnungs_register` | Eidg. Gebäude-/Wohnungsregister | Building metadata by EGID |
| `ch.swisstopo.amtliches-gebaeudeadressverzeichnis` | Amtl. Gebäudeadressverzeichnis | Official addresses |
| `ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill` | Gemeindegrenzen | Municipality boundaries / catchment areas |
| `ch.bfs.arealstatistik` | Arealstatistik | Land use classification |
| `ch.swisstopo.swisstlm3d-strassen` | Strassen swissTLM3D | Road network for accessibility |
| `ch.are.bauzonen` | Bauzonen | Zoning (WMTS) |
| `ch.swisstopo.swissimage` | SWISSIMAGE | Aerial imagery (WMTS) |

---

## Decisions & Trade-offs

| Decision | Rationale |
|----------|-----------|
| WGS84 as default SR | Most intuitive for LLM users (lat/lon) |
| No caching | Swisstopo has no documented rate limits |
| ÖREB canton registry | Pragmatic — avoids complexity of 26 different canton APIs |
| Markdown output | Consistent with existing servers, LLM-optimized |
| Modular by API family | 6 API families with 13 tools needs clean separation |
| No additional dependencies | httpx handles all HTTP; no XML parsing needed (JSON endpoints) |
