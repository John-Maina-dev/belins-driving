"""Safe handling of Google Maps embed input for branches.

Admins may paste either a plain embed URL or a full ``<iframe ...>`` snippet.
Only the ``src`` value is ever kept, and only if it is an https Google Maps URL.
Raw admin-pasted HTML is never stored or rendered.
"""
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError

GOOGLE_MAPS_PREFIX = "https://www.google.com/maps"
MAX_EMBED_LENGTH = 2000

# UNVERIFIED defaults for the main branch: staff must confirm the pin is on the
# right building and replace the embed with the exact one from Google Maps.
DEFAULT_MAIN_BRANCH_ADDRESS = "Ouru Power building, Kisii Town, Kisii County"
DEFAULT_MAIN_BRANCH_TOWN = "Kisii"
DEFAULT_MAIN_BRANCH_EMBED = "https://www.google.com/maps?q=Ouru+Power+Kisii&output=embed"

MAP_HELP_TEXT = (
    "Google Maps > Share > Embed a map > copy the link. You may paste the plain link or the whole "
    "iframe code; only the Google Maps address is kept."
)
UNVERIFIED_NOTE = (
    "UNVERIFIED default: the main branch map (Ouru Power, Kisii) is a search-based guess. "
    "Check the pin is on the right building, then replace it with the exact embed from Google Maps."
)

_CONTROL_OR_UNSAFE = re.compile(r"[\x00-\x20\"'<>\\`]")

ERR_NOT_GOOGLE = (
    "Invalid map link. It must be a secure Google Maps link starting with "
    "https://www.google.com/maps (use Google Maps > Share > Embed a map)."
)
ERR_BAD_HTML = (
    "Invalid map code. Paste either the plain Google Maps link or a single Google Maps "
    "<iframe> snippet; scripts and other HTML are not allowed."
)


class _SnippetParser(HTMLParser):
    """Collects tags so we can insist on exactly one <iframe> and nothing else."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.iframe_attrs = None
        self.stray_text = []
        self.depth_inside_iframe = 0

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)
        if tag == 'iframe' and self.iframe_attrs is None:
            self.iframe_attrs = dict(attrs)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_data(self, data):
        if data.strip():
            self.stray_text.append(data)

    def handle_comment(self, data):
        self.tags.append('!comment')

    def handle_decl(self, decl):
        self.tags.append('!decl')

    def handle_pi(self, data):
        self.tags.append('?pi')


def extract_iframe_src(snippet):
    """Return the ``src`` of a single pasted <iframe>, or raise ValidationError."""
    parser = _SnippetParser()
    try:
        parser.feed(snippet)
        parser.close()
    except Exception:
        raise ValidationError(ERR_BAD_HTML)
    if parser.tags != ['iframe'] or parser.stray_text or not parser.iframe_attrs:
        raise ValidationError(ERR_BAD_HTML)
    src = (parser.iframe_attrs.get('src') or '').strip()
    if not src:
        raise ValidationError("The pasted iframe has no src address.")
    return src


def normalize_map_embed_url(value):
    """Validate and clean a pasted map link / iframe. Returns '' for empty input.

    - an <iframe> snippet is reduced to its ``src`` value
    - ``&amp;`` is converted to ``&``
    - the result must be https://www.google.com/maps...
    """
    if value is None:
        return ""
    raw = str(value).strip()
    if not raw:
        return ""
    if len(raw) > 5000:
        raise ValidationError("The pasted map link is too long.")

    if '<' in raw or '>' in raw:
        raw = extract_iframe_src(raw)

    url = raw.replace('&amp;', '&').strip()

    if len(url) > MAX_EMBED_LENGTH:
        raise ValidationError("The map link is too long.")
    if _CONTROL_OR_UNSAFE.search(url):
        raise ValidationError(ERR_NOT_GOOGLE)

    parts = urlsplit(url)
    if (
        parts.scheme != 'https'
        or parts.netloc != 'www.google.com'
        or not (parts.path == '/maps' or parts.path.startswith('/maps/'))
        or not url.startswith(GOOGLE_MAPS_PREFIX)
    ):
        raise ValidationError(ERR_NOT_GOOGLE)
    return url


def is_safe_map_url(value):
    try:
        return bool(normalize_map_embed_url(value)) and normalize_map_embed_url(value) == str(value).strip()
    except ValidationError:
        return False

