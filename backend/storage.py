import os
import sqlite3 as lite


def save_to_db(bot, pageranks, db_name=None):

    db_name = db_name or os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend")), "search.db")
    con = lite.connect(db_name)
    print("Connected to", db_name)
    cur = con.cursor()

    cur.execute("""
                CREATE TABLE IF NOT EXISTS Lexicon (
                word_id INTEGER PRIMARY KEY, 
                WORD TEXT   
                )
                """)
    cur.execute("""
                CREATE TABLE IF NOT EXISTS Documents (
                doc_id INTEGER PRIMARY KEY, 
                url TEXT, 
                title TEXT, 
                description TEXT
                )
                """)
    cur.execute("""
                CREATE TABLE IF NOT EXISTS InvertedIndex (
                word_id INTEGER, 
                doc_id INTEGER
                )
                """)
    cur.execute("""
                CREATE TABLE IF NOT EXISTS PageRank (
                doc_id INTEGER, 
                score REAL 
                )
                """)
    cur.execute("""
                CREATE TABLE IF NOT EXISTS Links (
                from_doc_id INTEGER, 
                to_doc_id INTEGER, 
                count INTEGER
                )
                """)


    for word_id, word in bot.get_lexicon().items():
        cur.execute("INSERT OR IGNORE INTO Lexicon (word_id, WORD) VALUES (?, ?)", (word_id, word)) 

    for doc_id, doc in bot._document_index.items():
        cur.execute("INSERT OR IGNORE INTO Documents (doc_id, url, title, description) VALUES (?, ?, ?, ?)", 
                    (doc_id, doc['url'], doc.get('title', ''), doc.get('description', '')))
        
    for word_id, doc_ids in bot.get_inverted_index().items():
        for doc_id in doc_ids:
            cur.execute("INSERT INTO InvertedIndex (word_id, doc_id) VALUES (?, ?)", (word_id, doc_id))
            
    for doc_id, score in pageranks.items():
        cur.execute("INSERT INTO PageRank (doc_id, score) VALUES (?, ?)", (doc_id, score))
        
    for from_doc_id, to_docs in bot.get_link_graph().items():
        for to_doc_id, count in to_docs.items():
            cur.execute("INSERT INTO Links (from_doc_id, to_doc_id, count) VALUES (?, ?, ?)", 
                    (from_doc_id, to_doc_id, count))   
            
    print("Data has been saved to the database.")        
    con.commit()
    con.close()
