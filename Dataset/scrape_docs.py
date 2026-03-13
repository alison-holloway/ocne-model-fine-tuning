"""
scrape_docs.py — Phase 1 of the dataset generation pipeline.

Crawls Oracle CNE Release 2 documentation, extracts content from each page,
splits by heading into chunks, and saves to a JSON file for use by generate_qa.py.

Usage:
    python Dataset/scrape_docs.py
    python Dataset/scrape_docs.py --verbose
    python Dataset/scrape_docs.py --sections concepts,cli --delay 0.5
"""

import argparse
import json
import sys
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://docs.oracle.com/en/operating-systems/olcne/2/"
ALL_SECTIONS = [
    "relnotes",
    "concepts",
    "quickstart",
    "cli",
    "clusters",
    "applications",
    "kubernetes",
    "ockforge",
    "upgrade",
]
USER_AGENT = "ocne-dataset-builder/1.0 (educational use; contact via github)"


def fetch_page(url, session, delay):
    """GET a URL, sleep for delay seconds afterward. Returns HTML text or None."""
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            return resp.text
        else:
            print(f"  [skip] HTTP {resp.status_code}: {url}", file=sys.stderr)
            return None
    except requests.RequestException as e:
        print(f"  [error] {url}: {e}", file=sys.stderr)
        return None
    finally:
        time.sleep(delay)


def extract_main_content(html):
    """Parse HTML and return the <main> tag soup, or None if not found."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.find("main")


def find_next_link(soup, current_url):
    """
    Find the 'Next' navigation link on the page.
    Oracle docs use <link rel="next"> in <head>, or an <a> with rel="next".
    Returns the absolute URL or None.
    """
    # Try <link rel="next"> in head (most reliable)
    link_tag = soup.find("link", rel="next")
    if link_tag and link_tag.get("href"):
        return urljoin(current_url, link_tag["href"])

    # Fallback: <a rel="next">
    a_tag = soup.find("a", rel="next")
    if a_tag and a_tag.get("href"):
        return urljoin(current_url, a_tag["href"])

    # Fallback: navigation anchor with text "Next"
    for a in soup.find_all("a"):
        text = a.get_text(strip=True).lower()
        if text in ("next", "next »", "next page"):
            href = a.get("href")
            if href and not href.startswith("#"):
                return urljoin(current_url, href)

    return None


def get_text_between_headings(tag):
    """
    Collect all text content from siblings until the next heading tag.
    Returns cleaned text string.
    """
    parts = []
    for sibling in tag.next_siblings:
        if sibling.name and sibling.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
            break
        if hasattr(sibling, "get_text"):
            text = sibling.get_text(separator=" ", strip=True)
            if text:
                parts.append(text)
        elif isinstance(sibling, str):
            text = sibling.strip()
            if text:
                parts.append(text)
    return " ".join(parts).strip()


def split_into_chunks(main_soup, page_url, section, min_chunk):
    """
    Walk h1–h4 tags in main content, collect text under each heading as a chunk.
    Returns list of chunk dicts.
    """
    chunks = []
    headings = main_soup.find_all(["h1", "h2", "h3", "h4"])

    for heading in headings:
        heading_text = heading.get_text(separator=" ", strip=True)
        body_text = get_text_between_headings(heading)

        if not body_text or len(body_text) < min_chunk:
            continue

        chunks.append({
            "section": section,
            "page_url": page_url,
            "heading": heading_text,
            "text": body_text,
            "char_count": len(body_text),
        })

    return chunks


def crawl_section(index_url, section, session, delay, min_chunk, verbose):
    """
    Crawl all pages in a section by following next links.
    Returns list of all chunks from the section.
    """
    chunks = []
    visited = set()
    url = index_url

    while url:
        # Normalize URL (strip fragment)
        url = url.split("#")[0]

        if url in visited:
            break
        visited.add(url)

        if verbose:
            print(f"  Fetching: {url}")

        html = fetch_page(url, session, delay)
        if not html:
            break

        soup = BeautifulSoup(html, "html.parser")
        main = extract_main_content(html)

        if main:
            page_chunks = split_into_chunks(main, url, section, min_chunk)
            chunks.extend(page_chunks)
            if verbose:
                print(f"    → {len(page_chunks)} chunks")
        else:
            if verbose:
                print("    → no <main> found, skipping")

        url = find_next_link(soup, url)

        # Stay within this section — don't follow links to other sections
        if url:
            parsed = urlparse(url)
            path = parsed.path
            section_base = urlparse(index_url).path.rsplit("/", 1)[0] + "/"
            if not path.startswith(section_base):
                break

    return chunks


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Oracle CNE Release 2 docs into content chunks.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--output",
        default="Dataset/ocne_chunks.json",
        help="Path to write the chunks JSON file",
    )
    parser.add_argument(
        "--sections",
        default=",".join(ALL_SECTIONS),
        help="Comma-separated list of sections to scrape",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds to sleep between page fetches",
    )
    parser.add_argument(
        "--min-chunk",
        type=int,
        default=200,
        help="Minimum character count to keep a chunk",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each URL as it is fetched",
    )
    args = parser.parse_args()

    sections = [s.strip() for s in args.sections.split(",") if s.strip()]

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    all_chunks = []
    total_pages = 0

    for section in sections:
        index_url = BASE_URL + section + "/"
        print(f"\nSection: {section}  ({index_url})")

        chunks = crawl_section(
            index_url=index_url,
            section=section,
            session=session,
            delay=args.delay,
            min_chunk=args.min_chunk,
            verbose=args.verbose,
        )

        # Count unique pages in this section
        pages_in_section = len({c["page_url"] for c in chunks})
        total_pages += pages_in_section
        all_chunks.extend(chunks)
        print(f"  {pages_in_section} pages, {len(chunks)} chunks")

    print(f"\nTotal: {total_pages} pages, {len(all_chunks)} chunks")
    print(f"Writing to {args.output} ...")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    total_chars = sum(c["char_count"] for c in all_chunks)
    print(f"Done. {total_chars:,} total characters across {len(all_chunks)} chunks.")


if __name__ == "__main__":
    main()
