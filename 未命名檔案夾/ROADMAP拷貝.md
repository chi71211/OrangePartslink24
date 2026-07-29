# 後續規劃

## Phase 1 — 完整爬取 8 品牌 (立即)
- [ ] 執行完整 8 品牌爬取 (`python3 partslink_tpms_stable.py`)
- [ ] 檢查結果，確認各品牌都有 TPMS 零件
- [ ] 修復 BMW 只爬最新世代問題 (目前跳過 F30, F25 等舊世代)
- [ ] 檢查 Mini, Cupra 是否確實有 TPMS

## Phase 2 — BMW 多世代支援 (~1hr)
- [ ] `scrape_bmw()` 不只用 `min(models, key=_model_priority)` 選一個
- [ ] 改為遍歷 ALL 底盤代碼 (G20, F30, E90...)，直到找到 TPMS
- [ ] 如果找到就存檔並 break (避免重複)

## Phase 3 — Ford 調查 (待研究)
- [ ] Ford 使用 legacy UI (`vehicle.action`)
- [ ] 目前無法文字搜尋 (VIN only)
- [ ] 研究是否能透過「零件群組瀏覽」(如 "31 Räder & Reifen") 找到 TPMS
- [ ] 需要分析 Ford catalog 的 HTML 結構

## Phase 4 — 擴展品牌 (中長期)
- [ ] **Mercedes**: 搜尋框隱藏問題 — 可能需 JS 觸發
- [ ] **Toyota**: 0 結果問題 — 可能需要不同搜尋詞
- [ ] **Hyundai/Kia/Nissan**: legacy UI VIN 限制
- [ ] 重新評估間接 TPMS 品牌 (Volvo, Peugeot 等)

## Phase 5 — 優化 (長期)
- [ ] 多線程爬取 (同時爬多品牌)
- [ ] 失敗重試機制 (目前只重啟 EPIPE)
- [ ] Web UI 儀表板
- [ ] 自動排程 (cron 每 7 天)
- [ ] 差異報告 (新發現的零件 vs 之前)

## 已知問題清單

| 問題 | 影響 | 狀態 |
|------|------|------|
| BMW 只選最新底盤 (G > F > E) | 漏掉舊款 TPMS | ⏳ 待修 |
| usercentrics-root 反覆出現 | pointer events 被擋 | ✅ 已處理 |
| EPIPE crash (長時間) | 中斷爬取 | ✅ 已處理 (auto-recovery) |
| VAG 黏合零件號碼 | 無法正確解析 | ✅ 已處理 (regex preprocess) |
| Partslink24 慢 (8-20s 等待) | 爬取速度慢 | ⚠️ 無解 (網站限制) |
