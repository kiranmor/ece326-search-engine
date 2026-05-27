# Copyright (C) 2011 by Peter Goodman
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


# For Lab 1: All edits to the crawler class are marked with "Implementation #"
# comments. There are 12 such changes made

import urllib3
from urllib.parse import urlparse, urldefrag, urljoin
from urllib.request import urlopen
from bs4 import BeautifulSoup, Tag
from collections import defaultdict
import re
import ssl


def attr(elem, attr):
    """An html attribute from an html element. E.g. <a href="">, then
    attr(elem, "href") will get the href or an empty string."""
    try:
        return elem[attr]
    except:
        return ""


WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')


class crawler(object):
    """Represents 'Googlebot'. Populates a database by crawling and indexing
    a subset of the Internet.

    This crawler keeps track of font sizes and makes it simpler to manage word
    ids and document ids."""

    def __init__(self, db_conn, url_file):
        """Initialize the crawler with a connection to the database to populate
        and with the file containing the list of seed URLs to begin indexing."""
        self._url_queue = []
        self._doc_id_cache = {} # url -> doc_id
        self._word_id_cache = {} # word -> word_id


        # Implementation 1: Backend state 
        self._lexicon = {} # Lexicon: id -> word 
        self._document_index = {}  # Document index: id -> {"url","title","description"}
        self._inverted_index = defaultdict(set) # Inverted index: word_id -> set(doc_id)
        self._link_graph = defaultdict(lambda: defaultdict(int)) # Link graph : from_doc_id -> {to_doc_id: count}
    

        # functions to call when entering and exiting specific tags
        self._enter = defaultdict(lambda *a, **ka: self._visit_ignore)
        self._exit = defaultdict(lambda *a, **ka: self._visit_ignore)

        # add a link to our graph, and indexing info to the related page
        self._enter['a'] = self._visit_a

        # record the currently indexed document's title an increase
        # the font size
        def visit_title(*args, **kargs):
            self._visit_title(*args, **kargs)
            self._increase_font_factor(7)(*args, **kargs)

        # increase the font size when we enter these tags
        self._enter['b'] = self._increase_font_factor(2)
        self._enter['strong'] = self._increase_font_factor(2)
        self._enter['i'] = self._increase_font_factor(1)
        self._enter['em'] = self._increase_font_factor(1)
        self._enter['h1'] = self._increase_font_factor(7)
        self._enter['h2'] = self._increase_font_factor(6)
        self._enter['h3'] = self._increase_font_factor(5)
        self._enter['h4'] = self._increase_font_factor(4)
        self._enter['h5'] = self._increase_font_factor(3)
        self._enter['title'] = visit_title

        # decrease the font size when we exit these tags
        self._exit['b'] = self._increase_font_factor(-2)
        self._exit['strong'] = self._increase_font_factor(-2)
        self._exit['i'] = self._increase_font_factor(-1)
        self._exit['em'] = self._increase_font_factor(-1)
        self._exit['h1'] = self._increase_font_factor(-7)
        self._exit['h2'] = self._increase_font_factor(-6)
        self._exit['h3'] = self._increase_font_factor(-5)
        self._exit['h4'] = self._increase_font_factor(-4)
        self._exit['h5'] = self._increase_font_factor(-3)
        self._exit['title'] = self._increase_font_factor(-7)

        # never go in and parse these tags
        self._ignored_tags = {'meta', 'script', 'link', 'meta', 'embed', 'iframe', 'frame', 'noscript', 'object', 'svg',
                              'canvas', 'applet', 'frameset', 'textarea', 'style', 'area', 'map', 'base', 'basefont',
                              'param'}

        # set of words to ignore
        self._ignored_words = {'', 'the', 'of', 'at', 'on', 'in', 'is', 'it', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
                               'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
                               'and', 'or'}

        # TODO remove me in real version
        self._mock_next_doc_id = 1
        self._mock_next_word_id = 1

        # keep track of some info about the page we are currently parsing
        self._curr_depth = 0
        self._curr_url = ""
        self._curr_doc_id = 0
        self._font_size = 0
        self._curr_words = None

         # Implementation 2: Extra i]nformation for the page state for title/description
        self._curr_title = ""
        self._curr_text_lines = []  # collect raw lines to build a short description


        # get all urls into the queue
        try:
            with open(url_file, 'r') as f:
                for line in f:
                    self._url_queue.append((self._fix_url(line.strip(), ""), 0))
        except IOError:
            pass

    # TODO remove me in real version
    def _mock_insert_document(self, url):
        """A function that pretends to insert a url into a document db table
        and then returns that newly inserted document's id."""
        ret_id = self._mock_next_doc_id
        self._mock_next_doc_id += 1
        return ret_id

    # TODO remove me in real version
    def _mock_insert_word(self, word):
        """A function that pretends to inster a word into the lexicon db table
        and then returns that newly inserted word's id."""
        ret_id = self._mock_next_word_id
        self._mock_next_word_id += 1
        return ret_id

    def word_id(self, word):
        """Get the word id of some specific word."""
        if word in self._word_id_cache:
            return self._word_id_cache[word]

        # Implementation 3: Maintain lexicon and cache
        word_id = self._mock_insert_word(word)
        self._word_id_cache[word] = word_id
        self._lexicon[word_id] = word
        return word_id

    def document_id(self, url):
        """Get the document id for some url."""
        if url in self._doc_id_cache:
            return self._doc_id_cache[url]
        
        # Implementation 4: Allocate doc id and create a temp entry in document index
        doc_id = self._mock_insert_document(url)
        self._doc_id_cache[url] = doc_id
        self._document_index[doc_id] = {"url": url, "title": "", "description": ""}
        return doc_id

    def _fix_url(self, curr_url, rel):
        """Given a url and either something relative to that url or another url,
        get a properly parsed url."""

        rel_l = rel.lower()
        if rel_l.startswith("http://") or rel_l.startswith("https://"):
            curr_url, rel = rel, ""

        # compute the new url based on import
        curr_url = urldefrag(curr_url)[0]
        parsed_url = urlparse(curr_url)
        return urljoin(parsed_url.geturl(), rel)

    def add_link(self, from_doc_id, to_doc_id):
        """Add a link into the database, or increase the number of links between
        two pages in the database."""
        # Implementation 5: Record links in link graph
        if from_doc_id and to_doc_id and from_doc_id != to_doc_id:
            self._link_graph[from_doc_id][to_doc_id] += 1

    def _visit_title(self, elem):
        """Called when visiting the <title> tag."""
        title_text = self._text_of(elem).strip()
        print("document title=" + repr(title_text))

        # Implementation 6: Store page title in document index
        self._curr_title = title_text # update the current title
        if self._curr_doc_id in self._document_index:
            self._document_index[self._curr_doc_id]["title"] = title_text

    def _visit_a(self, elem):
        """Called when visiting <a> tags."""

        dest_url = self._fix_url(self._curr_url, attr(elem, "href"))

        # print "href="+repr(dest_url), \
        #      "title="+repr(attr(elem,"title")), \
        #      "alt="+repr(attr(elem,"alt")), \
        #      "text="+repr(self._text_of(elem))

        # add the just found URL to the url queue
        self._url_queue.append((dest_url, self._curr_depth))

        # add a link entry into the database from the current document to the
        # other document
        self.add_link(self._curr_doc_id, self.document_id(dest_url))

        # Implementation 7: add title/alt/text to index for destination url
        dest_doc_id = self.document_id(dest_url)  # cached; cheap if already created
        anchor_sources = [
            attr(elem, "title"),
            attr(elem, "alt"),
            self._text_of(elem)              # visible anchor text
        ]
        parts = []
        for s in anchor_sources:
            if s:                      # skip null or ""
                parts.append(s)
        anchor_text = " ".join(parts).lower().strip()
        if anchor_text:
            seen_wids = set()                # avoid duplicate (word, dest_doc) adds from this one anchor
            for w in WORD_SEPARATORS.split(anchor_text):
                w = w.strip()
                if not w or w in self._ignored_words: # if null or needs to be ginored thqn skip
                    continue
                wid = self.word_id(w)
                if wid in seen_wids: # if duplicate word for this anchor then skip
                    continue
                self._inverted_index[wid].add(dest_doc_id)  # otherwisee add to inverted index
                seen_wids.add(wid)

    def _add_words_to_document(self):

        # Implementation 8: Build the inverted index, and compute description

        seen_word_ids = set()         # no duplicate words as we only care if word appears in document
        for wid, _font in self._curr_words:
            if wid in seen_word_ids:
                continue
            self._inverted_index[wid].add(self._curr_doc_id)
            seen_word_ids.add(wid)

        # Short description as its recommended in lab by first ~3 non-empty lines collected 
        non_empty = [ln.strip() for ln in self._curr_text_lines if (ln or "").strip()] # Filter out empty/whitespace lines
        desc = " ".join(non_empty[:3]) # Take first 3 and join
        if self._curr_doc_id in self._document_index:
            self._document_index[self._curr_doc_id]["description"] = desc # update description

        print("    num words=" + str(len(self._curr_words)))

    def _increase_font_factor(self, factor):
        """Increade/decrease the current font size."""

        def increase_it(elem):
            self._font_size += factor

        return increase_it

    def _visit_ignore(self, elem):
        """Ignore visiting this type of tag"""
        pass

    def _add_text(self, elem):
        """Add some text to the document. This records word ids and word font sizes
        into the self._curr_words list for later processing."""
        
        # Implementation 9: Get the raw text and keep lines for description for document short description
        raw = (elem.string or "").strip()
        if raw:
            self._curr_text_lines.append(raw)

        words = WORD_SEPARATORS.split(elem.string.lower())
        for word in words:
            word = word.strip()
            if word in self._ignored_words:
                continue
            self._curr_words.append((self.word_id(word), self._font_size))

    def _text_of(self, elem):
        """Get the text inside some element without any tags."""
        if isinstance(elem, Tag):
            text = []
            for sub_elem in elem:
                text.append(self._text_of(sub_elem))

            return " ".join(text)
        else:
            return elem.string

    def _index_document(self, soup):
        """Traverse the document in depth-first order and call functions when entering
        and leaving tags. When we come accross some text, add it into the index. This
        handles ignoring tags that we have no business looking at."""

        class DummyTag(object):
            next = False
            name = ''

        class NextTag(object):
            def __init__(self, obj):
                self.next = obj

        tag = soup.html
        stack = [DummyTag(), soup.html]

        while tag and tag.next:
            tag = tag.next

            # html tag
            if isinstance(tag, Tag):

                if tag.parent != stack[-1]:
                    self._exit[stack[-1].name.lower()](stack[-1])
                    stack.pop()

                tag_name = tag.name.lower()

                # ignore this tag and everything in it
                if tag_name in self._ignored_tags:
                    if tag.nextSibling:
                        tag = NextTag(tag.nextSibling)
                    else:
                        self._exit[stack[-1].name.lower()](stack[-1])
                        stack.pop()
                        tag = NextTag(tag.parent.nextSibling)

                    continue

                # enter the tag
                self._enter[tag_name](tag)
                stack.append(tag)

            # text (text, cdata, comments, etc.)
            else:
                self._add_text(tag)

        # Implementation 10: Check for exit any remaining open tags 
        while len(stack) > 1:
            self._exit[stack[-1].name.lower()](stack[-1])
            stack.pop()

    def crawl(self, depth=2, timeout=3):
        """Crawl the web!"""
        seen = set()

        while len(self._url_queue):

            url, depth_ = self._url_queue.pop()

            # skip this url; it's too deep
            if depth_ > depth:
                continue

            doc_id = self.document_id(url)

            # we've already seen this document
            if doc_id in seen:
                continue

            seen.add(doc_id)  # mark this document as haven't been visited

            socket = None
            
            try:
                # Create SSL context that doesn't verify certs (safe for local coursework use)
                ssl_ctx = ssl._create_unverified_context()
                socket = urlopen(url, timeout=timeout, context=ssl_ctx)

                soup = BeautifulSoup(socket.read(), features="html.parser")

                self._curr_depth = depth_ + 1
                self._curr_url = url
                self._curr_doc_id = doc_id
                self._font_size = 0
                self._curr_words = []

                # Implementation 11: Reset per-page state for the line description features too
                self._curr_title = ""
                self._curr_text_lines = []

                self._index_document(soup)
                self._add_words_to_document()
                print("    url=" + repr(self._curr_url))

            except Exception as e:
                print(e)
                pass
            finally:
                if socket:
                    socket.close()

    # Implementation 12: Public getters required

    def get_inverted_index(self):
        """Return {word_id: sset of docs id}"""
        return dict(self._inverted_index)

    def get_resolved_inverted_index(self):
        """Return {word_string: set of url strings} with ids resolved"""
        """Meaning each word_id in the lexicon to get the word string, and each doc_id in the document index to get the URL string"""
        resolved = {}
        for wid, doc_set in self._inverted_index.items():
            word = self._lexicon.get(wid)
            if word is None:
                continue
            urls = set()
            for did in doc_set:
                entry = self._document_index.get(did)
                if entry:
                    urls.add(entry["url"])

            resolved[word] = urls
        return resolved

    def get_document(self, doc_id):
        """Return {'url','title','description'} for a document id as recommnedned in the lab"""
        return self._document_index.get(doc_id)

    def get_lexicon(self):
        """Return {word_id: word}"""
        return dict(self._lexicon)

    def get_link_graph(self):
        """Return links with multiplicity: {from: {to: count}}"""
        return {src: dict(dests) for src, dests in self._link_graph.items()}


if __name__ == "__main__":
    bot = crawler(None, "urls.txt")
    bot.crawl(depth=1)
