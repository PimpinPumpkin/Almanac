"""Polite fetching for registers that only offer a search form.

A Site is one host. It reads the host's robots.txt first and refuses any
path that file disallows (unless the owner has decided otherwise for that
one site), sends the project User-Agent, waits between requests, and
retries a failed request a few times. It does nothing to get past a block:
a 403, a challenge page or a CAPTCHA is the site saying no, always.
"""
import http.cookiejar
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

from evidence import UA

AGENT = "VelaAlmanac"


class Refused(Exception):
    """robots.txt does not allow this path."""


class Site:
    def __init__(self, base, pause=2.0, robots=True):
        """robots=False is for a site whose robots.txt the project's owner has decided not to follow,
        one site at a time, with the reason written in SOURCES.md. Everything else here still applies."""
        self.base = base.rstrip("/")
        self.obey = robots
        self.pause = pause
        self.last = 0.0
        # some lookups keep the search in a session cookie
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.robots = urllib.robotparser.RobotFileParser()
        try:
            req = urllib.request.Request(self.base + "/robots.txt", headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                self.robots.parse(r.read().decode("utf-8", "replace").splitlines())
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                # a robots.txt that is itself forbidden means stay out
                self.robots.parse(["User-agent: *", "Disallow: /"])
            else:
                self.robots.parse([])  # no robots.txt: nothing is disallowed
        except Exception:
            self.robots.parse([])

    def fetch(self, path, form=None, tries=4, timeout=180):
        """GET path, or POST the form to it. Returns bytes."""
        url = urllib.parse.urljoin(self.base + "/", path.lstrip("/"))
        if self.obey and not self.robots.can_fetch(AGENT, url):
            raise Refused(url)
        data = urllib.parse.urlencode(form, doseq=True).encode() if form is not None else None
        for attempt in range(tries):
            wait = self.pause - (time.time() - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
            try:
                req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
                with self.opener.open(req, timeout=timeout) as r:
                    return r.read()
            except urllib.error.HTTPError as e:
                if e.code in (401, 403, 404) or attempt == tries - 1:
                    raise
            except Exception:
                if attempt == tries - 1:
                    raise
            print("retry %s" % url[:90], file=sys.stderr)
            time.sleep(15 * (attempt + 1))
