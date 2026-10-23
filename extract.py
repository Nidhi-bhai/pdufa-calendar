import re, json, sys, time, html, urllib.request, urllib.parse, datetime as dt
UA = {"User-Agent": "PDUFA-Tracker research contact nidhi69n@gmail.com"}
MONTHS = "January|February|March|April|May|June|July|August|September|October|November|December"
DATE_RE = re.compile(rf"((?:{MONTHS})\s+\d{{1,2}},\s+20\d\d)|((?:first|second|third|fourth|1st|2nd|3rd|4th)\s+quarter\s+(?:of\s+)?20\d\d|(?:Q[1-4]|[1-4]Q)\s*20\d\d|(?:early|mid|late|end of|first half of|second half of)[\s-]+20\d\d)", re.I)
def get(url):
    for i in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "ignore")
        except Exception as e:
            time.sleep(1 + i)
    return ""
def search(q, start, end, forms="8-K", frm=0):
    u = "https://efts.sec.gov/LATEST/search-index?" + urllib.parse.urlencode({"q": q, "forms": forms, "dateRange": "custom", "startdt": start, "enddt": end, "from": frm})
    return json.loads(get(u) or "{}").get("hits", {})
def text_of(h):
    h = re.sub(r"(?is)<(script|style).*?</\1>", " ", h)
    t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    return re.sub(r"\s+", " ", t)
def parse_date(s):
    try: return dt.datetime.strptime(re.sub(r"\s+", " ", s), "%B %d, %Y").date().isoformat()
    except Exception: return None
def run(start, end, maxfilings=200, forms="8-K"):
    out, seen, frm = [], set(), 0
    while frm < maxfilings:
        h = search('"PDUFA"', start, end, forms, frm)
        hits = h.get("hits", [])
        if not hits: break
        for x in hits:
            s = x["_source"]; adsh, fn = x["_id"].split(":")
            cik = s["ciks"][0].lstrip("0")
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{adsh.replace('-','')}/{fn}"
            if url in seen: continue
            seen.add(url)
            t = text_of(get(url)); time.sleep(0.15)
            name = s["display_names"][0]
            m = re.search(r"\(([A-Z.\-, ]+)\)\s+\(CIK", name)
            ticker = m.group(1).split(",")[0].strip() if m else None
            company = re.sub(r"\s+\(.*$", "", name).strip()
            for sent in re.split(r"(?<=[.;])\s+", t):
                if "PDUFA" not in sent or len(sent) > 700: continue
                if re.search(r"forward-looking|risks and uncertainties|Safe Harbor", sent, re.I): continue
                if sent.startswith("EX-") or "Exhibit 99" in sent[:200]: sent = sent[sent.find("PDUFA")-300 if sent.find("PDUFA")>300 else 0:]
                ms = [m for m in DATE_RE.finditer(sent) if m.group(1)]
                if not ms: continue
                pi = sent.find("PDUFA")
                dm = min(ms, key=lambda m: abs(m.start() - pi))
                if abs(dm.start() - pi) > 220: continue
                raw = dm.group(0); iso = parse_date(raw)
                if not iso: continue
                if iso and iso < s["file_date"]: continue  # past dates = history, skip for upcoming
                drug = None
                dm2 = re.search(r"\b([A-Z][A-Za-z0-9\-]{2,}(?:\s*\([a-z\-]+\))?)\b(?=[^.]{0,120}PDUFA)", sent)
                out.append({"ticker": ticker, "company": company, "cik": cik, "pdufaDate": iso, "pdufaDateText": raw,
                            "dateIsExact": bool(iso), "evidenceQuote": sent.strip()[:600], "formType": s.get("form") or s.get("root_forms", [""])[0],
                            "filedAt": s["file_date"], "secUrl": url})
        frm += len(hits)
        if frm >= h.get("total", {}).get("value", 0): break
    # dedupe by ticker+date, keep latest filing
    best = {}
    for r in sorted(out, key=lambda r: r["filedAt"]):
        best[(r["ticker"], r["pdufaDate"] or r["pdufaDateText"].lower())] = r
    return sorted(best.values(), key=lambda r: (r["pdufaDate"] or "9999", r["ticker"] or ""))
if __name__ == "__main__":
    end = dt.date.today(); start = end - dt.timedelta(days=int(sys.argv[1]) if len(sys.argv) > 1 else 120)
    rows = run(start.isoformat(), end.isoformat(), 400)
    json.dump(rows, open("rows.json", "w"), indent=1); print(len(rows))
    for r in rows[:40]: print(r["pdufaDate"] or r["pdufaDateText"], r["ticker"], r["company"][:30], "|", r["evidenceQuote"][:140])
