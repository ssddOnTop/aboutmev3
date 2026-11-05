#!/usr/bin/env python3
"""Dependency-free checks: python3 -B -m unittest discover -s scripts -p 'test_*.py'."""

from html import escape
from html.parser import HTMLParser
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

from build import ROOT, load_posts, post_url, render


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.h1_count = 0
        self.main_count = 0
        self.script_count = 0
        self.canonical = []
        self.year_ids = []
        self.images = []
        self.entry_links = []
        self.summary_count = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
            if attrs["id"].startswith("year-"):
                self.year_ids.append(int(attrs["id"][5:]))
        if tag == "h1":
            self.h1_count += 1
        if tag == "main":
            self.main_count += 1
        if tag == "script":
            self.script_count += 1
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical.append(attrs["href"])
        if tag == "img":
            self.images.append(attrs)
        if tag == "a" and attrs.get("class") == "entry-title":
            self.entry_links.append(attrs["href"])
        if tag == "p" and attrs.get("class") == "entry-summary":
            self.summary_count += 1
        for attr in ("href", "src"):
            if attr in attrs:
                self.links.append(attrs[attr])


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = render()
        cls.posts = load_posts()
        cls.docs = {name: Document(text) for name, text in cls.pages.items()}

    def test_shared_typography_and_header_are_preserved(self):
        for name, doc in self.docs.items():
            with self.subTest(page=name):
                self.assertIn("/assets/css/base.css", doc.links)
                self.assertNotIn("/assets/css/notebook.css", doc.links)
                self.assertTrue({"left", "center", "right"}.issubset(doc.ids))
                self.assertNotIn("Simple Space, Beyond Base 2", self.pages[name])
                if name == "index.html":
                    self.assertNotIn("<header>", self.pages[name])
                    self.assertEqual(self.pages[name].count('class="social-links"'), 1)
                    self.assertIn("https://github.com/ssddOnTop", doc.links)
                    self.assertIn("https://www.linkedin.com/in/ssdddev", doc.links)
                else:
                    header = self.pages[name].split("<header>", 1)[1].split("</header>", 1)[0]
                    self.assertNotIn('class="social-links"', header)
                    self.assertIn('<a href="/">Home</a>', header)

    def test_generated_pages_are_current(self):
        for name, text in self.pages.items():
            with self.subTest(page=name):
                self.assertEqual((ROOT / name).read_text(), text)

    def test_unique_ids_and_accessible_structure(self):
        for name, doc in self.docs.items():
            with self.subTest(page=name):
                self.assertEqual(len(doc.ids), len(set(doc.ids)))
                self.assertEqual(doc.h1_count, 1)
                self.assertEqual(doc.main_count, 1)
                self.assertEqual(doc.script_count, 0, "Pages should work without JavaScript")
                self.assertEqual(len(doc.canonical), 1)
                for image in doc.images:
                    self.assertIn("alt", image)
                    self.assertIn("width", image)
                    self.assertIn("height", image)

    def test_local_routes_assets_and_fragments(self):
        for name, doc in self.docs.items():
            for href in doc.links:
                link = urlsplit(href)
                if link.scheme or link.netloc:
                    continue
                with self.subTest(page=name, link=href):
                    if not link.path:
                        target = ROOT / name
                    elif link.path.startswith("/"):
                        target = ROOT / unquote(link.path.lstrip("/"))
                    else:
                        target = (ROOT / name).parent / unquote(link.path)
                    if target.is_dir():
                        target /= "index.html"
                    self.assertTrue(target.is_file(), f"Missing local target: {href}")
                    if link.fragment:
                        destination = Document(target.read_text())
                        self.assertIn(unquote(link.fragment), destination.ids)

    def test_year_order_and_every_post_in_both_indexes(self):
        years = sorted({p["year"] for p in self.posts}, reverse=True)
        for name in ("index.html", "posts/index.html"):
            doc = self.docs[name]
            self.assertEqual(doc.year_ids, years)
            for post in self.posts:
                if name == "index.html" and post.get("home"):
                    self.assertNotIn(post_url(post), doc.links)
                else:
                    self.assertIn(post_url(post), doc.links)
                target = "index.html" if post.get("home") else f"posts/{post['slug']}/index.html"
                self.assertIn(target, self.pages)

    def test_original_articles_remain_linked(self):
        links = {link for doc in self.docs.values() for link in doc.links}
        for slug in ("taming-dependency-hell-in-async-rust", "building-async-jsonl", "how-i-won-2k-hackathon-rust"):
            self.assertIn(f"https://blog.ssdd.dev/{slug}", links)

    def test_legacy_home_fragments_remain(self):
        self.assertTrue({"blog", "achievements", "selected-heading", "timeline-heading", "timeline"}.issubset(self.docs["index.html"].ids))

    def test_entries_appear_once_with_no_favorites_or_categories(self):
        self.assertFalse(any("featured" in post for post in self.posts))
        for name in ("index.html", "posts/index.html"):
            expected = [post_url(post) for post in self.posts if name != "index.html" or not post.get("home")]
            self.assertEqual(self.docs[name].entry_links, expected)
            self.assertEqual(self.docs[name].summary_count, len(expected))
            for removed in ('class="selected-list"', 'class="tags"', 'class="year-intro"', '<a class="card"'):
                self.assertNotIn(removed, self.pages[name])

    def test_post_years_and_canonical_routes(self):
        for post in self.posts:
            name = "index.html" if post.get("home") else f"posts/{post['slug']}/index.html"
            self.assertEqual(self.docs[name].canonical, [f"https://www.ssdd.dev{post_url(post)}"])
            if not post.get("home"):
                self.assertIn(f'<span class="post-year">{post["year"]}</span>', self.pages[name])
                self.assertIn(f"/#year-{post['year']}", self.docs[name].links)

    def test_homepage_is_an_article_with_one_canonical_home(self):
        home = next(post for post in self.posts if post.get("home"))
        self.assertIn('<article class="home-post"', self.pages["index.html"])
        self.assertIn('<meta property="og:type" content="article">', self.pages["index.html"])
        self.assertIn(f'<h1 id="home-title">{escape(home["title"])}</h1>', self.pages["index.html"])
        entry = f'<a class="entry-title" href="/">{escape(home["title"])}</a>'
        self.assertIn(entry, self.pages["posts/index.html"])
        self.assertNotIn(entry, self.pages["index.html"], "The homepage should not recommend itself")
        self.assertNotIn(f"posts/{home['slug']}/index.html", self.pages)
        for section in home.get("sections", []):
            self.assertIn(f"note-{section['id']}", self.docs["index.html"].ids)
        self.assertIn("/about/", self.docs["index.html"].links)
        self.assertIn("/posts/", self.docs["index.html"].links)

    def test_homepage_has_one_compact_portrait(self):
        images = self.docs["index.html"].images
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["src"], "/assets/imgs/me_simple.png")
        self.assertEqual(images[0]["width"], "112")
        self.assertEqual(images[0]["height"], "112")
        self.assertIn('class="profile-email"', self.pages["index.html"])
        self.assertNotIn("stackoverflow.com", self.pages["index.html"])
        self.assertIn("Sandipsinh Rathod", images[0]["alt"])
        self.assertIn('class="post-heading home-heading"', self.pages["index.html"])

    def test_homepage_introduces_the_person_before_the_work(self):
        home = next(post for post in self.posts if post.get("home"))
        html = self.pages["index.html"]
        self.assertIn("Sandipsinh Rathod", home["title"])
        self.assertIn("backend systems", home["paragraphs"][0])
        for paragraph in home["paragraphs"]:
            self.assertLess(html.index(escape(paragraph)), html.index('id="timeline"'))
        self.assertNotIn('id="note-one-format"', html)
        transition = escape(home["timeline_intro"])
        self.assertEqual(html.count(transition), 1)
        self.assertLess(html.index(transition), html.index('id="year-'))
        self.assertNotIn('class="year-nav"', html)
        self.assertNotIn('class="section-heading"', html)

    def test_site_design_essay_is_a_separate_post(self):
        name = "posts/why-this-site-uses-posts/index.html"
        self.assertIn(name, self.pages)
        self.assertIn('id="note-one-format"', self.pages[name])
        self.assertIn("/posts/why-this-site-uses-posts/", self.docs["posts/index.html"].links)
        self.assertIn("https://swtch.com/~rsc/", self.docs[name].links)
        self.assertIn("I got inspired by", self.pages[name])
        self.assertNotIn("Read the source", self.pages[name])

    def test_intro_needs_a_transition_into_the_timeline(self):
        posts = copy.deepcopy(self.posts)
        home = next(post for post in posts if post.get("home"))
        home["timeline_intro"] = ""
        with patch.object(Path, "read_text", return_value=json.dumps(posts)):
            with self.assertRaisesRegex(ValueError, "transition"):
                load_posts()

    def test_copyright_footer_stays_removed(self):
        for html in self.pages.values():
            self.assertNotIn("<footer", html)
            self.assertNotIn("© 2026", html)

    def test_homepage_routing_rejects_missing_or_multiple_homes(self):
        for count in (0, 2):
            posts = copy.deepcopy(self.posts)
            for index, post in enumerate(posts):
                post["home"] = index < count
            with self.subTest(home_count=count), patch.object(Path, "read_text", return_value=json.dumps(posts)):
                with self.assertRaisesRegex(ValueError, "Exactly one homepage"):
                    load_posts()


if __name__ == "__main__":
    unittest.main()
