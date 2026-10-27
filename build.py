import json, os, datetime as dt, html
from extract import run
today = dt.date.today()
rows = run((today - dt.timedelta(days=400)).isoformat(), today.isoformat(), 1500)
hist_p = "data/history.json"
hist = json.load(open(hist_p)) if os.path.exists(hist_p) else {}
for r in rows:
    k = f'{r["ticker"]}|{r["secUrl"]}|{r["pdufaDateText"]}'
    hist.setdefault(k, {**r, "firstSeen": today.isoformat()})
json.dump(hist, open(hist_p, "w"), indent=0)
up = [r for r in rows if (r["pdufaDate"] or "9999") >= today.isoformat()]
json.dump(up, open("data/upcoming.json", "w"), indent=1)
E = html.escape
trs = "\n".join(f'<tr><td>{E(r["pdufaDate"] or r["pdufaDateText"])}</td><td><b>{E(r["ticker"] or "")}</b></td><td>{E(r["company"])}</td><td class=q>{E(r["evidenceQuote"][:320])}</td><td><a href="{E(r["secUrl"])}" rel=nofollow>SEC {E(r["filedAt"])}</a></td></tr>' for r in up)
API = "https://apify.com/prospect_antechamber/pdufa-fda-catalyst-calendar"
page = f'''<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>PDUFA Calendar {today.year}-{today.year+1}: Upcoming FDA Decision Dates (sourced from SEC filings)</title>
<meta name=description content="Free PDUFA date calendar: {len(up)} upcoming FDA target action dates for biotech stocks, each with the exact SEC filing sentence and link. Updated daily.">
<style>body{{font:15px system-ui;margin:0 auto;max-width:1100px;padding:16px;color:#111}}table{{border-collapse:collapse;width:100%}}td,th{{border-bottom:1px solid #ddd;padding:6px;vertical-align:top;text-align:left}}.q{{font-size:12px;color:#444}}.cta{{background:#f3f6ff;padding:12px;border-radius:8px}}</style></head><body>
<h1>PDUFA Calendar: upcoming FDA decision dates</h1>
<p>{len(up)} upcoming PDUFA target action dates. Each one is pulled straight from the company's own SEC filing and comes with the exact sentence and a link, so you can check it yourself. Updated daily ({today.isoformat()}).</p>
<p class=cta><b>Need it as data?</b> Get JSON/CSV, a ticker filter, daily schedules, webhooks and an MCP tool for AI agents on the <a href="{API}">PDUFA Calendar API on Apify</a>. Raw files are free here too: <a href="data/upcoming.json">upcoming.json</a> · <a href="feed.xml">RSS</a>.</p>
<table><tr><th>PDUFA date</th><th>Ticker</th><th>Company</th><th>Source sentence</th><th>Filing</th></tr>{trs}</table>
<p class=q>Informational data from public SEC EDGAR filings. Not investment advice. Not affiliated with the FDA or SEC. Dates can change, so always check the linked filing.</p><p class=q>More open datasets by the same author: <a href="https://nidhi-bhai.github.io/india-agri-export-prices/">India Agri Export Price Index</a> (weekly USD/kg prices for Indian agri exports).</p></body></html>'''
open("index.html", "w").write(page)
items = "".join(f'<item><title>{E((r["ticker"] or "")+" PDUFA "+(r["pdufaDate"] or r["pdufaDateText"]))}</title><link>{E(r["secUrl"])}</link><guid>{E(r["secUrl"]+r["pdufaDateText"])}</guid><description>{E(r["evidenceQuote"][:400])}</description></item>' for r in up)
open("feed.xml", "w").write(f'<?xml version="1.0"?><rss version="2.0"><channel><title>PDUFA Calendar</title><link>https://nidhi-bhai.github.io/pdufa-calendar/</link><description>Upcoming PDUFA dates from SEC filings</description>{items}</channel></rss>')
print(len(up), len(hist))
