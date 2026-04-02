# swisstopo-mcp Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an MCP server providing 13 tools for Swiss federal geodata access via Swisstopo APIs.

**Architecture:** Modular Python server using FastMCP. Each API family (REST API, Geocoding, Height, STAC, WMTS, ÖREB) gets its own module with Pydantic input models and handler functions. `server.py` imports handlers and registers them as MCP tools. Shared HTTP client and coordinate helpers in `api_client.py`.

**Tech Stack:** Python 3.11+, FastMCP (mcp[cli]), httpx, Pydantic v2, Hatchling

**Spec:** `docs/superpowers/specs/2026-04-02-swisstopo-mcp-design.md`

---

## Chunk 1: Project Scaffolding & Shared Infrastructure

### Task 1: Initialize project structure

**Files:**
- Create: `C:/Users/hayal/swisstopo-mcp/pyproject.toml`
- Create: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/__init__.py`
- Create: `C:/Users/hayal/swisstopo-mcp/LICENSE`
- Create: `C:/Users/hayal/swisstopo-mcp/claude_desktop_config.json`
- Create: `C:/Users/hayal/swisstopo-mcp/.gitignore`

- [ ] **Step 1: Create project directory and git init**

```bash
mkdir -p C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp
mkdir -p C:/Users/hayal/swisstopo-mcp/tests
cd C:/Users/hayal/swisstopo-mcp && git init
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "swisstopo-mcp"
version = "0.1.0"
description = "MCP server for Swiss federal geodata (Swisstopo APIs)"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
authors = [{ name = "Schulamt Stadt Zürich" }]
keywords = ["mcp", "swisstopo", "geodata", "switzerland", "gis"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "License :: OSI Approved :: MIT License",
]
dependencies = [
    "mcp[cli]>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "respx>=0.21.0",
    "ruff>=0.4.0",
]

[project.scripts]
swisstopo-mcp = "swisstopo_mcp.server:main"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = ["live: live API tests (require network, skipped in CI)"]
```

- [ ] **Step 3: Create __init__.py**

```python
"""swisstopo-mcp — MCP server for Swiss federal geodata."""

__version__ = "0.1.0"
```

- [ ] **Step 4: Create .gitignore, LICENSE, claude_desktop_config.json**

`.gitignore`:
```
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.eggs/
.pytest_cache/
.ruff_cache/
*.egg
.venv/
venv/
```

`LICENSE`: MIT License with "Schulamt Stadt Zürich" and year 2026.

`claude_desktop_config.json`:
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

- [ ] **Step 5: Commit**

```bash
cd C:/Users/hayal/swisstopo-mcp
git add -A
git commit -m "chore: initialize swisstopo-mcp project structure"
```

---

### Task 2: Build shared api_client.py with coordinate helpers

**Files:**
- Create: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/api_client.py`
- Create: `C:/Users/hayal/swisstopo-mcp/tests/test_api_client.py`

- [ ] **Step 1: Write tests for coordinate conversion and validation**

```python
# tests/test_api_client.py
from __future__ import annotations

import pytest
from swisstopo_mcp.api_client import (
    wgs84_to_lv95,
    lv95_to_wgs84,
    validate_sr,
    format_coordinates,
    handle_api_error,
    CH_LAT_MIN, CH_LAT_MAX, CH_LON_MIN, CH_LON_MAX,
)
import httpx


class TestWgs84ToLv95:
    def test_bern_federal_palace(self):
        """Bern Bundesplatz: known reference point."""
        e, n = wgs84_to_lv95(46.9481, 7.4474)
        assert abs(e - 2600000) < 500  # ~500m tolerance for approx formula
        assert abs(n - 1200000) < 500

    def test_zurich_hb(self):
        """Zürich HB: approximate check."""
        e, n = wgs84_to_lv95(47.3769, 8.5417)
        assert 2680000 < e < 2690000
        assert 1245000 < n < 1255000

    def test_round_trip(self):
        """WGS84 → LV95 → WGS84 should be close to original."""
        lat_orig, lon_orig = 47.38, 8.54
        e, n = wgs84_to_lv95(lat_orig, lon_orig)
        lat_back, lon_back = lv95_to_wgs84(e, n)
        assert abs(lat_back - lat_orig) < 0.001
        assert abs(lon_back - lon_orig) < 0.001


class TestValidateSr:
    def test_valid_srs(self):
        for sr in (4326, 2056, 21781, 3857):
            assert validate_sr(sr) == sr

    def test_invalid_sr_raises(self):
        with pytest.raises(ValueError, match="Nicht unterstütztes Koordinatensystem"):
            validate_sr(9999)


class TestFormatCoordinates:
    def test_wgs84_format(self):
        result = format_coordinates(47.38, 8.54, 4326)
        assert "47.38" in result
        assert "8.54" in result
        assert "WGS84" in result

    def test_lv95_format(self):
        result = format_coordinates(2683000, 1248000, 2056)
        assert "LV95" in result


class TestHandleApiError:
    def test_404_error(self):
        request = httpx.Request("GET", "https://example.com")
        response = httpx.Response(404, request=request)
        error = httpx.HTTPStatusError("Not found", request=request, response=response)
        result = handle_api_error(error, "Test")
        assert "nicht gefunden" in result.lower()

    def test_timeout_error(self):
        result = handle_api_error(httpx.TimeoutException("timeout"), "Test")
        assert "Zeitüberschreitung" in result or "zeitüberschreitung" in result.lower()

    def test_connection_error(self):
        result = handle_api_error(httpx.ConnectError("fail"), "Test")
        assert "Verbindung" in result or "verbindung" in result.lower()

    def test_generic_error(self):
        result = handle_api_error(RuntimeError("boom"), "Test")
        assert "boom" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd C:/Users/hayal/swisstopo-mcp
PYTHONPATH=src pytest tests/test_api_client.py -v
```
Expected: ImportError — module does not exist yet.

- [ ] **Step 3: Implement api_client.py**

```python
# src/swisstopo_mcp/api_client.py
from __future__ import annotations

from typing import Any

import httpx

# --- Constants ---

GEO_ADMIN_BASE = "https://api3.geo.admin.ch"
STAC_BASE = "https://data.geo.admin.ch/api/stac/v0.9"
WMTS_BASE = "https://wmts.geo.admin.ch/1.0.0"

REQUEST_TIMEOUT = 30.0
USER_AGENT = "SwisstopoMCP/0.1 (MCP Server; +https://github.com/schulamt-zurich/swisstopo-mcp)"

# Swiss bounding box (WGS84)
CH_LAT_MIN, CH_LAT_MAX = 45.8, 47.9
CH_LON_MIN, CH_LON_MAX = 5.9, 10.5

SUPPORTED_SRS = {4326, 2056, 21781, 3857}


# --- HTTP Client ---

async def _get_client() -> httpx.AsyncClient:
    """Create a configured async HTTP client."""
    return httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
    )


async def geo_admin_request(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """GET request on api3.geo.admin.ch, returns parsed JSON."""
    async with await _get_client() as client:
        url = f"{GEO_ADMIN_BASE}{path}"
        response = await client.get(url, params=params or {})
        response.raise_for_status()
        return response.json()


async def stac_request(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET request on data.geo.admin.ch STAC API, returns parsed JSON."""
    async with await _get_client() as client:
        url = f"{STAC_BASE}{path}"
        response = await client.get(url, params=params or {})
        response.raise_for_status()
        return response.json()


# --- Error Handling ---

def handle_api_error(e: Exception, context: str = "") -> str:
    """Translate exceptions into German user-friendly error messages."""
    prefix = f"Fehler bei {context}: " if context else "Fehler: "

    if isinstance(e, httpx.HTTPStatusError):
        status = e.response.status_code
        if status == 404:
            return f"{prefix}Ressource nicht gefunden (404)."
        if status == 403:
            return f"{prefix}Zugriff verweigert (403)."
        if status == 429:
            return f"{prefix}Zu viele Anfragen (429). Bitte warte kurz."
        if status == 500:
            return f"{prefix}Serverfehler bei Swisstopo (500). Bitte später erneut versuchen."
        return f"{prefix}HTTP-Fehler {status}."

    if isinstance(e, httpx.TimeoutException):
        return f"{prefix}Zeitüberschreitung. Der Server hat nicht rechtzeitig geantwortet."

    if isinstance(e, httpx.ConnectError):
        return f"{prefix}Verbindungsfehler. Prüfe die Netzwerkverbindung."

    return f"{prefix}{type(e).__name__}: {e}"


# --- Coordinate Helpers ---

def wgs84_to_lv95(lat: float, lon: float) -> tuple[float, float]:
    """Convert WGS84 (lat, lon) to LV95 (E, N).

    Uses the Swisstopo approximate polynomial formulas (~1m accuracy).
    Reference: Swisstopo 'Formeln und Konstanten', section 4.1.
    """
    # Auxiliary values (Bern as origin)
    lat_aux = (lat * 3600 - 169028.66) / 10000
    lon_aux = (lon * 3600 - 26782.5) / 10000

    # Easting
    e = (
        2600072.37
        + 211455.93 * lon_aux
        - 10938.51 * lon_aux * lat_aux
        - 0.36 * lon_aux * lat_aux**2
        - 44.54 * lon_aux**3
    )

    # Northing
    n = (
        1200147.07
        + 308807.95 * lat_aux
        + 3745.25 * lon_aux**2
        + 76.63 * lat_aux**2
        - 194.56 * lon_aux**2 * lat_aux
        + 119.79 * lat_aux**3
    )

    return e, n


def lv95_to_wgs84(e: float, n: float) -> tuple[float, float]:
    """Convert LV95 (E, N) to WGS84 (lat, lon).

    Uses the Swisstopo approximate polynomial formulas (~1m accuracy).
    """
    # Auxiliary values
    y_aux = (e - 2600000) / 1000000
    x_aux = (n - 1200000) / 1000000

    # Latitude in 10000" units
    lat_aux = (
        16.9023892
        + 3.238272 * x_aux
        - 0.270978 * y_aux**2
        - 0.002528 * x_aux**2
        - 0.0447 * y_aux**2 * x_aux
        - 0.0140 * x_aux**3
    )

    # Longitude in 10000" units
    lon_aux = (
        2.6779094
        + 4.728982 * y_aux
        + 0.791484 * y_aux * x_aux
        + 0.1306 * y_aux * x_aux**2
        - 0.0436 * y_aux**3
    )

    lat = lat_aux * 100 / 36
    lon = lon_aux * 100 / 36

    return lat, lon


def validate_sr(sr: int) -> int:
    """Validate spatial reference code. Returns sr if valid, raises ValueError otherwise."""
    if sr not in SUPPORTED_SRS:
        raise ValueError(
            f"Nicht unterstütztes Koordinatensystem: {sr}. "
            f"Unterstützt: {sorted(SUPPORTED_SRS)}"
        )
    return sr


def format_coordinates(x: float, y: float, sr: int) -> str:
    """Format coordinates with spatial reference label."""
    sr_names = {4326: "WGS84", 2056: "LV95", 21781: "LV03", 3857: "Web Mercator"}
    name = sr_names.get(sr, str(sr))
    if sr == 4326:
        return f"{x:.6f}, {y:.6f} ({name})"
    return f"{x:.1f}, {y:.1f} ({name})"


def parse_coordinate_string(coords_str: str) -> list[tuple[float, float]]:
    """Parse 'lat1,lon1;lat2,lon2;...' into list of (lat, lon) tuples."""
    pairs = []
    for pair in coords_str.strip().split(";"):
        parts = pair.strip().split(",")
        if len(parts) != 2:
            raise ValueError(f"Ungültiges Koordinatenpaar: '{pair}'. Erwartet: 'lat,lon'.")
        lat, lon = float(parts[0].strip()), float(parts[1].strip())
        pairs.append((lat, lon))
    if len(pairs) < 2:
        raise ValueError("Mindestens 2 Koordinatenpaare erforderlich.")
    return pairs
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd C:/Users/hayal/swisstopo-mcp
PYTHONPATH=src pytest tests/test_api_client.py -v
```
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```bash
cd C:/Users/hayal/swisstopo-mcp
git add src/swisstopo_mcp/api_client.py tests/test_api_client.py
git commit -m "feat: add shared api_client with HTTP helpers and coordinate conversion"
```

---

### Task 3: Create minimal server.py with entry point

**Files:**
- Create: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/server.py`

- [ ] **Step 1: Create server.py with FastMCP init and entry point (no tools yet)**

```python
# src/swisstopo_mcp/server.py
from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

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

# Tool imports will be added here as modules are implemented


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

- [ ] **Step 2: Verify server starts without error**

```bash
cd C:/Users/hayal/swisstopo-mcp
PYTHONPATH=src python -c "from swisstopo_mcp.server import mcp; print('Server OK:', mcp.name)"
```
Expected: `Server OK: swisstopo_mcp`

- [ ] **Step 3: Commit**

```bash
cd C:/Users/hayal/swisstopo-mcp
git add src/swisstopo_mcp/server.py
git commit -m "feat: add minimal server.py with FastMCP init and entry point"
```

---

## Chunk 2: REST API & Geocoding Tools (6 Tools)

### Task 4: Implement REST API module (4 tools)

**Files:**
- Create: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/rest_api.py`
- Create: `C:/Users/hayal/swisstopo-mcp/tests/test_rest_api.py`
- Modify: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/server.py`

- [ ] **Step 1: Write unit tests for input models and formatting**

```python
# tests/test_rest_api.py
from __future__ import annotations

import pytest
from pydantic import ValidationError
from swisstopo_mcp.rest_api import (
    SearchLayersInput,
    IdentifyInput,
    FindFeaturesInput,
    GetFeatureInput,
    format_layer_results,
    format_identify_results,
)


class TestSearchLayersInput:
    def test_valid_minimal(self):
        inp = SearchLayersInput(query="gebaeude")
        assert inp.query == "gebaeude"
        assert inp.lang == "de"
        assert inp.limit == 10

    def test_rejects_empty_query(self):
        with pytest.raises(ValidationError):
            SearchLayersInput(query="")

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            SearchLayersInput(query="test", unknown_field="x")


class TestIdentifyInput:
    def test_valid(self):
        inp = IdentifyInput(
            layers="ch.bfs.gebaeude_wohnungs_register",
            lat=47.38,
            lon=8.54,
        )
        assert inp.tolerance == 0
        assert inp.sr == 4326

    def test_lat_out_of_swiss_bounds(self):
        with pytest.raises(ValidationError):
            IdentifyInput(layers="test", lat=52.0, lon=8.54)

    def test_lon_out_of_swiss_bounds(self):
        with pytest.raises(ValidationError):
            IdentifyInput(layers="test", lat=47.0, lon=15.0)


class TestFindFeaturesInput:
    def test_valid(self):
        inp = FindFeaturesInput(
            layer="ch.bfs.gebaeude_wohnungs_register",
            search_text="1231641",
            search_field="egid",
        )
        assert inp.contains is True

    def test_contains_false(self):
        inp = FindFeaturesInput(
            layer="test", search_text="val", search_field="field", contains=False
        )
        assert inp.contains is False


class TestFormatLayerResults:
    def test_empty_results(self):
        result = format_layer_results([])
        assert "Keine Layer gefunden" in result

    def test_formats_results(self):
        layers = [
            {"layerBodId": "ch.test.layer", "title": "Test Layer", "abstract": "Desc"}
        ]
        result = format_layer_results(layers)
        assert "ch.test.layer" in result
        assert "Test Layer" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd C:/Users/hayal/swisstopo-mcp
PYTHONPATH=src pytest tests/test_rest_api.py -v
```
Expected: ImportError.

- [ ] **Step 3: Implement rest_api.py**

Create `src/swisstopo_mcp/rest_api.py` with:
- 4 Pydantic input models: `SearchLayersInput`, `IdentifyInput`, `FindFeaturesInput`, `GetFeatureInput`
- 4 async handler functions: `search_layers`, `identify_features`, `find_features`, `get_feature`
- Formatting helpers: `format_layer_results`, `format_identify_results`, `format_find_results`, `format_feature_detail`

Each handler:
1. Calls `geo_admin_request()` from `api_client.py`
2. Parses the JSON response
3. Returns a Markdown-formatted string
4. Wraps in `try/except` calling `handle_api_error()`

Key implementation details:
- `search_layers`: GET `/rest/services/ech/SearchServer` with `type=layers`
- `identify_features`: GET `/rest/services/ech/MapServer/identify` — must set `geometryType=esriGeometryPoint`, `geometry={lon},{lat}` (note: lon first for the API), `layers=all:{layer_ids}`, `tolerance`, `sr`, `returnGeometry=false`, `mapExtent={lon-1},{lat-1},{lon+1},{lat+1}`, `imageDisplay=1,1,96`
- `find_features`: GET `/rest/services/ech/MapServer/find` with `layer`, `searchText`, `searchField`, `contains`
- `get_feature`: GET `/rest/services/ech/MapServer/{layer}/{feature_id}` with `sr`

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd C:/Users/hayal/swisstopo-mcp
PYTHONPATH=src pytest tests/test_rest_api.py -v
```
Expected: All PASS.

- [ ] **Step 5: Register tools in server.py**

Add to `server.py` after the `mcp` declaration:

```python
from swisstopo_mcp.rest_api import (
    SearchLayersInput, search_layers,
    IdentifyInput, identify_features,
    FindFeaturesInput, find_features,
    GetFeatureInput, get_feature,
)

@mcp.tool(
    name="swisstopo_search_layers",
    annotations={"title": "Swisstopo Layer suchen", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def swisstopo_search_layers(params: SearchLayersInput) -> str:
    """Durchsucht den Swisstopo-Layerkatalog (500+ Layer) nach Geodatensätzen."""
    return await search_layers(params)

@mcp.tool(
    name="swisstopo_identify_features",
    annotations={"title": "Features an Koordinate identifizieren", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def swisstopo_identify_features(params: IdentifyInput) -> str:
    """Findet Features an einer bestimmten Koordinate (räumliche Abfrage auf Swisstopo-Layern)."""
    return await identify_features(params)

@mcp.tool(
    name="swisstopo_find_features",
    annotations={"title": "Features nach Attribut suchen", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def swisstopo_find_features(params: FindFeaturesInput) -> str:
    """Sucht Features anhand eines Attributwerts in einem Layer (z.B. Gebäude nach EGID)."""
    return await find_features(params)

@mcp.tool(
    name="swisstopo_get_feature",
    annotations={"title": "Feature-Details abrufen", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def swisstopo_get_feature(params: GetFeatureInput) -> str:
    """Ruft die vollständigen Attribute und Geometrie eines Features per ID ab."""
    return await get_feature(params)
```

- [ ] **Step 6: Write live test for search_layers**

```python
# tests/test_rest_api.py — append
@pytest.mark.live
async def test_live_search_layers():
    from swisstopo_mcp.rest_api import SearchLayersInput, search_layers
    result = await search_layers(SearchLayersInput(query="gebaeude"))
    assert "gebaeude" in result.lower() or "Gebäude" in result
```

- [ ] **Step 7: Commit**

```bash
cd C:/Users/hayal/swisstopo-mcp
git add src/swisstopo_mcp/rest_api.py tests/test_rest_api.py src/swisstopo_mcp/server.py
git commit -m "feat: add REST API module with 4 tools (search, identify, find, get)"
```

---

### Task 5: Implement Geocoding module (2 tools)

**Files:**
- Create: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/geocoding.py`
- Create: `C:/Users/hayal/swisstopo-mcp/tests/test_geocoding.py`
- Modify: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/server.py`

- [ ] **Step 1: Write unit tests for geocoding input models and formatting**

```python
# tests/test_geocoding.py
from __future__ import annotations

import pytest
from pydantic import ValidationError
from swisstopo_mcp.geocoding import (
    GeocodeInput,
    ReverseGeocodeInput,
    format_geocode_results,
)


class TestGeocodeInput:
    def test_valid(self):
        inp = GeocodeInput(search_text="Parkring 4 Zürich")
        assert inp.sr == 4326
        assert inp.limit == 10
        assert inp.origins is None

    def test_with_origins(self):
        inp = GeocodeInput(search_text="8001", origins="zipcode")
        assert inp.origins == "zipcode"

    def test_rejects_short_query(self):
        with pytest.raises(ValidationError):
            GeocodeInput(search_text="a")


class TestReverseGeocodeInput:
    def test_valid(self):
        inp = ReverseGeocodeInput(lat=47.38, lon=8.54)
        assert inp.limit == 5

    def test_out_of_bounds(self):
        with pytest.raises(ValidationError):
            ReverseGeocodeInput(lat=52.0, lon=8.54)


class TestFormatGeocodeResults:
    def test_empty(self):
        result = format_geocode_results([])
        assert "Keine Ergebnisse" in result

    def test_formats_results(self):
        results = [{"attrs": {"label": "Parkring 4, 8002 Zürich", "lat": 47.38, "lon": 8.54, "origin": "address"}}]
        result = format_geocode_results(results)
        assert "Parkring" in result
        assert "47.38" in result
```

- [ ] **Step 2: Run tests — expect ImportError**

```bash
cd C:/Users/hayal/swisstopo-mcp
PYTHONPATH=src pytest tests/test_geocoding.py -v
```

- [ ] **Step 3: Implement geocoding.py**

Create `src/swisstopo_mcp/geocoding.py` with:
- 2 Pydantic input models: `GeocodeInput`, `ReverseGeocodeInput`
- 2 async handlers: `geocode`, `reverse_geocode`
- `format_geocode_results` helper

Key details:
- `geocode`: GET `/rest/services/ech/SearchServer` with `type=locations`, `searchText`, `origins`, `sr`, `limit`, `returnGeometry=true`
- `reverse_geocode`: Same endpoint but with `type=locations`, `origins=address`, `bbox={lon-0.005},{lat-0.005},{lon+0.005},{lat+0.005}` (small bbox ~500m around point), `limit`

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd C:/Users/hayal/swisstopo-mcp
PYTHONPATH=src pytest tests/test_geocoding.py -v
```

- [ ] **Step 5: Register 2 geocoding tools in server.py**

Same pattern as Task 4 Step 5. Import handlers, wrap with `@mcp.tool()`.

- [ ] **Step 6: Write live tests**

```python
@pytest.mark.live
async def test_live_geocode():
    from swisstopo_mcp.geocoding import GeocodeInput, geocode
    result = await geocode(GeocodeInput(search_text="Bundesplatz Bern"))
    assert "Bern" in result or "bern" in result.lower()
```

- [ ] **Step 7: Commit**

```bash
cd C:/Users/hayal/swisstopo-mcp
git add src/swisstopo_mcp/geocoding.py tests/test_geocoding.py src/swisstopo_mcp/server.py
git commit -m "feat: add geocoding module with geocode and reverse_geocode tools"
```

---

## Chunk 3: Height, STAC & WMTS Tools (5 Tools)

### Task 6: Implement Height module (2 tools)

**Files:**
- Create: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/height.py`
- Create: `C:/Users/hayal/swisstopo-mcp/tests/test_height.py`
- Modify: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/server.py`

- [ ] **Step 1: Write unit tests**

```python
# tests/test_height.py
from __future__ import annotations

import pytest
from pydantic import ValidationError
from swisstopo_mcp.height import HeightInput, ElevationProfileInput, format_height_result
from swisstopo_mcp.api_client import parse_coordinate_string


class TestHeightInput:
    def test_valid(self):
        inp = HeightInput(lat=47.38, lon=8.54)
        assert inp.sr == 4326

    def test_out_of_bounds(self):
        with pytest.raises(ValidationError):
            HeightInput(lat=52.0, lon=8.54)


class TestElevationProfileInput:
    def test_valid(self):
        inp = ElevationProfileInput(coordinates="47.38,8.54;47.39,8.55")
        assert inp.nb_points == 200

    def test_rejects_empty(self):
        with pytest.raises(ValidationError):
            ElevationProfileInput(coordinates="")


class TestParseCoordinateString:
    def test_two_points(self):
        pairs = parse_coordinate_string("47.38,8.54;47.39,8.55")
        assert len(pairs) == 2
        assert pairs[0] == (47.38, 8.54)

    def test_three_points(self):
        pairs = parse_coordinate_string("47.38,8.54;47.39,8.55;47.40,8.56")
        assert len(pairs) == 3

    def test_single_point_raises(self):
        with pytest.raises(ValueError, match="Mindestens 2"):
            parse_coordinate_string("47.38,8.54")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            parse_coordinate_string("47.38;8.54")


class TestFormatHeightResult:
    def test_formats_correctly(self):
        result = format_height_result(47.38, 8.54, 408.3)
        assert "408.3" in result
        assert "m ü. M." in result
```

- [ ] **Step 2: Run tests — expect fail**

```bash
cd C:/Users/hayal/swisstopo-mcp
PYTHONPATH=src pytest tests/test_height.py -v
```
Expected: ImportError.

- [ ] **Step 3: Implement height.py**

- `HeightInput`: `lat` (float), `lon` (float), `sr` (int, default 4326)
- `ElevationProfileInput`: `coordinates` (str — "lat1,lon1;lat2,lon2"), `nb_points` (int, default 200), `sr` (int, default 4326)
- `get_height`: GET `/rest/services/height` with `easting={lon}`, `northing={lat}`, `sr=4326` → returns formatted German string
- `elevation_profile`: Parses coordinate string via `parse_coordinate_string()`, builds GeoJSON LineString `{"type":"LineString","coordinates":[[lon1,lat1],[lon2,lat2],...]}`, POST/GET to `/rest/services/profile.json` with `geom=<geojson>&nb_points=<n>&sr=<sr>` → returns Markdown table

- [ ] **Step 4: Run tests — expect pass**

- [ ] **Step 5: Register 2 height tools in server.py**

- [ ] **Step 6: Write live test for get_height**

```python
@pytest.mark.live
async def test_live_get_height():
    from swisstopo_mcp.height import HeightInput, get_height
    result = await get_height(HeightInput(lat=46.9481, lon=7.4474))
    assert "m ü. M." in result or "Höhe" in result
```

- [ ] **Step 7: Commit**

```bash
cd C:/Users/hayal/swisstopo-mcp
git add src/swisstopo_mcp/height.py tests/test_height.py src/swisstopo_mcp/server.py
git commit -m "feat: add height module with get_height and elevation_profile tools"
```

---

### Task 7: Implement STAC module (2 tools)

**Files:**
- Create: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/stac.py`
- Create: `C:/Users/hayal/swisstopo-mcp/tests/test_stac.py`
- Modify: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/server.py`

- [ ] **Step 1: Write unit tests**

```python
# tests/test_stac.py
from __future__ import annotations

import pytest
from pydantic import ValidationError
from swisstopo_mcp.stac import (
    SearchGeodataInput,
    GetCollectionInput,
    format_collection_card,
    format_collection_detail,
)


class TestSearchGeodataInput:
    def test_valid(self):
        inp = SearchGeodataInput(query="swissALTI3D")
        assert inp.limit == 10

    def test_rejects_empty(self):
        with pytest.raises(ValidationError):
            SearchGeodataInput(query="")

    def test_rejects_extra_fields(self):
        with pytest.raises(ValidationError):
            SearchGeodataInput(query="test", unknown="x")


class TestGetCollectionInput:
    def test_valid(self):
        inp = GetCollectionInput(collection_id="ch.swisstopo.swissalti3d")
        assert inp.collection_id == "ch.swisstopo.swissalti3d"


class TestFormatCollectionCard:
    def test_formats_card(self):
        collection = {
            "id": "ch.swisstopo.swissalti3d",
            "title": "swissALTI3D",
            "description": "Digitales Höhenmodell",
        }
        result = format_collection_card(collection)
        assert "swissALTI3D" in result
        assert "ch.swisstopo.swissalti3d" in result

    def test_empty_list(self):
        from swisstopo_mcp.stac import format_search_results
        result = format_search_results([])
        assert "Keine Geodaten" in result or "keine" in result.lower()
```

- [ ] **Step 2: Run tests — expect fail**

```bash
cd C:/Users/hayal/swisstopo-mcp
PYTHONPATH=src pytest tests/test_stac.py -v
```
Expected: ImportError.

- [ ] **Step 3: Implement stac.py**

- `SearchGeodataInput`: `query` (str, required), `limit` (int, default 10)
- `GetCollectionInput`: `collection_id` (str, required)
- `search_geodata`: GET `{STAC_BASE}/collections` → filter by query text in title/description client-side, return Markdown cards
- `get_collection`: GET `{STAC_BASE}/collections/{collection_id}` → return detailed metadata with asset links

- [ ] **Step 4: Run tests — expect pass**

- [ ] **Step 5: Register 2 STAC tools in server.py**

- [ ] **Step 6: Write live test**

```python
@pytest.mark.live
async def test_live_search_geodata():
    from swisstopo_mcp.stac import SearchGeodataInput, search_geodata
    result = await search_geodata(SearchGeodataInput(query="swissALTI3D"))
    assert "alti" in result.lower() or "Höhenmodell" in result
```

- [ ] **Step 7: Commit**

```bash
cd C:/Users/hayal/swisstopo-mcp
git add src/swisstopo_mcp/stac.py tests/test_stac.py src/swisstopo_mcp/server.py
git commit -m "feat: add STAC module with search_geodata and get_collection tools"
```

---

### Task 8: Implement WMTS module (1 tool)

**Files:**
- Create: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/wmts.py`
- Create: `C:/Users/hayal/swisstopo-mcp/tests/test_wmts.py`
- Modify: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/server.py`

- [ ] **Step 1: Write unit tests**

Test `MapUrlInput` validation and `build_map_url` output format.

```python
class TestBuildMapUrl:
    def test_default_url(self):
        from swisstopo_mcp.wmts import MapUrlInput, build_map_url
        result = build_map_url(MapUrlInput(lat=47.38, lon=8.54))
        assert "map.geo.admin.ch" in result
        assert "zoom=" in result

    def test_with_layers(self):
        from swisstopo_mcp.wmts import MapUrlInput, build_map_url
        result = build_map_url(MapUrlInput(lat=47.38, lon=8.54, layers="ch.are.bauzonen"))
        assert "bauzonen" in result
```

- [ ] **Step 2: Run tests — expect fail**

- [ ] **Step 3: Implement wmts.py**

- `MapUrlInput`: `lat` (float), `lon` (float), `zoom` (int, default 8, ge=1, le=13), `layers` (str|None), `lang` (str, default "de")
- `build_map_url`: Pure function (no HTTP call). Converts lat/lon to LV95 via `wgs84_to_lv95()`, builds URL: `https://map.geo.admin.ch/?lang={lang}&E={e:.0f}&N={n:.0f}&zoom={zoom}` + `&layers={layers}` if provided. Returns Markdown with the URL and a description of notable layers.

- [ ] **Step 4: Run tests — expect pass**

- [ ] **Step 5: Register 1 WMTS tool in server.py**

- [ ] **Step 6: Commit**

```bash
cd C:/Users/hayal/swisstopo-mcp
git add src/swisstopo_mcp/wmts.py tests/test_wmts.py src/swisstopo_mcp/server.py
git commit -m "feat: add WMTS module with map_url tool"
```

---

## Chunk 4: ÖREB Tools, CI/CD & Documentation

### Task 9: Implement ÖREB module (2 tools)

**Files:**
- Create: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/oereb.py`
- Create: `C:/Users/hayal/swisstopo-mcp/tests/test_oereb.py`
- Modify: `C:/Users/hayal/swisstopo-mcp/src/swisstopo_mcp/server.py`

- [ ] **Step 1: Write unit tests**

Test `GetEgridInput`, `GetOerebExtractInput`, canton registry lookup, and graceful degradation for unsupported cantons.

```python
class TestGetEgridInput:
    def test_valid(self):
        inp = GetEgridInput(lat=47.38, lon=8.54, canton="ZH")
        assert inp.canton == "ZH"

    def test_canton_required(self):
        with pytest.raises(ValidationError):
            GetEgridInput(lat=47.38, lon=8.54)


class TestCantonRegistry:
    def test_zh_in_default_registry(self):
        from swisstopo_mcp.oereb import get_oereb_endpoint
        url = get_oereb_endpoint("ZH")
        assert url is not None
        assert "zh.ch" in url

    def test_unsupported_canton_returns_none(self):
        from swisstopo_mcp.oereb import get_oereb_endpoint
        assert get_oereb_endpoint("XX") is None
```

- [ ] **Step 2: Run tests — expect fail**

- [ ] **Step 3: Implement oereb.py**

- `OEREB_ENDPOINTS` dict with ZH, BE
- `get_oereb_endpoint(canton)` helper
- `GetEgridInput`: `lat`, `lon`, `canton` (required)
- `GetOerebExtractInput`: `egrid` (required), `canton` (required), `topics` (optional), `lang` (default "de")
- `get_egrid`: Reads `SWISSTOPO_OEREB_CANTONS` env var to filter registry. Calls `{base}/getegrid/json/?EN={e},{n}` where e,n are LV95 coordinates converted from WGS84. Returns EGRID or error.
- `get_oereb_extract`: Calls `{base}/extract/json/?EGRID={egrid}&GEOMETRY=false&LANG={lang}`. Parses restriction topics, returns Markdown list.
- Both tools: check canton against registry first, return helpful error if unsupported.

- [ ] **Step 4: Run tests — expect pass**

- [ ] **Step 5: Register 2 ÖREB tools in server.py**

- [ ] **Step 6: Commit**

```bash
cd C:/Users/hayal/swisstopo-mcp
git add src/swisstopo_mcp/oereb.py tests/test_oereb.py src/swisstopo_mcp/server.py
git commit -m "feat: add ÖREB module with get_egrid and get_oereb_extract tools"
```

---

### Task 10: Add CI/CD workflows

**Files:**
- Create: `C:/Users/hayal/swisstopo-mcp/.github/workflows/ci.yml`
- Create: `C:/Users/hayal/swisstopo-mcp/.github/workflows/publish.yml`

- [ ] **Step 1: Create ci.yml**

```yaml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: ruff check src/ tests/
      - run: pytest tests/ -m "not live" -v
```

- [ ] **Step 2: Create publish.yml**

```yaml
name: Publish to PyPI
on:
  release:
    types: [published]

permissions:
  id-token: write

jobs:
  publish:
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

- [ ] **Step 3: Commit**

```bash
cd C:/Users/hayal/swisstopo-mcp
git add .github/
git commit -m "ci: add CI and PyPI publish workflows"
```

---

### Task 11: Add README.md and README.de.md

**Files:**
- Create: `C:/Users/hayal/swisstopo-mcp/README.md`
- Create: `C:/Users/hayal/swisstopo-mcp/README.de.md`
- Create: `C:/Users/hayal/swisstopo-mcp/CHANGELOG.md`
- Create: `C:/Users/hayal/swisstopo-mcp/CONTRIBUTING.md`

- [ ] **Step 1: Write README.md (English)**

Structure following the existing servers:
- Title + badges
- What it does (13 tools, 6 API families)
- Quick start (pip install, Claude Desktop config)
- Tool overview table
- Environment variables
- Examples (geocode, identify, height)
- Development section (install dev, run tests)
- License

- [ ] **Step 2: Write README.de.md (German)**

Same content in German.

- [ ] **Step 3: Write CHANGELOG.md and CONTRIBUTING.md**

CHANGELOG: Initial v0.1.0 entry.
CONTRIBUTING: Standard contribution guide matching existing servers.

- [ ] **Step 4: Commit**

```bash
cd C:/Users/hayal/swisstopo-mcp
git add README.md README.de.md CHANGELOG.md CONTRIBUTING.md
git commit -m "docs: add README, CHANGELOG, and CONTRIBUTING"
```

---

### Task 12: Run full test suite and final verification

- [ ] **Step 1: Run all unit tests**

```bash
cd C:/Users/hayal/swisstopo-mcp
PYTHONPATH=src pytest tests/ -m "not live" -v
```
Expected: All tests PASS.

- [ ] **Step 2: Run ruff lint**

```bash
cd C:/Users/hayal/swisstopo-mcp
ruff check src/ tests/
```
Expected: No errors.

- [ ] **Step 3: Verify server starts and lists all 13 tools**

```bash
cd C:/Users/hayal/swisstopo-mcp
PYTHONPATH=src python -c "
from swisstopo_mcp.server import mcp
tools = mcp._tool_manager._tools if hasattr(mcp, '_tool_manager') else {}
print(f'Tools registered: {len(tools)}')
for name in sorted(tools): print(f'  - {name}')
"
```
Expected: 13 tools listed.

- [ ] **Step 4: Run live tests (optional, requires network)**

```bash
cd C:/Users/hayal/swisstopo-mcp
PYTHONPATH=src pytest tests/ -m live -v
```

- [ ] **Step 5: Final commit if any fixes were needed**

```bash
cd C:/Users/hayal/swisstopo-mcp
git add -A
git commit -m "fix: final adjustments after full test suite"
```
