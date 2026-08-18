import html
import re
import argparse
from pathlib import Path
from datetime import datetime

REPORTS_DIR = Path(__file__).resolve().parent / "reports" / "stocks-dialogues"
OUT_DIR = REPORTS_DIR / "html"
OUT_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = OUT_DIR / "index.html"

CORE_OVERRIDES = {
    '3017': 'AI 散熱 / 液冷熱管理',
    '3293': '遊戲 / 授權平台 / 高現金流',
    '2395': '工業電腦 / 邊緣 AI',
    '2376': 'AI 伺服器 / GPU 平台週期',

    # Traditional / Automation / Non-standard tech overrides
    '2027': '北美鋼鋁通路 / 關稅保護 / 資料中心',
    '1503': '重電設備 / AIDC電力基建',
    '1590': '氣動元件 / 工業自動化',
    '2049': '線性傳動 / 工業自動化',
    '5536': '半導體建廠 / 潔淨室工程',
    '6548': '導線架 / 半導體封裝材料',
    '8150': '記憶體與面板驅動IC封測',    '8358': '高頻高速電子銅箔',
    '1303': '塑化與電子材料平台',
    '2303': '晶圓代工 / 成熟與特殊製程',
    '8996': '熱管理 / 散熱與液冷系統',
}

SKIP_META_PREFIXES = (
    '- 角色 A：',
    '- 角色 B：',
    '- 本次模式：',
    '- 報告目的：',
    '- 本次整稿重點：',
    '- 本次重整重點：',
)

TAG_RULES = [
    ('ai-server', 'AI伺服器', ('AI伺服器', '機櫃', 'Rack-scale', '資料中心', 'GPU', '伺服器')),
    ('semiconductor', '半導體 / 封裝', ('半導體', '封裝', '先進封裝', '晶圓代工', 'DRAM', 'OSAT')),
    ('power', '電力 / 電源', ('電力', '電源', 'HVDC')),
    ('asic', 'AI ASIC / TPU', ('ASIC', 'TPU', 'SoC')),
    ('materials', '材料 / CCL', ('CCL', '載板', '玻纖', 'ABF', '基板', '銅箔基板', '玻纖布')),
    ('network', '網通 / 交換器', ('交換器', '網通', '800G', '1.6T', '光互連', 'CPO', '光通訊', '低軌衛星')),
    ('components', '被動元件 / 零組件', ('被動元件', 'MLCC', '晶片電阻', '電容')),
    ('highspeed-io', '高速介面 / SerDes', ('SerDes', 'Retimer', 'Redriver', '高速傳輸', 'DisplayPort', 'eDP', 'PCIe', 'USB4', '訊號補償')),
    ('iiiv-photonics', 'III-V 光電 / RF', ('GaAs', '砷化鎵', 'InP', '磷化銦', 'VCSEL', 'CW Laser', 'EML', 'PD', '光電子', 'RF 前端', 'PA')),
    ('advanced-packaging-equip', '先進封裝設備 / 濕製程', ('濕製程', '電鍍', 'CoWoS', 'CoPoS', 'FOPLP', '玻璃填孔', '背面供電', 'TGV', '化學品')),
    ('test-interface', '測試介面 / 探針卡', ('探針卡', '測試板', '測試介面', 'KGD', 'Chiplet', 'Probe Card', 'Load Board', '高頻驗證', '高速驗證')),
    ('traditional', '傳統產業 / 自動化', ('不銹鋼', '鋼鐵', '鋁廠', '鋼鋁', '自動化', '氣動', '滑軌', '傳動')),
    ('software-ipc', '軟體 / 遊戲 / 工業電腦', ('遊戲', '博弈', '工業電腦', '邊緣AI', 'IPC', '軟體')),
]

TAG_BLACKLIST = {
    '2027': {'ai-server'},                     # 大成鋼 (Steel/Aluminum)
    '1503': {'ai-server', 'semiconductor'},     # 士電 (Heavy Electrical)
    '1590': {'semiconductor', 'materials'},    # 亞德客-KY (Pneumatic Automation)
    '2049': {'semiconductor', 'materials'},    # 上銀 (Linear Guides)
    '2059': {'semiconductor', 'materials'},    # 川湖 (Server Slide Rails - keep AI-server)
    '1560': {'materials', 'power'},            # 中砂 (Diamond Disks - keep Semiconductor)
    '5536': {'materials'},                     # 聖暉 (Cleanroom - keep Semiconductor)
    '6187': {'network'},                       # 萬潤 (Packaging Equip - keep Semiconductor/Equip)
    '7795': {'materials'},                     # 長廣 (Packaging Equip - keep Semiconductor/Equip)
    '6548': {'ai-server', 'network'},          # 長科 (Leadframe - keep Semiconductor)
    '8150': {'materials', 'network'},          # 南茂 (OSAT - keep Semiconductor)
    '8358': {'ai-server', 'network'},          # 金居 (Copper Foil - keep Materials)
    '8996': {'network'},                       # 高力 (Heat Exchangers - keep Power/AI-server)
    '1303': {'advanced-packaging-equip'},      # 南亞 (Chemicals - keep Materials/AI-server)
    '2303': {'network'},                       # 聯電 (Foundry - keep Semiconductor/ASIC)
    '3017': {'network'},                       # 奇鋐 (Cooling - keep AI-server)
    '6173': {'ai-server'},                     # 信昌電 (Passive components - keep Power/Components)
    '6770': {'components'},                    # 力積電 (Foundry - keep Semiconductor)
}

TAG_OVERRIDES = {}


CORE_CATEGORY_RULES = [
    {
        'label': 'AI 散熱 / 液冷熱管理',
        'keywords': [('散熱', 6), ('液冷', 6), ('熱管理', 6), ('熱交換', 5), ('均熱板', 5), ('冷板', 5), ('CDU', 5), ('快接頭', 5), ('風扇', 4), ('水冷', 5)],
        'require_any': ['散熱', '液冷', '熱管理', '熱交換', '冷板', 'CDU', '水冷'],
    },
    {
        'label': 'AI 伺服器 / GPU 平台週期',
        'keywords': [('GPU 平台', 6), ('NVIDIA', 6), ('GB300', 6), ('Rubin', 6), ('AI Server', 6), ('AI伺服器', 5), ('整櫃', 5), ('液冷', 5)],
        'require_any': ['GPU 平台', 'NVIDIA', 'GB300', 'Rubin', 'AI Server', 'AI伺服器'],
    },
    {
        'label': '遊戲 / 授權平台 / 高現金流',
        'keywords': [('線上博弈', 6), ('授權收入', 6), ('授權輸出', 6), ('遊戲軟體', 5), ('高現金流', 6), ('股東回饋', 4), ('平台化能力', 5), ('內容池', 4)],
        'require_any': ['線上博弈', '授權收入', '授權輸出', '遊戲軟體', '高現金流'],
    },
    {
        'label': '先進製程 / 先進封裝 (CoWoS)',
        'keywords': [('CoWoS', 6), ('先進封裝', 5), ('2nm', 4), ('3nm', 4), ('GAAFET', 4), ('BPDN', 4), ('先進製程', 3)],
        'require_any': ['先進製程', '先進封裝', 'CoWoS', 'GAAFET'],
    },
    {
        'label': '成熟製程 / 特殊製程',
        'keywords': [('成熟製程', 6), ('特殊製程', 6), ('8吋晶圓', 4), ('12吋成熟', 4), ('eHV FinFET', 5), ('DDIC', 4)],
        'require_any': ['成熟製程', '特殊製程', 'eHV'],
    },
    {
        'label': 'AI 電力基建 / 電源系統',
        'keywords': [('HVDC', 6), ('800VDC', 6), ('SOFC', 5), ('CDU', 5), ('微電網', 5), ('伺服器電源', 5), ('SST', 5), ('電力基礎設施', 5), ('AI 電力', 4)],
        'require_any': ['HVDC', '800VDC', 'SOFC', 'CDU', '微電網', '伺服器電源', 'SST', '電力基礎設施', 'AI 電力'],
    },
    {
        'label': 'AI 伺服器 / 整機整櫃 (Rack-scale)',
        'keywords': [('整機整櫃', 6), ('Rack-scale', 6), ('L10', 5), ('L11', 5), ('AI機櫃', 5), ('AI 伺服器', 3), ('伺服器 ODM', 5)],
        'require_any': ['整機整櫃', 'Rack-scale', 'L10', 'L11', 'AI機櫃', '伺服器 ODM'],
    },
    {
        'label': 'MLCC / 被動元件平台',
        'keywords': [('MLCC', 6), ('被動元件', 6), ('電阻', 4), ('電容', 4), ('感應器', 3)],
        'require_any': ['MLCC', '被動元件'],
    },
    {
        'label': '高階 CCL / Low CTE 玻纖布',
        'keywords': [('Low CTE', 6), ('高階 CCL', 6), ('CCL', 4), ('玻纖布', 5), ('銅箔基板', 5), ('UBB', 4), ('OAM', 4)],
        'require_any': ['CCL', '玻纖布', '銅箔基板', 'Low CTE'],
    },
    {
        'label': '高速交換器 / CPO 矽光子',
        'keywords': [('1.6T', 6), ('800G', 5), ('CPO', 6), ('矽光子', 5), ('高速交換器', 6), ('光互連', 4)],
        'require_any': ['1.6T', '800G', 'CPO', '矽光子', '高速交換器'],
    },
    {
        'label': 'DRAM 記憶體 / HBM 外溢',
        'keywords': [('DRAM', 6), ('HBM', 6), ('記憶體循環', 5), ('HBM外溢', 6), ('DDR5', 4)],
        'require_any': ['DRAM', 'HBM', '記憶體'],
    },
    {
        'label': 'AI ASIC / 手機與晶片平台',
        'keywords': [('天璣', 6), ('手機 SoC', 6), ('AI ASIC', 6), ('TPU', 5), ('晶片平台', 4)],
        'require_any': ['天璣', 'SoC', 'ASIC', 'TPU'],
    },
    {
        'label': 'ABF 載板 / 先進基板',
        'keywords': [('ABF', 6), ('ABF載板', 6), ('先進基板', 5), ('BT載板', 4), ('載板', 3)],
        'require_any': ['ABF', '載板', '基板'],
    },
    {
        'label': '先進封測 / OSAT 平台',
        'keywords': [('OSAT', 6), ('封測', 5), ('SiP', 5), ('日月光', 4), ('先進封測', 6)],
        'require_any': ['OSAT', '封測', 'SiP'],
    },
    {
        'label': '晶片測試設備 / SLT Handler',
        'keywords': [('SLT', 6), ('Handler', 6), ('測試設備', 5), ('FT/SLT', 6), ('測試分選機', 6), ('鴻勁', 4)],
        'require_any': ['SLT', 'Handler', '分選機', '測試設備'],
    },
    {
        'label': '工業電腦 / 邊緣 AI',
        'keywords': [('工業電腦', 6), ('邊緣AI', 6), ('Edge AI', 6), ('邊緣運算', 5), ('嵌入式', 5), ('自動化', 4), ('工業', 3)],
        'require_any': ['工業電腦', '邊緣AI', 'Edge AI', '邊緣運算', '嵌入式'],
    },
    {
        'label': '高速介面 / SerDes 平台',
        'keywords': [('SerDes', 6), ('Retimer', 6), ('Redriver', 5), ('高速傳輸', 5), ('DisplayPort', 5), ('eDP', 5), ('PCIe', 5), ('USB4', 4), ('訊號補償', 5)],
        'require_any': ['SerDes', 'Retimer', 'Redriver', '高速傳輸', 'DisplayPort', 'PCIe'],
    },
    {
        'label': 'III-V 光電 / RF 平台',
        'keywords': [('GaAs', 6), ('砷化鎵', 6), ('InP', 6), ('磷化銦', 6), ('VCSEL', 5), ('CW Laser', 5), ('EML', 5), ('PD', 4), ('光電子', 5), ('RF 前端', 5), ('PA', 4), ('低軌衛星', 4)],
        'require_any': ['GaAs', '砷化鎵', 'InP', '磷化銦', 'VCSEL', '光電子'],
    },
    {
        'label': '先進封裝濕製程設備',
        'keywords': [('濕製程', 6), ('電鍍', 6), ('CoWoS', 5), ('CoPoS', 5), ('FOPLP', 5), ('玻璃填孔', 5), ('背面供電', 5), ('TGV', 4), ('化學品', 4), ('高密度封裝', 4)],
        'require_any': ['濕製程', '電鍍', 'CoWoS', 'CoPoS', 'FOPLP', '玻璃填孔', '背面供電'],
    },
    {
        'label': '高階測試介面平台',
        'keywords': [('探針卡', 6), ('測試板', 6), ('測試介面', 5), ('KGD', 5), ('Chiplet', 5), ('Probe Card', 5), ('Load Board', 5), ('高頻驗證', 4), ('高速驗證', 4), ('HPC 測試', 4)],
        'require_any': ['探針卡', '測試板', '測試介面', 'KGD', 'Chiplet', 'Probe Card', 'Load Board'],
    },
]


def extract_core_keywords(title, meta, rounds, summary_sections, company):
    ticker_match = re.search(r'TW-(\d{4})', title)
    if ticker_match:
        override = CORE_OVERRIDES.get(ticker_match.group(1))
        if override:
            return override

    # 1. Explicit metadata check (優先讀取手動前置標註)
    for line in meta:
        m = re.search(r'-\s*(?:核心關鍵字|核心主題)[：:]\s*(.+)', line)
        if m:
            return m.group(1).strip()

    # 2. Section extraction with weights (分區加權)
    title_text = title + ' ' + ' '.join(meta)
    summary_text = ' '.join(s['title'] + ' ' + ' '.join(s['items']) for s in summary_sections)
    senior_text = ' '.join(r['title'] + ' ' + ' '.join(seg[1] for seg in r['segments'] if seg[0] == 'senior') for r in rounds)
    junior_text = ' '.join(seg[1] for r in rounds for seg in r['segments'] if seg[0] == 'junior')

    weighted_sections = [
        (title_text, 5.0),
        (summary_text, 3.0),
        (senior_text, 2.0),
        (junior_text, 0.2)
    ]

    best_label = ''
    best_score = -1.0

    for rule in CORE_CATEGORY_RULES:
        has_req = any(req in text for text, _ in weighted_sections for req in rule['require_any'])
        if not has_req:
            continue

        score = 0.0
        for text, weight in weighted_sections:
            for kw, kw_weight in rule['keywords']:
                count = text.count(kw)
                score += count * kw_weight * weight

        if score > best_score:
            best_score = score
            best_label = rule['label']

    if best_label and best_label != company:
        return best_label

    fallback_candidates = [
        ('AI 伺服器 / 資料中心', ('AI伺服器', '資料中心', 'GPU', '伺服器', '機櫃', 'Rack-scale')),
        ('先進封裝 / CoWoS', ('CoWoS', '先進封裝', 'CoPoS', 'FOPLP', '玻璃基板', '封裝')),
        ('網通 / 乙太網 / Wi-Fi', ('網通', '乙太網', 'Wi-Fi', '交換器', '光通訊', 'CPO')),
        ('車用 / 邊緣裝置', ('車用', '智慧座艙', '邊緣AI', '工業電腦', '工業')),
        ('材料 / 載板 / CCL', ('CCL', '載板', 'ABF', '玻纖布', '銅箔基板', '材料')),
        ('散熱 / 電源 / 電力', ('散熱', '熱交換', '電源', '供電', 'HVDC', '800VDC')),
        ('估值 / 驗證框架', ('估值', '本益比', '獲利品質', '毛利率', '營業利益率', '淨利率')),
    ]

    title_hits = []
    for round_info in rounds:
        round_title = round_info.get('title', '')
        merged = ' '.join(seg[1] for seg in round_info.get('segments', []))
        heading = infer_section_label(round_title, merged)
        if heading and heading != company and not re.fullmatch(r'第\s*\d+\s*段', heading):
            title_hits.append(heading)

    title_priority = [
        '遊戲 / 授權平台 / 高現金流',
        'AI 驅動與產業脈絡',
        '先進製程與先進封裝',
        'HVDC 與供電架構',
        '晶圓代工與商業模式',
    ]
    for preferred in title_priority:
        if preferred in title_hits:
            return preferred

    combined_text = ' '.join(text for text, _ in weighted_sections)
    for label, keywords in fallback_candidates:
        hit_count = sum(combined_text.count(keyword) for keyword in keywords)
        if hit_count >= 2:
            return label

    return ''


INDEX_FILTERS = [
    ('all', '全部'),
    ('ai-server', 'AI伺服器'),
    ('semiconductor', '半體 / 封裝'),
    ('power', '電力 / 電源'),
    ('asic', 'AI ASIC / TPU'),
    ('materials', '材料 / CCL'),
    ('network', '網通 / 交換器'),
    ('components', '被動元件 / 零組件'),
    ('traditional', '傳統產業 / 自動化'),
    ('software-ipc', '軟體 / 遊戲 / 工業電腦'),
]

CORE_BUCKETS = [
    ('all-core', '全部主線'),
    ('core-ai-server', 'AI伺服器 / GPU'),
    ('core-packaging', '先進封裝 / 封測'),
    ('core-network', '網通 / CPO'),
    ('core-materials', '材料 / 載板 / CCL'),
    ('core-memory', '記憶體 / HBM'),
    ('core-power', '電力 / 電源'),
    ('core-industrial', '工業 / 邊緣AI'),
    ('core-gaming', '遊戲 / 授權平台'),
    ('core-highspeed-io', '高速介面 / SerDes'),
    ('core-iiiv', 'III-V 光電 / RF'),
    ('core-packaging-equip', '先進封裝濕製程設備'),
    ('core-test', '高階測試介面'),
]


def classify_core_bucket(core_text: str) -> str:
    core_text = core_text or ''
    mapping = [
        (('AI 伺服器', 'GPU 平台', '整機整櫃', '液冷熱管理'), 'core-ai-server'),
        (('先進封裝', 'CoWoS', 'OSAT', 'SLT Handler'), 'core-packaging'),
        (('高速交換器', 'CPO', '矽光子', 'Wi-Fi', '乙太網'), 'core-network'),
        (('CCL', '玻纖布', 'ABF', '載板', '材料'), 'core-materials'),
        (('DRAM', 'HBM', '記憶體'), 'core-memory'),
        (('電力', '電源', 'HVDC'), 'core-power'),
        (('工業電腦', '邊緣 AI'), 'core-industrial'),
        (('遊戲', '授權平台', '高現金流'), 'core-gaming'),
        (('高速介面', 'SerDes', 'Retimer', 'Redriver', 'DisplayPort', 'PCIe'), 'core-highspeed-io'),
        (('III-V', 'GaAs', '砷化鎵', 'InP', '磷化銦', 'VCSEL', 'RF 平台'), 'core-iiiv'),
        (('先進封裝濕製程設備', '濕製程', '電鍍', 'FOPLP', '玻璃填孔', '背面供電'), 'core-packaging-equip'),
        (('高階測試介面', '探針卡', '測試板', 'KGD', 'Chiplet'), 'core-test'),
    ]
    for keywords, bucket in mapping:
        if any(keyword in core_text for keyword in keywords):
            return bucket
    return 'all-core'


def convert_inline(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    return text


def slugify(text: str) -> str:
    return re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]+', '-', text).strip('-').lower() or 'section'


def pretty_round_title(round_title: str) -> str:
    m = re.match(r'^###\s*Round\s*(\d+)\s*$', round_title.strip(), flags=re.I)
    if m:
        return f'第 {m.group(1)} 段'
    return round_title.replace('###', '').strip()


def infer_section_label(round_title: str, merged_text: str) -> str:
    candidates = [
        (('晶圓代工', '製造平台', '商業模式'), '晶圓代工與商業模式'),
        (('先進製程', '先進封裝', 'CoWoS', 'GAAFET', 'BPDN'), '先進製程與先進封裝'),
        (('HVDC', '800VDC', 'Power Rack', '供電架構'), 'HVDC 與供電架構'),
        (('AI', '算力', '資料中心', '用電'), 'AI 驅動與產業脈絡'),
        (('毛利率', '獲利', '利潤', '價格權'), '獲利品質與經營槓桿'),
        (('估值', '本益比', 'price in', '溢價', '風險報酬'), '估值與市場預期'),
        (('反方', '最強反方', '失效', '質疑'), '反方壓力測試'),
        (('光寶科',), '光寶科比較'),
        (('高力', '散熱', '熱交換器'), '散熱與跨子題比較'),
        (('Vertiv', '施耐德', 'ABB', 'Eaton'), '海外平台商比較'),
        (('風險', '地緣政治', '資本支出'), '風險與失效條件'),
    ]
    for keys, label in candidates:
        if any(k in merged_text for k in keys):
            return label
    return pretty_round_title(round_title)


def parse_md(md: str):
    lines = md.splitlines()
    title = lines[0].lstrip('#').strip() if lines else 'Report'
    meta = []
    rounds = []
    summary_sections = []
    current_round = None
    current_summary = None
    mode = 'body'
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('## 對話設定'):
            i += 1
            while i < len(lines) and not lines[i].startswith('## '):
                raw = lines[i].rstrip()
                if raw.strip() and not raw.strip().startswith(SKIP_META_PREFIXES):
                    meta.append(raw)
                i += 1
            continue
        if line.startswith('### Round '):
            mode = 'rounds'
            if current_round:
                rounds.append(current_round)
            current_round = {'title': line.strip(), 'segments': []}
            i += 1
            continue
        if line.startswith('## 對話後總結') or line.startswith('## 投資收斂') or line.startswith('### 最短版記法'):
            mode = 'summary'
            if current_round:
                rounds.append(current_round)
                current_round = None
            if line.startswith('### 最短版記法'):
                if current_summary:
                    summary_sections.append(current_summary)
                current_summary = {'title': '最短版記法', 'items': []}
            i += 1
            continue
        if mode == 'rounds' and current_round is not None:
            if line.startswith('菜鳥研究員：') or line.startswith('資深研究員：'):
                speaker = 'junior' if line.startswith('菜鳥研究員：') else 'senior'
                content_lines = []
                first = line.split('：', 1)[1].strip()
                if first:
                    content_lines.append(first)
                i += 1
                while i < len(lines):
                    nxt = lines[i]
                    if nxt.startswith('菜鳥研究員：') or nxt.startswith('資深研究員：') or nxt.strip().startswith('#'):
                        break
                    content_lines.append(nxt)
                    i += 1
                text = '\n'.join(content_lines).strip()
                current_round['segments'].append((speaker, text))
                continue
        if mode == 'summary':
            if line.startswith('### '):
                title_val = line[4:].strip()
                if current_summary and current_summary['title'] == title_val:
                    i += 1
                    continue
                if current_summary:
                    summary_sections.append(current_summary)
                current_summary = {'title': title_val, 'items': []}
                i += 1
                continue
            if current_summary:
                stripped = line.strip()
                if stripped:
                    val = None
                    if stripped.startswith('- '):
                        val = stripped[2:].strip()
                    elif not stripped.startswith('#'):
                        val = stripped
                    
                    if val and val not in current_summary['items']:
                        current_summary['items'].append(val)
        i += 1
    if current_round:
        rounds.append(current_round)
    if current_summary:
        summary_sections.append(current_summary)
    return title, meta, rounds, summary_sections


def render_meta(meta):
    normal = []
    date_items = []
    date_mode = False
    for raw in meta:
        stripped = raw.strip()
        if stripped.startswith('- 資料截止日：'):
            date_mode = True
            continue
        if date_mode and raw.startswith('  - '):
            date_items.append(raw.strip()[2:].strip())
            continue
        if date_mode and not raw.startswith('  - '):
            date_mode = False
        normal.append(stripped)

    parts = []
    for line in normal:
        parts.append(f'<div class="meta-chip">{convert_inline(line)}</div>')
    if date_items:
        cleaned_items = []
        for x in date_items:
            c = re.sub(r'KG\s*公司頁\s*`?as_of`?:\s*', '公司資料：', x)
            c = re.sub(r'(?:daily DB\s*)?股價資料：最新台灣交易日為\s*', '交易股價：', c)
            c = re.sub(r'monthly revenue：最新為\s*(\d{4}\s*年\s*\d{1,2}\s*月)營收，公告日\s*(\d{4}-\d{2}-\d{2})', r'月營收：\1', c)
            c = c.replace('`as_of`:', '').replace('`', '')
            cleaned_items.append(c)
        chips = ''.join(f'<span class="deadline-chip">{convert_inline(item)}</span>' for item in cleaned_items)
        parts.append(f'''<section class="meta-card meta-deadline">
<div class="meta-card-title">AS_OF_DATES // 資料截止日</div>
<div class="deadline-chips">{chips}</div>
</section>''')
    return '\n'.join(parts)


def render_text_block(text: str) -> str:
    if not text:
        return ''
    paras = text.split('\n\n')
    out = []
    for para in paras:
        p = para.strip()
        if not p:
            continue
        if p.startswith('- '):
            items = [x.strip()[2:] for x in p.split('\n') if x.strip().startswith('- ')]
            lis = ''.join(f'<li>{convert_inline(x)}</li>' for x in items)
            out.append(f'<ul>{lis}</ul>')
        else:
            lines = '<br>'.join(convert_inline(x) for x in p.split('\n'))
            out.append(f'<p>{lines}</p>')
    return '\n'.join(out)


def build_senior_digest(rounds):
    cards = []
    toc = []
    for idx, r in enumerate(rounds, start=1):
        senior_segments = [text for speaker, text in r['segments'] if speaker == 'senior']
        if not senior_segments:
            continue
        merged = '\n\n'.join(senior_segments)
        label = infer_section_label(r['title'], merged)
        anchor = f'digest-{idx}-{slugify(label)}'
        toc.append((label, anchor))
        cards.append(f'''<section class="digest-card section-card" id="{anchor}">
<div class="digest-title">{html.escape(label)}</div>
<div class="content">{render_text_block(merged)}</div>
</section>''')
    return '\n'.join(cards), toc


def render_digest_toc(toc):
    return '\n'.join(f'<a href="#{anchor}">{html.escape(label)}</a>' for label, anchor in toc)


def render_rounds(rounds):
    blocks = []
    for r in rounds:
        senior_segments = [text for speaker, text in r['segments'] if speaker == 'senior']
        merged = '\n\n'.join(senior_segments) if senior_segments else ''
        title = infer_section_label(r['title'], merged)
        segs = []
        for speaker, text in r['segments']:
            label = '菜鳥研究員' if speaker == 'junior' else '資深研究員'
            segs.append(f'''<article class="bubble {speaker}">
<div class="bubble-head"><div class="speaker">{label}</div></div>
<div class="content">{render_text_block(text)}</div>
</article>''')
        blocks.append(f'''<section class="round section-card" id="{slugify(title)}">
<div class="round-title">{html.escape(title)}</div>
<div class="round-grid">{''.join(segs)}</div>
</section>''')
    return '\n'.join(blocks)


def format_revenue_amount(val_str: str) -> str:
    s = val_str.strip()
    multiplier = 1.0
    if '兆' in s:
        multiplier = 1e12
    elif '億' in s:
        multiplier = 1e8
    elif '萬' in s:
        multiplier = 1e4
    elif '千' in s:
        multiplier = 1e3

    clean_num_str = re.sub(r'[^0-9.]', '', s)
    if not clean_num_str:
        return val_str
    try:
        num = float(clean_num_str)
        ntd_val = num * multiplier

        if ntd_val >= 1e12:
            return f'{ntd_val / 1e12:,.2f} 兆'
        elif ntd_val >= 1e8:
            val_hundred_m = ntd_val / 1e8
            if val_hundred_m >= 1000:
                return f'{val_hundred_m:,.1f} 億'
            elif val_hundred_m >= 100:
                return f'{val_hundred_m:.1f} 億'
            else:
                return f'{val_hundred_m:.2f} 億'
        elif ntd_val >= 1e4:
            val_ten_k = ntd_val / 1e4
            return f'{val_ten_k:,.1f} 萬'
        else:
            return f'{ntd_val:,.0f} 元'
    except Exception:
        return val_str



def format_summary_section(items):
    normal_bullets = []
    price_val = None
    price_change = None
    valuation_chips = []
    revenue_dict = {}

    for raw in items:
        s = raw.strip()
        if not s:
            continue
        
        if re.search(r'最新台灣交易日.*股價資料', s) or re.search(r'最新月營收依月份語意解讀', s) or s.startswith('- 資料截止日：'):
            continue
            
        s = re.sub(r'^KG\s*已?將\s*', '', s)
        s = re.sub(r'^KG\s*定位：?\s*', '', s)

        # 1. Price & Change
        m_price = re.match(r'^收盤價\s*[:：]?\s*(.+)$', s)
        if m_price:
            price_val = m_price.group(1).strip()
            continue
        
        m_change = re.match(r'^(?:單日漲幅|單日漲跌|漲跌幅)\s*[:：]?\s*(.+)$', s)
        if m_change:
            price_change = m_change.group(1).strip()
            if not price_change.startswith(('+', '-')):
                price_change = '+' + price_change
            continue

        # 2. Valuation metrics (PE, PB, Market Cap)
        if re.match(r'^(?:本益比|股價淨值比|PB|PE|總市值)\s*', s):
            valuation_chips.append(s)
            continue

        # 3. Revenue metrics
        m_rev = re.match(r'^(?:單月合併營收|單月營收|營收)\s*[:：]?\s*(.+)$', s)
        if m_rev:
            revenue_dict['單月營收'] = format_revenue_amount(m_rev.group(1).strip())
            continue
        m_yoy = re.match(r'^年增\s*[:：]?\s*(.+)$', s)
        if m_yoy:
            v = m_yoy.group(1).strip()
            revenue_dict['單月年增'] = v if v.startswith(('+', '-')) else '+' + v
            continue
        m_mom = re.match(r'^(?:月增|月減)\s*[:：]?\s*(.+)$', s)
        if m_mom:
            v = m_mom.group(1).strip()
            if '月減' in s and not v.startswith('-'):
                v = '-' + v
            elif '月增' in s and not v.startswith(('+', '-')):
                v = '+' + v
            revenue_dict['單月月增'] = v
            continue
        m_3m = re.match(r'^近三月.*?年增\s*[:：]?\s*(.+)$', s)
        if m_3m:
            v = m_3m.group(1).strip()
            revenue_dict['近 3 月年增'] = v if v.startswith(('+', '-')) else '+' + v
            continue
        m_12m = re.match(r'^近\s*12\s*月.*?成長\s*[:：]?\s*(.+)$', s)
        if m_12m:
            v = m_12m.group(1).strip()
            revenue_dict['近 12 月成長'] = v if v.startswith(('+', '-')) else '+' + v
            continue

        normal_bullets.append(s)

    # Combine Price + Change into single formatted bullet if present
    if price_val:
        if price_change:
            price_text = f'收盤價：{price_val} ({price_change})'
        else:
            price_text = f'收盤價：{price_val}'
        normal_bullets.insert(0, price_text)

    for v in valuation_chips:
        normal_bullets.append(v)

    html_out = []
    if normal_bullets:
        rendered_bullets = []
        for b in normal_bullets:
            b_html = convert_inline(b)
            b_html = re.sub(
                r'\(\+([^)]+)\)',
                r'(<span style="color: #f87171; font-weight: 700;">+\1</span>)',
                b_html
            )
            b_html = re.sub(
                r'\(\-([^)]+)\)',
                r'(<span style="color: #34d399; font-weight: 700;">-\1</span>)',
                b_html
            )
            rendered_bullets.append(f'<li>{b_html}</li>')
        html_out.append(f'<ul>{"".join(rendered_bullets)}</ul>')

    if revenue_dict:
        rows_html = []
        for k, v in revenue_dict.items():
            val_style = ''
            if '+' in v:
                val_style = ' style="color: #f87171; font-weight: 700;"'
            elif '-' in v:
                val_style = ' style="color: #34d399; font-weight: 700;"'
            rows_html.append(f'<tr><td class="tbl-k">{html.escape(k)}</td><td class="tbl-v"{val_style}>{html.escape(v)}</td></tr>')
        
        table_html = f'''<div class="summary-table-wrap">
<div class="summary-table-title">營收數據彙整</div>
<table class="summary-table">
  <tbody>
    {''.join(rows_html)}
  </tbody>
</table>
</div>'''
        html_out.append(table_html)

    return '\n'.join(html_out)


def render_summary(sections):
    cards = []
    for s in sections:
        sec_html = format_summary_section(s['items'])
        if not sec_html:
            continue
        cards.append(f'''<section class="summary-card section-card">
<h3>{html.escape(s['title'])}</h3>
{sec_html}
</section>''')
    return '\n'.join(cards)


def render_tail_sections_from_markdown(md_text: str) -> str:
    cards = []

    summary_block_start = md_text.find('## 對話後總結')
    if summary_block_start != -1:
        summary_block_end = md_text.find('### 最短版記法', summary_block_start)
        if summary_block_end == -1:
            summary_block_end = len(md_text)
        body = md_text[summary_block_start + len('## 對話後總結'):summary_block_end]
        summary_chunks = []
        current_title = None
        current_items = []
        for raw_line in body.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith('### '):
                if current_title is not None:
                    summary_chunks.append((current_title, current_items[:]))
                current_title = line[4:].strip()
                current_items = []
                continue
            if line.startswith('- '):
                current_items.append(line[2:].strip())
            else:
                current_items.append(line)
        if current_title is not None:
            summary_chunks.append((current_title, current_items[:]))

        for title, items in summary_chunks:
            sec_html = format_summary_section(items)
            if sec_html:
                cards.append(f'<section class="summary-card section-card"><h3>{html.escape(title)}</h3>{sec_html}</section>')

    m_short = re.search(r'^### 最短版記法\s*(.*?)(?=^## |^### |\Z)', md_text, flags=re.M | re.S)
    if m_short:
        short_lines = [line.strip() for line in m_short.group(1).splitlines() if line.strip()]
        short_lines = [line[2:].strip() if line.startswith('- ') else line for line in short_lines]
        if short_lines:
            deduped = []
            seen = set()
            for line in short_lines:
                if line not in seen:
                    seen.add(line)
                    deduped.append(line)
            short_html = format_summary_section(deduped)
            cards.append('<section class="summary-card section-card"><h3>最短版記法</h3>' + short_html + '</section>')

    return '\n'.join(cards)


def build_html(title, meta, rounds, summary, md_text=''):
    generated = datetime.now().strftime('%Y-%m-%d %H:%M')
    senior_digest, digest_toc = build_senior_digest(rounds)
    tail_summary_cards = render_tail_sections_from_markdown(md_text) if md_text else render_summary(summary)
    clean_display_title = re.sub(r'\s*深度對話式研究報告.*$', '', title)
    m_title = re.match(r'^(TW-\d{4})\s+(.+)$', clean_display_title)
    if m_title:
        ticker_code, company_name = m_title.group(1), m_title.group(2)
        title_dom = f'''<div class="company-badge-row">
            <span class="ticker-badge">[{html.escape(ticker_code)}]</span>
            <h1 class="company-name" id="top">{html.escape(company_name)}</h1>
          </div>'''
    else:
        title_dom = f'<h1 class="company-name" id="top">{html.escape(clean_display_title)}</h1>'

    return f'''<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(clean_display_title)} - 台股死當 TERMINAL</title>
<style>
:root {{
  --bg-dark: #07090e;
  --bg-panel: rgba(14, 20, 32, 0.85);
  --border-cyan: rgba(0, 240, 255, 0.18);
  --border-amber: rgba(255, 183, 0, 0.25);
  --amber: #ffb700;
  --cyan: #00f0ff;
  --red: #ff4d4d;
  --green: #00e676;
  --text-main: #e2e8f0;
  --text-muted: #8492a6;
  --font-mono: "JetBrains Mono", "Roboto Mono", "Consolas", monospace, "Noto Sans TC", sans-serif;
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  font-family: var(--font-mono);
  background: var(--bg-dark);
  color: var(--text-main);
  line-height: 1.7;
}}
a {{ color: inherit; text-decoration: none; }}
.container {{ max-width: 1440px; margin: 0 auto; padding: 16px 24px 48px; }}

.term-top-bar {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: var(--text-muted);
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 183, 0, 0.2);
  border-radius: 8px;
  padding: 4px 12px;
  margin-bottom: 12px;
}}
.term-dot {{ color: var(--green); font-weight: 700; margin-right: 6px; }}
.term-cmd {{ color: var(--amber); font-weight: 700; }}

.hero {{
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(16px);
  background: rgba(11, 16, 26, 0.94);
  border: 1px solid var(--border-cyan);
  border-radius: 14px;
  margin: 0 0 20px;
  padding: 12px 20px;
  box-shadow: 0 10px 36px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(0, 240, 255, 0.1);
}}
.hero-inner {{ width: 100%; }}
.top-nav {{ display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 8px; }}
.nav-brand-btn {{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  border-radius: 8px;
  background: rgba(255, 183, 0, 0.08);
  border: 1px solid var(--border-amber);
  transition: all 0.2s ease;
  text-decoration: none;
}}
.nav-brand-btn:hover {{
  background: rgba(255, 183, 0, 0.18);
  border-color: var(--amber);
  transform: translateY(-1px);
}}
.nav-logo {{
  width: 22px;
  height: 22px;
  border-radius: 4px;
  object-fit: cover;
  image-rendering: pixelated;
}}
.nav-brand {{
  font-weight: 800;
  color: var(--amber);
  font-size: 13px;
  letter-spacing: 0.05em;
}}
.nav-back-hint {{
  font-size: 12px;
  color: var(--amber);
  font-weight: 700;
}}
.mode-tools {{ display: flex; gap: 8px; }}
.header-main {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}}
.header-title-box {{ display: flex; flex-direction: column; gap: 4px; }}
.company-badge-row {{
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}}
.ticker-badge {{
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 800;
  color: var(--cyan);
  background: rgba(0, 240, 255, 0.08);
  border: 1px solid var(--border-cyan);
  padding: 4px 10px;
  border-radius: 6px;
  letter-spacing: 0.08em;
}}
.company-name {{
  font-size: 28px;
  font-weight: 800;
  color: #ffffff;
  margin: 0;
  letter-spacing: -0.01em;
  line-height: 1.2;
}}
.sub-title-hint {{ font-size: 12px; color: var(--text-muted); font-weight: 500; }}
.header-meta-box {{ display: flex; align-items: center; }}
.header-meta-box .meta-card {{
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid var(--border-cyan);
  border-radius: 8px;
  padding: 6px 12px;
}}
.toolbtn {{
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--text-muted);
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: var(--font-mono);
}}
.toolbtn:hover {{ background: rgba(0, 240, 255, 0.15); color: #ffffff; border-color: var(--cyan); }}
.meta-grid {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }}
.meta-chip {{ background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.07); border-radius: 6px; padding: 5px 10px; color: var(--text-muted); font-size: 12px; }}
.meta-card {{ background: rgba(0, 0, 0, 0.35); border: 1px solid var(--border-cyan); border-radius: 8px; padding: 6px 12px; }}
.meta-card-title {{ font-size: 10px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; color: var(--cyan); margin-bottom: 4px; }}
.deadline-chips {{ display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }}
.deadline-chip {{
  font-size: 11px;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.035);
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 2px 7px;
  border-radius: 4px;
  font-family: var(--font-mono);
  white-space: nowrap;
}}
.meta-card-title {{ font-size: 11px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; color: var(--cyan); margin-bottom: 4px; }}
.meta-deadline ul {{ margin: 0; padding-left: 16px; color: var(--text-main); line-height: 1.5; font-size: 12px; }}

.floating-top-btn {{
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 999;
  width: 42px;
  height: 42px;
  border-radius: 8px;
  background: rgba(14, 20, 32, 0.9);
  border: 1px solid var(--cyan);
  backdrop-filter: blur(12px);
  color: var(--cyan);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
  transition: all 0.2s ease;
}}
.floating-top-btn:hover {{
  background: rgba(0, 240, 255, 0.25);
  color: #ffffff;
  transform: translateY(-2px);
}}

.layout {{ display: grid; grid-template-columns: minmax(0, 1.75fr) minmax(300px, 0.9fr); gap: 24px; align-items: start; }}
.section-card {{
  background: var(--bg-panel);
  border: 1px solid var(--border-cyan);
  border-radius: 14px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(12px);
}}
.main-stack {{ display: flex; flex-direction: column; gap: 20px; }}
.digest-wrap {{ display: none; }}
.sidebar {{ position: sticky; top: 110px; display: flex; flex-direction: column; gap: 16px; }}
.reader-note {{ padding: 16px 20px; color: var(--text-muted); line-height: 1.6; font-size: 13px; position: relative; border-color: var(--border-amber); }}
.round {{ padding: 20px 24px; }}
.round-title {{ font-size: 16px; font-weight: 800; color: var(--cyan); margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid rgba(0, 240, 255, 0.12); letter-spacing: 0.05em; }}
.round-grid {{ display: grid; gap: 16px; }}
.bubble {{ padding: 18px 20px; border-radius: 12px; transition: border-color 0.2s ease; }}
.bubble.junior {{
  background: rgba(0, 240, 255, 0.03);
  border: 1px solid var(--border-cyan);
  border-left: 4px solid var(--cyan);
}}
.bubble.senior {{
  background: rgba(255, 183, 0, 0.03);
  border: 1px solid var(--border-amber);
  border-left: 4px solid var(--amber);
}}
.speaker {{ font-size: 11px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 8px; }}
.junior .speaker {{ color: var(--cyan); }}
.senior .speaker {{ color: var(--amber); }}
.content p {{ margin: 0 0 12px; line-height: 1.75; color: #e2e8f0; font-size: 14px; }}
.content p:last-child {{ margin-bottom: 0; }}
.content ul {{ margin: 0 0 12px 0; padding-left: 20px; line-height: 1.7; color: #e2e8f0; }}
.content li {{ margin-bottom: 6px; }}
code {{ background: rgba(0, 240, 255, 0.08); padding: 2px 7px; border-radius: 4px; font-size: 0.9em; color: var(--cyan); font-family: var(--font-mono); }}
.summary-card {{ padding: 18px 20px; border-color: var(--border-amber); }}
.summary-card h3 {{ margin: 0 0 12px; font-size: 15px; font-weight: 800; color: var(--amber); letter-spacing: 0.05em; }}
.summary-card ul {{ margin: 0; padding-left: 18px; line-height: 1.7; color: var(--text-main); font-size: 13px; }}
.summary-table-wrap {{
  margin-top: 12px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid var(--border-cyan);
  border-radius: 8px;
  padding: 10px 12px;
}}
.summary-table-title {{
  font-size: 11px;
  font-weight: 800;
  color: var(--cyan);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin-bottom: 6px;
}}
.summary-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
  font-family: var(--font-mono);
}}
.summary-table td {{
  padding: 4px 4px;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.06);
}}
.summary-table tr:last-child td {{ border-bottom: none; }}
.tbl-k {{ color: var(--text-muted); font-weight: 500; }}
.tbl-v {{ color: var(--text-main); font-weight: 700; text-align: right; }}
.digest-card {{ padding: 20px; scroll-margin-top: 110px; }}
.digest-title {{ font-size: 16px; font-weight: 800; color: var(--green); margin-bottom: 10px; border-bottom: 1px solid rgba(0, 230, 118, 0.2); padding-bottom: 6px; }}
.digest-toc {{ padding: 16px; display: flex; flex-direction: column; gap: 6px; }}
.digest-toc h3 {{ margin: 0 0 8px; font-size: 13px; color: var(--amber); font-weight: 800; }}
.digest-toc a {{ padding: 8px 12px; border-radius: 6px; color: var(--text-main); background: rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.05); font-size: 12px; font-weight: 600; transition: all 0.2s ease; }}
.digest-toc a:hover {{ border-color: var(--cyan); background: rgba(0, 240, 255, 0.1); color: #ffffff; transform: translateX(3px); }}
.footer {{ color: var(--text-muted); font-size: 11px; margin-top: 4px; padding: 0 4px; font-family: var(--font-mono); }}
.focus-mode .sidebar {{ display: none; }}
.focus-mode .layout {{ grid-template-columns: 1fr; }}
.digest-mode .full-rounds {{ display: none; }}
.digest-mode .digest-wrap {{ display: block; }}
.digest-mode .digest-only {{ display: block; }}
.digest-only {{ display: none; }}
@media (max-width: 860px) {{
  .layout {{ grid-template-columns: 1fr; }}
  .sidebar {{ position: static; }}
  .header-main {{ grid-template-columns: 1fr; gap: 12px; }}
  .header-meta-box {{ justify-content: flex-start; }}
}}
</style>
</head>
<body>
<div class="container" id="app">
  <div class="term-top-bar">
    <div><span class="term-dot">● LIVE</span><span class="term-cmd">RUN &gt; {html.escape(ticker_code if m_title else "EQUITY")}.TW &lt;GO&gt;</span> // TPE FINANCIAL TERMINAL</div>
    <div>LOGGED AS: SENIOR_ANALYST</div>
  </div>

  <header class="hero">
    <div class="hero-inner">
      <div class="top-nav">
        <a class="nav-brand-btn" href="index.html" title="點擊返回台股死當首頁">
          <span class="nav-back-hint">←</span>
          <img src="stonk_logo.png" alt="台股死當 Logo" class="nav-logo">
          <span class="nav-brand">台股死當</span>
        </a>
        <div class="mode-tools">
          <button class="toolbtn" onclick="document.body.classList.toggle('digest-mode')">資深研究員摘要版</button>
          <button class="toolbtn" onclick="document.body.classList.toggle('focus-mode')">Focus 閱讀模式</button>
        </div>
      </div>
      <div class="header-main">
        <div class="header-title-box">
          {title_dom}
        </div>
        <div class="header-meta-box">{render_meta(meta)}</div>
      </div>
    </div>
  </header>
  <main class="layout">
    <div class="main-stack">
      <section class="reader-note section-card" id="readerNote">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
          <h2 style="margin:0; font-size:15px; font-weight:700; color:#fbbf24;">💡 閱讀說明</h2>
          <button onclick="document.getElementById('readerNote').style.display='none';" style="background:none; border:none; color:#64748b; font-size:16px; cursor:pointer; padding:0 4px; transition:color 0.2s;" onmouseover="this.style.color='#f87171'" onmouseout="this.style.color='#64748b'" title="關閉說明">✕</button>
        </div>
        <div>預設保留完整 Mentor / Junior 擬真對話。「資深研究員摘要版」可切換至單欄精華稿並提供智慧自動目錄。</div>
      </section>
      <div class="digest-wrap">
        <section class="digest-only section-card digest-toc">
          <h3>自動目錄</h3>
          {render_digest_toc(digest_toc)}
        </section>
        {senior_digest}
      </div>
      <div class="full-rounds">{render_rounds(rounds)}</div>
    </div>
    <aside class="sidebar">
      {tail_summary_cards}
      <div class="footer">Generated at {generated}</div>
    </aside>
  </main>
</div>
<button onclick="window.scrollTo({{top: 0, behavior: 'smooth'}});" class="floating-top-btn" title="回到頂部" aria-label="回到頂部">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>
</button>
<div class="giscus-section">
  <div class="giscus-header">
    <span class="term-dot">● COMMENT</span>
    <span class="term-cmd">DISCUSSION BOARD</span>
    <span style="color:var(--muted); font-size:11px; font-family:monospace;">// 需要 GitHub 帳號才能留言</span>
  </div>
  <div class="giscus-wrap">
    <script src="https://giscus.app/client.js"
            data-repo="iamernie8199/stonk"
            data-repo-id="R_kgDOTtmdFQ"
            data-category="Ideas"
            data-category-id="DIC_kwDOTtmdFc4DCqA1"
            data-mapping="pathname"
            data-strict="0"
            data-reactions-enabled="1"
            data-emit-metadata="0"
            data-input-position="bottom"
            data-theme="noborder_dark"
            data-lang="zh-TW"
            crossorigin="anonymous"
            async>
    </script>
  </div>
</div>
<style>
  .giscus-section {{
    max-width: 860px;
    margin: 40px auto 0;
    padding: 0 24px 64px;
  }}
  .giscus-header {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--muted, #64748b);
    letter-spacing: 0.08em;
    padding: 10px 0 12px;
    border-top: 1px solid rgba(0, 240, 255, 0.15);
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .giscus-wrap {{
    margin-top: 8px;
  }}
</style>
</body>
</html>
'''


def infer_index_entry(md_path: Path):
    m = re.match(r'^TW-(\d{4})_(.+?)_深度對話式研究報告_(\d{4}-\d{2}-\d{2})$', md_path.stem)
    if not m:
        return None
    ticker, company, date_str = m.group(1), m.group(2), m.group(3)
    md = md_path.read_text(encoding='utf-8')
    title, meta, rounds, summary_sections = parse_md(md)

    full_text = '\n'.join([title] + meta + [seg[1] for r in rounds for seg in r['segments']])
    summary_text = ' '.join(' '.join(section['items']) for section in summary_sections)
    combined = ' '.join([full_text, summary_text])

    tag_scores = []
    for key, label, keywords in TAG_RULES:
        if ticker in TAG_BLACKLIST and key in TAG_BLACKLIST[ticker]:
            continue

        # Force match if overridden
        is_overridden = ticker in TAG_OVERRIDES and key in TAG_OVERRIDES[ticker]

        hit_count = 0
        if is_overridden:
            hit_count = 999
        else:
            for keyword in keywords:
                count = combined.count(keyword)
                if keyword == '交換器':
                    count -= combined.count('熱交換器')
                hit_count += count

        min_hits = 2 if key in {'ai-server', 'semiconductor', 'components', 'power', 'traditional', 'software-ipc'} else 1
        if key == 'semiconductor':
            min_hits = 5

        if hit_count >= min_hits:
            tag_scores.append((key, label, hit_count))

    # 保留最有代表性的主題分類，避免首頁每檔掛太多泛用 tag
    priority_order = {
        'ai-server': 0,
        'semiconductor': 1,
        'power': 2,
        'asic': 3,
        'materials': 4,
        'network': 5,
        'components': 6,
        'traditional': 7,
        'software-ipc': 8,
    }
    tag_scores.sort(key=lambda item: (-item[2], priority_order.get(item[0], 99)))
    selected = tag_scores[:3]
    tags = [key for key, _, _ in selected]
    tag_labels = [label for _, label, _ in selected]

    summary = ''
    summary_sources = []
    if summary_sections:
        for sec in summary_sections:
            if any(k in sec['title'] for k in ('資料與資訊邊界', '資料截至', '資訊邊界')):
                continue
            valid_items = [
                item for item in sec['items']
                if not any(k in item for k in ('最新台灣交易日', '股價資料', 'monthly revenue', 'as_of', 'KG 公司頁'))
            ]
            if valid_items:
                summary = '；'.join(valid_items[:2])
                break

    core = extract_core_keywords(title, meta, rounds, summary_sections, company)

    if not summary and core:
        summary = f'{company}目前主線聚焦「{core}」，市場主要在交易其平台能力能否延續並擴張。'

    if not summary:
        preferred_labels = {
            '高速介面 / SerDes 平台',
            'III-V 光電 / RF 平台',
            '先進封裝濕製程設備',
            '高階測試介面平台',
        }
        for r in rounds:
            merged = ' '.join(seg[1] for seg in r['segments'] if seg[0] == 'senior')
            label = infer_section_label(r.get('title', ''), merged)
            if label in preferred_labels and merged.strip():
                summary = re.sub(r'\s+', ' ', merged.strip())
                break

    if not summary:
        for r in rounds:
            for speaker, text in r['segments']:
                if speaker == 'senior' and text.strip():
                    summary = re.sub(r'\s+', ' ', text.strip())
                    break
            if summary:
                break

    # 清理 KG 系統詞彙
    summary = re.sub(r'^KG\s*已?將\s*', '', summary)
    summary = re.sub(r'^KG\s*定位[：:]\s*', '', summary)
    summary = re.sub(r'^KG\s*', '', summary)
    summary = re.sub(r'(?<=[；。])\s*KG\s*已?將\s*', '；', summary)
    summary = re.sub(r'(?<=[；。])\s*KG\s*定位[：:]\s*', '；', summary)
    summary = re.sub(r'(?<=[；。])\s*KG\s*', '；', summary)
    summary = summary.strip('；')
    summary = summary[:110].rstrip('，、；。 ') + ('。' if summary and not summary.endswith(('。', '！', '？')) else '')

    core = extract_core_keywords(title, meta, rounds, summary_sections, company)

    search = ' '.join(filter(None, [ticker, company, title.replace('深度對話式研究報告', ''), combined[:160]]))

    return {
        'ticker': ticker,
        'company': company,
        'date': date_str,
        'tags': tags,
        'search': ' '.join([ticker, company, title, summary, combined])[:3000],
        'summary': summary,
        'tag_labels': tag_labels,
        'core': core,
        'core_bucket': classify_core_bucket(core),
        'excerpt': summary,
        'href': md_path.stem + '.html'
    }


def build_index_html(entries):
    total = len(entries)
    INDEX_FILTERS_TERM = [
        ('all', '&lt;F1: 全部&gt;'),
        ('ai-server', '&lt;F2: AI伺服器&gt;'),
        ('semiconductor', '&lt;F3: 半導體 / 封裝&gt;'),
        ('power', '&lt;F4: 電力 / 電源&gt;'),
        ('asic', '&lt;F5: AI ASIC / TPU&gt;'),
        ('materials', '&lt;F6: 材料 / CCL&gt;'),
        ('network', '&lt;F7: 網通 / 交換器&gt;'),
        ('components', '&lt;F8: 被動元件 / 零組件&gt;'),
        ('highspeed-io', '&lt;F9: 高速介面 / SerDes&gt;'),
        ('iiiv-photonics', '&lt;F10: III-V 光電 / RF&gt;'),
        ('advanced-packaging-equip', '&lt;F11: 先進封裝設備 / 濕製程&gt;'),
        ('test-interface', '&lt;F12: 測試介面 / 探針卡&gt;'),
        ('traditional', '傳統產業 / 自動化'),
        ('software-ipc', '軟體 / 遊戲 / 工業電腦')
    ]
    main_filters = INDEX_FILTERS_TERM[:4]
    extra_filters = INDEX_FILTERS_TERM[4:]

    main_btns = []
    for key, label in main_filters:
        cls = "filter-btn active" if key == "all" else "filter-btn"
        main_btns.append(f'            <button class="{cls}" data-filter="{key}">{label}</button>')
    main_btns_str = '\n'.join(main_btns)

    extra_btns = []
    for key, label in extra_filters:
        extra_btns.append(f'              <button class="filter-btn" data-filter="{key}">{label}</button>')
    extra_btns_str = '\n'.join(extra_btns)

    core_filter_btns = []
    for key, label in CORE_BUCKETS:
        cls = "core-filter-btn active" if key == "all-core" else "core-filter-btn"
        core_filter_btns.append(f'          <button class="{cls}" data-core-filter="{key}">{label}</button>')
    core_filter_buttons = '\n'.join(core_filter_btns)

    filter_buttons = f'''{main_btns_str}
          <div class="more-filters" id="moreFilters">
{extra_btns_str}
          </div>
          <button id="toggleFilterBtn" class="filter-toggle-btn" title="展開更多主題">更多 &#9662;</button>'''

    cards_html = []
    for e in sorted(entries, key=lambda x: x['ticker']):
        tags_attr = ' '.join(e['tags'])
        tag_row = ''.join(
            f'<button class="tag tag-btn" data-tagkey="{html.escape(k)}">{html.escape(lbl)}</button>'
            for k, lbl in zip(e['tags'], e['tag_labels'])
        )
        cards_html.append(f'''      <article class="card" data-tags="{html.escape(tags_attr)}" data-core-bucket="{html.escape(e['core_bucket'])}" data-search="{html.escape(e['search'])}" data-ticker="{html.escape(e['ticker'])}" data-name="{html.escape(e['company'])}">
        <div class="card-top">
          <div class="ticker-box">
            <div class="ticker">[TW-{html.escape(e['ticker'])}]</div>
            <div class="company">{html.escape(e['company'])}</div>
          </div>
          <div class="date-chip">DATE: {html.escape(e['date'])}</div>
        </div>
        <div class="core-box" data-core-bucket="{html.escape(e['core_bucket'])}" title="點擊依此主線進行篩選">
          <div class="core-label">THESIS // 投資主線 ↵</div>
          <div class="core-value">{html.escape(e['core'])}</div>
        </div>
        <div class="summary">{html.escape(e['excerpt'])}</div>
        <div class="tag-row">{tag_row}</div>
        <div class="actions"><a class="btn btn-primary" href="{html.escape(e['href'])}">RUN &gt; 閱讀研究報告 &lt;GO&gt;</a></div>
      </article>''')

    cards_block = '\n\n'.join(cards_html)
    return f'''<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>台股死當 TERMINAL - 深度對話式研究報告索引庫</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #07090e;
      --panel: rgba(14, 20, 32, 0.85);
      --panel-border: rgba(0, 240, 255, 0.18);
      --text: #f8fafc;
      --muted: #8492a6;
      --accent: #00f0ff;
      --amber: #ffb700;
      --accent-emerald: #00e676;
      --chip-bg: rgba(0, 240, 255, 0.08);
      --shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
      --font-mono: "JetBrains Mono", "Roboto Mono", "Consolas", monospace, "Noto Sans TC", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: var(--font-mono);
      background: var(--bg);
      color: var(--text);
      line-height: 1.7;
    }}
    .container {{
      max-width: 1440px;
      margin: 0 auto;
      padding: 16px 24px 48px;
    }}
    .term-top-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: var(--muted);
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid rgba(255, 183, 0, 0.2);
      border-radius: 8px;
      padding: 4px 12px;
      margin-bottom: 12px;
    }}
    .term-dot {{ color: var(--accent-emerald); font-weight: 700; margin-right: 6px; }}
    .term-cmd {{ color: var(--amber); font-weight: 700; }}
    
    .hero {{
      background: var(--panel);
      border: 1px solid var(--panel-border);
      border-radius: 14px;
      padding: 14px 18px;
      box-shadow: var(--shadow);
      margin-bottom: 20px;
      backdrop-filter: blur(12px);
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}
    .hero-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }}
    .hero-brand {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}
    .hero-logo {{
      width: 44px;
      height: 44px;
      border-radius: 10px;
      object-fit: cover;
      image-rendering: pixelated;
      flex-shrink: 0;
      box-shadow: 0 4px 14px rgba(0, 240, 255, 0.25);
      border: 1px solid var(--accent);
    }}
    .hero-text h1 {{
      margin: 0;
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.01em;
      color: #ffffff;
      display: inline-flex;
      align-items: center;
      gap: 10px;
    }}
    .slogan {{
      margin: 2px 0 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }}
    .slogan code {{
      color: var(--amber);
      background: rgba(255, 183, 0, 0.1);
      padding: 2px 6px;
      border-radius: 4px;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      padding: 3px 10px;
      border-radius: 6px;
      background: var(--chip-bg);
      color: var(--accent);
      font-size: 11px;
      font-weight: 700;
      border: 1px solid var(--panel-border);
      white-space: nowrap;
      letter-spacing: 0.05em;
    }}
    .search-box {{
      position: relative;
      display: flex;
      align-items: center;
      width: 100%;
    }}
    .cmd-prompt {{
      position: absolute;
      left: 12px;
      color: var(--amber);
      font-weight: 800;
      font-size: 13px;
      pointer-events: none;
      font-family: var(--font-mono);
    }}
    .search-input {{
      width: 100%;
      border: 1px solid var(--panel-border);
      background: rgba(0, 0, 0, 0.4);
      color: var(--text);
      border-radius: 8px;
      padding: 10px 36px 10px 65px;
      font-size: 13px;
      outline: none;
      transition: all 0.2s ease;
      font-family: var(--font-mono);
    }}
    .search-input:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(0, 240, 255, 0.15);
      background: rgba(0, 0, 0, 0.6);
    }}
    .search-input::placeholder {{ color: var(--muted); }}
    .clear-btn {{
      position: absolute;
      right: 10px;
      background: rgba(255, 255, 255, 0.1);
      border: none;
      color: var(--muted);
      width: 20px;
      height: 20px;
      border-radius: 50%;
      font-size: 11px;
      cursor: pointer;
      display: none;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;
      line-height: 1;
    }}
    .clear-btn:hover {{
      background: rgba(239, 68, 68, 0.25);
      color: #f87171;
    }}
    .toolbar-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .filter-pills {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
    }}
    .core-filter-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: center;
      padding-top: 6px;
      border-top: 1px dashed rgba(255, 255, 255, 0.08);
    }}
    .more-filters {{
      display: none;
      gap: 6px;
      flex-wrap: wrap;
    }}
    .more-filters.open {{
      display: flex;
    }}
    .filter-toggle-btn {{
      appearance: none;
      border: 1px solid var(--panel-border);
      background: rgba(0, 240, 255, 0.08);
      color: var(--accent);
      border-radius: 6px;
      padding: 6px 12px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
      font-family: var(--font-mono);
    }}
    .filter-toggle-btn:hover {{
      background: rgba(0, 240, 255, 0.2);
      border-color: var(--accent);
    }}
    .filter-btn, .sort-btn, .core-filter-btn {{
      appearance: none;
      border: 1px solid rgba(255, 255, 255, 0.1);
      background: rgba(0, 0, 0, 0.3);
      color: var(--muted);
      border-radius: 6px;
      padding: 5px 12px;
      font-size: 12px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      font-family: var(--font-mono);
    }}
    .filter-btn:hover, .sort-btn:hover, .core-filter-btn:hover {{
      background: rgba(0, 240, 255, 0.12);
      color: var(--text);
      border-color: var(--accent);
    }}
    .filter-btn.active, .sort-btn.active, .core-filter-btn.active {{
      background: rgba(255, 183, 0, 0.18);
      color: var(--amber);
      border-color: var(--amber);
      box-shadow: 0 2px 8px rgba(255, 183, 0, 0.2);
    }}
    .sort-pills {{
      display: flex;
      gap: 6px;
    }}
    .filter-status-row {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      color: var(--muted);
      padding-top: 4px;
      border-top: 1px dashed rgba(255, 255, 255, 0.05);
    }}
    .reset-btn {{
      appearance: none;
      border: 1px dashed var(--amber);
      background: rgba(255, 183, 0, 0.1);
      color: var(--amber);
      border-radius: 6px;
      padding: 3px 10px;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s ease;
      font-family: var(--font-mono);
    }}
    .reset-btn:hover {{
      background: rgba(255, 183, 0, 0.25);
      border-style: solid;
      box-shadow: 0 2px 8px rgba(255, 183, 0, 0.3);
    }}
    .kbd-hint {{
      display: inline-block;
      padding: 1px 5px;
      font-size: 10px;
      border: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 4px;
      background: rgba(255, 255, 255, 0.05);
      color: var(--muted);
      margin-left: 4px;
    }}
    mark.hl {{
      background: rgba(255, 183, 0, 0.25);
      color: var(--amber);
      border-bottom: 2px solid var(--amber);
      padding: 0 2px;
      border-radius: 2px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(330px, 1fr));
      gap: 20px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--panel-border);
      border-radius: 14px;
      padding: 20px 22px;
      box-shadow: var(--shadow);
      display: flex;
      flex-direction: column;
      gap: 14px;
      backdrop-filter: blur(12px);
      transition: all 0.2s ease;
    }}
    .card:hover {{
      transform: translateY(-3px);
      border-color: var(--accent);
      box-shadow: 0 16px 36px rgba(0, 240, 255, 0.12);
    }}
    .card[hidden] {{ display: none !important; }}
    .card-top {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
    }}
    .ticker-box {{
      display: flex;
      flex-direction: column;
    }}
    .date-chip {{
      font-size: 11px;
      color: var(--muted);
      font-weight: 600;
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 3px 8px;
      border-radius: 6px;
      white-space: nowrap;
      font-family: var(--font-mono);
    }}
    .ticker {{
      font-size: 13px;
      color: var(--accent);
      letter-spacing: 0.05em;
      font-weight: 700;
      font-family: var(--font-mono);
    }}
    .company {{
      margin-top: 2px;
      font-size: 24px;
      font-weight: 800;
      line-height: 1.2;
      color: #ffffff;
    }}
    .core-box {{
      background: rgba(0, 230, 118, 0.04);
      border: 1px solid rgba(0, 230, 118, 0.2);
      border-radius: 8px;
      padding: 8px 12px;
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .core-box:hover {{
      background: rgba(0, 230, 118, 0.12);
      border-color: var(--accent-emerald);
    }}
    .core-label {{
      color: var(--accent-emerald);
      font-size: 11px;
      font-weight: 800;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 2px;
    }}
    .core-value {{
      font-size: 13px;
      font-weight: 700;
      color: #f1f5f9;
    }}
    .summary {{
      font-size: 13px;
      color: var(--muted);
      line-height: 1.6;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }}
    .tag-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}
    .tag {{
      display: inline-flex;
      align-items: center;
      padding: 3px 9px;
      border-radius: 6px;
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid rgba(255, 255, 255, 0.08);
      color: var(--muted);
      font-size: 11px;
      font-weight: 600;
      font-family: var(--font-mono);
    }}
    .tag-btn {{
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .tag-btn:hover {{
      background: rgba(0, 240, 255, 0.15);
      border-color: var(--accent);
      color: #ffffff;
    }}
    .actions {{
      margin-top: auto;
      padding-top: 6px;
    }}
    .btn {{
      display: block;
      width: 100%;
      text-align: center;
      padding: 10px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 800;
      text-decoration: none;
      transition: all 0.2s ease;
      font-family: var(--font-mono);
    }}
    .btn-primary {{
      background: rgba(0, 240, 255, 0.1);
      color: var(--accent);
      border: 1px solid var(--accent);
    }}
    .btn-primary:hover {{
      background: rgba(0, 240, 255, 0.25);
      color: #ffffff;
      box-shadow: 0 4px 16px rgba(0, 240, 255, 0.3);
    }}
    .empty {{
      display: none;
      margin-top: 24px;
      padding: 32px;
      border-radius: 12px;
      border: 1px dashed var(--panel-border);
      color: var(--muted);
      text-align: center;
      background: rgba(0, 0, 0, 0.3);
    }}
    @media (max-width: 720px) {{
      .container {{ padding: 16px 12px 36px; }}
      .hero {{ padding: 16px; margin-bottom: 16px; border-radius: 12px; gap: 12px; }}
      .hero-logo {{ width: 38px; height: 38px; border-radius: 8px; }}
      .hero-text h1 {{ font-size: 20px; }}
      .slogan {{ font-size: 12px; }}
      .toolbar-row {{ flex-direction: column; align-items: stretch; gap: 10px; }}
      .filter-pills {{ overflow-x: auto; flex-wrap: nowrap; padding-bottom: 4px; -webkit-overflow-scrolling: touch; }}
      .filter-pills.expanded {{ flex-wrap: wrap; overflow-x: visible; }}
      .filter-pills.expanded .more-filters {{ display: flex; flex-wrap: wrap; gap: 6px; }}
      .filter-btn {{ flex-shrink: 0; }}
      .sort-pills {{ justify-content: flex-end; }}
      .grid {{ gap: 14px; }}
    }}
  </style>
  <link rel="icon" type="image/png" href="stonk_logo.png">
</head>
<body>
  <div class="container">
    <div class="term-top-bar">
      <div><span class="term-dot">● LIVE</span><span class="term-cmd">STONKS TERMINAL v2.0</span> // TPE MARKET PORTAL</div>
      <div>TOTAL: {total} REPORTS</div>
    </div>

    <header class="hero">
      <div class="hero-top">
        <div class="hero-brand">
          <img src="stonk_logo.png" alt="Stonks Logo" class="hero-logo">
          <div class="hero-text">
            <h1>台股死當 <span class="chip">TOTAL: {total}</span></h1>
            <p class="slogan"><code>[STATUS: ACTIVE]</code> 「死當之前做功課叫預防，死當之後做功課叫覺悟。」深度個股對話研究報告，直擊護城河與失效條件。</p>
          </div>
        </div>
      </div>

      <div class="search-box">
        <span class="cmd-prompt">RUN &gt;</span>
        <input id="searchInput" class="search-input" type="text" placeholder="搜尋股票代號、公司名或關鍵字 (按 '/' 鍵快速搜尋) &lt;GO&gt;" />
        <button id="clearSearchBtn" class="clear-btn" title="清空指令" aria-label="清空指令">✕</button>
      </div>

      <div class="toolbar-row">
        <div class="filter-pills" id="filters">
{filter_buttons}
        </div>
        <div class="sort-pills" id="sorts">
          <button class="sort-btn active" data-field="ticker">代號 <span class="sort-indicator">↑</span></button>
          <button class="sort-btn" data-field="name">名稱 <span class="sort-indicator">↓</span></button>
        </div>
      </div>
      <div class="core-filter-row" id="coreFilters">
{core_filter_buttons}
      </div>
      <div class="filter-status-row">
        <div>已顯示 <strong id="visibleCount" style="color: var(--accent);">{total}</strong> / <span id="totalCount">{total}</span> 份報告</div>
        <button id="resetFiltersBtn" class="reset-btn" style="display: none;" title="重置全部條件 (Esc)">⟲ 重置條件 <span class="kbd-hint">Esc</span></button>
      </div>
    </header>

    <section class="grid" id="reportGrid">
{cards_block}
    </section>

    <div class="empty" id="emptyState">沒有符合目前條件的報告。</div>

  </div>

  <script>
    const cards = Array.from(document.querySelectorAll('.card'));
    const filterButtons = Array.from(document.querySelectorAll('.filter-btn'));
    const sortButtons = Array.from(document.querySelectorAll('.sort-btn'));
    const coreFilterButtons = Array.from(document.querySelectorAll('.core-filter-btn'));
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const grid = document.getElementById('reportGrid');
    const emptyState = document.getElementById('emptyState');
    const filtersContainer = document.getElementById('filters');
    const visibleCountEl = document.getElementById('visibleCount');
    const resetFiltersBtn = document.getElementById('resetFiltersBtn');

    let activeFilter = 'all';
    let activeCoreFilter = 'all-core';
    let activeSortField = 'ticker';
    let activeSortDirection = 'asc';
    let searchTerm = '';

    function updateSortButtons() {{
      sortButtons.forEach(btn => {{
        const field = btn.dataset.field;
        const isActive = field === activeSortField;
        btn.classList.toggle('active', isActive);
        const indicator = btn.querySelector('.sort-indicator');
        if (indicator) {{
          indicator.textContent = isActive
            ? (activeSortDirection === 'asc' ? '↑' : '↓')
            : '↕';
        }}
      }});
    }}

    function matchesSearch(card) {{
      if (!searchTerm) return true;
      const haystack = [
        card.dataset.search || '',
        card.dataset.ticker || '',
        card.dataset.name || '',
        card.textContent || ''
      ].join(' ').toLowerCase();
      return haystack.includes(searchTerm);
    }}

    function applyHighlighting(card, query) {{
      ['ticker', 'company', 'core-value', 'summary'].forEach(cls => {{
        const el = card.querySelector('.' + cls);
        if (!el) return;
        if (!el.dataset.raw) {{
          el.dataset.raw = el.textContent;
        }}
        const raw = el.dataset.raw;
        if (!query) {{
          el.textContent = raw;
        }} else {{
          const escaped = query.replace(/[.*+?^${{}}()\\[\\]\\\\]/g, '\\$&');
          const regex = new RegExp(`(${{escaped}})`, 'gi');
          el.innerHTML = raw.replace(regex, '<mark class="hl">$1</mark>');
        }}
      }});
    }}

    function applyFilterAndSort() {{
      let visibleCount = 0;
      cards.forEach(card => {{
        const tags = (card.dataset.tags || '').split(' ');
        const coreBucket = card.dataset.coreBucket || 'all-core';
        const matchFilter = activeFilter === 'all' || tags.includes(activeFilter);
        const matchCore = activeCoreFilter === 'all-core' || coreBucket === activeCoreFilter;
        const matchSearch = matchesSearch(card);
        const show = matchFilter && matchCore && matchSearch;
        card.hidden = !show;
        if (show) {{
          visibleCount += 1;
          applyHighlighting(card, searchTerm);
        }}
      }});

      const sortedCards = [...cards].sort((a, b) => {{
        const tickerA = a.dataset.ticker || '';
        const tickerB = b.dataset.ticker || '';
        const nameA = a.dataset.name || '';
        const nameB = b.dataset.name || '';
        const compareValue = activeSortField === 'name'
          ? nameA.localeCompare(nameB, 'zh-Hant-u-kn-true')
          : tickerA.localeCompare(tickerB, 'zh-Hant-u-kn-true');
        return activeSortDirection === 'asc' ? compareValue : -compareValue;
      }});

      sortedCards.forEach(card => grid.appendChild(card));
      emptyState.style.display = visibleCount === 0 ? 'block' : 'none';

      if (visibleCountEl) {{
        visibleCountEl.textContent = visibleCount;
      }}

      const isFiltered = activeFilter !== 'all' || activeCoreFilter !== 'all-core' || searchTerm !== '';
      if (resetFiltersBtn) {{
        resetFiltersBtn.style.display = isFiltered ? 'inline-flex' : 'none';
      }}

      updateSortButtons();
    }}

    function resetAllFilters() {{
      activeFilter = 'all';
      activeCoreFilter = 'all-core';
      searchTerm = '';
      if (searchInput) searchInput.value = '';
      if (clearSearchBtn) clearSearchBtn.style.display = 'none';

      filterButtons.forEach(b => b.classList.toggle('active', b.dataset.filter === 'all'));
      coreFilterButtons.forEach(b => b.classList.toggle('active', b.dataset.coreFilter === 'all-core'));

      applyFilterAndSort();
    }}

    if (resetFiltersBtn) {{
      resetFiltersBtn.addEventListener('click', resetAllFilters);
    }}

    const toggleFilterBtn = document.getElementById('toggleFilterBtn');
    const moreFilters = document.getElementById('moreFilters');

    if (toggleFilterBtn && moreFilters) {{
      toggleFilterBtn.addEventListener('click', () => {{
        const isOpen = moreFilters.classList.toggle('open');
        toggleFilterBtn.textContent = isOpen ? '收起 ▴' : '更多 ▾';
        if (filtersContainer) {{
          filtersContainer.classList.toggle('expanded', isOpen);
        }}
      }});
    }}

    filterButtons.forEach(btn => {{
      btn.addEventListener('click', () => {{
        filterButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeFilter = btn.dataset.filter;
        applyFilterAndSort();
      }});
    }});

    coreFilterButtons.forEach(btn => {{
      btn.addEventListener('click', () => {{
        coreFilterButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeCoreFilter = btn.dataset.coreFilter;
        applyFilterAndSort();
      }});
    }});

    document.querySelectorAll('.core-box').forEach(box => {{
      box.addEventListener('click', (e) => {{
        e.stopPropagation();
        const bucket = box.dataset.coreBucket;
        if (!bucket) return;
        const targetBtn = coreFilterButtons.find(b => b.dataset.coreFilter === bucket);
        if (targetBtn) {{
          coreFilterButtons.forEach(b => b.classList.remove('active'));
          targetBtn.classList.add('active');
          activeCoreFilter = bucket;
          applyFilterAndSort();
          window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
      }});
    }});

    document.querySelectorAll('.tag-btn').forEach(tagBtn => {{
      tagBtn.addEventListener('click', (e) => {{
        e.stopPropagation();
        const tagKey = tagBtn.dataset.tagkey;
        const targetFilterBtn = filterButtons.find(b => b.dataset.filter === tagKey);
        if (targetFilterBtn) {{
          if (moreFilters && moreFilters.contains(targetFilterBtn) && !moreFilters.classList.contains('open')) {{
            moreFilters.classList.add('open');
            if (filtersContainer) {{
              filtersContainer.classList.add('expanded');
            }}
            if (toggleFilterBtn) toggleFilterBtn.textContent = '收起 ▴';
          }}
          filterButtons.forEach(b => b.classList.remove('active'));
          targetFilterBtn.classList.add('active');
          activeFilter = tagKey;
          applyFilterAndSort();
          window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
      }});
    }});

    sortButtons.forEach(btn => {{
      btn.addEventListener('click', () => {{
        const field = btn.dataset.field;
        if (field === activeSortField) {{
          activeSortDirection = activeSortDirection === 'asc' ? 'desc' : 'asc';
        }} else {{
          activeSortField = field;
          activeSortDirection = field === 'name' ? 'asc' : 'asc';
        }}
        applyFilterAndSort();
      }});
    }});

    searchInput.addEventListener('input', () => {{
      searchTerm = searchInput.value.trim().toLowerCase();
      clearSearchBtn.style.display = searchInput.value ? 'inline-flex' : 'none';
      applyFilterAndSort();
    }});

    clearSearchBtn.addEventListener('click', () => {{
      searchInput.value = '';
      searchTerm = '';
      clearSearchBtn.style.display = 'none';
      searchInput.focus();
      applyFilterAndSort();
    }});

    document.addEventListener('keydown', (e) => {{
      if (e.key === '/' && document.activeElement !== searchInput) {{
        e.preventDefault();
        if (searchInput) searchInput.focus();
      }} else if (e.key === 'Escape') {{
        resetAllFilters();
        if (searchInput) searchInput.blur();
      }}
    }});

    applyFilterAndSort();
  </script>
</body>
</html>'''


def update_index():
    entries = []
    for md_file in sorted(REPORTS_DIR.glob('*.md')):
        entry = infer_index_entry(md_file)
        if entry:
            html_file = OUT_DIR / entry['href']
            if html_file.exists():
                entries.append(entry)
    INDEX_PATH.write_text(build_index_html(entries), encoding='utf-8')
    return INDEX_PATH


def convert_file(md_path: Path):
    md = md_path.read_text(encoding='utf-8')
    title, meta, rounds, summary = parse_md(md)
    html_text = build_html(title, meta, rounds, summary, md)
    out_path = OUT_DIR / (md_path.stem + '.html')
    out_path.write_text(html_text, encoding='utf-8')
    return out_path


def resolve_input_path(input_arg: str) -> Path:
    p = Path(input_arg)
    if p.exists():
        return p
    candidate = REPORTS_DIR / input_arg
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f'Input markdown not found: {input_arg}')


def main():
    parser = argparse.ArgumentParser(description='Render stock dialogue markdown reports to one-page HTML.')
    parser.add_argument('--input', help='Single markdown report path to render. If omitted, render all markdown files in reports directory.')
    parser.add_argument('--skip-index', action='store_true', help='Skip auto-updating html/index.html after rendering.')
    args = parser.parse_args()

    created = []
    if args.input:
        md_file = resolve_input_path(args.input)
        created.append(convert_file(md_file))
    else:
        for md_file in sorted(REPORTS_DIR.glob('*.md')):
            created.append(convert_file(md_file))

    index_path = None
    if not args.skip_index:
        index_path = update_index()

    print('Created HTML files:')
    for p in created:
        print(str(p))
    if index_path:
        print('Updated index:')
        print(str(index_path))

if __name__ == '__main__':
    main()
