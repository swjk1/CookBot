import json
import logging
import re
from html.parser import HTMLParser

import httpx

from backend.models.recipe import Ingredient, Recipe, Step
from backend.pipeline.text_parser import parse_recipe_text

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
}


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

class _TextExtractor(HTMLParser):
    """Strip HTML tags and collect visible text."""
    SKIP_TAGS = {"script", "style", "noscript", "head", "meta", "link"}

    def __init__(self):
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self.parts.append(text)


def _strip_html(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return "\n".join(parser.parts)


def _extract_jsonld_blocks(html: str) -> list[dict]:
    """Return all parsed JSON-LD objects found in the page."""
    blocks = []
    for raw in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.DOTALL | re.IGNORECASE
    ):
        try:
            obj = json.loads(raw.strip())
            # Could be a single object or a @graph array
            if isinstance(obj, list):
                blocks.extend(obj)
            elif obj.get("@graph"):
                blocks.extend(obj["@graph"])
            else:
                blocks.append(obj)
        except json.JSONDecodeError:
            pass
    return blocks


# ---------------------------------------------------------------------------
# ISO 8601 duration → minutes
# ---------------------------------------------------------------------------

def _iso_duration_to_minutes(value: str | None) -> int | None:
    if not value:
        return None
    m = re.search(r'(?:(\d+)H)?(?:(\d+)M)?', value.upper())
    if not m:
        return None
    hours = int(m.group(1) or 0)
    minutes = int(m.group(2) or 0)
    total = hours * 60 + minutes
    return total or None


# ---------------------------------------------------------------------------
# JSON-LD Recipe → Recipe model
# ---------------------------------------------------------------------------

def _parse_instruction(item) -> str:
    if isinstance(item, str):
        return item.strip()
    if isinstance(item, dict):
        return item.get("text", "").strip()
    return str(item)


def _jsonld_to_recipe(data: dict, source_url: str) -> Recipe:
    title = data.get("name") or "Untitled Recipe"

    raw_ingredients = data.get("recipeIngredient", [])
    ingredients = [Ingredient(name=i) for i in raw_ingredients if isinstance(i, str) and i.strip()]

    raw_steps = data.get("recipeInstructions", [])
    # recipeInstructions can be a string, a list of strings, or a list of HowToStep dicts
    if isinstance(raw_steps, str):
        raw_steps = [raw_steps]
    steps = [
        Step(index=i, instruction=_parse_instruction(s))
        for i, s in enumerate(raw_steps)
        if _parse_instruction(s)
    ]

    cuisine = data.get("recipeCuisine")
    if isinstance(cuisine, list):
        cuisine = ", ".join(cuisine)

    tags: list[str] = []
    for field in ("recipeCategory", "keywords"):
        val = data.get(field, "")
        if isinstance(val, list):
            tags.extend(val)
        elif isinstance(val, str) and val:
            tags.extend([t.strip() for t in re.split(r"[,;]", val) if t.strip()])

    raw_yield = data.get("recipeYield")
    if isinstance(raw_yield, list):
        # Pick the longest string — usually the most descriptive (e.g. "8 to 10 servings" vs "8")
        raw_yield = max((str(v).strip() for v in raw_yield if v), key=len, default=None)
    servings = str(raw_yield or "").strip() or None

    return Recipe(
        title=title,
        description=data.get("description"),
        servings=servings,
        prep_time_minutes=_iso_duration_to_minutes(data.get("prepTime")),
        cook_time_minutes=_iso_duration_to_minutes(data.get("cookTime")),
        cuisine=cuisine or None,
        tags=tags,
        ingredients=ingredients,
        steps=steps,
        source_url=source_url,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def scrape_recipe_url(url: str) -> Recipe:
    """Fetch a recipe webpage and return a structured Recipe."""
    logger.info("Scraping recipe URL: %s", url)

    async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True, timeout=20) as client:
        response = await client.get(url)
        response.raise_for_status()
        html = response.text

    # 1. Try JSON-LD structured data (most recipe sites support this)
    for block in _extract_jsonld_blocks(html):
        rtype = block.get("@type", "")
        if isinstance(rtype, list):
            rtype = " ".join(rtype)
        if "Recipe" in rtype:
            logger.info("Found JSON-LD Recipe schema — using structured extraction")
            recipe = _jsonld_to_recipe(block, source_url=url)
            if recipe.steps:
                return recipe
            logger.info("JSON-LD had no steps, falling back to text extraction")
            break

    # 2. Fall back: strip HTML and run through the LLM text parser
    logger.info("No usable JSON-LD found — falling back to text extraction")
    text = _strip_html(html)
    # Trim to avoid token overflow — recipe content is usually near the top
    return await parse_recipe_text(text[:40_000], source_url=url)
