# Partslink24 TPMS 爬蟲 v4.0 更新說明

## 主要新增功能

### 1. 記憶體/斷點續爬系統
- **`scrape_progress.json`**：記錄已完成的品牌+車款組合
- **7天週期**：7天內接續執行，超過7天自動重新開始
- **斷點跳過**：已完成的車款不會重複爬取

### 2. 優雅中斷處理
- **Signal Handler**：捕捉 SIGINT (Ctrl+C) 和 SIGTERM 訊號
- **`graceful_stop` 標誌**：在每個車款處理前檢查，安全中斷
- **緊急安全存檔**：`finally` 區塊確保進度不丢失

### 3. CLI 進度查詢
```bash
python partslink_tpms.py --status      # 查看資料庫統計
python partslink_tpms.py --progress    # 查看進度檔案
python partslink_tpms.py --reset       # 強制清空進度
python partslink_tpms.py --brands bmw  # 只跑特定品牌
```

## 進度檔案格式

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

## 7天週期邏輯

```
每次啟動：
  1. 讀取 scrape_progress.json
  2. 如果 cycle_start 不存在 → 全新開始
  3. 如果 cycle_start < 7天 → 接續執行，跳過已完成車款
  4. 如果 cycle_start > 7天 → 清空進度，重新開始
```

## 已驗證品牌（v3.0 成果）

| 品牌 | 搜尋關鍵字 | 已驗證零件 |
|------|-----------|-----------|
| BMW | `433MHz` | `36 10 6 856 227`, `36 10 6 890 964`, `36 10 6 874 830` 等 |
| Audi | `Sensor für Reifendruck` | `95C 907 255` (2026-2027最新) |
| VW | `Sensor für Reifendruck` | `5Q0 907 275 G/C/B/F/H` (Tiguan/Touareg/Arteon) |
| SEAT | `Sensor für Reifendruck` | `5FA 837 901 F` (Leon) |
| Skoda | `Sensor für Reifendruck` | `5Q0 907 275 F` (Kodiaq), `81A 907 660 B` (Octavia) |
| Cupra | `Sensor für Reifendruck` | `5FA 837 901 F` (同SEAT) |
| Porsche | `Sensor für Reifendruck` | `PAD 907 255 A/B/C` (Macan), `9J1 907 275` (Taycan) |
| MINI | `433MHz` | 使用BMW感測器，無獨立零件 |

## 待處理品牌

| 品牌 | 狀態 | 問題 |
|------|------|------|
| Mercedes-Benz | ❌ | chassis代碼（W206等）列匹配失敗 |
| Toyota | ❌ | 目錄結構有，但搜尋回傳0結果 |
| Volvo | ❌ | 同Toyota |
| Honda/Nissan/Mazda等 | ❌ | 服務名稱可能錯誤，內容載入失敗 |

## 技術文件

- `技術架構報告_詳細版.md`：完整技術架構（已更新v4.0）
- `技術報告_TPMS爬蟲.md`：中文技術報告
- `flowchart_TPMS_scraper.md`：Mermaid流程圖（已更新v4.0）
- `tpms_verified_summary.md`：已驗證零件摘要

---

*更新日期：2026 年 7 月 24 日*
*版本：v4.0*
