# TPMS Sensor Parts Summary - Partslink24 Verified Results v4.0

## 爬蟲版本：v4.0（支援記憶體/斷點續爬）

### 7天週期系統
- 每次啟動檢查 `scrape_progress.json`
- 7天內接續執行，跳過已完成車款
- 超過7天自動重新開始
- 支援 SIGINT/SIGTERM 優雅中斷

## BMW Group

### BMW - Direct TPMS (RDC 433MHz)
Found on: F07 GT (5'), F30 (3') with S2VBA = JA

| Part Number | Description | Notes |
|---|---|---|
| 36 10 6 856 227 | Radelektronikmodul RDC 433MHZ | LOW COST variant, orange |
| 36 10 6 890 964 | Radelektronikmodul RDC 433MHZ | Current |
| 36 10 6 874 830 | Radelektronikmodul RDC 433MHZ | |
| 36 10 6 874 829 | Radelektronikmodul RDC 433MHZ | |
| 36 14 6 792 829 | Schraubventil RDC | Valve |
| 36 14 6 792 830 | Schraubventil RDC | GRÜN (green) |
| 36 14 6 792 831 | Schraubventil RDC | GELB (yellow) |
| 36 10 6 881 474 | Steuergerät RDC | **Control unit, NOT sensor** |

### BMW - Indirect TPMS (RDCi)
Found on: F30 (3') - uses ABS-based indirect sensing

| Part Number | Description | Notes |
|---|---|---|
| 36 10 6 881 890 | Radelektronikmodul RDCi m. Schraubventil | Combined module |
| 36 14 6 867 031 | Ventileinsatz RDCi | Valve insert |
| 36 14 6 867 030 | Ventilkappe RDCi | Valve cap |
| 36 10 6 876 673 | Rep. Satz Schraubventil RDCi | Repair kit |

### MINI
- Uses **BMW's 433MHz RDC sensors** (same as BMW)
- MINI Countryman F60 confirmed
- No separate TPMS parts in Partslink24
- One sensor per car

---

## Audi Group

### Audi - Direct TPMS
Found on: A3 2025

| Part Number | Description | Notes |
|---|---|---|
| 95C 907 255 | Sensor für Reifendruck | Latest (2026-2027) |
| 5Q0 907 275 F | Sensor für Reifendruck | Reifendruckkontrollsystem |
| 9J1 907 255 | Sensor für Reifendruck | Older (to 2026-03-09) |
| 9J1 907 255 D | Sensor für Reifendruck | Variant |

**NOT sensors (control units):**
- 8S0 907 273 B - Steuergerät für Reifendruckkontrolle
- 3WA 907 273 H - Steuergerät für Reifendruckkontrolle

### VW - Direct TPMS
Found on: Tiguan, Touareg
NOT found on: Golf, Polo, T-Roc (likely use indirect TPMS)

| Part Number | Description | Found On |
|---|---|---|
| 5Q0 907 275 G | Sensor für Reifendruck | Tiguan (from 2020-06-15) |
| 5Q0 907 275 C | Sensor für Reifendruck | Tiguan (to 2020-06-15) |
| 5Q0 907 275 B | Sensor für Reifendruck | Tiguan (to 2020-06-15) |
| 5Q0 907 275 F | Sensor für Reifendruck | Tiguan/Kodiaq |
| 5Q0 907 275 H | Sensor für Reifendruck | Touareg |

### SEAT - Direct TPMS
Found on: Leon

| Part Number | Description | Notes |
|---|---|---|
| 5FA 837 901 F | Sensor für Reifendruck | Leon/Cupra shared |

### Cupra
- Same parts as SEAT (Leon shared platform)

### Skoda - Direct TPMS
Found on: Kodiaq, Octavia

| Part Number | Description | Found On |
|---|---|---|
| 5Q0 907 275 F | Sensor für Reifendruck | Kodiaq (same as VW) |
| 5E3 010 000 L | Sensor für Reifendruck | Octavia |
| 81A 907 660 B | Sensor für Reifendruck | Octavia |

### Porsche - Direct TPMS (433MHz)
Found on: Taycan, Macan

| Part Number | Description | Found On |
|---|---|---|
| PAD 907 255 A | Sensor für Reifendruck | Macan (current) |
| PAD 907 255 B | Sensor für Reifendruck | Macan |
| PAD 907 255 C | Sensor für Reifendruck | Macan |
| PAD 907 255 | Sensor für Reifendruck | Macan |
| PAB 907 275 A | Sensor für Reifendruck | Taycan/Macan |
| PAB 907 275 | Sensor für Reifendruck | Taycan (discontinued) |
| 9J1 907 275 A/B/C | Sensor für Reifendruck | Taycan (A,B discontinued) |
| 9A7 907 275 02 | Sensor für Reifendruck | Macan (discontinued, 433MHz) |
| 9A7 907 275 03 | Sensor für Reifendruck | Macan (discontinued) |

---

## Key Notes

1. **BMW has TWO TPMS systems:**
   - **RDC (433MHz direct)** - older models, dedicated sensors on wheels
   - **RDCi (indirect)** - newer models, uses ABS wheel speed sensors

2. **VAG models vary:**
   - Tiguan, Touareg, Kodiaq, Octavia have direct TPMS
   - Golf, Polo, T-Roc likely use indirect TPMS (no sensor parts found)

3. **All Porsche models use direct TPMS (433MHz)**

4. **SEAT and Cupra share parts** (Leon platform)

5. **MINI uses BMW's sensors** (433MHz RDC)

6. **Verification needed:** User requested clicking into each part detail page to confirm it's a wheel-mounted TPMS sensor (not control unit). Screenshots saved in `TPMS_Exports/screenshots/details/`.

---

## v4.0 記憶體系統

### 進度檔案格式
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

### CLI 命令
```bash
# 查看進度
python partslink_tpms.py --progress

# 查看資料庫統計
python partslink_tpms.py --status

# 強制重新開始
python partslink_tpms.py --reset

# 只跑特定品牌
python partslink_tpms.py --brands bmw audi
```

### 7天週期邏輯
```
每次啟動：
  1. 讀取 scrape_progress.json
  2. 如果 cycle_start 不存在 → 全新開始
  3. 如果 cycle_start < 7天 → 接續執行
  4. 如果 cycle_start > 7天 → 清空進度重新開始
```

---

*更新日期：2026 年 7 月 24 日*
*爬蟲版本：v4.0*
*已驗證零件：48 個（BMW/Audi/VW/SEAT/Skoda/Cupra/Porsche/MINI）*
