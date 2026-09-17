from __future__ import annotations
from typing import Any
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from bs4 import BeautifulSoup


def fetch_url_text(url: str, timeout: int = 15) -> dict[str, Any]:
    """Fetch a public HTML page and return readable text. No claim is made about video/transcript availability."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("source_url must use http or https")
    req = Request(url, headers={"User-Agent": "NahaLabs-Reactivate/0.16 (+public-source-ingestion)"})
    with urlopen(req, timeout=timeout) as response:
        content_type = (response.headers.get("content-type") or "").lower()
        raw = response.read(2_000_000)
    if "html" not in content_type and not raw.lstrip().startswith(b"<"):
        return {"url": url, "content_type": content_type, "text": "", "status": "UNSUPPORTED_CONTENT"}
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg"]):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
    return {"url": url, "content_type": content_type, "title": title, "text": text, "status": "FETCHED" if text else "EMPTY"}
