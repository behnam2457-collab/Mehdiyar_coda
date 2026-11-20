# -*- coding: utf-8 -*-
"""Mehdiyar - Codal-connected local server (Python 3 / Pydroid 3)
No third-party packages required.
"""
import json
import os
import re
import io
import zipfile
import xml.etree.ElementTree as ET
import time
import threading
from datetime import datetime
from urllib.parse import urlencode, urlparse, parse_qs, quote, unquote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from html.parser import HTMLParser

# Dashboard HTML is embedded below; no separate HTML file is required.
DASHBOARD_HTML = '<!doctype html>\n<html lang="fa" dir="rtl">\n<head>\n<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n<meta name="theme-color" content="#0a1220"><title>مهدیار | تحلیل هوشمند کدال</title>\n<style>\n:root{color-scheme:dark;--bg:#0a1220;--panel:#121f33;--panel2:#192b43;--line:#2c405c;--text:#eef5ff;--muted:#9fb0c8;--green:#3ad5a2;--blue:#83bdff;--red:#ff9292}\n*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 80% 0,#1a3856 0,transparent 38%),var(--bg);color:var(--text);font-family:Tahoma,Arial,sans-serif}\n.wrap{max-width:1180px;margin:auto;padding:20px}.top{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}\n.brand{display:flex;align-items:center;gap:12px}.logo{width:48px;height:48px;border-radius:15px;background:linear-gradient(135deg,#3ad5a2,#167b82);display:grid;place-items:center;color:#06251e;font-weight:bold;font-size:25px}\nh1{font-size:23px;margin:0}.sub{font-size:12px;color:var(--muted);margin-top:6px}.pill{border:1px solid #315b54;background:#10372e;color:#9cf0d0;border-radius:30px;padding:9px 13px;font-size:12px}\n.panel{margin-top:16px;background:linear-gradient(145deg,#14243a,#101b2c);border:1px solid var(--line);border-radius:17px;padding:17px;box-shadow:0 14px 36px #0003}\n.controls{display:flex;gap:10px;flex-wrap:wrap}input,select{background:#0a1526;color:white;border:1px solid #344b68;border-radius:11px;padding:13px;font-size:14px;min-width:0}input{flex:1}\nbutton{background:var(--green);color:#06251d;border:0;border-radius:11px;padding:13px 18px;font-size:14px;font-weight:bold;cursor:pointer}button:disabled{opacity:.55}\n.status{margin-top:13px;padding:12px;background:#0a1728;border:1px solid #293f5b;border-radius:11px;line-height:1.9;font-size:13px}.muted{color:var(--muted);font-size:12px;line-height:2}\n.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:10px;margin-top:13px}.card{background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:13px}.card small{color:var(--muted)}.card strong{display:block;font-size:19px;margin-top:7px;overflow-wrap:anywhere}\n.tablebox{overflow:auto;margin-top:13px}table{border-collapse:collapse;width:100%;min-width:760px;font-size:12px}th,td{text-align:right;padding:10px;border-bottom:1px solid var(--line);vertical-align:top;line-height:1.8}th{background:#1b2e48;color:#b8d6fa;position:sticky;top:0}a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}\n.action{background:#234363;color:#e8f3ff;padding:8px 10px;border-radius:9px;font-size:12px}.empty{padding:24px;text-align:center;color:var(--muted)}.danger{color:var(--red)}.good{color:#83efc5}\n.sheethead{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}.sheethead h3{margin:0}\nfooter{text-align:center;color:#8396af;font-size:11px;padding:22px;line-height:2}\n@media(max-width:620px){.wrap{padding:12px}.panel{padding:13px}h1{font-size:19px}.controls{display:grid}button{width:100%}}\n</style></head>\n<body><main class="wrap">\n<header class="top"><div class="brand"><div class="logo">م</div><div><h1>مهدیار | تحلیل هوشمند کدال</h1><div class="sub">دریافت اطلاعیه\u200cها و جداول اصلی از گزارش\u200cهای ناشران</div></div></div><span class="pill" id="health">در حال بررسی سرویس…</span></header>\n<section class="panel">\n<h3 style="margin:0 0 13px">انتخاب نماد و دریافت گزارش\u200cها</h3>\n<div class="controls"><input id="symbol" value="نوری" placeholder="نماد؛ مثل نوری، وبملت، فملی"><select id="type"><option value="-1">همه اطلاعیه\u200cها</option><option value="6" selected>صورت\u200cهای مالی (کد ۶)</option><option value="58">گزارش فعالیت ماهانه (کد ۵۸)</option></select><button id="search" onclick="searchCodal()">دریافت از کدال</button></div>\n<div class="muted">اطلاعات از سرویس جست\u200cوجوی کدال دریافت می\u200cشود. برای بازکردن جداول مالی، روی «نمایش صورت مالی» در ردیف گزارش موردنظر بزنید.</div>\n<div class="status" id="status">آماده دریافت گزارش واقعی.</div>\n<div class="cards"><div class="card"><small>نماد انتخابی</small><strong id="symbolCard">نوری</strong></div><div class="card"><small>شرکت</small><strong id="company">—</strong></div><div class="card"><small>تعداد گزارش\u200cهای برگشتی</small><strong id="count">—</strong></div><div class="card"><small>وضعیت دریافت</small><strong id="state">در انتظار</strong></div></div>\n<div id="results" class="empty">پس از دریافت، گزارش\u200cهای کدال اینجا نمایش داده می\u200cشوند.</div>\n</section>\n<section class="panel" id="reportPanel" hidden>\n<div class="sheethead"><h3 id="reportTitle">جداول گزارش</h3><select id="sheet" onchange="loadSheet()"><option value="0">جدول / برگه ۱</option><option value="1">جدول / برگه ۲</option><option value="2">جدول / برگه ۳</option><option value="3">جدول / برگه 4</option><option value="4">جدول / برگه 5</option><option value="5">جدول / برگه 6</option><option value="6">جدول / برگه 7</option><option value="7">جدول / برگه 8</option><option value="8">جدول / برگه 9</option><option value="9">جدول / برگه 10</option></select></div>\n<div class="status" id="reportStatus">برای استخراج جدول، یک گزارش انتخاب کنید.</div><div id="tables" class="empty">جدولی بارگذاری نشده است.</div>\n</section>\n<footer>منبع داده: کدال · داده\u200cهای خام بدون تغییر ماهیت نمایش داده می\u200cشوند.<br>تا زمانی که عنوان ستون، دوره و واحد هر ردیف با سند تطبیق نشود، نسبت یا عدد تحلیلی ساخته نمی\u200cشود.</footer>\n</main>\n<script>\nconst $=id=>document.getElementById(id);let activeSymbol="نوری",activeTracing="",searchRequestNo=0,searchController=null;\nfunction esc(v){return String(v??"—").replace(/[&<>"\']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",\'"\':"&quot;","\'":"&#39;"}[c]))}\nasync function health(){try{let r=await fetch("/api/health"),j=await r.json();$("health").textContent=j.ok?"درگاه مهدیار فعال":"خطای درگاه"}catch(e){$("health").textContent="سرور اجرا نشده است"}}\nasync function searchCodal(){\n const symbol=$("symbol").value.trim(),type=$("type").value;if(!symbol){$("status").textContent="نماد را وارد کنید.";return}\n activeSymbol=symbol;$("symbolCard").textContent=symbol;$("status").textContent="در حال دریافت فهرست گزارش\u200cها از کدال…";$("state").textContent="در حال اتصال";$("count").textContent="…";$("company").textContent="—";$("results").innerHTML=\'<div class="empty">در حال دریافت…</div>\';$("reportPanel").hidden=true;\n const b=$("search");b.disabled=true;b.textContent="در حال دریافت…";\n try{\n  const r=await fetch("/api/search?symbol="+encodeURIComponent(symbol)+"&type="+encodeURIComponent(type));const j=await r.json();if(!r.ok||!j.ok)throw Error(j.error||"خطای دریافت");\n  const a=j.reports||[];$("count").textContent=j.total??a.length;$("company").textContent=a[0]?.company||"—";$("state").textContent="موفق";$("status").innerHTML=\'<span class="good">پاسخ از کدال دریافت شد.</span> زمان: \'+esc(j.fetched_at)+(j.cached?" · از حافظه موقت":"");\n  if(!a.length){$("results").innerHTML=\'<div class="empty">گزارشی برای این نماد و نوع انتخاب\u200cشده برنگشت.</div>\';return}\n  const rows=a.map((x,i)=>\'<tr><td>\'+(i+1)+\'</td><td>\'+esc(x.title)+\'</td><td>\'+esc(x.date)+\'</td><td>\'+esc(x.tracing_no)+\'</td><td>\'+esc(x.letter_code)+\'</td><td>\'+(true?\'<button class="action" onclick="openReport(\\\'\'+esc(x.tracing_no)+\'\\\')">نمایش صورت مالی</button>\':\'<span class="muted">Excel ندارد</span>\')+\'<br><a target="_blank" rel="noopener" href="\'+esc(x.page_url)+\'">صفحه کدال</a>\'+(x.pdf_url?\'<br><a target="_blank" rel="noopener" href="\'+esc(x.pdf_url.startsWith("http")?x.pdf_url:"https://www.codal.ir/"+x.pdf_url)+\'">PDF</a>\':\'\')+\'</td></tr>\').join("");\n  $("results").innerHTML=\'<div class="tablebox"><table><thead><tr><th>ردیف</th><th>عنوان گزارش</th><th>تاریخ انتشار</th><th>شماره پیگیری</th><th>کد نامه</th><th>مشاهده صورت مالی</th></tr></thead><tbody>\'+rows+\'</tbody></table></div>\';\n }catch(e){$("state").textContent="ناموفق";$("count").textContent="—";$("status").innerHTML=\'<span class="danger">خطا:</span> \'+esc(e.message);$("results").innerHTML=\'<div class="empty">اتصال یا دریافت گزارش انجام نشد. متن خطا بالاست.</div>\'}\n finally{b.disabled=false;b.textContent="دریافت از کدال"}\n}\nasync function openReport(tracing){\n activeTracing=tracing;$("reportPanel").hidden=false;$("reportTitle").textContent="جداول گزارش شماره "+tracing;$("sheet").value="0";await loadSheet();$("reportPanel").scrollIntoView({behavior:"smooth",block:"start"});\n}\nasync function loadSheet(){\n const sheet=$("sheet").value;$("reportStatus").textContent="در حال دریافت و استخراج جدول از فایل Excel کدال…";$("tables").innerHTML=\'<div class="empty">در حال پردازش فایل گزارش…</div>\';\n try{\n  const r=await fetch("/api/report?symbol="+encodeURIComponent(activeSymbol)+"&tracingNo="+encodeURIComponent(activeTracing)+"&sheet="+sheet);const j=await r.json();if(!r.ok||!j.ok)throw Error(j.error||"استخراج جدول ناموفق بود");\n  const d=j.report;$("reportTitle").textContent=d.title||("گزارش "+activeTracing);$("reportStatus").innerHTML=\'<span class="good">محتوای فایل گزارش کدال استخراج شد.</span> · شرکت: \'+esc(d.company)+\' · تاریخ: \'+esc(d.publish_date)+\' · برگه: \'+(Number(sheet)+1)+\' · <a target="_blank" rel="noopener" href="\'+esc(d.page_url)+\'">سند اصلی</a>\';\n  $("tables").innerHTML=d.tables.map((t,ti)=>\'<h4>جدول \'+(ti+1)+\'</h4><div class="tablebox"><table><tbody>\'+t.map((row,ri)=>\'<tr>\'+row.map(c=>ri===0?\'<th>\'+esc(c)+\'</th>\':\'<td>\'+esc(c)+\'</td>\').join("")+\'</tr>\').join("")+\'</tbody></table></div>\').join("");\n }catch(e){$("reportStatus").innerHTML=\'<span class="danger">خطا در استخراج:</span> \'+esc(e.message);$("tables").innerHTML=\'<div class="empty">این برگه دریافت نشد. ممکن است گزارش Excel نداشته باشد یا کدال پاسخ نداده باشد.</div>\'}\n}\n$("symbol").addEventListener("keydown",e=>{if(e.key==="Enter")searchCodal()});health();\n</script></body></html>\n'
HOST = '0.0.0.0'
PORT = int(os.environ.get('PORT', '10000'))
CODAL_SEARCH = 'https://search.codal.ir/api/search/v2/q'
EXCEL_BASE = 'https://excel.codal.ir/service/Excel/GetAll/'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.codal.ir/',
    'Origin': 'https://www.codal.ir',
}
CACHE = {}
CACHE_LOCK = threading.Lock()
CACHE_TTL = 180
LAST_CODEL_CALL = 0.0
CALL_LOCK = threading.Lock()


def http_get(url, accept=None, timeout=35):
    headers = dict(HEADERS)
    if accept:
        headers['Accept'] = accept
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=timeout) as response:
            return response.status, response.headers.get('Content-Type', ''), response.read()
    except HTTPError as e:
        body = e.read(500).decode('utf-8', 'replace')
        if e.code == 429:
            raise RuntimeError('کدال موقتاً درخواست‌ها را محدود کرده است (429). کمی بعد دوباره امتحان کنید.')
        raise RuntimeError('پاسخ کدال: HTTP %s - %s' % (e.code, body[:180]))
    except URLError as e:
        raise RuntimeError('ارتباط با کدال برقرار نشد: %s' % e.reason)
    except TimeoutError:
        raise RuntimeError('مهلت پاسخ کدال تمام شد؛ اتصال اینترنت یا دسترسی سرور را بررسی کنید.')


def codal_search(symbol, letter_type='6', tracing_no=None):
    global LAST_CODEL_CALL
    key = ('search', symbol, str(letter_type), str(tracing_no or ''))
    now = time.time()
    with CACHE_LOCK:
        item = CACHE.get(key)
        if item and now - item[0] < CACHE_TTL:
            return item[1], True
    # gentle pacing to avoid repeatedly hitting Codal
    with CALL_LOCK:
        wait = 2.2 - (time.time() - LAST_CODEL_CALL)
        if wait > 0:
            time.sleep(wait)
        params = {
            'Symbol': symbol,
            'LetterType': str(letter_type),
            'PageNumber': '1',
            'Audited': 'true', 'NotAudited': 'true',
            'IsNotAudited': 'false', 'Consolidatable': 'true',
            'NotConsolidatable': 'true', 'Childs': 'false', 'Mains': 'true',
            'CompanyState': '-1', 'CompanyType': '-1', 'AuditorRef': '-1',
            'Category': '1' if str(letter_type) == '6' else ('3' if str(letter_type) == '58' else '-1'),
            'Length': '-1', 'TracingNo': str(tracing_no or '-1'),
            'Publisher': 'false', 'search': 'true'
        }
        url = CODAL_SEARCH + '?' + urlencode(params)
        status, content_type, raw = http_get(url, 'application/json')
        LAST_CODEL_CALL = time.time()
    try:
        payload = json.loads(raw.decode('utf-8-sig'))
    except Exception:
        preview = raw[:180].decode('utf-8', 'replace')
        raise RuntimeError('پاسخ کدال JSON قابل‌خواندن نبود. پاسخ: ' + preview)
    if not isinstance(payload, dict):
        raise RuntimeError('ساختار پاسخ کدال غیرمنتظره است.')
    with CACHE_LOCK:
        CACHE[key] = (time.time(), payload)
    return payload, False


def clean_letter(letter):
    title = letter.get('Title') or ''
    symbol = letter.get('Symbol') or ''
    company = letter.get('CompanyName') or ''
    url = letter.get('Url') or ''
    pdf = letter.get('PdfUrl') or ''
    tracing = letter.get('TracingNo')
    page_url = url if str(url).startswith('http') else 'https://www.codal.ir' + str(url)
    pdf_url = pdf if str(pdf).startswith('http') else ('https://www.codal.ir/' + str(pdf).lstrip('/') if pdf else '')
    return {
        'title': title, 'date': letter.get('PublishDateTime') or letter.get('SentDateTime') or '',
        'tracing_no': str(tracing or ''), 'letter_code': letter.get('LetterCode') or '',
        'company': company, 'symbol': symbol,
        'has_excel': str(letter.get('HasExcel', '')).strip().lower() in ('true', '1', 'yes', 'بله'),
        'page_url': page_url, 'pdf_url': pdf_url,
        'excel_url': letter.get('ExcelUrl') or '',
        'letter_serial': letter.get('LetterSerial') or ''
    }


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_table = []
        self.current_row = []
        self.cell_text = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'table':
            if not self.in_table:
                self.in_table = True
                self.current_table = []
        elif self.in_table and tag == 'tr':
            self.in_row = True
            self.current_row = []
        elif self.in_table and self.in_row and tag in ('td', 'th'):
            self.in_cell = True
            self.cell_text = []
        elif self.in_cell and tag == 'br':
            self.cell_text.append(' ')

    def handle_data(self, data):
        if self.in_cell:
            s = data.strip()
            if s:
                self.cell_text.append(s)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in ('td', 'th') and self.in_cell:
            self.current_row.append(' '.join(self.cell_text).strip())
            self.in_cell = False
        elif tag == 'tr' and self.in_row:
            if self.current_row:
                self.current_table.append(self.current_row)
            self.in_row = False
        elif tag == 'table' and self.in_table:
            if self.current_table:
                self.tables.append(self.current_table)
            self.in_table = False


def xlsx_sheet_tables(raw, sheet_index):
    """Read a real XLSX workbook using Python standard-library modules only."""
    ns = {
        'm': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'rel': 'http://schemas.openxmlformats.org/package/2006/relationships'
    }
    try:
        zf = zipfile.ZipFile(io.BytesIO(raw))
    except Exception:
        return None
    names = set(zf.namelist())
    if 'xl/workbook.xml' not in names:
        return None
    try:
        shared = []
        if 'xl/sharedStrings.xml' in names:
            root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
            for si in root.findall('m:si', ns):
                shared.append(''.join((t.text or '') for t in si.findall('.//m:t', ns)))
        wb = ET.fromstring(zf.read('xl/workbook.xml'))
        sheets = wb.findall('m:sheets/m:sheet', ns)
        if sheet_index < 0 or sheet_index >= len(sheets):
            raise RuntimeError('این گزارش فقط %s برگه دارد؛ شماره برگه انتخاب‌شده وجود ندارد.' % len(sheets))
        rel_id = sheets[sheet_index].attrib.get('{%s}id' % ns['r'])
        relroot = ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
        target = None
        for rel in relroot.findall('rel:Relationship', ns):
            if rel.attrib.get('Id') == rel_id:
                target = rel.attrib.get('Target')
                break
        if not target:
            target = 'worksheets/sheet%d.xml' % (sheet_index + 1)
        if target.startswith('/'):
            sheet_path = target.lstrip('/')
        elif target.startswith('xl/'):
            sheet_path = target
        else:
            sheet_path = 'xl/' + target
        if sheet_path not in names:
            raise RuntimeError('فایل برگه در Excel پیدا نشد: ' + sheet_path)
        root = ET.fromstring(zf.read(sheet_path))
        rows = []
        for row_el in root.findall('.//m:sheetData/m:row', ns):
            row = []
            for cell in row_el.findall('m:c', ns):
                ref = cell.attrib.get('r', '')
                col_letters = ''.join(ch for ch in ref if ch.isalpha())
                col = 0
                for ch in col_letters.upper():
                    col = col * 26 + ord(ch) - 64
                col = max(0, col - 1)
                while len(row) <= col:
                    row.append('')
                typ = cell.attrib.get('t', '')
                value_el = cell.find('m:v', ns)
                value = value_el.text if value_el is not None and value_el.text is not None else ''
                if typ == 's' and value != '':
                    try: value = shared[int(value)]
                    except Exception: pass
                elif typ == 'inlineStr':
                    value = ''.join((t.text or '') for t in cell.findall('.//m:t', ns))
                elif typ == 'b':
                    value = 'بله' if value == '1' else 'خیر'
                row[col] = str(value)
            # Keep rows with at least one non-empty cell.
            if any(str(v).strip() for v in row):
                rows.append(row)
        if rows:
            width = max(len(r) for r in rows)
            rows = [r + [''] * (width - len(r)) for r in rows]
            return [rows]
        return []
    finally:
        zf.close()


def get_report(symbol, tracing_no, sheet):
    payload, _ = codal_search(symbol, '-1', tracing_no)
    letters = payload.get('Letters') or []
    match = None
    for letter in letters:
        if str(letter.get('TracingNo', '')) == str(tracing_no):
            match = letter
            break
    if match is None:
        raise RuntimeError('گزارش با این شماره پیگیری در پاسخ کدال پیدا نشد. دوباره فهرست گزارش‌ها را دریافت کنید.')
    has_excel = str(match.get('HasExcel', '')).strip().lower() in ('true', '1', 'yes', 'بله')
    if not has_excel:
        raise RuntimeError('کدال برای این اطلاعیه فایل Excel اعلام نکرده است. از لینک PDF یا صفحه اصلی کدال استفاده کنید.')
    serial = match.get('LetterSerial')
    excel_url = match.get('ExcelUrl')
    if not excel_url and serial:
        excel_url = EXCEL_BASE + quote(str(serial), safe='') + '/' + str(sheet)
    if not excel_url:
        report_url = match.get('Url') or ''
        m = re.search(r'LetterSerial=([^&]+)', report_url, re.I)
        if m:
            serial = unquote(m.group(1))
            excel_url = EXCEL_BASE + quote(serial, safe='') + '/' + str(sheet)
    if not excel_url:
        raise RuntimeError('نشانی فایل Excel در پاسخ کدال وجود ندارد.')
    if '/GetAll/' in excel_url:
        excel_url = re.sub(r'/GetAll/([^/]+)/\d+(?:\?.*)?$', lambda m: '/GetAll/' + m.group(1) + '/' + str(sheet), excel_url)
    status, content_type, raw = http_get(excel_url, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,text/html,*/*', 45)
    if not raw:
        raise RuntimeError('فایل Excel کدال خالی دریافت شد.')
    tables = None
    source_format = ''
    # XLSX is a ZIP package (PK signature).
    if raw[:2] == b'PK':
        tables = xlsx_sheet_tables(raw, int(sheet))
        source_format = 'XLSX'
    elif raw.startswith(bytes.fromhex('D0CF11E0')):
        raise RuntimeError('این گزارش با فرمت قدیمی XLS دریافت شد. این نسخه بدون نصب کتابخانه جانبی، XLS قدیمی را نمی‌خواند؛ PDF یا خروجی XLSX همان گزارش را از کدال باز کنید.')
    else:
        text = raw.decode('utf-8-sig', 'replace')
        if 'unknown error' in text[:1000].lower() or 'خطای سیستمی' in text[:1000]:
            raise RuntimeError('سرویس فایل Excel کدال خطا برگرداند.')
        parser = TableParser()
        parser.feed(text)
        tables = parser.tables
        source_format = 'HTML/Excel Codal'
    if tables is None:
        raise RuntimeError('ساختار فایل Excel کدال قابل شناسایی نیست؛ نوع پاسخ: ' + str(content_type))
    if not tables:
        raise RuntimeError('در برگه انتخاب‌شده جدول قابل نمایش پیدا نشد. برگه دیگری را انتخاب کنید.')
    clean = clean_letter(match)
    return {
        'title': clean['title'], 'company': clean['company'],
        'publish_date': clean['date'], 'page_url': clean['page_url'],
        'tables': tables, 'excel_url': excel_url,
        'source_format': source_format
    }


class Handler(BaseHTTPRequestHandler):
    server_version = 'MehdiyarCodal/1.0'

    def log_message(self, fmt, *args):
        print('[مهدیار] ' + (fmt % args))

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Connection', 'close')
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            print('[مهدیار] مرورگر درخواست را پیش از پایان پاسخ بست؛ سرور فعال می‌ماند.')

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == '/api/health':
            self.send_json({'ok': True, 'service': 'Mehdiyar Codal Gateway', 'port': PORT, 'time': datetime.now().isoformat(timespec='seconds')})
            return
        if parsed.path == '/api/search':
            symbol = (params.get('symbol') or [''])[0].strip()
            letter_type = (params.get('type') or ['6'])[0].strip()
            if not symbol:
                self.send_json({'ok': False, 'error': 'نماد وارد نشده است.'}, 400); return
            try:
                payload, cached = codal_search(symbol, letter_type)
                letters = payload.get('Letters') or []
                reports = [clean_letter(x) for x in letters]
                self.send_json({'ok': True, 'symbol': symbol, 'company': reports[0]['company'] if reports else '',
                                'total': payload.get('Total', len(reports)), 'reports': reports,
                                'cached': cached, 'fetched_at': datetime.now().isoformat(timespec='seconds')})
            except Exception as e:
                self.send_json({'ok': False, 'error': str(e)}, 502)
            return
        if parsed.path == '/api/report':
            symbol = (params.get('symbol') or [''])[0].strip()
            tracing = (params.get('tracingNo') or [''])[0].strip()
            sheet = (params.get('sheet') or ['0'])[0].strip()
            if not symbol or not tracing:
                self.send_json({'ok': False, 'error': 'نماد یا شماره پیگیری مشخص نیست.'}, 400); return
            if not sheet.isdigit() or int(sheet) > 20:
                self.send_json({'ok': False, 'error': 'شماره برگه نامعتبر است.'}, 400); return
            try:
                report = get_report(symbol, tracing, sheet)
                self.send_json({'ok': True, 'report': report})
            except Exception as e:
                self.send_json({'ok': False, 'error': str(e)}, 502)
            return
        if parsed.path in ('/', '/index.html', '/mahdiar.html'):
            body = DASHBOARD_HTML.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Connection', 'close')
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                print('[مهدیار] مرورگر صفحه را بست؛ سرور فعال می‌ماند.')
            return
        self.send_json({'ok': False, 'error': 'مسیر پیدا نشد.'}, 404)


def main():
    try:
        server = ThreadingHTTPServer((HOST, PORT), Handler)
        server.daemon_threads = True
        server.block_on_close = False
    except OSError as e:
        print('خطا در راه‌اندازی سرور: %s' % e)
        return
    print('\nمهدیار | درگاه کدال آماده است')
    print('داشبورد: http://127.0.0.1:%d/' % PORT)
    print('آزمایش سلامت: http://127.0.0.1:%d/api/health' % PORT)
    print('برای توقف: Ctrl+C\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nسرور متوقف شد.')
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
