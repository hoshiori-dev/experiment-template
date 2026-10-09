#!/usr/bin/env python3
"""Verify that a citation resolves to a real, matching publication.

Looks up a DOI, arXiv id, PubMed id, or title against public scholarly
APIs (Crossref, DOI.org, Semantic Scholar, arXiv, PubMed) and prints the
matched metadata as JSON so the caller can confirm the source exists and
says what the manuscript claims.

Exit codes: 0 = source found; 1 = not found or lookup error (see JSON
"status" and stderr); 2 = bad arguments.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

USER_AGENT = "verify-citation/1.0 (academic-writing skill; +https://github.com/ryan-minato/skills)"
DEFAULT_TIMEOUT = 15


def log(message: str) -> None:
    print(message, file=sys.stderr)


def fetch(url: str, timeout: int) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch_json(url: str, timeout: int) -> dict:
    return json.loads(fetch(url, timeout))


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def title_matches(expected: str, candidate: str) -> bool:
    expected_norm, candidate_norm = normalize(expected), normalize(candidate)
    if not expected_norm or not candidate_norm:
        return False
    if expected_norm in candidate_norm or candidate_norm in expected_norm:
        return True
    expected_tokens, candidate_tokens = (
        set(expected_norm.split()),
        set(candidate_norm.split()),
    )
    overlap = len(expected_tokens & candidate_tokens)
    return overlap / max(len(expected_tokens), 1) >= 0.8


def crossref_metadata(item: dict) -> dict:
    return {
        "title": (item.get("title") or [""])[0],
        "authors": [
            " ".join(part for part in (author.get("given"), author.get("family")) if part)
            for author in item.get("author", [])
        ],
        "year": (item.get("issued", {}).get("date-parts") or [[None]])[0][0],
        "venue": (item.get("container-title") or [""])[0],
        "doi": item.get("DOI"),
        "url": item.get("URL"),
    }


def lookup_doi(doi: str, timeout: int) -> dict | None:
    try:
        data = fetch_json(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}", timeout)
        return {"source": "crossref", "metadata": crossref_metadata(data["message"])}
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
        log(f"Crossref has no record for DOI {doi}; trying DOI.org resolution.")
    try:
        data = fetch_json(f"https://doi.org/api/handles/{urllib.parse.quote(doi)}", timeout)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise
    if data.get("responseCode") != 1:
        return None
    url = next(
        (value["data"]["value"] for value in data.get("values", []) if value.get("type") == "URL"),
        None,
    )
    return {"source": "doi.org", "metadata": {"doi": doi, "url": url}}


def lookup_arxiv(arxiv_id: str, timeout: int) -> dict | None:
    raw = fetch(
        f"https://export.arxiv.org/api/query?id_list={urllib.parse.quote(arxiv_id)}",
        timeout,
    )
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entry = ET.fromstring(raw).find("atom:entry", ns)
    if entry is None or entry.find("atom:id", ns) is None:
        return None
    title_node = entry.find("atom:title", ns)
    if title_node is None or not (title_node.text or "").strip():
        return None
    return {
        "source": "arxiv",
        "metadata": {
            "title": " ".join(title_node.text.split()),
            "authors": [node.text for node in entry.findall("atom:author/atom:name", ns) if node.text],
            "year": (entry.findtext("atom:published", "", ns) or "")[:4] or None,
            "venue": "arXiv",
            "url": entry.findtext("atom:id", "", ns),
        },
    }


def lookup_pmid(pmid: str, timeout: int) -> dict | None:
    data = fetch_json(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        f"?db=pubmed&retmode=json&id={urllib.parse.quote(pmid)}",
        timeout,
    )
    record = data.get("result", {}).get(pmid)
    if not record or record.get("error"):
        return None
    return {
        "source": "pubmed",
        "metadata": {
            "title": record.get("title"),
            "authors": [author.get("name") for author in record.get("authors", [])],
            "year": (record.get("pubdate") or "")[:4] or None,
            "venue": record.get("fulljournalname"),
            "doi": next(
                (aid.get("value") for aid in record.get("articleids", []) if aid.get("idtype") == "doi"),
                None,
            ),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        },
    }


def search_crossref(title: str, author: str | None, year: int | None, timeout: int) -> dict | None:
    params = {"query.bibliographic": title, "rows": "5"}
    if author:
        params["query.author"] = author
    data = fetch_json(f"https://api.crossref.org/works?{urllib.parse.urlencode(params)}", timeout)
    for item in data.get("message", {}).get("items", []):
        metadata = crossref_metadata(item)
        if not title_matches(title, metadata["title"]):
            continue
        if year and metadata["year"] and abs(int(metadata["year"]) - year) > 1:
            continue
        return {"source": "crossref", "metadata": metadata}
    return None


def search_semantic_scholar(title: str, year: int | None, timeout: int) -> dict | None:
    params = {
        "query": title,
        "limit": "5",
        "fields": "title,authors,year,venue,externalIds,url",
    }
    data = fetch_json(
        "https://api.semanticscholar.org/graph/v1/paper/search?" + urllib.parse.urlencode(params),
        timeout,
    )
    for item in data.get("data", []):
        if not title_matches(title, item.get("title", "")):
            continue
        if year and item.get("year") and abs(item["year"] - year) > 1:
            continue
        return {
            "source": "semanticscholar",
            "metadata": {
                "title": item.get("title"),
                "authors": [author.get("name") for author in item.get("authors", [])],
                "year": item.get("year"),
                "venue": item.get("venue"),
                "doi": (item.get("externalIds") or {}).get("DOI"),
                "url": item.get("url"),
            },
        }
    return None


def search_arxiv(title: str, timeout: int) -> dict | None:
    query = urllib.parse.quote(f'ti:"{title}"')
    raw = fetch(
        f"https://export.arxiv.org/api/query?search_query={query}&max_results=5",
        timeout,
    )
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in ET.fromstring(raw).findall("atom:entry", ns):
        candidate = " ".join((entry.findtext("atom:title", "", ns) or "").split())
        if title_matches(title, candidate):
            return {
                "source": "arxiv",
                "metadata": {
                    "title": candidate,
                    "authors": [node.text for node in entry.findall("atom:author/atom:name", ns) if node.text],
                    "year": (entry.findtext("atom:published", "", ns) or "")[:4] or None,
                    "venue": "arXiv",
                    "url": entry.findtext("atom:id", "", ns),
                },
            }
    return None


def search_pubmed(title: str, timeout: int) -> dict | None:
    data = fetch_json(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&retmode=json&term={urllib.parse.quote(title)}&retmax=5",
        timeout,
    )
    for pmid in data.get("esearchresult", {}).get("idlist", []):
        result = lookup_pmid(pmid, timeout)
        if result and title_matches(title, result["metadata"].get("title") or ""):
            return result
    return None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    identifier = parser.add_mutually_exclusive_group(required=True)
    identifier.add_argument("--doi", help="DOI to verify, e.g. 10.1145/3297280.3297641")
    identifier.add_argument("--arxiv", help="arXiv id to verify, e.g. 1706.03762")
    identifier.add_argument("--pmid", help="PubMed id to verify, e.g. 32015508")
    identifier.add_argument("--title", help="Title to search for across sources")
    parser.add_argument("--author", help="Author surname to narrow a --title search")
    parser.add_argument("--year", type=int, help="Publication year (±1 tolerated) for --title")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Per-request timeout in seconds (default {DEFAULT_TIMEOUT})",
    )
    return parser


def resolve(args: argparse.Namespace) -> dict | None:
    if args.doi:
        return lookup_doi(args.doi, args.timeout)
    if args.arxiv:
        return lookup_arxiv(args.arxiv, args.timeout)
    if args.pmid:
        return lookup_pmid(args.pmid, args.timeout)
    searchers = (
        lambda: search_crossref(args.title, args.author, args.year, args.timeout),
        lambda: search_semantic_scholar(args.title, args.year, args.timeout),
        lambda: search_arxiv(args.title, args.timeout),
        lambda: search_pubmed(args.title, args.timeout),
    )
    for searcher in searchers:
        try:
            result = searcher()
        except Exception as error:
            log(f"Search step failed ({error}); trying the next source.")
            continue
        if result:
            return result
    return None


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if (args.author or args.year) and not args.title:
        parser.error("--author/--year only apply together with --title")

    query = {key: value for key, value in vars(args).items() if key != "timeout" and value is not None}
    try:
        result = resolve(args)
    except Exception as error:
        log(
            f"Lookup failed: {error}. Check network access to the citation APIs, "
            "then rerun; the command is read-only and safe to retry."
        )
        print(json.dumps({"query": query, "status": "error", "detail": str(error)}))
        return 1

    if result is None:
        log("No matching record found. Treat the citation as unverified: correct the identifier or drop the reference.")
        print(json.dumps({"query": query, "status": "not_found"}))
        return 1

    print(
        json.dumps(
            {"query": query, "status": "found", **result},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
