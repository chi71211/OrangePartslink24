# Partslink24 TPMS 爬蟲技術報告 v4.0

---

## 一、專案概況

### 目標
從 Partslink24（歐洲汽車零件目錄系統）自動化爬取 **BMW 集團**（BMW、MINI）與 **Audi 集團**（Audi、VW、Porsche、SEAT、Skoda、Cupra）的 TPMS（胎壓監測系統）感測器零件號碼。

### 涵蓋範圍

| 集團 | 品牌 | 車款數量 | 搜尋關鍵字 |
|------|------|----------|-----------|
| BMW | BMW | 16 個車系 | `433MHz` |
| BMW | MINI | 3 個車系 | `433MHz` |
| Audi | Audi | 9 個車款 | `Sensor für Reifendruck` |
| VW | Volkswagen | 11 個車款 | `Sensor für Reifendruck` |
| VW | Porsche | 6 個車款 | `Sensor für Reifendruck` |
| VW | SEAT | 5 個車款 | `Sensor für Reifendruck` |
| VW | Skoda | 7 個車款 | `Sensor für Reifendruck` |
| VW | Cupra | 4 個車款 | `Sensor für Reifendruck` |

### 技術棧
- **語言**：Python 3.12
- **瀏覽器自動化**：Playwright（headless Chromium）
- **資料儲存**：SQLite + CSV 匯出
- **平台**：macOS（Darwin）

---

## 二、程式設計架構

### 核心類別

```
┌─────────────────────────────────────────────┐
│                 Config                      │
│  ├── BASE_URL, LOGIN_URL                    │
│  ├── COMPANY_ID, USERNAME, PASSWORD         │
│  ├── DB_FILE, CSV_DIR, PROGRESS_FILE        │
│  ├── CYCLE_DAYS, MAX_RUNTIME_HOURS          │
│  └── BRANDS (dict: 品牌設定)                │
├─────────────────────────────────────────────┤
│              ProgressManager                │
│  ├── load/save  → 讀寫 scrape_progress.json │
│  ├── mark_completed() → 標記車款完成        │
│  ├── is_completed() → 檢查是否已爬取        │
│  ├── should_reset() → 7天週期檢查           │
│  └── reset() → 清空進度重新開始             │
├─────────────────────────────────────────────┤
│                   DB                        │
│  ├── __init__()  → 建立 SQLite 資料表       │
│  ├── add()       → 新增感測器記錄           │
│  ├── count()     → 統計總筆數               │
│  ├── by_brand()  → 按品牌統計               │
│  ├── unique_parts() → 去重零件清單          │
│  └── export()    → 匯出 CSV                 │
├─────────────────────────────────────────────┤
│                 Scraper                     │
│  ├── login()     → 自動登入                 │
│  ├── goto_brand() → 切換品牌目錄            │
│  ├── click_sel() → CSS 選擇器空間定位       │
│  ├── search()    → 搜尋零件                 │
│  ├── scrape_bmw() → BMW 式導覽              │
│  ├── scrape_vag() → VAG 式導覽              │
│  ├── extract_bmw() → BMW 格式解析           │
│  ├── extract_vag() → VAG 格式解析           │
│  ├── filter_tpms() → TPMS 過濾             │
│  └── run()       → 主迴圈 + 進度管理        │
└─────────────────────────────────────────────┘
```
│                Scraper                      │
│  ├── login()          → 自動登入           │
│  ├── goto_brand()     → 進入品牌目錄       │
│  ├── scrape_bmw()     → BMW 式導覽+搜尋    │
│  ├── scrape_vag()     → VAG 式導覽+搜尋    │
│  ├── search()         → 零件搜尋           │
│  ├── extract_bmw()    → 解析 BMW 零件號    │
│  ├── extract_vag()    → 解析 VAG 零件號    │
│  └── filter_tpms()    → 過濾 TPMS 感測器  │
└─────────────────────────────────────────────┘
```

### 兩種導覽模式

Partslink24 是一個 React SPA（單頁應用），BMW 和 VAG 集團使用**不同的導覽結構**：

**BMW 式導覽**（BMW、MINI）：
```
品牌目錄 → 車系(3'/5'/X3...) → 車型(F30/G05...) → 引擎 → ECE → 搜尋
```

**VAG 式導覽**（Audi/VW/Porsche/SEAT/Skoda/Cupra）：
```
品牌目錄 → 車款(A3/Golf/Tiguan...) → 年份(2024) → 限制條件1 → 限制條件2 → 搜尋
```

---

## 三、簡化流程圖

```
START
  │
  ▼
┌──────────────────┐
│  啟動 Chromium     │
│  (headless 模式)   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  自動登入          │
│  ├ 移除彈窗廣告    │
│  ├ 填入帳號密碼    │
│  ├ 點擊登入按鈕    │
│  └ 等待 Cookie    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  遍歷所有品牌      │
│  (BMW→MINI→       │
│   Audi→VW→Porsche │
│   →SEAT→Skoda→    │
│   Cupra)          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐    ┌─────────────────────┐
│  判斷導覽模式      │    │  BMW 式導覽          │
│  nav == 'bmw'?    │───→│  ├ 選擇車系          │
└────────┬─────────┘    │  ├ 選擇車型(非M)      │
         │              │  ├ 選擇引擎           │
         │ No           │  └ 選擇 ECE           │
         ▼              └────────┬────────────┘
┌──────────────────┐             │
│  VAG 式導覽       │             │
│  ├ 選擇車款       │             │
│  ├ 選擇年份       │             │
│  └ 選擇限制條件   │             │
└────────┬─────────┘             │
         │                       │
         ▼                       ▼
┌──────────────────────────────────────┐
│           執行零件搜尋                │
│  ├ 清空搜尋框                        │
│  ├ 輸入關鍵字 (433MHz/Sensor...)     │
│  ├ 點擊搜尋按鈕                      │
│  └ 等待 12 秒載入                    │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│           解析搜尋結果                │
│  ├ 正則表達式提取零件號碼             │
│  ├ 過濾 TPMS 相關零件               │
│  ├ 排除控制單元(Steuergerät)        │
│  └ 儲存至 SQLite                     │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  匯出 CSV         │
│  關閉瀏覽器       │
│  輸出統計         │
└──────────────────┘
         │
         ▼
        END
```

---

## 四、技術問題與解決方法

### 問題 1：輸出緩衝導致長時間無反應

**現象**：執行爬蟲後長時間無任何輸出，看起來像當機。

**原因**：Python 的 `print()` 在非 TTY 環境下會啟用行緩衝（line buffering），導致輸出積累在緩衝區。

**解決**：在腳本最頂部加入：
```python
import sys; print("START", flush=True)
```
所有後續的 `print()` 都加上 `flush=True`。

---

### 問題 2：Usercentrics Cookie 同意彈窗阻擋操作

**現象**：頁面上出現 `#usercentrics-root` 影子 DOM 元素，擋住所有滑鼠事件。

**原因**：Partslink24 使用 Usercentrics 作為 Cookie 同意管理，該元素以 shadow DOM 形式存在，無法直接點擊。

**解決**：反覆執行 JS 移除該元素：
```python
async def uc(self):
    await self.page.evaluate(
        '() => { const u = document.querySelector("#usercentrics-root"); if (u) u.remove(); }')
```
在每個關鍵操作前後都呼叫 `uc()`，通常執行 3 次確保完全移除。

---

### 問題 3：CSS 模組選擇器格式

**現象**：`querySelectorAll('[class* "_selectable_"]')` 拋出 `SyntaxError: not a valid selector`。

**原因**：CSS 屬性選擇器語法錯誤，缺少 `=` 符號。

**解決**：必須使用 `[class*="_selectable_"]`（有等號）。

```python
SEL = '[class*="_selectable_"]'  # 正確
# SEL = '[class* "_selectable_"]'  # 錯誤！
```

---

### 問題 4：BMW 車型選擇錯誤（選到 M 系列或老車）

**現象**：`models[-1]` 總是選到 M3/M4/M5 等高性能版本，`models[0]` 選到 E21 等老車。

**原因**：Partslink24 的車型列表按字母排序，不按年代排列。M 系列排在後面，E 系列排在前面。

**解決**：從列表中優先選擇 G/F/U 開頭的現代非 M 車型：
```python
for m in models:
    code = m.split('(')[0].strip().upper()
    is_m = 'M3' in code or 'M4' in code or 'M5' in code
    if not is_m and any(p in code for p in ['G2','G3','F2','F3','F4','F5','F6','F7','U1','U2']):
        model = m; break
```

---

### 問題 5：BMW 和 VAG 使用不同的目錄結構

**現象**：VAG 品牌用 `modelTable` 導覽方式無法在 BMW 上運作，反之亦然。

**原因**：
- **BMW** 使用多欄表格：`modelTable`(x≈60) → `modelTypeTable`(x≈334) → 引擎(x>500) → ECE(x>600)
- **VAG** 使用 `modelFamiliesTable` + 行點擊 → `modelYearTable` → `restrictionTable1/2/3`

**解決**：在 `Config.BRANDS` 中為每個品牌標記 `'nav': 'bmw'` 或 `'nav': 'vag'`，分別使用 `scrape_bmw()` 和 `scrape_vag()` 兩套導覽邏輯。

---

### 問題 6：部分車款搜尋不到 TPMS 感測器

**現象**：VW Golf、Polo、T-Roc、ID.3、ID.4、SEAT Ibiza、Skoda Fabia 等車款搜尋 `Sensor für Reifendruck` 均無結果。

**原因**：這些車款可能使用**間接式 TPMS**（Indirect TPMS），依靠 ABS 車速感測器運算胎壓變化，不需要獨立的胎壓感測器零件。而 Tiguan、Touareg、Arteon、Kodiaq 等使用**直接式 TPMS**（Direct TPMS），有獨立感測器。

**解決**：需確認哪些車款使用直接式 TPMS。目前確認有直接式感測器的車款：
- VW：Tiguan、Touareg、Arteon
- Skoda：Kodiaq、Octavia
- SEAT：Leon

---

### 問題 7：Playwright 長時間執行後 EPIPE 錯誤

**現象**：執行超過 10 分鐘後出現 `Error: write EPIPE` 並崩潰。

**原因**：Playwright 的 Node.js 子進程與 Python 通訊時，長時間運行可能導致 pipe 斷裂。

**解決**：將大型爬蟲任務拆分為多個小批次執行（例如每次只跑 2-3 個品牌），或加入錯誤處理與重試機制。

---

## 五、已確認的 TPMS 感測器零件號碼

### BMW 集團（433MHz 直接式）

| 品牌 | 零件號碼 | 描述 | 備註 |
|------|---------|------|------|
| BMW | `36 10 6 856 227` | Radelektronikmodul RDC 433MHz | LOW COST，橘色 |
| BMW | `36 10 6 890 964` | Radelektronikmodul RDC 433MHz | 目前使用 |
| BMW | `36 10 6 874 830` | Radelektronikmodul RDC 433MHz | |
| BMW | `36 10 6 874 829` | Radelektronikmodul RDC 433MHz | |
| BMW | `36 14 6 792 829/830/831` | Schraubventil RDC | 氣門嘴（標準/綠/黃） |
| MINI | 同 BMW | 同上 | MINI 使用 BMW 感測器 |

### BMW 集團（間接式 RDCi）

| 零件號碼 | 描述 | 備註 |
|---------|------|------|
| `36 10 6 881 890` | Radelektronikmodul RDCi m. Schraubventil | 搭配 ABS |
| `36 14 6 867 031` | Ventileinsatz RDCi | 氣門嘴內芯 |
| `36 14 6 867 030` | Ventilkappe RDCi | 氣門嘴蓋 |

### Audi 集團（直接式）

| 品牌 | 零件號碼 | 描述 | 適用車款 |
|------|---------|------|---------|
| Audi | `95C 907 255` | Sensor für Reifendruck | A3 (2025) |
| Audi | `5Q0 907 275 F` | Sensor für Reifendruck | A3 |
| Audi | `9J1 907 255/D` | Sensor für Reifendruck | A3 |
| VW | `5Q0 907 275 G` | Sensor für Reifendruck | Tiguan (2020+) |
| VW | `5Q0 907 275 H` | Sensor für Reifendruck | Touareg |
| VW | `5Q0 907 275 C/B/F` | Sensor für Reifendruck | Tiguan/Arteon |
| SEAT | `5FA 837 901 F` | Sensor für Reifendruck | Leon/Cupra |
| Skoda | `5Q0 907 275 F` | Sensor für Reifendruck | Kodiaq |
| Skoda | `5E3 010 000 L` | Sensor für Reifendruck | Octavia |
| Skoda | `81A 907 660 B` | Sensor für Reifendruck | Octavia |
| Porsche | `PAD 907 255 A/B/C` | Sensor für Reifendruck | Macan |
| Porsche | `PAB 907 275/A` | Sensor für Reifendruck | Taycan |
| Porsche | `9J1 907 275 A/B/C` | Sensor für Reifendruck | Taycan |

### 沒有直接式 TPMS 的車款

VW Golf、Polo、T-Roc、ID.3、ID.4、ID.5、Caddy、Taigo、Amarok、SEAT Ibiza、Arona、Skoda Fabia 等車款在 Partslink24 中**找不到直接式 TPMS 感測器零件**，推測使用間接式 TPMS。

---

## 六、未來改進方向

### 1. 零件詳情頁驗證
目前只從搜尋結果頁提取零件號碼，**未驗證**該零件是否為輪框上的胎壓感測器（而非控制單元或支架）。

**改進**：對每個搜尋到的零件，點擊進入詳情頁，截圖並檢查：
- 是否有輪框/輪胎圖片
- 描述中是否包含 `Radelektronikmodul`、`Schraubventil`、`Rad`、`Felge`、`Ventil` 等關鍵字
- 排除 `Steuergerät`（控制單元）、`Halter`（支架）等非感測器零件

### 2. 容錯與重試機制
目前遇到 Playwright EPIPE 錯誤會直接崩潰。

**改進**：
- 每個品牌/車款獨立 try-except
- 自動重新啟動瀏覽器
- 記錄失敗車款清單，支援斷點續爬

### 3. 更完整的車款清單
目前 BMW 只爬了 16 個車系，VAG 品牌也未涵蓋所有車款。

**改進**：
- 動態讀取 Partslink24 上的所有車系/車款
- 自動遍歷所有可用選項
- 加入 Audi Q2、Q4 e-tron、A7 等遺漏車款

### 4. 搜尋關鍵字優化
目前 BMW 用 `433MHz`，VAG 用 `Sensor für Reifendruck`，但部分車款可能需要不同關鍵字。

**改進**：
- 嘗試多組關鍵字：`433MHz`、`RDC`、`RDK`、`Reifendruckmodul`
- 嘗試直接搜尋已知零件號碼前綴（如 `5Q0 907`、`36 10`）

### 5. 資料庫去重與版本追蹤
目前 `UNIQUE` 約束只基於品牌+車系+車型+引擎+零件號碼，無法追蹤零件號碼的更迭歷史。

**改進**：
- 新增 `valid_from`、`valid_to` 欄位
- 記錄零件的取代關係（如 `5Q0 907 275 G` 取代 `5Q0 907 275 C`）
- 建立零件號碼對照表

### 6. 自動化排程
目前需要手動執行。

**改進**：
- 設定 cron job 定期執行（如每週一次）
- 比對新舊資料，自動通知新增/變更的零件
- 產生 HTML 報告供業務使用

### 7. 輸出格式優化
目前只匯出 CSV。

**改進**：
- 匯出 Excel（含多個工作表：按品牌、按車款、零件對照表）
- 生成 PDF 報告
- 建立簡易 Web 看板展示爬取結果

---

## 七、附錄

### 截圖存證
所有截圖存放於 `TPMS_Exports/screenshots/` 目錄：

| 目錄 | 內容 |
|------|------|
| `screenshots/` | 各品牌搜尋結果頁截圖（01-08） |
| `screenshots/details/` | 各零件詳情頁截圖 |
| `screenshots/verified/` | 全面驗證截圖 |
| `screenshots/` | 各品牌搜尋結果頁截圖（01-08） |

### 檔案結構
```
partslink24/
├── partslink_tpms.py          # 主爬蟲腳本 v4.0
├── explore_brands.py          # 品牌探索工具
├── partslink_tpms.db          # SQLite 資料庫
├── scrape_progress.json       # 進度檔案（7天週期）
└── TPMS_Exports/
    ├── tpms_*.csv             # CSV 匯出
    ├── 技術報告_TPMS爬蟲.md     # 本報告（v4.0）
    ├── 技術架構報告_詳細版.md   # 詳細技術架構
    ├── flowchart_TPMS_scraper.md # Mermaid 流程圖
    ├── 更新說明_v4.0.md        # v4.0 更新說明
    └── screenshots/
        ├── 01_BMW_5_433MHz.png
        ├── 02_MINI_Countryman_433MHz.png
        ├── 03_Audi_A3_Sensor_Reifendruck.png
        ├── ...
        ├── details/
        │   ├── BMW_5_F07_36_10_6_856_227.png
        │   ├── Audi_A3_95C_907_255.png
        │   ├── Porsche_Taycan_9J1_detail.png
        │   └── ...
        └── verified/
            ├── VW_Tiguan_results.png
            ├── VW_Touareg_results.png
            └── VW_Arteon_results.png
```

### 執行指令
```bash
# 執行全部品牌
python3 partslink_tpms.py

# 只跑特定品牌
python3 partslink_tpms.py --brands bmw audi vw

# 查看目前狀態
python3 partslink_tpms.py --status

# 查看進度檔案
python3 partslink_tpms.py --progress

# 強制清空進度重新開始
python3 partslink_tpms.py --reset

# 重置資料庫
python3 partslink_tpms.py --reset
```

---

## 六、v4.0 新增功能：記憶體與斷點續爬

### 進度管理系統

我們加入了 `ProgressManager` 類別，用於管理爬取進度：

**進度檔案格式（scrape_progress.json）：**
```json
{
    "cycle_start": 1721827200.0,
    "completed": ["bmw:3'", "bmw:5'", "audi:Audi A3"],
    "last_brand": "vw",
    "last_model": "Tiguan",
    "total_scraped": 42,
    "last_save": 1721830800.0
}
```

**7天週期邏輯：**
```
每次啟動：
  1. 讀取 scrape_progress.json
  2. 如果 cycle_start 不存在 → 全新開始
  3. 如果 cycle_start < 7天 → 接續執行，跳過已完成車款
  4. 如果 cycle_start > 7天 → 清空進度，重新開始
```

### 優雅中斷處理

**Signal Handler：**
```python
graceful_stop = False

def _signal_handler(sig, frame):
    global graceful_stop
    graceful_stop = True
    print("\n[Signal] 收到中斷訊號，正在安全關閉...", flush=True)

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)
```

**斷點跳過邏輯：**
```python
async def scrape_bmw(self, key):
    for series in cfg['series']:
        if graceful_stop or self.timeout():
            return

        # 斷點跳過：如果此車款已完成，跳過
        if self.progress.is_completed(key, series):
            print(f"  {series}: [skip] 已完成", flush=True)
            continue

        # ... 爬取邏輯 ...

        # 標記完成並儲存進度
        self.progress.mark_completed(key, series)
        self.progress.save(brand=key, model=series, count_add=part_count)
```

### 進度查詢CLI

```bash
# 查看進度檔案內容
python partslink_tpms.py --progress

# 顯示內容：
# [Progress] 週期開始: 2026-07-24 10:00
#   已運行: 2.5h / 168h
#   剩餘: 165.5h 後重頭開始
#   已完成: 25/60 個車款
#   已爬取: 42 個零件
#   上次儲存: 10:30:15
```

---

*報告日期：2026 年 7 月 24 日*
*爬蟲版本：v4.0*
*Partslink24 存取帳號：de-416440*
