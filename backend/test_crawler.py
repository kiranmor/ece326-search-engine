# Tests for the crawler class
# Use the crawler by feeding it local HTML files via file:// URLs

from pathlib import Path
from crawler import crawler  

def test_direct_file_urls(tmp_path):
    """
    Create two local HTML files:
      - A links to B
      - B links back to A
    Seed the crawler with A's file:// URL and crawl to depth 1.
    Verify titles, descriptions, inverted index, and link graph.
    """

    # Paths for two local HTML files (pytest gives us a temp dir)
    a_path = tmp_path / "a.html"
    b_path = tmp_path / "b.html"

    # Converts paths to absolute URIs that urlopen understands
    a_uri = a_path.as_uri()  
    b_uri = b_path.as_uri()

    # Write tiny HTML pages that link to each other using file:// URIs
    HTML_A = f"""<html><head><title>Page A</title></head>
    <body>
      <h1>Welcome to A</h1>
      <p>Cats and dogs play.</p>
      <a href="{b_uri}">Best Tutorial</a>
    </body></html>"""

    HTML_B = f"""<html><head><title>Page B</title></head>
    <body>
      <h2>About B</h2>
      <p>Fish swim. Cats walk.</p>
      <a href="{a_uri}" title="Back to A">Home</a>
    </body></html>"""

    # Writes to the files
    a_path.write_text(HTML_A, encoding="utf-8")
    b_path.write_text(HTML_B, encoding="utf-8")

    # Seed file with A's URL
    urls_txt = tmp_path / "urls.txt"
    urls_txt.write_text(a_uri + "\n", encoding="utf-8")

    # Run the craewler
    bot = crawler(None, str(urls_txt))
    bot.crawl(depth=1)  # should visit A, discover B, then visit B

    # ---- Basic checks ----

    # There should be two documents in the index
    assert len(bot._document_index) == 2

    # Resolve doc IDs for convenience
    a_id = bot.document_id(a_uri)
    b_id = bot.document_id(b_uri)

    # Titles captured
    assert bot.get_document(a_id)["title"] == "Page A"
    assert bot.get_document(b_id)["title"] == "Page B"

    # Descriptions not empty
    assert bot.get_document(a_id)["description"].strip()
    assert bot.get_document(b_id)["description"].strip()

    # Resolved inverted index: word -> {urls}
    rinv = bot.get_resolved_inverted_index()

    # Content word "cats" should appear in both pages
    assert "cats" in rinv
    assert a_uri in rinv["cats"]
    assert b_uri in rinv["cats"]

    # Anchor text indexing: "best" comes from A's link to B, should map to B
    assert "best" in rinv
    assert b_uri in rinv["best"]

    # Link graph has A -> B and B -> A
    graph = bot.get_link_graph()
    assert b_id in graph.get(a_id, {})
    assert a_id in graph.get(b_id, {})
