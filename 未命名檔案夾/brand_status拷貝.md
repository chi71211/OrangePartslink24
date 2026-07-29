# Partslink24 Brand Status Reference

## Confirmed TPMS Brands (Stable Version)

| Brand | Service | Navigation | Status | Notes |
|-------|---------|------------|--------|-------|
| BMW | bmw_parts | BMW (series/modelType/restrictions) | ✅ Confirmed | 1362, 8507 634, 6877 937, etc. |
| Mini | mini_parts | BMW | ✅ Confirmed | Same nav as BMW |
| Audi | audi_parts | VAG (generic tables) | ✅ Confirmed | 4G5 071 210 A, S0 907 273 B, etc. |
| VW | vw_parts | VAG | ✅ Confirmed | H4 839 901 B, WA 959 651 A, etc. |
| Porsche | porsche_parts | VAG | ✅ Confirmed | 95B 010 128 K, PP 907 273 D, etc. |
| SEAT | seat_parts | VAG | ✅ Confirmed | FA 837 902 E, etc. |
| Skoda | skoda_parts | VAG | ✅ Confirmed | 81A 907 660 B, etc. |
| Cupra | cupra_parts | VAG | ✅ Confirmed | Shared with SEAT models |

## Indirect TPMS Brands (No direct TPMS parts)

| Brand | Service | Navigation | Status | Notes |
|-------|---------|------------|--------|-------|
| Volvo | volvo_parts | VAG | ❌ Indirect | Uses ABS-based system |
| Peugeot | peugeot_parts | VAG | ❌ Indirect | Uses ABS-based system |
| Opel | psa_opel_parts | VAG | ❌ Indirect | Uses ABS-based system |
| Citroen | citroen_parts | VAG | ❌ Indirect | Uses ABS-based system |
| Fiat | fiatp_parts | VAG | ❌ Indirect | Uses ABS-based system |
| Dacia | dacia_parts | VAG | ❌ Indirect | Uses ABS-based system |
| Mitsubishi | mmc_parts | Mitsubishi (DIV) | ❌ Indirect | Uses ABS-based system |
| Polestar | polestar_parts | VAG | ❌ Indirect | Uses ABS-based system |
| Jaguar | jaguar_parts | VAG | ❌ Indirect | Uses ABS-based system |
| Land Rover | landrover_parts | VAG | ❌ Indirect | Uses ABS-based system |

## Blocked Brands (Cannot scrape)

| Brand | Service | Navigation | Status | Notes |
|-------|---------|------------|--------|-------|
| Mercedes | mercedes_parts | Mercedes | 🔒 Blocked | Search box hidden at all levels |
| Toyota | toyota_parts | VAG | 🔒 Blocked | 0 results for all search terms |
| Ford | fordp_parts | Legacy | 🔒 Blocked | VIN-based lookup only |
| Hyundai | hyundai_parts | Legacy | 🔒 Blocked | VIN-based lookup only |
| Kia | kia_parts | Legacy | 🔒 Blocked | VIN-based lookup only |
| Nissan | nissan_parts | Legacy | 🔒 Blocked | VIN-based lookup only |

## Brands Not on Partslink24

| Brand | Notes |
|-------|-------|
| Honda | Does not exist on Partslink24 |
| Mazda | Does not exist on Partslink24 |

## Key Technical Notes

1. **React SPA vs Legacy UI**: BMW/VAG brands use React SPA with `_selectable_` CSS class. Ford/Hyundai/Kia/Nissan use legacy table UI with `vehicle.action` URLs.

2. **Search Box**: Standard search requires `[data-test-id="partSearchInput"]` input field + `[data-test-id="sendPartSearch"]` button. Some brands (Mitsubishi) use div-based search.

3. **Usercentrics Blocker**: `#usercentrics-root` blocks all pointer events. Must remove via JS 3x (login, goto_brand, search).

4. **VAG Part Number Format**: VAG uses concatenated format (e.g., `S0 907 273 B`). Regex preprocessing with `re.sub(r'(\d{4,})', r' \1 ', clean)` is required.

5. **BMW Model Priority**: Prefers G > F > U > others > E > C prefix to get latest generation.

6. **Auto-Save**: Stable version saves checkpoint every 5 models. Resume from last checkpoint on restart.
