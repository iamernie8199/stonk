# 📈 台股深度對話式研究報告 (Taiwan Stock Dialogue Research Reports)

歡迎來到 **台股深度對話式研究報告索引庫**！本專案收錄由 AI 研究團隊（資深研究員 Mentor 與菜鳥研究員 Junior）針對台股關鍵產業與焦點個股所進行的深度擬真對話研究報告。

🌐 **線上閱讀網站 (GitHub Pages)**：[https://iamernie8199.github.io/stonk/](https://iamernie8199.github.io/stonk/)

---

## ✨ 網站亮點與特色

### 1. 💡 多元閱讀模式 (One-Page Interactive Reader)
每一份個股報告皆採用一頁式 HTML 現代化 UI 設計，支援以下切換模式：
- **完整對話模式**：呈現 Mentor 與 Junior 雙方來回問答，深入產業脈絡、估值與反方質疑壓力測試。
- **資深研究員摘要版 (Senior Digest)**：一鍵抽出資深研究員精華結論，並自動建置頁面目錄索引（TOC）。
- **Focus 沉浸閱讀**：隱藏邊欄與干擾元素，提供單欄高專注度的閱讀體驗。

### 2. 🎯 精準區域加權核心關鍵字 (Section-Weighted Core Keywords)
索引頁卡片標註每家公司的核心亮點，採用 **區域加權評分引擎 (Section-Weighted Scoring Engine)**：
- 優先權重比對報告標題、研究目的與對話總結，確保核心關鍵字能精準反映公司主營業務與產業地位（例如台積電 ➔ `先進製程 / 先進封裝 (CoWoS)`；台達電 ➔ `AI 電力基建 / 電源系統`）。

### 3. 🔍 即時搜尋與主題篩選 (Search & Topic Filters)
- **主題篩選**：支援 `AI 伺服器`、`半導體 / 封裝`、`電力 / 電源`、`AI ASIC / TPU`、`材料 / CCL`、`網通 / 交換器`、`被動元件 / 零組件` 等主題快速切換。
- **多維度搜尋**：支援按股票代號、公司名稱、產業關鍵字即時模糊搜尋。
- **排序切換**：可自由按股票代號（升/降序）或公司名稱順序排列報告卡片。

---

## 📊 目前收錄個股總覽

| 股票代號 | 公司名稱 | 核心關鍵字標籤 | 核心研究主線 |
| :--- | :--- | :--- | :--- |
| **TW-1303** | **南亞** | `高階 CCL / Low CTE 玻纖布` | 電子材料、Low CTE 玻纖布、高階 CCL、記憶體資產 |
| **TW-2303** | **聯電** | `成熟製程 / 特殊製程` | 成熟與特殊製程、8/12吋晶圓代工、eHV FinFET、CPO 矽光子 |
| **TW-2308** | **台達電** | `AI 電力基建 / 電源系統` | AI 伺服器電源、HVDC / 800VDC、CDU 散熱、微電網 |
| **TW-2317** | **鴻海** | `AI 伺服器 / 整機整櫃 (Rack-scale)` | AI 伺服器、Rack-scale 整機整櫃、電動車、人形機器人 |
| **TW-2327** | **國巨** | `MLCC / 被動元件平台` | 全球 MLCC 與被動元件平台、車用 / 工控 / AI 伺服器元件 |
| **TW-2330** | **台積電** | `先進製程 / 先進封裝 (CoWoS)` | N3/N2 先進製程、CoWoS 先進封裝、GAAFET、晶圓代工領導者 |
| **TW-2345** | **智邦** | `高速交換器 / CPO 矽光子` | 高速網通交換器 (800G / 1.6T)、CPO / NPO 光通訊 |
| **TW-2382** | **廣達** | `AI 伺服器 / 整機整櫃 (Rack-scale)` | AI 伺服器代工、L10-L11 Rack-scale 機櫃整合、ODM 龍頭 |
| **TW-2383** | **台光電** | `高階 CCL / Low CTE 玻纖布` | AI 伺服器 UBB/OAM 銅箔基板、高階 CCL 領導廠 |
| **TW-2408** | **南亞科** | `DRAM 記憶體 / HBM 外溢` | DRAM 記憶體循環、成熟 DRAM、HBM 缺貨外溢效應 |
| **TW-2454** | **聯發科** | `AI ASIC / 手機與晶片平台` | 天璣系列手機 SoC、AI ASIC 邊緣運算、晶片設計平台 |
| **TW-3037** | **欣興** | `ABF 載板 / 先進基板` | ABF 高階載板、先進晶片基板、PCB 升級需求 |
| **TW-3711** | **日月光** | `先進封測 / OSAT 平台` | 全球 OSAT 封測龍頭、先進封測、SiP 系統級封裝 |
| **TW-6669** | **緯穎** | `AI 伺服器 / 整機整櫃 (Rack-scale)` | 雲端資料中心 AI 伺服器、L10-L11 液冷機櫃整合 |
| **TW-7769** | **鴻勁** | `晶片測試設備 / SLT Handler` | 高階晶片 FT / SLT 測試分選機 (Handler)、CPO 測試介面 |

---

## 🛠️ 專案結構

```
stonk/
├── index.html                                        # 站點首頁與個股卡片索引
├── README.md                                         # 本說明文件
├── TW-1303_南亞_深度對話式研究報告_2026-08-04.html       # 各個股深度 HTML 報告
├── TW-2330_台積電_深度對話式研究報告_2026-08-03.html
└── ... (其他個股一頁式 HTML 報告)
```

---

## 🚀 本地維護與自動部署

報告生成與索引檔案由根目錄腳本 `render_dialogue_reports.py` 自動管理：

```bash
# 重新渲染所有 Markdown 報告並更新 index.html
python render_dialogue_reports.py

# 推送更新至 GitHub Pages
git add .
git commit -m "Update stock dialogue reports and index"
git push origin main
```

---

© 2026 台股深度對話式研究報告團隊 | Powered by GitHub Pages
