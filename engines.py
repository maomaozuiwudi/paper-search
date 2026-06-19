"""PaperSearch v2.0 API Engines"""
import urllib.request, urllib.parse, json, re, ssl, time, queue, threading, hashlib

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE
TIMEOUT = 8
UA = "PaperSearch/2.0 (mailto:user@example.com)"


def _get(url: str, headers: dict = None, cancel_event: threading.Event = None) -> bytes:
    if cancel_event and cancel_event.is_set():
        return None
    req = urllib.request.Request(url, headers=headers or {})
    return urllib.request.urlopen(req, timeout=TIMEOUT, context=_CTX).read()


class OpenAlexClient:
    BASE = "https://api.openalex.org/works"

    @staticmethod
    def search(queries: list, cancel_event: threading.Event, out_queue: queue.Queue):
        for q in queries:
            if cancel_event.is_set(): return
            for page in range(6):
                if cancel_event.is_set(): return
                try:
                    page_param = page + 1
                    params = {"search": q, "per_page": "200", "page": str(page_param), "mailto": "papersearch@toolcat.dev"}
                    url = f"{OpenAlexClient.BASE}?{urllib.parse.urlencode(params)}"
                    data = json.loads(_get(url, {"User-Agent": UA}, cancel_event))
                    count = 0
                    for w in data.get("results", []):
                        if cancel_event.is_set(): return
                        try:
                            title = w.get("title", "")
                            if not title: continue
                            doi = w.get("doi") or ""
                            oid = w.get("id", "")
                            if doi and not doi.startswith("http"):
                                doi = f"https://doi.org/{doi}"
                            abstract = w.get("abstract_inverted_index", {}) or {}
                            if isinstance(abstract, dict):
                                words = []
                                for word, pos in sorted(abstract.items(), key=lambda x: min(x[1]) if x[1] else 0):
                                    words.append(word)
                                abstract = " ".join(words)[:1000]
                            else:
                                abstract = str(abstract)[:1000]
                            authors = ", ".join([a.get("author",{}).get("display_name","") for a in w.get("authorships",[])])[:200]
                            oa = w.get("open_access", {}) or {}
                            out_queue.put(("result", {
                                "title": title, "abstract": abstract, "authors": authors,
                                "year": str(w.get("publication_year","")), "source": "OpenAlex",
                                "url": doi or f"https://openalex.org/works/{oid}",
                                "doi": w.get("doi",""), "source_id": oid, "citations": w.get("cited_by_count",0) or 0,
                                "language": w.get("language") or "en", "tldr": "",
                                "is_oa": oa.get("is_oa", False), "pdf_url": oa.get("oa_url", "") or "",
                            }))
                            count += 1
                        except Exception:
                            continue
                    if count < 200:
                        break
                    time.sleep(0.15)
                except Exception as e:
                    out_queue.put(("log", f"[OpenAlex] {e}"))
                    break
            time.sleep(0.1)


class SemanticScholarClient:
    BASE = "https://api.semanticscholar.org/graph/v1/paper/search"

    @staticmethod
    def search(queries: list, cancel_event: threading.Event, out_queue: queue.Queue):
        fields = "title,abstract,authors,year,url,externalIds,citationCount,tldr,isOpenAccess,openAccessPdf"
        for q in queries:
            if cancel_event.is_set(): return
            for offset in [0, 100, 200]:
                if cancel_event.is_set(): return
                for attempt in range(2):
                    if cancel_event.is_set(): return
                    try:
                        params = {"query": q, "limit": "100", "offset": str(offset), "fields": fields}
                        url = f"{SemanticScholarClient.BASE}?{urllib.parse.urlencode(params)}"
                        data = json.loads(_get(url, {"User-Agent": UA}, cancel_event))
                        items = data.get("data") or []
                        if len(items) < 50:
                            break
                        for p in items:
                            if cancel_event.is_set(): return
                            try:
                                title = p.get("title","")
                                if not title: continue
                                ext = p.get("externalIds") or {}
                                pu = p.get("url") or ext.get("DOI") or ext.get("ArXiv") or ""
                                if pu and not pu.startswith("http"):
                                    pu = f"https://doi.org/{pu}" if "/" not in pu else f"https://arxiv.org/abs/{pu}"
                                authors = ", ".join([a.get("name","") for a in (p.get("authors") or [])])[:200]
                                tldr = (p.get("tldr") or {}).get("text","") or ""
                                is_oa = p.get("isOpenAccess", False)
                                pdf_url = (p.get("openAccessPdf") or {}).get("url", "") or ""
                                out_queue.put(("result", {
                                    "title": title, "abstract": (p.get("abstract") or "")[:1000],
                                    "authors": authors, "year": str(p.get("year") or ""),
                                    "source": "Semantic Scholar",
                                    "url": pu or f"https://api.semanticscholar.org/paper/{p.get('paperId','')}",
                                    "doi": ext.get("DOI",""), "source_id": p.get("paperId",""), "citations": p.get("citationCount",0) or 0,
                                    "language": "en", "tldr": tldr,
                                    "is_oa": is_oa, "pdf_url": pdf_url,
                                }))
                            except Exception:
                                continue
                        break
                    except Exception as e:
                        if attempt < 1:
                            time.sleep(2 ** attempt)
                        else:
                            out_queue.put(("log", f"[Semantic Scholar] {e}"))
                    time.sleep(1.0)


class ArxivClient:
    BASE = "https://export.arxiv.org/api/query"

    @staticmethod
    def search(queries: list, cancel_event: threading.Event, out_queue: queue.Queue):
        for q in queries:
            if cancel_event.is_set(): return
            try:
                url = f"{ArxivClient.BASE}?search_query=all:{urllib.parse.quote(q)}&max_results=200"
                data = _get(url, {"User-Agent": UA}, cancel_event).decode()
                for entry in re.findall(r"<entry>(.*?)</entry>", data, re.DOTALL):
                    if cancel_event.is_set(): return
                    try:
                        t_m = re.search(r"<title>(.*?)</title>", entry)
                        title = t_m.group(1).strip() if t_m else ""
                        if not title: continue
                        a_m = re.search(r"<summary>(.*?)</summary>", entry)
                        abstract = a_m.group(1).strip()[:1000] if a_m else ""
                        y_m = re.search(r"<published>(\d{4})", entry)
                        year = y_m.group(1) if y_m else ""
                        authors = ", ".join(re.findall(r"<name>(.*?)</name>", entry))[:200]
                        id_m = re.search(r"<id>(.*?)</id>", entry)
                        arx_url = id_m.group(1).strip() if id_m else ""
                        arx_id = arx_url.split("/abs/")[-1] if "/abs/" in arx_url else ""
                        pdf_url = f"https://arxiv.org/pdf/{arx_id}" if arx_id else ""
                        out_queue.put(("result", {
                            "title": title, "abstract": abstract, "authors": authors,
                            "year": year, "source": "arXiv", "url": arx_url,
                            "source_id": arx_id,
                            "citations": 0, "language": "en", "tldr": "",
                            "doi": arx_id, "is_oa": True, "pdf_url": pdf_url,
                        }))
                    except Exception:
                        continue
                time.sleep(1.0)
            except Exception as e:
                out_queue.put(("log", f"[arXiv] {e}"))
                time.sleep(1.0)


class CiNiiClient:
    BASE = "https://cir.nii.ac.jp/opensearch/articles"

    @staticmethod
    def search(queries: list, cancel_event: threading.Event, out_queue: queue.Queue):
        for q in queries:
            if cancel_event.is_set(): return
            try:
                url = f"{CiNiiClient.BASE}?q={urllib.parse.quote(q)}&format=json&count=200"
                data = json.loads(_get(url, {"User-Agent": UA}, cancel_event))
                items = data.get("items", data.get("result",{}).get("items", data.get("graph",[])))
                if not items:
                    items = []
                for item in items:
                    if cancel_event.is_set(): return
                    if not isinstance(item, dict): continue
                    try:
                        title = item.get("title") or item.get("dc:title","")
                        if isinstance(title, list):
                            title = next((t.get("@value","") for t in title if isinstance(t,dict) and t.get("@language") in ("ja","en")), str(title[0].get("@value","")) if title else "")
                        title = str(title) if title else ""
                        if not title: continue
                        abstract = item.get("description") or item.get("dc:description","")
                        if isinstance(abstract, list) and abstract:
                            abstract = abstract[0].get("@value","") if isinstance(abstract[0],dict) else str(abstract[0])
                        abstract = str(abstract)[:1000]
                        authors = item.get("creator") or item.get("dc:creator","")
                        if isinstance(authors, list):
                            authors = ", ".join([a.get("@value","") if isinstance(a,dict) else str(a) for a in authors])[:200]
                        authors = str(authors) if authors else ""
                        yr = item.get("date") or item.get("dc:date","")
                        if isinstance(yr, list) and yr:
                            yr = yr[0].get("@value","") if isinstance(yr[0],dict) else str(yr[0])
                        yr = re.search(r"(\d{4})", str(yr)) if yr else None
                        year = yr.group(1) if yr else ""
                        paper_url = item.get("url") or item.get("@id","")
                        ids = item.get("productIdentifier") or item.get("dc:identifier") or []
                        if not paper_url and isinstance(ids, list):
                            for i in ids:
                                if isinstance(i,dict) and "DOI" in str(i.get("@name","")):
                                    paper_url = f"https://doi.org/{i.get('@value','')}"
                                    break
                        out_queue.put(("result", {
                            "title": title, "abstract": abstract, "authors": authors,
                            "year": year, "source": "CiNii",
                            "url": str(paper_url) if paper_url else f"https://cir.nii.ac.jp/crid/{item.get('@id','')}",
                            "doi": "","source_id": item.get("@id",""), "citations": 0, "language": "ja", "tldr": "",
                        }))
                    except Exception:
                        continue
                time.sleep(0.3)
            except Exception as e:
                out_queue.put(("log", f"[CiNii] {e}"))


class CoreClient:
    BASE = "https://api.core.ac.uk/v3/search/works"

    @staticmethod
    def search(queries: list, cancel_event: threading.Event, out_queue: queue.Queue):
        for q in queries:
            if cancel_event.is_set(): return
            try:
                params = {"q": q, "limit": "200"}
                url = f"{CoreClient.BASE}?{urllib.parse.urlencode(params)}"
                data = json.loads(_get(url, {"User-Agent": UA}, cancel_event))
                for w in (data.get("results") or []):
                    if cancel_event.is_set(): return
                    try:
                        title = w.get("title","")
                        if not title: continue
                        dl = w.get("downloadUrl") or ""
                        out_queue.put(("result", {
                            "title": title, "abstract": (w.get("abstract") or "")[:1000],
                            "authors": ", ".join([a.get("name","") for a in (w.get("authors") or [])])[:200],
                            "year": str(w.get("yearPublished","")), "source": "CORE",
                            "url": dl or w.get("sourceUrl",""),
                            "doi": w.get("doi","") or "", "source_id": w.get("id",""), "citations": 0,
                            "language": w.get("language") or "en", "tldr": "",
                            "is_oa": bool(dl), "pdf_url": dl,
                        }))
                    except Exception:
                        continue
                time.sleep(0.5)
            except Exception as e:
                out_queue.put(("log", f"[CORE] {e}"))


class PubMedClient:
    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    @staticmethod
    def search(queries: list, cancel_event: threading.Event, out_queue: queue.Queue):
        for q in queries:
            if cancel_event.is_set(): return
            try:
                url = f"{PubMedClient.BASE}/esearch.fcgi?db=pubmed&term={urllib.parse.quote(q)}&retmax=200&retmode=json"
                data = json.loads(_get(url, {"User-Agent": UA}, cancel_event))
                ids = data.get("esearchresult",{}).get("idlist",[])
                if not ids: continue
                summary_url = f"{PubMedClient.BASE}/esummary.fcgi?db=pubmed&id={','.join(ids[:200])}&retmode=json"
                summary = json.loads(_get(summary_url, {"User-Agent": UA}, cancel_event))
                for pid in ids[:200]:
                    if cancel_event.is_set(): return
                    try:
                        r = summary.get("result",{}).get(pid,{})
                        title = r.get("title","")
                        if not title: continue
                        authors = ", ".join([a.get("name","") for a in r.get("authors",[])])[:200]
                        yr = r.get("pubdate","")[:4]
                        out_queue.put(("result", {
                            "title": title, "abstract": "",
                            "authors": authors, "year": yr, "source": "PubMed",
                            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pid}/",
                            "doi": "","source_id": pid, "citations": 0, "language": "en", "tldr": "",
                        }))
                    except Exception:
                        continue
                time.sleep(0.4)
            except Exception as e:
                out_queue.put(("log", f"[PubMed] {e}"))
                time.sleep(1.0)


class DOAJClient:
    BASE = "https://doaj.org/api/v2/search/articles"

    @staticmethod
    def search(queries: list, cancel_event: threading.Event, out_queue: queue.Queue):
        for q in queries:
            if cancel_event.is_set(): return
            try:
                url = f"{DOAJClient.BASE}/{urllib.parse.quote(q)}?pageSize=200"
                data = json.loads(_get(url, {"User-Agent": UA}, cancel_event))
                for r in (data.get("results") or []):
                    if cancel_event.is_set(): return
                    try:
                        bib = r.get("bibjson",{})
                        title = bib.get("title","")
                        if not title: continue
                        authors = ", ".join([a.get("name","") for a in bib.get("author",[])])[:200]
                        yr = bib.get("year","")
                        link = next((l.get("url","") for l in bib.get("link",[]) if l.get("type")=="fulltext"), "")
                        out_queue.put(("result", {
                            "title": title, "abstract": (bib.get("abstract","") or "")[:1000],
                            "authors": authors, "year": str(yr), "source": "DOAJ",
                            "url": link or f"https://doaj.org/article/{r.get('id','')}",
                            "doi": bib.get("doi","") or "", "source_id": r.get("id",""), "citations": 0,
                            "language": bib.get("language","en") or "en", "tldr": "",
                            "is_oa": True, "pdf_url": link or "",
                        }))
                    except Exception:
                        continue
                time.sleep(0.5)
            except Exception as e:
                out_queue.put(("log", f"[DOAJ] {e}"))


class BaiduScholarClient:
    BASE = "https://xueshu.baidu.com/s"
    _pw_available = None

    @classmethod
    def _has_playwright(cls):
        if cls._pw_available is None:
            try:
                __import__('playwright.sync_api', fromlist=['sync_playwright'])
                cls._pw_available = True
            except ImportError:
                cls._pw_available = False
        return cls._pw_available

    @classmethod
    def search(cls, queries: list, cancel_event: threading.Event, out_queue: queue.Queue):
        if cls._has_playwright():
            cls._search_playwright(queries, cancel_event, out_queue)
        else:
            out_queue.put(("log", "[百度学术] Playwright未安装，跳过(需要浏览器环境)"))

    @classmethod
    def _search_playwright(cls, queries: list, cancel_event: threading.Event, out_queue: queue.Queue):
        import time as _time
        try:
            from playwright.sync_api import sync_playwright as _sync_pw
        except ImportError:
            return

        try:
            with _sync_pw() as p:
                browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="zh-CN"
                )
                page = context.new_page()
                count = 0

                for q in queries[:3]:
                    if cancel_event.is_set(): break
                    try:
                        url = f"https://xueshu.baidu.com/s?wd={urllib.parse.quote(q)}"
                        page.goto(url, timeout=20000, wait_until="domcontentloaded")

                        for _ in range(15):
                            if cancel_event.is_set(): break
                            title = page.title()
                            if "安全验证" not in title and "百度安全验证" not in title:
                                break
                            _time.sleep(1)

                        if "安全验证" in page.title() or "百度安全验证" in page.title():
                            continue

                        page.wait_for_timeout(1500)

                        items = page.evaluate("""() => {
                            const papers = [];
                            document.querySelectorAll('.result-item, [class*="result"]').forEach(el => {
                                const titleEl = el.querySelector('h3 a, .title a, a.title');
                                const t = titleEl ? titleEl.textContent.trim().replace(/<[^>]+>/g, '') : '';
                                if (!t || t.length < 3) return;
                                const absEl = el.querySelector('.abstract, .desc, [class*="abstract"]');
                                const yMatch = el.textContent.match(/(\\d{4})年/);
                                const cMatch = el.textContent.match(/被引(\\d+)/);
                                papers.push({
                                    title: t,
                                    abstract: (absEl ? absEl.textContent.trim() : '').substring(0, 600),
                                    year: yMatch ? yMatch[1] : '',
                                    citations: cMatch ? parseInt(cMatch[1]) : 0,
                                    url: titleEl ? titleEl.href : ''
                                });
                            });
                            return papers;
                        }""")

                        for item in items[:100]:
                            if cancel_event.is_set(): break
                            out_queue.put(("result", {
                                "title": item.get("title", ""),
                                "abstract": item.get("abstract", ""),
                                "authors": "",
                                "year": item.get("year", ""),
                                "source": "百度学术",
                                "url": item.get("url", ""),
                                "doi": "", "source_id": hashlib.sha256(item.get("title","").encode()).hexdigest()[:16],
                                "citations": item.get("citations", 0),
                                "language": "zh",
                                "tldr": "",
                            }))
                            count += 1

                        _time.sleep(0.5)
                    except Exception as e:
                        out_queue.put(("log", f"[百度学术] 查询失败: {e}"))
                        continue

                browser.close()
                if count == 0:
                    out_queue.put(("log", "[百度学术] 搜索完成但未获取到结果(可能被安全验证拦截)"))
        except Exception as e:
            out_queue.put(("log", f"[百度学术] 浏览器启动失败: {e}"))

    @classmethod
    def _search_urllib(cls, queries: list, cancel_event: threading.Event, out_queue: queue.Queue):
        for q in queries:
            if cancel_event.is_set(): return
            try:
                params = {"wd": q, "pn": "0", "tn": "SE_baiduxueshu_c1g0upa"}
                url = f"{cls.BASE}?{urllib.parse.urlencode(params)}"
                html = _get(url, {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, cancel_event).decode(errors='replace')
                if '百度安全验证' in html or len(html) < 3000:
                    continue
                items = re.findall(r'<div class="result[^"]*"[\s\S]*?</div>\s*</div>\s*</div>', html)
                for item in items[:25]:
                    if cancel_event.is_set(): return
                    try:
                        t_m = re.search(r'class="title[^"]*"[^>]*>\s*<a[^>]*>([\s\S]*?)</a>', item)
                        if not t_m: continue
                        title = re.sub(r'<[^>]+>', '', t_m.group(1)).strip()
                        if not title: continue
                        a_m = re.search(r'class="abstract[^"]*"[^>]*>([\s\S]*?)</div>', item)
                        abstract = re.sub(r'<[^>]+>', '', a_m.group(1)).strip()[:1000] if a_m else ""
                        url_m = re.search(r'href="(https?://[^"]+)"', item)
                        paper_url = url_m.group(1) if url_m else ""
                        out_queue.put(("result", {
                            "title": title, "abstract": abstract, "authors": "",
                            "year": "", "source": "百度学术",
                            "url": paper_url, "doi": "", "source_id": hashlib.sha256(title.encode()).hexdigest()[:16],
                            "citations": 0, "language": "zh", "tldr": "",
                        }))
                    except Exception:
                        continue
                time.sleep(0.3)
            except Exception as e:
                out_queue.put(("log", f"[百度学术] {e}"))
