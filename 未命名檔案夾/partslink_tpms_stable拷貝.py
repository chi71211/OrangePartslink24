#!/usr/bin/env python3
"""
Partslink24 TPMS Sensor Scraper v6 (Stable)
Format: Brand, Model, Typ, Year, TPMS (part number), Frequency
Only confirmed TPMS brands: BMW, Mini, VW, Audi, Porsche, SEAT, Skoda, Cupra
Auto-saves every N models and resumes from checkpoint on restart.
"""
import sys; print("START", flush=True)
import asyncio, sqlite3, time, random, os, csv, re, argparse, json, signal
from datetime import datetime
try:
    import nest_asyncio; nest_asyncio.apply()
except ImportError:
    pass
from playwright.async_api import async_playwright

SEL = '[class*="_selectable_"]'

graceful_stop = False
def _signal_handler(sig, frame):
    global graceful_stop
    graceful_stop = True
    print("\n[Signal] 安全關閉...", flush=True)
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


class Config:
    BASE_URL = "https://www.partslink24.com"
    LOGIN_URL = f"{BASE_URL}/partslink24/user/login.do"
    COMPANY_ID = "de-416440"
    USERNAME = "admin"
    PASSWORD = "Orangetpms*"
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_FILE = os.path.join(SCRIPT_DIR, "partslink_tpms.db")
    CSV_DIR = os.path.join(SCRIPT_DIR, "TPMS_Exports")
    PROGRESS_FILE = os.path.join(SCRIPT_DIR, "scrape_progress.json")
    MAX_RUNTIME_HOURS = 4.0
    CYCLE_DAYS = 7
    AUTO_SAVE_INTERVAL = 5  # Auto-save every N models

    GENERIC_TABLES = [
        'catalogTable', 'modelTable', 'modelTypeTable', 'modelYearTable',
        'bodyTable', 'engineTable', 'gearboxTable', 'transmissionTable',
        'driveTypeTable', 'bodyTypeTable',
        'fuelTypeTable', 'restrictionTable1', 'restrictionTable2', 'restrictionTable3',
        'partnerGroupTable', 'variantTable', 'subModelTable', 'categoryTable',
    ]

    BRANDS = {
        # ===== BMW Group (confirmed TPMS parts) =====
        'bmw': {
            'service': 'bmw_parts',
            'search': 'Reifendrucksensor', 'freq': '433MHz', 'nav': 'bmw',
            'search_terms': ['Reifendrucksensor', 'RDKS Sensor', 'RDC Sensor',
                             'RDC', 'Reifendruck-Control', '433MHz', 'Wheel Sensor'],
            'series': ["3'", "5'", "X3", "X5", "X1", "X7", "4'", "2'", "1'", "i4", "iX"],
        },
        'mini': {
            'service': 'mini_parts',
            'search': 'Reifendrucksensor', 'freq': '433MHz', 'nav': 'bmw',
            'search_terms': ['Reifendrucksensor', 'RDKS Sensor', 'RDC Sensor',
                             'RDC', 'Wheel Sensor', '433MHz'],
            'series': ["MINI Countryman", "MINI Clubman", "MINI Cooper", "MINI"],
        },

        # ===== VAG Group (confirmed TPMS parts) =====
        'audi': {
            'service': 'audi_parts',
            'search': 'Reifendrucksensor', 'freq': '433MHz', 'nav': 'vag',
            'search_terms': ['Reifendrucksensor', 'RDKS', 'Wheel Sensor',
                             'RDK-Sensor', 'Sensor für Reifendruck', '433MHz'],
            'models': ["Audi A3", "Audi A4", "Audi A5", "Audi A6", "Audi A8",
                       "Audi Q3", "Audi Q5", "Audi Q7", "Audi Q8"],
        },
        'vw': {
            'service': 'vw_parts',
            'search': 'Reifendrucksensor', 'freq': '433MHz', 'nav': 'vag',
            'search_terms': ['Reifendrucksensor', 'RDKS', 'Wheel Sensor',
                             'RDK-Sensor', 'Sensor für Reifendruck', '433MHz'],
            'models': ["Golf", "Tiguan", "Passat", "T-Roc", "Touareg", "Polo", "ID.4", "ID.3"],
        },
        'porsche': {
            'service': 'porsche_parts',
            'search': 'Reifendrucksensor', 'freq': '433MHz', 'nav': 'vag',
            'search_terms': ['Reifendrucksensor', 'RDKS', 'Wheel Sensor',
                             'RDK', '433MHz', 'Tire Pressure'],
            'models': ["Macan", "Cayenne", "Taycan", "Panamera"],
        },
        'seat': {
            'service': 'seat_parts',
            'search': 'Reifendrucksensor', 'freq': '433MHz', 'nav': 'vag',
            'search_terms': ['Reifendrucksensor', 'RDKS', 'Wheel Sensor',
                             'Sensor für Reifendruck', '433MHz'],
            'models': ["Leon (SEAT & CUPRA)", "Ibiza/ST (SEAT)", "Arona (SEAT)",
                       "Ateca (SEAT & CUPRA)", "Tarraco (SEAT)"],
        },
        'skoda': {
            'service': 'skoda_parts',
            'search': 'Reifendrucksensor', 'freq': '433MHz', 'nav': 'vag',
            'search_terms': ['Reifendrucksensor', 'RDKS', 'Wheel Sensor',
                             'Sensor für Reifendruck', '433MHz'],
            'models': ["Octavia", "Fabia", "Superb", "Karoq", "Kodiaq", "Enyaq"],
        },
        'cupra': {
            'service': 'cupra_parts',
            'search': 'Reifendrucksensor', 'freq': '433MHz/ABS', 'nav': 'vag',
            'search_terms': ['Reifendrucksensor', 'RDKS', 'Wheel Sensor',
                             'Sensor für Reifendruck', '433MHz'],
            'models': ["Leon (SEAT & CUPRA)", "Born", "Arona (SEAT & CUPRA)", "Formentor"],
        },
    }


class ProgressManager:
    def __init__(self):
        self.file = Config.PROGRESS_FILE
        self.data = self._load()

    def _load(self):
        if os.path.exists(self.file):
            try:
                with open(self.file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return self._fresh()
        return self._fresh()

    def _fresh(self):
        return {
            "cycle_start": time.time(),
            "completed": [],
            "last_brand": None,
            "last_model": None,
            "total_scraped": 0,
            "last_save": time.time()
        }

    def save(self, brand=None, model=None, count_add=0):
        if brand is not None:
            self.data["last_brand"] = brand
        if model is not None:
            self.data["last_model"] = model
        self.data["total_scraped"] += count_add
        self.data["last_save"] = time.time()
        try:
            with open(self.file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            print(f"[Progress] Save error: {e}", flush=True)

    def mark_completed(self, brand_key, model_name):
        entry = f"{brand_key}:{model_name}"
        if entry not in self.data["completed"]:
            self.data["completed"].append(entry)
            self.save()

    def is_completed(self, brand_key, model_name):
        return f"{brand_key}:{model_name}" in self.data["completed"]

    def should_reset(self):
        return (time.time() - self.data["cycle_start"]) > (Config.CYCLE_DAYS * 86400)

    def reset(self):
        self.data = self._fresh()
        self.save()
        print("[Progress] 已清空進度", flush=True)

    def summary(self):
        elapsed_h = (time.time() - self.data["cycle_start"]) / 3600
        remaining_h = max(0, Config.CYCLE_DAYS * 24 - elapsed_h)
        print(f"\n[Progress] 週期: {datetime.fromtimestamp(self.data['cycle_start']).strftime('%m-%d %H:%M')}", flush=True)
        print(f"  已運行: {elapsed_h:.1f}h | 剩餘: {remaining_h:.1f}h | 完成: {len(self.data['completed'])} 車款 | 爬取: {self.data['total_scraped']} 零件", flush=True)


class DB:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_FILE)
        self.conn.execute('''CREATE TABLE IF NOT EXISTS sensors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Brand TEXT, Model TEXT, Typ TEXT, Year TEXT,
            Teilenummer TEXT, Frequency TEXT, Description TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(Brand, Model, Typ, Year, Teilenummer)
        )''')
        self.conn.commit()

    def add(self, brand, model, typ, year, pn, freq, desc):
        try:
            self.conn.execute(
                'INSERT OR REPLACE INTO sensors (Brand,Model,Typ,Year,Teilenummer,Frequency,Description) VALUES (?,?,?,?,?,?,?)',
                (brand, model, typ, year, pn, freq, desc))
            self.conn.commit()
            return True
        except:
            return False

    def count(self):
        return self.conn.execute('SELECT COUNT(*) FROM sensors').fetchone()[0]

    def by_brand(self):
        return self.conn.execute('SELECT Brand, COUNT(*) FROM sensors GROUP BY Brand ORDER BY Brand').fetchall()

    def all_rows(self):
        return self.conn.execute('SELECT Brand,Model,Typ,Year,Teilenummer,Frequency,Description FROM sensors ORDER BY Brand,Model,Typ,Year,Teilenummer').fetchall()

    def export(self):
        os.makedirs(Config.CSV_DIR, exist_ok=True)
        rows = self.all_rows()
        if not rows:
            return
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        f = os.path.join(Config.CSV_DIR, f"tpms_{ts}.csv")
        with open(f, 'w', newline='', encoding='utf-8') as fp:
            w = csv.writer(fp)
            w.writerow(['Brand','Model','Typ','Year','TPMS','Frequency','Description'])
            w.writerows(rows)
        print(f"[Export] {f} ({len(rows)} rows)", flush=True)

    def close(self):
        self.conn.close()


class Scraper:
    def __init__(self, brands=None, force_reset=False):
        self.db = DB()
        self.progress = ProgressManager()
        self.brands = brands
        self.force_reset = force_reset
        self.start = time.time()
        self.count = 0
        self.page = None
        self.models_since_save = 0  # Counter for auto-save

    async def uc(self):
        await self.page.evaluate('() => { const u = document.querySelector("#usercentrics-root"); if (u) u.remove(); }')

    async def login(self):
        print("[Login]", flush=True)
        await self.page.goto(Config.LOGIN_URL, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(5)
        if "Attention" in await self.page.title():
            r = await self.page.query_selector('a:has-text("Reload")')
            if r:
                await r.click(); await asyncio.sleep(5)
        await self.uc(); await asyncio.sleep(2); await self.uc()
        await self.page.fill("#login-id", Config.COMPANY_ID); await asyncio.sleep(1)
        await self.page.fill("#login-name", Config.USERNAME); await asyncio.sleep(1)
        await self.page.fill("#inputPassword", Config.PASSWORD); await asyncio.sleep(2)
        await self.page.click("#hidden-login"); await asyncio.sleep(15)
        await self.uc()
        c = await self.page.query_selector('#squeezeout-login-btn')
        if c:
            await c.click(); await asyncio.sleep(5); await self.uc()
        print("  OK", flush=True)

    async def goto_brand(self, key):
        cfg = Config.BRANDS[key]
        url = f"{Config.BASE_URL}/partslink24/launchCatalog.do?service={cfg['service']}"
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(20); await self.uc()

    async def click_sel(self, text, x_min=0):
        return await self.page.evaluate("""([text, xmin]) => {
            const items = Array.from(document.querySelectorAll('""" + SEL + """'))
                .filter(r => r.getBoundingClientRect().width > 0 && r.getBoundingClientRect().x >= xmin);
            for (const r of items)
                if (r.textContent.trim().toLowerCase().includes(text.toLowerCase())) { r.click(); return r.textContent.trim().substring(0, 60); }
            return null;
        }""", [text, x_min])

    async def click_table_item(self, table_id, text):
        return await self.page.evaluate("""([tid, text]) => {
            const col = document.querySelector('[data-test-id="' + tid + '"]');
            if (!col) return false;
            const items = Array.from(col.querySelectorAll('""" + SEL + """'))
                .filter(r => r.getBoundingClientRect().width > 0);
            for (const r of items)
                if (r.textContent.trim().toLowerCase().includes(text.toLowerCase())) { r.click(); return true; }
            return false;
        }""", [table_id, text])

    async def click_row(self, text):
        return await self.page.evaluate("""(text) => {
            const rows = document.querySelectorAll('[data-test-id="row"]');
            const lower = text.toLowerCase();
            for (const row of rows)
                if (row.textContent.trim().toLowerCase().includes(lower)) { row.click(); return row.textContent.trim().substring(0, 60); }
            return null;
        }""", text)

    async def get_table_items(self, table_id, x_min=0):
        return await self.page.evaluate("""([tid, xmin]) => {
            const col = document.querySelector('[data-test-id="' + tid + '"]');
            if (!col) return [];
            return Array.from(col.querySelectorAll('""" + SEL + """'))
                .filter(r => r.getBoundingClientRect().width > 0 && r.getBoundingClientRect().x >= xmin)
                .map(r => r.textContent.trim().substring(0, 60));
        }""", [table_id, x_min])

    async def bc(self):
        return await self.page.evaluate("() => document.querySelector('[data-test-id=\"breadcrumbs\"]')?.textContent?.trim() || ''")

    async def search(self, term):
        visible = await self.page.evaluate("""() => {
            const el = document.querySelector('[data-test-id="partSearchInput"]');
            if (!el) return false;
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
        }""")
        if not visible:
            await self.page.evaluate("() => window.scrollTo(0, 0)")
            await asyncio.sleep(2)
            visible = await self.page.evaluate("""() => {
                const el = document.querySelector('[data-test-id="partSearchInput"]');
                if (!el) return false;
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height > 0;
            }""")
        if not visible:
            return "keine Einträge"

        await self.page.evaluate("""() => {
            const el = document.querySelector('[data-test-id="partSearchInput"]');
            if (el) { const i = el.querySelector('input'); if (i) { i.value = ''; i.focus(); } }
        }""")
        await asyncio.sleep(0.5)
        await self.page.keyboard.type(term, delay=40)
        await asyncio.sleep(0.5)
        await self.page.evaluate("() => document.querySelector('[data-test-id=\"sendPartSearch\"]')?.click()")
        await asyncio.sleep(12); await self.uc()
        return await self.page.evaluate("""() => {
            const companion = document.querySelector('[data-test-id="companion"]');
            if (companion && companion.textContent.includes('Teilenummer')) {
                return companion.textContent.trim();
            }
            const rows = document.querySelectorAll('[data-test-id="row"]');
            return Array.from(rows).map(r => r.textContent.trim()).filter(r => r.length > 3).join('\\n');
        }""")

    async def extract_bmw(self, text):
        parts = []
        clean = re.sub(r'\n', ' ', text)
        clean = re.sub(r'\s+', ' ', clean)
        pns = re.findall(r'(\d{2}\s\d{2}\s\d\s\d{3}\s\d{3})', clean)
        seen = set()
        for pn in pns:
            if pn in seen:
                continue
            seen.add(pn)
            desc = ''
            idx = clean.find(pn)
            if idx >= 0:
                after = clean[idx+len(pn):idx+len(pn)+200]
                for seg in after.split('.'):
                    seg = seg.strip()
                    if seg and ('RDC' in seg or 'Reifendruck' in seg or '433' in seg or '315' in seg or 'Schraubventil' in seg):
                        desc = seg[:100]
                        break
            parts.append((pn, desc))
        return parts

    async def extract_vag(self, text):
        parts = []
        clean = re.sub(r'\n', ' ', text)
        clean = re.sub(r'\s+', ' ', clean)
        clean = re.sub(r'(\d{4,})', r' \1 ', clean)
        pns = re.findall(r'(?<![0-9A-Z])([0-9A-Z]{2,4}\s[0-9A-Z]{3}\s[0-9A-Z]{3}(?:\s[0-9A-Z]{1,2})?)(?![0-9A-Z])', clean)
        for pn in set(pns):
            if not re.match(r'^[0-9A-Z]{2,4}\s[0-9A-Z]{3}\s[0-9A-Z]{3}', pn):
                continue
            prefix = pn.split()[0]
            if prefix in ('000', '011', '100', '999'):
                continue
            desc = ''
            idx = clean.find(pn)
            if idx >= 0:
                after = clean[idx+len(pn):idx+len(pn)+300]
                for seg in after.split('.'):
                    seg = seg.strip()
                    if seg and ('Sensor' in seg or 'Reifendruck' in seg or 'RDC' in seg or 'RDK' in seg or 'TPMS' in seg):
                        desc = seg[:120]
                        break
            parts.append((pn, desc))
        return parts

    def filter_tpms(self, parts):
        EXCLUDE = ['KENNSCHILD', 'DEKORLEISTE', 'SCHUTZLEISTE', 'HALTER', 'ABDECKUNG',
                    'SCHRAUBE', 'MUTTER', 'ABGASDRUCK', 'KRAFTSTOFF', 'OELDRUCK',
                    'Temperatur', 'Luftmassen', 'Lambda', 'NOX', 'PARTIKEL',
                    'SOMMERRÄDER', 'WINTERRÄDER', 'RAD Complete',
                    'Radausrüstung', 'Felge', 'Sonnenschutz']
        TPMS_KW = ['REIFENDRUCK', 'TPMS', 'RDC', 'RDK', 'RDKS',
                    'RADSENSOR', 'TIRE PRESSURE', 'TYRE PRESSURE',
                    'WHEEL SENSOR', 'RAD ELEKTRONIK', 'REIFENDRUCKKONTROLLE']
        TPMS_PN = ['907 255', '907 275', '907 273', '907 274',
                    '959 65', '837 90', '907 66', '839 90', '880 74',
                    '907 04', '880 20', '998 270',
                    '6 877', '6 856', '6 874', '6 890', '6 881']
        return [(p, d) for p, d in parts
                if not any(ex in d.upper() for ex in EXCLUDE)
                and (any(kw in d.upper() for kw in TPMS_KW)
                     or any(pn in p for pn in TPMS_PN))]

    # ========== BMW navigation ==========
    async def scrape_bmw(self, key):
        cfg = Config.BRANDS[key]
        freq = cfg['freq']
        print(f"\n{'='*50}", flush=True)
        print(f"  {key.upper()} - {len(cfg['series'])} series", flush=True)
        print(f"{'='*50}", flush=True)

        for series in cfg['series']:
            if graceful_stop or self.timeout():
                return
            if self.progress.is_completed(key, series):
                print(f"  {series}: [skip]", flush=True)
                continue

            print(f"\n  {series}:", flush=True)
            await self.goto_brand(key)

            r = await self.js_click_table('modelTable', series)
            if not r:
                r = await self.click_sel(series)
            if not r:
                print(f"    Not found in modelTable", flush=True)
                self.progress.mark_completed(key, series)
                continue
            await asyncio.sleep(12); await self.uc()

            models = await self.get_table_items('modelTypeTable')
            if not models:
                print(f"    No models in modelTypeTable", flush=True)
                self.progress.mark_completed(key, series)
                continue

            def _model_priority(m):
                code = m.split('(')[0].strip().upper()
                is_m = any(x in code for x in ['M3', 'M4', 'M5', 'ALPINA'])
                if is_m:
                    return 999
                if code.startswith('G'):
                    return 0
                if code.startswith('F'):
                    return 1
                if code.startswith('U'):
                    return 2
                if code.startswith('E') or code.startswith('C'):
                    return 5
                return 3

            model = min(models, key=_model_priority)

            print(f"    Model: {model[:50]}", flush=True)
            await self.js_click_table('modelTypeTable', model)
            await asyncio.sleep(12); await self.uc()

            r1_items = await self.get_table_items('restrictionTable1')
            if r1_items:
                clicked = False
                for item in r1_items:
                    if 'ECE' in item or 'Lim' in item or 'Sedan' in item:
                        await self.js_click_table('restrictionTable1', item)
                        clicked = True; break
                if not clicked:
                    await self.js_click_table('restrictionTable1', r1_items[0])
                await asyncio.sleep(10); await self.uc()

            r2_items = await self.get_table_items('restrictionTable2')
            if not r2_items:
                print(f"    No engines in restrictionTable2", flush=True)
                self.progress.mark_completed(key, series)
                continue

            engine = r2_items[0]
            for e in r2_items:
                if '320d' in e or '330i' in e:
                    engine = e; break
            print(f"    Engine: {engine[:40]}", flush=True)
            await self.js_click_table('restrictionTable2', engine)
            await asyncio.sleep(10); await self.uc()

            r3_items = await self.get_table_items('restrictionTable3')

            found = False
            part_count = 0
            markets = r3_items if r3_items else ['']
            for market in markets:
                if found:
                    break
                if market:
                    print(f"    Market: {market[:30]}", flush=True)
                    await self.js_click_table('restrictionTable3', market)
                    await asyncio.sleep(10); await self.uc()

                for term in cfg.get('search_terms', [cfg['search']]):
                    ft = await self.search(term)
                    if "keine Einträge" in ft:
                        continue
                    parts = self.filter_tpms(await self.extract_bmw(ft))
                    if parts:
                        print(f"    Found {len(parts)} parts (term: {term}, market: {market or 'N/A'})", flush=True)
                        for pn, desc in parts[:3]:
                            print(f"      {pn} - {desc[:60]}", flush=True)
                        for pn, desc in parts:
                            self.db.add(key.upper(), series, model, engine, pn, freq, desc)
                            self.count += 1
                            part_count += 1
                        found = True
                        break
            if not found:
                print(f"    No TPMS results", flush=True)
            self.progress.mark_completed(key, series)
            self.progress.save(brand=key, model=series, count_add=part_count)
            self.models_since_save += 1
            if self.models_since_save >= Config.AUTO_SAVE_INTERVAL:
                self._auto_save()
            await asyncio.sleep(random.uniform(5, 10))

    async def js_click_table(self, table_id, text):
        return await self.page.evaluate("""([tid, text]) => {
            const col = document.querySelector('[data-test-id="' + tid + '"]');
            if (!col) return false;
            const items = Array.from(col.querySelectorAll('""" + SEL + """'))
                .filter(r => r.getBoundingClientRect().width > 0);
            for (const r of items)
                if (r.textContent.trim().includes(text)) { r.click(); return true; }
            return false;
        }""", [table_id, text])

    # ========== Generic React SPA navigation (VAG brands) ==========
    async def click_through_tables(self, skip_tables=None):
        clicked_tables = set(skip_tables or [])
        for step in range(15):
            search_visible = await self.page.evaluate("""() => {
                const el = document.querySelector('[data-test-id="partSearchInput"]');
                if (!el) return false;
                const r = el.getBoundingClientRect();
                return r.width > 50 && r.height > 20;
            }""")
            if search_visible:
                return True

            clicked = await self.page.evaluate("""(args) => {
                const [tableIds, clickedSet] = args;
                for (const tid of tableIds) {
                    if (clickedSet.includes(tid)) continue;
                    const col = document.querySelector('[data-test-id="' + tid + '"]');
                    if (!col) continue;
                    const items = Array.from(col.querySelectorAll('""" + SEL + """'))
                        .filter(r => r.getBoundingClientRect().width > 0);
                    if (items.length === 0) continue;
                    let target = items[0];
                    for (const item of items) {
                        const t = item.textContent.trim();
                        if (t === 'Alle' || t === 'ALLE' || t === 'ALL') { target = item; break; }
                    }
                    target.click();
                    return tid + ':' + target.textContent.trim().substring(0, 30);
                }
                return null;
            }""", [Config.GENERIC_TABLES, list(clicked_tables)])
            if clicked:
                table_id = clicked.split(':')[0]
                clicked_tables.add(table_id)
                print(f"      [{clicked}]", flush=True)
                await asyncio.sleep(8); await self.uc()
            else:
                break
        return False

    async def scrape_vag(self, key):
        cfg = Config.BRANDS[key]
        freq = cfg['freq']
        print(f"\n{'='*50}", flush=True)
        print(f"  {key.upper()} - {len(cfg['models'])} models", flush=True)
        print(f"{'='*50}", flush=True)

        for model in cfg['models']:
            if graceful_stop or self.timeout():
                return
            if self.progress.is_completed(key, model):
                print(f"  {model}: [skip]", flush=True)
                continue

            print(f"\n  {model}:", flush=True)
            await self.goto_brand(key)
            r = await self.click_row(model)
            if not r:
                print(f"    Not found", flush=True)
                self.progress.mark_completed(key, model)
                continue
            await asyncio.sleep(15); await self.uc()

            sidebar_skip = ['catalogTable', 'modelTypeTable', 'modelFamiliesTable']
            if cfg.get('skip_model_table'):
                sidebar_skip.append('modelTable')

            years = await self.get_table_items('modelYearTable')
            if not years:
                search_ok = await self.click_through_tables(skip_tables=sidebar_skip)
                if search_ok:
                    await self._search_and_save_tpms(key, model, '', '', freq, cfg)
                else:
                    print(f"    No years, search box not visible", flush=True)
                self.progress.mark_completed(key, model)
                self.progress.save(brand=key, model=model)
                self.models_since_save += 1
                if self.models_since_save >= Config.AUTO_SAVE_INTERVAL:
                    self._auto_save()
                await asyncio.sleep(random.uniform(5, 10))
                continue

            year_list = sorted([y for y in years if y.isdigit()], reverse=True)
            if not year_list:
                year_list = years

            for year in year_list[:5]:
                if graceful_stop or self.timeout():
                    return
                print(f"    Year: {year}", flush=True)

                await self.goto_brand(key)
                await self.click_row(model)
                await asyncio.sleep(15); await self.uc()

                await self.click_table_item('modelYearTable', year)
                await asyncio.sleep(10); await self.uc()

                skip_list = sidebar_skip + ['modelTable', 'modelYearTable']
                search_ok = await self.click_through_tables(skip_tables=skip_list)

                typ = await self.bc()
                typ_short = typ.split(model)[-1].strip()[:50] if model in typ else ''

                if search_ok:
                    await self._search_and_save_tpms(key, model, typ_short, year, freq, cfg)
                else:
                    print(f"      {year}: search box not visible after navigation", flush=True)

            self.progress.mark_completed(key, model)
            self.progress.save(brand=key, model=model)
            self.models_since_save += 1
            if self.models_since_save >= Config.AUTO_SAVE_INTERVAL:
                self._auto_save()
            await asyncio.sleep(random.uniform(5, 10))

    async def _search_and_save_tpms(self, key, model, typ, year, freq, cfg):
        found = False
        for term in cfg.get('search_terms', [cfg['search']]):
            ft = await self.search(term)
            if "keine Einträge" in ft:
                continue
            if cfg.get('nav') == 'bmw':
                parts = self.filter_tpms(await self.extract_bmw(ft))
            else:
                parts = self.filter_tpms(await self.extract_vag(ft))
            if parts:
                print(f"      {year or 'N/A'}: {len(parts)} parts (term: {term})", flush=True)
                for pn, desc in parts[:2]:
                    print(f"        {pn} - {desc[:50]}", flush=True)
                for pn, desc in parts:
                    self.db.add(key.upper(), model, typ, year, pn, freq, desc)
                    self.count += 1
                found = True
                break
        if not found:
            print(f"      {year or 'N/A'}: No results", flush=True)

    def _auto_save(self):
        """Auto-save checkpoint to disk."""
        self.progress.save()
        self.models_since_save = 0
        print(f"\n[AutoSave] Checkpoint saved ({self.count} parts total)", flush=True)

    def timeout(self):
        return (time.time() - self.start) / 3600 >= Config.MAX_RUNTIME_HOURS

    async def run(self):
        if self.force_reset:
            self.progress.reset()
        elif self.progress.should_reset():
            elapsed_days = (time.time() - self.progress.data["cycle_start"]) / 86400
            print(f"\n[Progress] 週期已過期 ({elapsed_days:.1f} 天)", flush=True)
            self.progress.reset()
        elif self.progress.data["completed"]:
            print(f"\n[Progress] 接續上次進度", flush=True)
            self.progress.summary()
        else:
            print(f"\n[Progress] 全新開始", flush=True)

        print(f"\n{'='*60}", flush=True)
        print(f"  Partslink24 TPMS Scraper v6 (Stable)", flush=True)
        print(f"  Format: Brand | Model | Typ | Year | TPMS | Frequency", flush=True)
        print(f"  Auto-save interval: {Config.AUTO_SAVE_INTERVAL} models", flush=True)
        print(f"{'='*60}", flush=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=[
                '--disable-blink-features=AutomationControlled', '--no-sandbox'])
            ctx = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={'width': 1920, 'height': 1080}, locale='de-DE')
            self.page = await ctx.new_page()
            await self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined })")

            try:
                await self.login()
                keys = list(Config.BRANDS.keys())
                if self.brands:
                    keys = [k for k in keys if k in self.brands]

                for key in keys:
                    if graceful_stop or self.timeout():
                        break
                    cfg = Config.BRANDS[key]
                    try:
                        if cfg['nav'] == 'bmw':
                            await self.scrape_bmw(key)
                        else:
                            await self.scrape_vag(key)
                    except Exception as e:
                        print(f"\n[Error] {key}: {e}", flush=True)
                        if 'EPIPE' in str(e):
                            print("[Recovery] Restarting browser...", flush=True)
                            try: await browser.close()
                            except: pass
                            browser = await p.chromium.launch(headless=True, args=[
                                '--disable-blink-features=AutomationControlled', '--no-sandbox'])
                            ctx = await browser.new_context(
                                user_agent="Mozilla/5.0", viewport={'width': 1920, 'height': 1080}, locale='de-DE')
                            self.page = await ctx.new_page()
                            await self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined })")
                            await self.login()
                            print("[Recovery] OK", flush=True)

            except KeyboardInterrupt:
                print("\n[Interrupt]", flush=True)
            except Exception as e:
                print(f"\n[Error] {e}", flush=True)
                import traceback; traceback.print_exc()
            finally:
                self.progress.save()
                self.db.export()
                await browser.close()

        self.db.close()
        elapsed = (time.time() - self.start) / 60
        print(f"\n{'='*60}", flush=True)
        print(f"  Done! {elapsed:.1f} min, {self.count} parts saved", flush=True)
        self.progress.summary()

        db2 = DB()
        for brand, cnt in db2.by_brand():
            print(f"    {brand}: {cnt}", flush=True)
        print(f"    Total: {db2.count()}", flush=True)
        print(f"\n  All records:", flush=True)
        for brand, model, typ, year, pn, freq, desc in db2.all_rows():
            print(f"    {brand:10s} | {model:20s} | {typ:20s} | {year:5s} | {pn:20s} | {freq}", flush=True)
        db2.close()
        print(f"{'='*60}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Partslink24 TPMS Scraper v6 (Stable)")
    parser.add_argument("--brands", nargs="+", default=None)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--progress", action="store_true")
    args = parser.parse_args()

    if args.status:
        db = DB()
        for b, c in db.by_brand():
            print(f"  {b}: {c}")
        print(f"  Total: {db.count()}")
        print(f"\nAll records:")
        for brand, model, typ, year, pn, freq, desc in db.all_rows():
            print(f"  {brand:10s} | {model:20s} | {typ:20s} | {year:5s} | {pn:20s} | {freq}")
        db.close()

    elif args.progress:
        pm = ProgressManager()
        pm.summary()

    else:
        asyncio.run(Scraper(brands=args.brands, force_reset=args.reset).run())