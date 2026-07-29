# Partslink24 TPMS Sensor Scraper v6 (Stable)

## 概述

自動爬取 Partslink24 線上零件目錄，收集 **TPMS 胎壓感測器** 零件號碼。支援 8 個已確認有 TPMS 零件的品牌。

輸出格式: `Brand | Model | Typ | Year | TPMS(Teilenummer) | Frequency`

輸出儲存: SQLite DB (`partslink_tpms.db`) + CSV Export (`TPMS_Exports/`)

## 支援品牌 (8)

| 品牌 | 導覽方式 | 車型數 | 已確認 |
|------|---------|--------|--------|
| BMW | BMW 式 (series → chassis → engine → market) | 11 | ✅ |
| Mini | BMW 式 | 4 | ✅ |
| Audi | VAG (通用表格) | 9 | ✅ |
| VW | VAG (通用表格) | 8 | ✅ |
| Porsche | VAG (通用表格) | 4 | ✅ |
| SEAT | VAG (通用表格) | 5 | ✅ |
| Skoda | VAG (通用表格) | 6 | ✅ |
| Cupra | VAG (通用表格) | 4 | ✅ |

## 環境需求

```bash
# Python 3.8+
pip install playwright nest_asyncio
playwright install chromium
```

## 快速開始

```bash
# 爬取全部 8 品牌
python3 partslink_tpms_stable.py

# 爬取指定品牌
python3 partslink_tpms_stable.py --brands bmw audi vw

# 查看 DB 內容
python3 partslink_tpms_stable.py --status

# 查看當前進度
python3 partslink_tpms_stable.py --progress

# 重置進度重新開始
python3 partslink_tpms_stable.py --reset
# 或指定品牌重置:
python3 partslink_tpms_stable.py --brands bmw --reset
```

## 架構

```
partslink_tpms_stable.py        # 主程式 (788 lines)
partslink_tpms.db               # SQLite DB (自動建立)
TPMS_Exports/                   # CSV 匯出目錄
scrape_progress.json            # 進度記錄 (7天週期)
brand_status.md                 # 品牌狀態參考
```

### 類別說明

**Config** — 設定: 登入資訊、品牌清單、導覽表格順序
**ProgressManager** — 進度管理: 7天週期、每個車款完成標記、自動存檔
**DB** — 資料庫: sensors 表 (Brand, Model, Typ, Year, Teilenummer, Frequency, Description)
**Scraper** — 爬蟲核心: Playwright 自動化、導覽、搜尋、解析

## 導覽方式

### BMW 式 (scrape_bmw)
1. 選擇車系 (3', 5', X3...) → `modelTable`
2. 選擇底盤代碼 (G20 > F30...) → `modelTypeTable` (跳過 M 車型)
3. 選擇車體類型 → `restrictionTable1`
4. 選擇引擎 → `restrictionTable2`
5. 遍歷市場 (ECE, IND, THA...) → `restrictionTable3`
6. 搜尋 TPMS 關鍵字

### VAG 通用表格 (scrape_vag / click_through_tables)
1. 點選車型 (`data-test-id="row"`)
2. 選擇年份 → `modelYearTable`
3. 自動點選所有剩餘表格直到搜尋框出現
4. 表格順序: catalogTable → modelTable → modelTypeTable → modelYearTable → bodyTable → engineTable → gearboxTable → transmissionTable → driveTypeTable → bodyTypeTable → fuelTypeTable → restrictionTable1/2/3 → partnerGroupTable → variantTable → subModelTable → categoryTable
5. 搜尋 TPMS 關鍵字

## 搜尋引擎 (search)

使用 Proactslink24 React SPA 的搜尋框 `[data-test-id="partSearchInput"]`:
1. 驗證搜尋框可見 (不可見則 scrollTo(0,0) 重試)
2. 清空輸入框 (`i.value = ''`)
3. 鍵入搜尋詞 (`page.keyboard.type(term, delay=40)`) — React 需要 keyboard event
4. 點擊搜尋按鈕 `[data-test-id="sendPartSearch"]`
5. 等待 12 秒載入
6. 移除 usercentrics-root
7. 擷取結果: companion 區域或所有 `data-test-id="row"` 元素

## 零件解析

### BMW 零件格式
- 正規表示式: `\d{2}\s\d{2}\s\d\s\d{3}\s\d{3}` (範例: `13 62 8 507 634`)
- 描述篩選: RDC, Reifendruck, 433, 315, Schraubventil

### VAG 零件格式
- 正規表示式: `[0-9A-Z]{2,4}\s[0-9A-Z]{3}\s[0-9A-Z]{3}(\s[0-9A-Z]{1,2})?`
- 預處理: `re.sub(r'(\d{4,})', r' \1 ', clean)` 處理黏合格式
- 排除前綴: 000, 011, 100, 999
- 描述篩選: Sensor, Reifendruck, RDC, RDK, TPMS

### filter_tpms 過濾規則
- 排除關鍵字: KENNSCHILD, DEKORLEISTE, SCHUTZLEISTE, HALTER, ABDECKUNG, SCHRAUBE, MUTTER, 等
- TPMS 關鍵字: REIFENDRUCK, TPMS, RDC, RDK, RDKS, RADSENSOR, TIRE PRESSURE, TYRE PRESSURE, WHEEL SENSOR, RAD ELEKTRONIK, REIFENDRUCKKONTROLLE
- TPMS 零件號碼片段: 907 255, 907 275, 907 273, 959 65, 837 90, 907 66, 839 90, 880 74, 998 270, 6 877, 6 856, 6 874, 6 890, 6 881

## 已知問題

### usercentrics-root
`#usercentrics-root` iframe 會阻擋所有 pointer events。需在 login, goto_brand, search 後各移除一次。

### EPIPE Crash
長時間運行後 Playwright browser process 會 crash (EPIPE)。程式有自動 recovery 機制:
- 關閉舊 browser
- 開啟新 browser + context + page
- 重新登入
- 繼續爬取

### BMW 型號優先順序
`_model_priority`: G(0) > F(1) > U(2) > 其他(3) > E/C(5) > M(999)
只選最高優先級的底盤代碼，不會嘗試多個世代。

### 網路延遲
Partslink24 反應慢: goto_brand 需等 20s, click 後等 8-15s, search 等 12s。

## DB Schema

```sql
CREATE TABLE sensors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    Brand TEXT,
    Model TEXT,
    Typ TEXT,
    Year TEXT,
    Teilenummer TEXT,
    Frequency TEXT,
    Description TEXT,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(Brand, Model, Typ, Year, Teilenummer)
);
```

## 進度系統 (ProgressManager)

- **7 天週期**: 到期自動重置
- **模型級粒度**: 每個車款完成即記錄
- **Auto-save**: 每 5 車款自動存檔
- **JSON 格式**: `scrape_progress.json`

```json
{
    "cycle_start": 1785131707.59,
    "completed": ["audi:Audi A3"],
    "last_brand": "audi",
    "last_model": "Audi A4",
    "total_scraped": 51,
    "last_save": 1785206765.61
}
```
