import os
import sqlite3
from crawler import crawler
from storage import save_to_db
from pagerank import pagerank

def test_storage(tmp_path):
    db_file = tmp_path / "test_search.db"
    bot = crawler(None, "urls.txt")
    bot.crawl(depth=1)
    pr = pagerank(bot.get_link_graph()).calculate() 
    save_to_db(bot, pr, db_name=db_file)


    con = sqlite3.connect(db_file)
    con = con.cursor()

    for table in ["Lexicon", "Documents", "InvertedIndex", "PageRank", "Links"]:
        con.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        assert con.fetchone() is not None, f"Table {table} should exist in the database."       

    con.close()