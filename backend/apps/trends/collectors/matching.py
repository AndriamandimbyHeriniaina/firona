"""Match public trend titles / search terms to curated Product rows.

Whole words only, accent-insensitive: "riz" matches "prix du riz" and
"vary gasy" but not "prize money"; "telephone" matches "Téléphone".

Example:
    product = match_title_to_product("findy tecno", products)
    # (Product(slug="telephone"), "findy") or None — never creates a new article.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from functools import lru_cache

from apps.catalog.models import Product

MIN_TERM_LENGTH = 3
_NON_WORD = re.compile(r"[^\w]+")


def normalize(text: str) -> str:
    """Casefold, strip accents and punctuation, collapse whitespace.

    Example:
        normalize("  Téléphone, Findy! ") == "telephone findy"
    """
    folded = unicodedata.normalize("NFKD", text.casefold())
    bare = "".join(ch for ch in folded if not unicodedata.combining(ch))
    return " ".join(_NON_WORD.sub(" ", bare).split())


@lru_cache(maxsize=512)
def _word_pattern(term: str) -> re.Pattern[str]:
    return re.compile(rf"(?<!\w){re.escape(term)}(?!\w)")


def product_terms(product: Product) -> list[str]:
    """Search strings for one curated article (name, slug, aliases), normalized.

    Example:
        product_terms(phone)  # ["telephone", "findy", "smartphone", "capteur"]
    """
    raw = [product.name, product.slug.replace("-", " ")]
    raw.extend(product.aliases or [])
    terms: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not item or not str(item).strip():
            continue
        term = normalize(str(item))
        if len(term) < MIN_TERM_LENGTH or term in seen:
            continue
        seen.add(term)
        terms.append(term)
    return terms


def title_matches_product(title: str, product: Product) -> str | None:
    """Return the longest term of this product found as whole words in the title.

    A short title that is itself a whole word of a longer alias also matches
    ("vary" → alias "vary gasy").

    Example:
        title_matches_product("prix findy analakely", phone) == "findy"
        title_matches_product("prize money", riz) is None
    """
    haystack = normalize(title)
    if len(haystack) < MIN_TERM_LENGTH:
        return None
    best: str | None = None
    for term in product_terms(product):
        hit = _word_pattern(term).search(haystack) or _word_pattern(haystack).search(term)
        if hit and (best is None or len(term) > len(best)):
            best = term
    return best


def match_title_to_product(
    title: str,
    products: Iterable[Product],
) -> tuple[Product, str] | None:
    """Curated product whose longest matching term fits the title, or None.

    Example:
        match_title_to_product("riz tsena", products)  # (riz, "riz")
    """
    best: tuple[Product, str] | None = None
    for product in products:
        term = title_matches_product(title, product)
        if term and (best is None or len(term) > len(best[1])):
            best = (product, term)
    return best
