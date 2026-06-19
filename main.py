"""论文秒搜 PaperSearch v2.0 — 中英日三语学术论文搜索 FTS5+5平台并发"""
import tkinter as tk
from tkinter import Menu
import customtkinter as ctk
import os, sys, json, sqlite3, urllib.request, urllib.parse, re, threading, queue, webbrowser, ssl, hashlib, time

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

if getattr(sys, 'frozen', False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE, "papers.db")
PROXY_PATH = os.path.join(_BASE, "proxy.txt")
DIAG_PATH = os.path.join(_BASE, "diag.log")

def load_proxy() -> str:
    try:
        with open(PROXY_PATH, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except:
        return ""

def save_proxy(url: str):
    with open(PROXY_PATH, 'w', encoding='utf-8') as f:
        f.write(url.strip())

def _diag(msg):
    try:
        with open(DIAG_PATH, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except:
        pass

APP_TITLE = "论文秒搜 PaperSearch v2.0"
WINDOW_SIZE = "1200x800"
REQUEST_TIMEOUT = 8
MAX_RESULTS = 1000
FTS5_LIMIT = 500
POLL_INTERVAL = 100
TOTAL_ENGINES = 8

CN2EN = {
    '人工智能':'artificial intelligence','机器学习':'machine learning','深度学习':'deep learning',
    '神经网络':'neural network','自然语言':'natural language','计算机视觉':'computer vision',
    '机器人':'robotics','数据挖掘':'data mining','大数据':'big data','云计算':'cloud computing',
    '区块链':'blockchain','物联网':'internet of things','量子':'quantum','纳米':'nano',
    '基因':'gene','蛋白质':'protein','细胞':'cell','癌症':'cancer','免疫':'immune',
    '气候':'climate','能源':'energy','材料':'material','半导体':'semiconductor',
    '经济':'economics','金融':'finance','管理':'management','心理':'psychology',
    '教育':'education','社会':'sociology','政治':'politics','法律':'law',
    '哲学':'philosophy','数学':'mathematics','物理':'physics','化学':'chemistry',
    '生物':'biology','医学':'medicine','工程':'engineering','计算机':'computer',
    '遥感':'remote sensing','卫星':'satellite','雷达':'radar','传感器':'sensor',
    '无人':'unmanned','自动驾驶':'autonomous driving','电动汽车':'electric vehicle',
    '光伏':'photovoltaic','太阳能':'solar','风能':'wind energy','电池':'battery',
    '碳中和':'carbon neutral','碳达峰':'carbon peak','ESG':'ESG sustainability',
    'GPT':'GPT large language model','大模型':'large language model','ChatGPT':'ChatGPT',
    'AIGC':'AIGC generative AI','生成式':'generative','扩散模型':'diffusion model',
    'transformer':'transformer attention','注意力':'attention mechanism',
    '知识图谱':'knowledge graph','图神经网络':'graph neural network',
    '联邦学习':'federated learning','强化学习':'reinforcement learning',
    '网络安全':'cybersecurity','隐私':'privacy','加密':'encryption',
    '元宇宙':'metaverse','数字孪生':'digital twin','边缘计算':'edge computing',
    '5G':'5G communication','6G':'6G communication','WIFI':'wireless communication',
    '脑机':'brain computer interface','BCI':'brain computer interface',
    '合成生物':'synthetic biology','基因编辑':'gene editing CRISPR',
    'mRNA':'mRNA vaccine','疫苗':'vaccine','抗体':'antibody',
    '纳米材料':'nanomaterial','石墨烯':'graphene','钙钛矿':'perovskite',
    '固态电池':'solid state battery','钠离子':'sodium ion battery',
    '氢能':'hydrogen energy','核聚变':'nuclear fusion',
    '黑洞':'black hole','引力波':'gravitational wave','暗物质':'dark matter',
    '系外行星':'exoplanet','火星':'Mars','月球':'Moon',
    '柔性电子':'flexible electronics','可穿戴':'wearable',
    '3D打印':'3D printing additive manufacturing','增材制造':'additive manufacturing',
    '机器人手术':'robotic surgery','精准医疗':'precision medicine',
    '单细胞':'single cell sequencing','多组学':'multi omics',
    '力学':'mechanics','光学':'optics','电磁':'electromagnetic','热力学':'thermodynamics',
    '流体':'fluid dynamics','湍流':'turbulence','声学':'acoustics','超导':'superconductivity',
    '拓扑':'topology','凝聚态':'condensed matter','粒子':'particle physics','核物理':'nuclear physics',
    '等离子':'plasma physics','激光':'laser','光谱':'spectroscopy','衍射':'diffraction',
    '催化':'catalysis','有机合成':'organic synthesis','高分子':'polymer','色谱':'chromatography',
    '质谱':'mass spectrometry','电化学':'electrochemistry','结晶':'crystallization',
    '遗传':'genetics','基因组':'genomics','转录':'transcriptomics','代谢':'metabolomics',
    '微生物':'microbiome','病毒':'virus','细菌':'bacteria','真菌':'fungi',
    '干细胞':'stem cell','类器官':'organoid','组织工程':'tissue engineering',
    '神经科学':'neuroscience','认知':'cognitive science','行为':'behavioral science',
    '生态':'ecology','生物多样性':'biodiversity','进化':'evolution','分类学':'taxonomy',
    '海洋':'marine ocean','极地':'polar','沙漠':'desert','湿地':'wetland',
    '地震':'earthquake','火山':'volcano','海啸':'tsunami','地质':'geology',
    '气象':'meteorology','水文':'hydrology','冰川':'glacier','土壤':'soil science',
    '机械':'mechanical engineering','制造':'manufacturing','焊接':'welding','铸造':'casting',
    '模具':'mold die','轴承':'bearing','齿轮':'gear','液压':'hydraulic','气动':'pneumatic',
    '内燃机':'internal combustion engine','涡轮':'turbine','压缩机':'compressor',
    '制冷':'refrigeration','暖通':'HVAC heating ventilation','通风':'ventilation',
    '建筑':'architecture','结构':'structural engineering','抗震':'seismic','桥梁':'bridge',
    '隧道':'tunnel','岩土':'geotechnical','混凝土':'concrete','钢结构':'steel structure',
    '水处理':'water treatment','废水':'wastewater','固废':'solid waste','大气污染':'air pollution',
    '噪声':'noise pollution','环境':'environmental','生态修复':'ecological restoration',
    '测绘':'surveying mapping','GIS':'geographic information system','导航':'navigation',
    '交通':'transportation','物流':'logistics','供应链':'supply chain','铁路':'railway',
    '航空':'aviation aerospace','航天':'spacecraft','卫星导航':'GNSS','无人机':'UAV drone',
    '船舶':'ship marine','港口':'port','航道':'waterway',
    '纺织':'textile','服装':'garment','食品科学':'food science','发酵':'fermentation',
    '包装':'packaging','印刷':'printing','造纸':'papermaking',
    '芯片':'chip semiconductor','集成电路':'integrated circuit','FPGA':'FPGA','ARM':'ARM processor',
    '嵌入式':'embedded system','RFID':'RFID','NFC':'NFC',
    '天线':'antenna','射频':'radio frequency','微波':'microwave','毫米波':'millimeter wave',
    '信号处理':'signal processing','图像处理':'image processing','语音识别':'speech recognition',
    '模式识别':'pattern recognition','推荐系统':'recommender system',
    '时间序列':'time series','异常检测':'anomaly detection','聚类':'clustering','分类':'classification',
    '回归':'regression','优化':'optimization','运筹':'operations research',
    '控制':'control theory','自动化':'automation','SLAM':'SLAM',
    '人机交互':'human computer interaction','增强现实':'augmented reality',
    '虚拟现实':'virtual reality','混合现实':'mixed reality',
    '数据库':'database','分布式':'distributed system','并行':'parallel computing',
    '操作系统':'operating system','编译器':'compiler','编程语言':'programming language',
    '软件工程':'software engineering','DevOps':'DevOps','容器':'container docker',
    '微服务':'microservice','Serverless':'serverless',
    '临床':'clinical trial','诊断':'diagnosis','影像':'medical imaging',
    'CT':'computed tomography','MRI':'magnetic resonance imaging','超声':'ultrasound',
    '病理':'pathology','药理学':'pharmacology','药物递送':'drug delivery',
    '中药':'traditional Chinese medicine','针灸':'acupuncture',
    '流行病':'epidemiology','公共卫生':'public health','营养':'nutrition',
    '康复':'rehabilitation','护理':'nursing','心理健康':'mental health',
    '抑郁':'depression','焦虑':'anxiety','阿尔茨海默':'Alzheimer','帕金森':'Parkinson',
    '糖尿病':'diabetes','心血管':'cardiovascular','高血压':'hypertension',
    '肥胖':'obesity','自身免疫':'autoimmune disease',
    '农业':'agriculture','作物':'crop','育种':'plant breeding','灌溉':'irrigation',
    '肥料':'fertilizer','农药':'pesticide','病虫害':'pest disease','除草':'herbicide',
    '温室':'greenhouse','无土栽培':'hydroponics','精准农业':'precision agriculture',
    '林业':'forestry','畜牧':'livestock','水产':'aquaculture','渔业':'fishery',
    '宏观经济':'macroeconomics','微观经济':'microeconomics','计量经济':'econometrics',
    '博弈论':'game theory','行为经济':'behavioral economics','发展经济':'development economics',
    '国际贸易':'international trade','产业经济':'industrial organization',
    '劳动经济':'labor economics','公共财政':'public finance',
    '公司治理':'corporate governance','战略管理':'strategic management',
    '市场营销':'marketing','消费者行为':'consumer behavior','品牌':'branding',
    '组织行为':'organizational behavior','人力资源':'human resource management',
    '领导力':'leadership','创业':'entrepreneurship','创新':'innovation',
    '社会网络':'social network','人口':'demography','城市化':'urbanization',
    '移民':'immigration migration','不平等':'inequality','贫困':'poverty',
    '犯罪':'criminology','恐怖主义':'terrorism','国际关系':'international relations',
    '地缘政治':'geopolitics','外交':'diplomacy','冲突':'conflict',
    '考古':'archaeology','人类学':'anthropology','语言学':'linguistics',
    '文学':'literature','艺术史':'art history','音乐学':'musicology',
    '复合材料':'composite material','陶瓷材料':'ceramic material','金属材料':'metallic material',
    '高分子材料':'polymer material','生物材料':'biomaterial','智能材料':'smart material',
    '超材料':'metamaterial','二维材料':'two dimensional material',
    '碳纤维':'carbon fiber','玻璃纤维':'glass fiber','碳纳米管':'carbon nanotube',
    '量子点':'quantum dot','纳米线':'nanowire','薄膜':'thin film',
    '涂层':'coating','表面':'surface engineering','界面':'interface',
    '腐蚀':'corrosion','疲劳':'fatigue','断裂':'fracture','摩擦':'tribology',
    '无损检测':'nondestructive testing','结构健康':'structural health monitoring',
    '可再生能源':'renewable energy','生物质':'biomass energy','地热':'geothermal',
    '海洋能':'ocean energy','潮汐':'tidal energy','波浪能':'wave energy',
    '核能':'nuclear energy','核废料':'nuclear waste','核安全':'nuclear safety',
    '储能':'energy storage','超级电容':'supercapacitor','飞轮':'flywheel',
    '智能电网':'smart grid','微电网':'microgrid','需求响应':'demand response',
    '碳捕集':'carbon capture','碳封存':'carbon sequestration',
    '节能':'energy efficiency','建筑节能':'building energy saving',
    '自然语言处理':'NLP natural language processing',
}

JA2EN = {
    '人工知能':'artificial intelligence','機械学習':'machine learning','深層学習':'deep learning',
    '自然言語処理':'natural language processing','コンピュータビジョン':'computer vision',
    'ロボット':'robotics','データマイニング':'data mining','ビッグデータ':'big data',
    'クラウド':'cloud computing','ブロックチェーン':'blockchain','量子':'quantum computing',
    '遺伝子':'gene genome','タンパク質':'protein','細胞':'cell biology','癌':'cancer',
    '免疫':'immunology','気候変動':'climate change','エネルギー':'energy',
    '半導体':'semiconductor','経済':'economics','金融':'finance','心理学':'psychology',
    '教育':'education','社会学':'sociology','法学':'law','哲学':'philosophy',
    '数学':'mathematics','物理学':'physics','化学':'chemistry','生物学':'biology',
    '医学':'medicine','工学':'engineering','リモートセンシング':'remote sensing',
    '自動運転':'autonomous driving','電気自動車':'electric vehicle',
    '太陽光':'photovoltaic solar','風力':'wind energy','電池':'battery',
    'カーボンニュートラル':'carbon neutral','大規模言語モデル':'large language model',
    '生成AI':'generative AI','拡散モデル':'diffusion model',
    '知識グラフ':'knowledge graph','グラフニューラルネットワーク':'graph neural network',
    '連合学習':'federated learning','強化学習':'reinforcement learning',
    'サイバーセキュリティ':'cybersecurity','暗号':'encryption cryptography',
    'メタバース':'metaverse','デジタルツイン':'digital twin',
    'エッジコンピューティング':'edge computing','脳':'brain neuroscience',
    'ゲノム編集':'gene editing CRISPR','ワクチン':'vaccine',
    'ナノマテリアル':'nanomaterial','グラフェン':'graphene',
    '固体電池':'solid state battery','水素':'hydrogen energy',
    '核融合':'nuclear fusion','ブラックホール':'black hole',
    '重力波':'gravitational wave','ダークマター':'dark matter',
    'フレキシブル':'flexible electronics','ウェアラブル':'wearable',
    '3Dプリント':'3D printing additive manufacturing',
    'ロボット手術':'robotic surgery','精密医療':'precision medicine',
    '有機合成':'organic synthesis','触媒':'catalysis',
    '電気化学':'electrochemistry','幹細胞':'stem cell',
    '微生物':'microbiome','ウイルス':'virus','細菌':'bacteria',
    'バイオマス':'biomass energy','地熱':'geothermal',
    '超伝導':'superconductivity','レーザー':'laser',
    '再生可能':'renewable energy','ニューラルネットワーク':'neural network',
    '音声認識':'speech recognition','画像処理':'image processing',
    'パターン認識':'pattern recognition','レコメンド':'recommender system',
    '時系列':'time series analysis','異常検知':'anomaly detection',
}

SYNONYMS = {
    'AI':['artificial intelligence','machine intelligence','deep learning','neural network'],
    'NLP':['natural language processing','computational linguistics','text mining','language model','semantic analysis'],
    'CV':['computer vision','image recognition','visual recognition','object detection','image segmentation'],
    'ML':['machine learning','statistical learning','pattern recognition','predictive modeling'],
    'DL':['deep learning','neural network','deep neural network','CNN','transformer'],
    'RL':['reinforcement learning','deep reinforcement learning','Q-learning','policy gradient'],
    'IoT':['internet of things','ubiquitous computing','pervasive computing','smart home','sensor network'],
    'blockchain':['blockchain','distributed ledger','smart contract','decentralized','consensus protocol'],
    'EV':['electric vehicle','EV battery','lithium ion battery','battery management','charging infrastructure'],
    'solar':['solar energy','photovoltaic','perovskite solar cell','solar panel','solar efficiency'],
    'cancer':['cancer','tumor','oncology','immunotherapy','chemotherapy','tumor microenvironment'],
    'climate':['climate change','global warming','carbon emission','greenhouse gas','extreme weather'],
    'gene':['gene editing','CRISPR','genetic engineering','gene therapy','genome sequencing'],
    'robot':['robot','robotics','autonomous robot','humanoid robot','robot manipulation'],
    'chip':['semiconductor','chip','integrated circuit','transistor','Moore law','lithography'],
    'brain':['brain','neuroscience','neural','cognitive','brain computer interface','EEG','fMRI'],
    'drug':['drug discovery','pharmaceutical','drug delivery','small molecule','antibody drug','clinical trial'],
    'energy':['energy storage','renewable energy','battery','fuel cell','supercapacitor','energy efficiency'],
    'water':['water treatment','wastewater','desalination','water quality','membrane filtration'],
    'quantum':['quantum computing','quantum information','qubit','quantum entanglement','quantum supremacy'],
    '3dprint':['3D printing','additive manufacturing','bioprinting','metal 3D printing','stereolithography'],
    'covid':['COVID-19','SARS-CoV-2','coronavirus','pandemic','long COVID','mRNA vaccine','epidemiology'],
    'llm':['large language model','LLM','GPT','ChatGPT','prompt engineering','instruction tuning','RLHF'],
    'imagegen':['stable diffusion','image generation','text-to-image','DALL-E','Midjourney','latent diffusion'],
    'semiconductor':['semiconductor','silicon','wafer fabrication','FinFET','EUV lithography','Moore law'],
    'battery':['lithium ion battery','solid state battery','sodium ion battery','battery degradation','anode cathode'],
    'graphene':['graphene','2D material','transition metal dichalcogenide','hexagonal boron nitride','van der Waals'],
    'microbiome':['gut microbiome','metagenomics','probiotics','16S rRNA','dysbiosis','fecal microbiota transplant'],
    'autophagy':['autophagy','lysosome','mTOR','LC3','mitophagy','cellular senescence'],
    'epigenetics':['DNA methylation','histone modification','chromatin remodeling','epigenomics','CRISPR epigenome editing'],
    'exoplanet':['exoplanet','habitable zone','transit method','radial velocity','James Webb','Kepler mission'],
    'lidar':['LiDAR','point cloud','3D mapping','autonomous vehicle sensor','SLAM','depth sensing'],
    'cybersecurity':['cybersecurity','zero trust','ransomware','phishing','threat detection','penetration testing'],
    'edge':['edge computing','fog computing','IoT gateway','edge AI','mobile edge computing'],
    'metaverse':['metaverse','virtual reality','augmented reality','digital twin','spatial computing','AR/VR'],
    'biomaterial':['biomaterial','hydrogel','tissue scaffold','biocompatibility','degradable polymer','bioink'],
    'carbon':['carbon capture','carbon neutrality','CCUS','carbon trading','net zero','decarbonization'],
    'fusion':['nuclear fusion','tokamak','stellarator','ITER','plasma confinement','inertial confinement'],
    'spintronics':['spintronics','magnetic tunnel junction','MRAM','skyrmion','spin-orbit torque','ferromagnet'],
    'metamaterial':['metamaterial','negative refractive index','cloaking','photonic crystal','plasmonics','metasurface'],
    'gan':['generative adversarial network','style transfer','image synthesis','data augmentation','anomaly detection GAN'],
    'transformer':['transformer','attention mechanism','self-attention','BERT','vision transformer','multi-head attention'],
    'knowledge':['knowledge graph','knowledge distillation','graph neural network','relational learning','entity linking'],
    'multimodal':['multimodal learning','vision-language model','audio-visual','cross-modal retrieval','CLIP','multimodal fusion'],
    'robot_jp':['ロボット','自律ロボット','ロボット工学','知能ロボット','ヒューマノイド'],
    'ai_jp':['人工知能','機械学習','深層学習','ニューラルネットワーク','AI'],
    'climate_jp':['気候変動','地球温暖化','温暖化対策','脱炭素','カーボンニュートラル'],
    'gene_jp':['ゲノム','遺伝子','DNA','RNA','遺伝子編集','ゲノム編集'],
    'cancer_jp':['がん研究','腫瘍学','がん治療','がん免疫療法','抗がん剤'],
    'energy_jp':['再生可能エネルギー','太陽光発電','風力発電','水素エネルギー','蓄電池'],
    'nano_jp':['ナノテクノロジー','ナノ材料','量子ドット','ナノ粒子','カーボンナノチューブ'],
    'brain_jp':['脳科学','ニューロサイエンス','認知科学','神経科学','fMRI'],
    'material_jp':['材料科学','新素材','高分子','セラミックス','複合材料'],
}


def log(msg):
    try: print(f"[PaperSearch] {msg}")
    except: pass


def detect_language(text: str) -> str:
    for ch in text:
        cp = ord(ch)
        if 0x3040 <= cp <= 0x30FF:
            return 'ja'
    for ch in text:
        if 0x4E00 <= cp <= 0x9FFF:
            for ja_term in JA2EN:
                if ja_term in text:
                    return 'ja'
            return 'zh'
    return 'en'


def translate_query(q: str) -> list:
    terms = set()
    terms.add(q)
    q_stripped = q.strip()
    lang = detect_language(q_stripped)

    if lang == 'ja':
        if q_stripped in JA2EN:
            terms.add(JA2EN[q_stripped])
        for ja, en in JA2EN.items():
            if ja in q_stripped:
                terms.add(en)
        for key, syns in SYNONYMS.items():
            if key.endswith('_jp'):
                base = key.replace('_jp','')
                if base in q_stripped.lower() or any(s in q_stripped for s in syns):
                    terms.update(syns)
    else:
        if q_stripped in CN2EN:
            terms.add(CN2EN[q_stripped])
        for cn, en in CN2EN.items():
            if cn in q_stripped:
                terms.add(en)

        # 第二轮：翻译出的英文词再去匹配同义词
        en_terms = list(terms)
        for et in en_terms:
            et_lower = et.lower()
            for key, syns in SYNONYMS.items():
                if key.endswith('_jp'):
                    continue
                if key.lower() in et_lower or any(s.lower() in et_lower for s in syns):
                    terms.update(syns)

    q_lower = q_stripped.lower()
    for key, syns in SYNONYMS.items():
        if key.endswith('_jp'):
            continue
        if key.lower() in q_lower or any(s.lower() in q_lower for s in syns):
            terms.update(syns)

    return list(terms)[:25]


def init_db(db: sqlite3.Connection):
    db.execute("CREATE TABLE IF NOT EXISTS cache (id TEXT PRIMARY KEY, title TEXT, abstract TEXT, authors TEXT, year TEXT, source TEXT)")
    cur = db.execute("PRAGMA table_info(cache)")
    cols = {r[1] for r in cur.fetchall()}
    for col, sql in [
        ('url', "ALTER TABLE cache ADD COLUMN url TEXT"),
        ('source_id', "ALTER TABLE cache ADD COLUMN source_id TEXT"),
        ('language', "ALTER TABLE cache ADD COLUMN language TEXT"),
        ('tldr', "ALTER TABLE cache ADD COLUMN tldr TEXT"),
        ('citations', "ALTER TABLE cache ADD COLUMN citations INTEGER DEFAULT 0"),
        ('fetched_at', "ALTER TABLE cache ADD COLUMN fetched_at TEXT"),
        ('is_oa', "ALTER TABLE cache ADD COLUMN is_oa INTEGER DEFAULT -1"),
        ('pdf_url', "ALTER TABLE cache ADD COLUMN pdf_url TEXT"),
        ('doi', "ALTER TABLE cache ADD COLUMN doi TEXT"),
    ]:
        if col not in cols:
            try:
                db.execute(sql)
                log(f"DB迁移: 新增列 {col}")
            except Exception as e:
                log(f"DB迁移跳过 {col}: {e}")

    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(title, abstract, authors, year, source, tokenize='unicode61')")
    for t in ['cache_ai','cache_ad','cache_au']:
        db.execute(f"DROP TRIGGER IF EXISTS {t}")
    db.execute("CREATE TRIGGER cache_ai AFTER INSERT ON cache BEGIN INSERT INTO fts(rowid,title,abstract,authors,year,source) VALUES(new.rowid,new.title,new.abstract,new.authors,new.year,new.source); END")
    db.execute("CREATE TRIGGER cache_ad AFTER DELETE ON cache BEGIN INSERT INTO fts(fts,rowid,title,abstract,authors,year,source) VALUES('delete',old.rowid,old.title,old.abstract,old.authors,old.year,old.source); END")
    db.execute("CREATE TRIGGER cache_au AFTER UPDATE ON cache BEGIN INSERT INTO fts(fts,rowid,title,abstract,authors,year,source) VALUES('delete',old.rowid,old.title,old.abstract,old.authors,old.year,old.source); INSERT INTO fts(rowid,title,abstract,authors,year,source) VALUES(new.rowid,new.title,new.abstract,new.authors,new.year,new.source); END")

    try:
        missing = db.execute("SELECT count(*) FROM cache WHERE rowid NOT IN (SELECT rowid FROM fts)").fetchone()[0]
        if missing > 0:
            log(f"FTS索引修复: 补建 {missing} 篇旧论文索引")
            db.execute("INSERT INTO fts(rowid, title, abstract, authors, year, source) SELECT rowid, title, abstract, authors, year, source FROM cache WHERE rowid NOT IN (SELECT rowid FROM fts)")
    except:
        pass
    db.commit()


def db_insert_paper(db: sqlite3.Connection, paper: dict) -> bool:
    key = hashlib.sha256(paper.get('title','')[:80].lower().encode()).hexdigest()
    try:
        is_oa = paper.get('is_oa', None)
        is_oa_val = -1 if is_oa is None else (1 if is_oa else 0)
        db.execute("INSERT OR IGNORE INTO cache (id,title,abstract,authors,year,source,url,source_id,language,tldr,citations,fetched_at,is_oa,pdf_url,doi) VALUES(?,?,?,?,?,?,?,?,?,?,?,datetime('now'),?,?,?)", (
            key, paper.get('title',''), paper.get('abstract',''), paper.get('authors',''),
            paper.get('year',''), paper.get('source',''), paper.get('url',''),
            paper.get('source_id',''), paper.get('language',''), paper.get('tldr',''),
            paper.get('citations',0), is_oa_val, paper.get('pdf_url',''), paper.get('doi','')
        ))
        return db.changes() > 0
    except:
        return False


def db_search_fts(db: sqlite3.Connection, query: str, limit: int = 50) -> list:
    safe = query.replace(':',' ').replace('(',' ').replace(')',' ').replace('*',' ').replace('"',' ')
    try:
        rows = db.execute("SELECT c.title,c.abstract,c.authors,c.year,c.source,c.url,c.citations,c.tldr,c.language,c.is_oa,c.pdf_url,c.doi FROM cache c INNER JOIN (SELECT rowid FROM fts WHERE fts MATCH ? LIMIT ?) f ON c.rowid=f.rowid", (safe, limit)).fetchall()
        return [{'title':r[0],'abstract':r[1] or '','authors':r[2] or '','year':r[3] or '','source':'本地','url':r[5] or '','citations':r[6] or 0,'tldr':r[7] or '','language':r[8] or '','is_oa':None if r[9]==-1 else bool(r[9]),'pdf_url':r[10] or '','doi':r[11] or ''} for r in rows]
    except:
        return []


def db_search_like(db: sqlite3.Connection, query: str, limit: int = 100) -> list:
    safe = query.replace("'", "''")[:120]
    try:
        rows = db.execute(
            "SELECT title,abstract,authors,year,source,url,citations,tldr,language,is_oa,pdf_url,doi FROM cache WHERE title LIKE ? OR abstract LIKE ? LIMIT ?",
            (f"%{safe}%", f"%{safe}%", limit)
        ).fetchall()
        return [{'title':r[0],'abstract':r[1] or '','authors':r[2] or '','year':r[3] or '','source':'本地','url':r[5] or '','citations':r[6] or 0,'tldr':r[7] or '','language':r[8] or '','is_oa':None if r[9]==-1 else bool(r[9]),'pdf_url':r[10] or '','doi':r[11] or ''} for r in rows]
    except:
        return []


def db_count(db: sqlite3.Connection) -> int:
    try: return db.execute("SELECT count(*) FROM cache").fetchone()[0]
    except: return 0


# ── 来源颜色 ──
SRC_COLORS = {'本地':'#6c757d','OpenAlex':'#20c997','Semantic Scholar':'#339af0','arXiv':'#e94560','CiNii':'#f08c00','CORE':'#ae3ec9','PubMed':'#0d6efd','DOAJ':'#198754','百度学术':'#e74c3c'}


class PaperSearchApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.root = ctk.CTk()
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(900, 550)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        init_db(self.db)

        self.cancel_event = threading.Event()
        self.result_queue = queue.Queue()
        self.error_queue = queue.Queue()
        self.search_threads = []
        self.search_active = False
        self.all_results = []
        self.seen_ids = set()
        self.engine_counts = {}
        self._pending_inserts = []

        self._build_ui()
        self._update_cache_label()
        self.root.bind('<Escape>', lambda e: self._on_cancel())
        self.root.bind('<Control-l>', lambda e: self.search_entry.focus_set())

    def _build_ui(self):
        self.header = ctk.CTkFrame(self.root, fg_color="#1a1a4e", corner_radius=0, height=48)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)
        # ── 渐变背景: #1a1a4e → #2d1a4e ──
        self._gradient_bg = tk.Canvas(self.header, height=48, highlightthickness=0, bd=0)
        self._gradient_bg.place(relx=0, rely=0, relwidth=1, relheight=1)
        for i in range(48):
            r = int(0x1a + (0x2d - 0x1a) * i / 47)
            color = f'#{r:02x}1a4e'
            self._gradient_bg.create_line(0, i, 2000, i, fill=color)
        self._gradient_bg.lower()
        ctk.CTkLabel(self.header, text="论文秒搜 PaperSearch v2.0", font=ctk.CTkFont(size=16, weight="bold"), text_color="#e94560").pack(side=tk.LEFT, padx=18, pady=10)
        self.cache_label = ctk.CTkLabel(self.header, text="", font=ctk.CTkFont(size=11), text_color="#a0a0b0")
        self.cache_label.pack(side=tk.RIGHT, padx=18, pady=10)

        top_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        top_frame.pack(fill=tk.X, padx=14, pady=(12, 0))

        self.search_entry = ctk.CTkEntry(top_frame, placeholder_text="输入关键词，支持中文/English/日本語...", font=ctk.CTkFont(size=14), height=44, corner_radius=16, border_width=2, border_color="#3a3a6e")
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.search_entry.bind("<Return>", lambda e: self._start_search())

        self.cancel_btn = ctk.CTkButton(top_frame, text="取消", fg_color="#dc3545", hover_color="#c82333", width=70, height=42, font=ctk.CTkFont(size=12, weight="bold"), command=self._on_cancel)
        self.search_btn = ctk.CTkButton(top_frame, text="搜索", fg_color="#e94560", hover_color="#c72c4a", width=80, height=42, font=ctk.CTkFont(size=13, weight="bold"), command=self._start_search)
        self.search_btn.pack(side=tk.RIGHT)

        filter_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        filter_frame.pack(fill=tk.X, padx=14, pady=(8, 0))

        ctk.CTkLabel(filter_frame, text="语言:", font=ctk.CTkFont(size=11), text_color="#a0a0b0").pack(side=tk.LEFT, padx=(0, 4))
        self.lang_var = ctk.StringVar(value="auto")
        self.lang_combo = ctk.CTkComboBox(filter_frame, values=["自动", "中文", "English", "日本語"], width=90, height=26, font=ctk.CTkFont(size=11), command=self._on_lang_change, state="readonly")
        self.lang_combo.pack(side=tk.LEFT, padx=(0, 14))

        self.src_vars = {}
        self._src_chips = {}
        src_list = [("OpenAlex", True), ("Semantic Scholar", True), ("arXiv", True), ("PubMed", True), ("DOAJ", True), ("百度学术", True), ("CiNii", False), ("CORE", False)]
        for s, default in src_list:
            var = tk.BooleanVar(value=default)
            self.src_vars[s] = var
            base_color = SRC_COLORS.get(s, "#6c757d")
            btn_color = base_color if default else "#2a2a3e"
            chip = ctk.CTkButton(filter_frame, text=s, width=72, height=26,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color=btn_color, hover_color=base_color,
                corner_radius=12,
                command=lambda name=s: self._toggle_source_chip(name))
            chip.pack(side=tk.LEFT, padx=2)
            self._src_chips[s] = chip

        self.results_frame = ctk.CTkScrollableFrame(self.root, fg_color="transparent")
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 0))

        # 筛选栏始终显示
        self.filter_frame = ctk.CTkFrame(self.root, fg_color="#141428", corner_radius=8)
        self.filter_frame.pack(fill=tk.X, padx=14, pady=(6, 0))
        self.filter_vars = {}
        self.filter_cbs = {}
        self._build_filter_bar()

        # ── 底部状态栏 ──
        self.status_frame = ctk.CTkFrame(self.root, fg_color="#1a1a3e", corner_radius=0, height=36)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_frame.pack_propagate(False)
        # 分隔线
        separator = tk.Frame(self.root, bg="#2a2a4e", height=1)
        separator.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_label = ctk.CTkLabel(self.status_frame, text="就绪 | 输入关键词后按回车搜索", font=ctk.CTkFont(size=11), text_color="#8b949e")
        self.status_label.pack(side=tk.LEFT, padx=14, pady=8)
        self.progress = ctk.CTkProgressBar(self.status_frame, width=160, height=8, mode="determinate")
        self.progress.set(0)
        self.progress.pack(side=tk.RIGHT, padx=14, pady=8)
        self._set_progress(False)

    def _on_lang_change(self, val):
        self.lang_var.set(val)

    def _toggle_source_chip(self, name):
        """切换平台chip按钮的开关状态和颜色"""
        var = self.src_vars[name]
        new_val = not var.get()
        var.set(new_val)
        chip = self._src_chips[name]
        if new_val:
            chip.configure(fg_color=SRC_COLORS.get(name, "#6c757d"))
        else:
            chip.configure(fg_color="#2a2a3e")

    def _build_filter_bar(self):
        """构建筛选栏（初始隐藏），搜索完成后显示"""
        # row 0: 引用次数 + 发表年份
        row0 = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
        row0.pack(fill=tk.X, padx=10, pady=(8, 0))

        ctk.CTkLabel(row0, text="被引 ≥", font=ctk.CTkFont(size=11), text_color="#a0a0b0").pack(side=tk.LEFT)
        self.filter_cite = ctk.CTkEntry(row0, width=60, height=24, font=ctk.CTkFont(size=11), placeholder_text="0")
        self.filter_cite.pack(side=tk.LEFT, padx=(4, 14))
        self.filter_cite.insert(0, "0")

        ctk.CTkLabel(row0, text="年份:", font=ctk.CTkFont(size=11), text_color="#a0a0b0").pack(side=tk.LEFT)
        self.filter_yr_from = ctk.CTkEntry(row0, width=50, height=24, font=ctk.CTkFont(size=11), placeholder_text="起始")
        self.filter_yr_from.pack(side=tk.LEFT, padx=(4, 2))
        ctk.CTkLabel(row0, text="—", font=ctk.CTkFont(size=11), text_color="#a0a0b0").pack(side=tk.LEFT)
        self.filter_yr_to = ctk.CTkEntry(row0, width=50, height=24, font=ctk.CTkFont(size=11), placeholder_text="截止")
        self.filter_yr_to.pack(side=tk.LEFT, padx=(2, 14))

        ctk.CTkButton(row0, text="应用筛选", fg_color="#20c997", hover_color="#1a7f6e",
            width=80, height=26, font=ctk.CTkFont(size=11, weight="bold"),
            command=self._apply_filter).pack(side=tk.LEFT, padx=(0, 8))
        ctk.CTkButton(row0, text="清除", fg_color="#6c757d", hover_color="#545b62",
            width=50, height=26, font=ctk.CTkFont(size=11),
            command=self._clear_filter).pack(side=tk.LEFT)

        # 代理按钮
        proxy_text = "⚙ 代理" if not load_proxy() else "⚙ 代理:ON"
        self.proxy_btn = ctk.CTkButton(row0, text=proxy_text, fg_color="#6f42c1", hover_color="#563d7c",
            width=85, height=26, font=ctk.CTkFont(size=11), command=self._config_proxy)
        self.proxy_btn.pack(side=tk.RIGHT, padx=(8, 0))

        # row 1: 平台选择
        self.filter_src_row = ctk.CTkFrame(self.filter_frame, fg_color="transparent")
        self.filter_src_row.pack(fill=tk.X, padx=10, pady=(4, 8))
        ctk.CTkLabel(self.filter_src_row, text="筛选平台:", font=ctk.CTkFont(size=11), text_color="#a0a0b0").pack(side=tk.LEFT, padx=(0, 4))
        self.filter_placeholder = ctk.CTkLabel(self.filter_src_row, text="搜索后自动显示", font=ctk.CTkFont(size=10), text_color="#5a5a70")
        self.filter_placeholder.pack(side=tk.LEFT, padx=4)

    def _show_filter_bar(self):
        """搜索完成后动态创建平台checkbox"""
        for w in list(self.filter_src_row.winfo_children()):
            if not isinstance(w, ctk.CTkLabel):
                w.destroy()
        self.filter_vars.clear()
        self.filter_cbs.clear()

        self.filter_placeholder.configure(text="")
        available = sorted([src for src in self.engine_counts if src != '本地'], key=lambda s: self.engine_counts.get(s,0), reverse=True)
        for src in available:
            var = tk.BooleanVar(value=True)
            self.filter_vars[src] = var
            cb = ctk.CTkCheckBox(self.filter_src_row, text=f"{src}({self.engine_counts.get(src,0)})",
                variable=var, font=ctk.CTkFont(size=10), width=20, height=18,
                checkbox_width=14, checkbox_height=14)
            cb.pack(side=tk.LEFT, padx=2)

    def _apply_filter(self):
        """应用筛选条件，重新渲染"""
        try: min_cite = int(self.filter_cite.get().strip() or "0")
        except: min_cite = 0
        try: yr_from = int(self.filter_yr_from.get().strip() or "0")
        except: yr_from = 0
        try: yr_to = int(self.filter_yr_to.get().strip() or "0")
        except: yr_to = 0

        enabled_srcs = {s for s, v in self.filter_vars.items() if v.get()}

        filtered = []
        for r in self.all_results:
            if r.get('source','') not in enabled_srcs:
                continue
            if (r.get('citations',0) or 0) < min_cite:
                continue
            yr_str = r.get('year','') or '0'
            if yr_str == '' or yr_str is None:
                yr = 0
            else:
                try: yr = int(str(yr_str)[:4])
                except: yr = 0
            if yr_from > 0 and yr < yr_from:
                continue
            if yr_to > 0 and yr > yr_to:
                continue
            filtered.append(r)

        self._render_results(filtered)
        self.status_label.configure(text=f"筛选: {len(filtered)}/{len(self.all_results)}篇")

    def _clear_filter(self):
        """清除筛选条件，显示全部"""
        self.filter_cite.delete(0, tk.END); self.filter_cite.insert(0, "0")
        self.filter_yr_from.delete(0, tk.END)
        self.filter_yr_to.delete(0, tk.END)
        for var in self.filter_vars.values():
            var.set(True)
        self._apply_filter()

    def _config_proxy(self):
        """代理配置对话框"""
        dlg = ctk.CTkToplevel(self.root)
        dlg.title("配置学校代理 (EZproxy / CARSI)")
        dlg.geometry("600x420")
        dlg.resizable(False, False)
        dlg.transient(self.root)
        dlg.grab_set()
        dlg.configure(fg_color="#1a1a2e")

        ctk.CTkLabel(dlg, text="配置学校代理 — 付费墙论文通过校园IP下载", font=ctk.CTkFont(size=14, weight="bold"), text_color="#e0e0e0").pack(pady=(16, 2))
        ctk.CTkLabel(dlg, text="选学校或手动输入代理前缀 (CARSI联盟已有1100+所高校)", font=ctk.CTkFont(size=11), text_color="#8b949e").pack()

        # 预设学校下拉
        sel_row = ctk.CTkFrame(dlg, fg_color="transparent")
        sel_row.pack(fill=tk.X, padx=20, pady=(12, 6))
        ctk.CTkLabel(sel_row, text="选择学校:", font=ctk.CTkFont(size=11), text_color="#a0a0b0").pack(side=tk.LEFT, padx=(0, 6))

        PROXY_PRESETS = [
            ("请选择或手动输入", ""),
            ("清华大学", "https://ezproxy.lib.tsinghua.edu.cn/login?url="),
            ("北京大学", "https://libproxy.pku.edu.cn/login?url="),
            ("浙江大学", "https://libproxy.zju.edu.cn/login?url="),
            ("上海交通大学", "https://libproxy.sjtu.edu.cn/login?url="),
            ("复旦大学", "https://ezproxy.fudan.edu.cn/login?url="),
            ("南京大学", "https://ezproxy.nju.edu.cn/login?url="),
            ("武汉大学", "https://ezproxy.lib.whu.edu.cn/login?url="),
            ("中山大学", "https://ezproxy.sysu.edu.cn/login?url="),
            ("中国科学技术大学", "https://ezproxy.ustc.edu.cn/login?url="),
            ("华中科技大学", "https://ezproxy.hust.edu.cn/login?url="),
            ("西安交通大学", "https://ezproxy.lib.xjtu.edu.cn/login?url="),
            ("哈尔滨工业大学", "https://ezproxy.hit.edu.cn/login?url="),
            ("同济大学", "https://ezproxy.lib.tongji.edu.cn/login?url="),
            ("东南大学", "https://ezproxy.seu.edu.cn/login?url="),
            ("北京航空航天大学", "https://ezproxy.buaa.edu.cn/login?url="),
            ("北京理工大学", "https://ezproxy.bit.edu.cn/login?url="),
            ("南开大学", "https://ezproxy.nankai.edu.cn/login?url="),
            ("天津大学", "https://ezproxy.tju.edu.cn/login?url="),
            ("四川大学", "https://ezproxy.scu.edu.cn/login?url="),
            ("重庆大学", "https://ezproxy.cqu.edu.cn/login?url="),
            ("厦门大学", "https://ezproxy.xmu.edu.cn/login?url="),
            ("山东大学", "https://ezproxy.sdu.edu.cn/login?url="),
            ("吉林大学", "https://ezproxy.jlu.edu.cn/login?url="),
            ("华南理工大学", "https://ezproxy.scut.edu.cn/login?url="),
            ("中南大学", "https://ezproxy.csu.edu.cn/login?url="),
            ("大连理工大学", "https://ezproxy.dlut.edu.cn/login?url="),
            ("西北工业大学", "https://ezproxy.nwpu.edu.cn/login?url="),
            ("电子科技大学", "https://ezproxy.uestc.edu.cn/login?url="),
        ]

        preset_names = [p[0] for p in PROXY_PRESETS]
        self.proxy_combo = ctk.CTkComboBox(sel_row, values=preset_names, width=180, height=28, font=ctk.CTkFont(size=11), state="readonly")
        self.proxy_combo.pack(side=tk.LEFT)
        self.proxy_combo.set("请选择或手动输入")

        entry = ctk.CTkEntry(dlg, placeholder_text="https://ezproxy.lib.xxx.edu.cn/login?url=", font=ctk.CTkFont(size=12), height=36)
        entry.pack(fill=tk.X, padx=20, pady=(8, 4))
        current = load_proxy()
        if current:
            entry.insert(0, current)
            for name, url in PROXY_PRESETS:
                if url and url in current:
                    self.proxy_combo.set(name)
                    break

        def on_preset_chosen(val):
            for name, url in PROXY_PRESETS:
                if name == val and url:
                    entry.delete(0, tk.END)
                    entry.insert(0, url)

        self.proxy_combo.configure(command=on_preset_chosen)

        hint = ctk.CTkLabel(dlg, text="其他学校搜: CARSI官网 IdPlist → 找到学校代理地址 → 粘贴到上方", font=ctk.CTkFont(size=10), text_color="#5a5a70")
        hint.pack()

        btn_row = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_row.pack(pady=(12, 0))

        def do_save():
            url = entry.get().strip()
            save_proxy(url)
            self.proxy_btn.configure(text="⚙ 代理:ON" if url else "⚙ 代理")
            self._refresh_oa_badges()
            dlg.destroy()

        def do_clear():
            entry.delete(0, tk.END)
            do_save()

        ctk.CTkButton(btn_row, text="保存", fg_color="#20c997", hover_color="#1a7f6e",
            width=80, height=32, font=ctk.CTkFont(size=12, weight="bold"), command=do_save).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(btn_row, text="清除", fg_color="#dc3545", hover_color="#c82333",
            width=80, height=32, font=ctk.CTkFont(size=12), command=do_clear).pack(side=tk.LEFT, padx=4)
        ctk.CTkButton(btn_row, text="取消", fg_color="#6c757d", hover_color="#545b62",
            width=80, height=32, font=ctk.CTkFont(size=12), command=dlg.destroy).pack(side=tk.LEFT, padx=4)

        entry.focus_set()
        entry.bind("<Return>", lambda e: do_save())

    def _wrap_proxy(self, url: str) -> str:
        """如果有代理配置，把URL包进代理前缀"""
        prefix = load_proxy()
        if not prefix:
            return url
        return prefix + url

    def _refresh_oa_badges(self):
        """代理配置改变后刷新所有卡片标题的OA标记"""
        proxy = load_proxy()
        for w in self.results_frame.winfo_children()[1:]:
            paper = getattr(w, '_paper_data', None)
            oa_lbl = getattr(w, '_oa_label', None)
            tl = getattr(w, '_title_label', None)
            if not paper or not oa_lbl:
                continue
            is_oa = paper.get('is_oa', None)
            if is_oa is True:
                oa_lbl.configure(text="🟢 OA")
            elif is_oa is False and proxy:
                oa_lbl.configure(text="🟡 代理")
            elif is_oa is False:
                oa_lbl.configure(text="🔴 付费")
            else:
                oa_lbl.configure(text="⚪")
            if is_oa is False and proxy and tl:
                new_url = self._wrap_proxy(paper.get('url', ''))
                tl.unbind("<Button-1>")
                tl.bind("<Button-1>", lambda e, u=new_url: webbrowser.open(u))

    def _set_progress(self, active: bool):
        if active:
            self.progress.set(0)
            self.progress.pack(side=tk.RIGHT, padx=14, pady=8)
        else:
            try: self.progress.pack_forget()
            except: pass

    def _update_progress(self):
        total = len([s for s, v in self.src_vars.items() if v.get()])
        if total == 0:
            self.progress.set(1)
            return
        done = sum(1 for s in self.engine_status.values() if s.startswith("完成") or s.startswith("失败") or s.startswith("无结果"))
        self.progress.set(done / total)

    def _update_status_text(self):
        total = len(self.all_results)
        parts = []
        for name in self.engine_status:
            st = self.engine_status[name]
            if st == "等待中...":
                parts.append(f"{name}:⏳")
            elif st.startswith("搜索中"):
                parts.append(f"{name}:🔍")
            elif st.startswith("失败"):
                parts.append(f"{name}:❌")
            elif st.startswith("无结果"):
                parts.append(f"{name}:0篇")
            else:
                parts.append(f"{name}:{st.replace('完成(','').replace(')','')}")
        local_count = self.engine_counts.get('本地', 0)
        prefix = f"本地:{local_count}篇 | " if local_count else ""
        self.status_label.configure(text=f"[已收{total}篇] {prefix}{' '.join(parts)}")

    def _update_cache_label(self):
        n = db_count(self.db)
        self.cache_label.configure(text=f"本地缓存: {n:,}篇")

    DOI_RE = re.compile(r'10\.\d{4,}/[^\s一-鿿"\'<>]+', re.I)

    def _start_search(self):
        q = self.search_entry.get().strip()
        if not q: return

        doi_match = self.DOI_RE.search(q)
        if doi_match:
            doi = doi_match.group().rstrip('.')
            threading.Thread(target=self._resolve_doi, args=(doi,), daemon=True).start()
            return
        print(f"[PaperSearch] 搜索: {q}")
        self._on_cancel()
        self.cancel_event.clear()
        self.all_results.clear()
        self.seen_ids.clear()
        self.engine_counts.clear()
        self._pending_inserts.clear()
        self.search_active = True
        _diag(f"=== 搜索开始: {q} ===")
        _diag(f"启用引擎: {[s for s, v in self.src_vars.items() if v.get()]}")
        self.engine_status = {}
        for s in [s for s, v in self.src_vars.items() if v.get()]:
            self.engine_status[s] = "等待中..."
        self.engine_status['本地'] = "等待中..."

        for w in self.results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.results_frame, text=f"正在搜索: {q}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#e0e0e0").pack(anchor=tk.W, pady=(0, 6))

        self._set_progress(True)
        self.status_label.configure(text="搜索中...")
        self.cancel_btn.pack(side=tk.RIGHT, padx=(8, 0), before=self.search_btn)

        lang_override = self.lang_var.get()
        enabled_srcs = [s for s, v in self.src_vars.items() if v.get()]
        def _safe_do_search():
            try:
                self._do_search(q, lang_override, enabled_srcs)
            except Exception as e:
                _diag(f"_do_search 线程崩溃: {e}")
                import traceback
                _diag(traceback.format_exc())
                self.result_queue.put(('done', None))
        threading.Thread(target=_safe_do_search, daemon=True).start()
        self.root.after(POLL_INTERVAL, self._process_results)

    def _on_cancel(self):
        self.cancel_event.set()
        self.status_label.configure(text="正在取消...")

    def _on_close(self):
        self.cancel_event.set()
        for t in list(self.search_threads):
            t.join(timeout=0.8)
        try:
            self.db.commit()
            self.db.close()
        except:
            pass
        self.root.destroy()

    ENGINE_LANG_PREF = {
        '百度学术': ['zh'],
        'CiNii': ['ja', 'en'],
        'OpenAlex': ['en', 'zh', 'ja'],
        'Semantic Scholar': ['en'],
        'arXiv': ['en'],
        'PubMed': ['en'],
        'DOAJ': ['en'],
        'CORE': ['en'],
    }

    def _resolve_doi(self, doi: str):
        """DOI 直搜：在线程中查 Crossref，结果用 after 回调到主线程"""
        self.search_active = True
        self.root.after(0, lambda: self._doi_ui_loading(doi))

        paper = None
        try:
            crossref_url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
            data = json.loads(self._get(crossref_url))
            msg = data.get("message", {})
            title = msg.get("title", [""])[0] or msg.get("container-title", [""])[0] or ""
            abstract = msg.get("abstract", "")[:1000]
            authors = ", ".join([f"{a.get('given','')} {a.get('family','')}" for a in msg.get("author", [])])[:200]
            year = str(msg.get("published-print", {}).get("date-parts", [[0]])[0][0]
                       or msg.get("published-online", {}).get("date-parts", [[0]])[0][0]
                       or msg.get("created", {}).get("date-parts", [[0]])[0][0] or "")[:4]
            publisher = msg.get("publisher", "")
            journal = msg.get("container-title", [""])[0] or publisher
            citations = msg.get("is-referenced-by-count", 0) or 0
            pdf_url = ""
            is_oa = None
            for l in msg.get("link", []):
                if l.get("content-type") in ("application/pdf", "text/html"):
                    pdf_url = l.get("URL", "")
                    is_oa = True
                    break
            paper = {
                "title": title, "abstract": abstract, "authors": authors,
                "year": year, "source": f"DOI: {journal}" if journal else "DOI",
                "url": f"https://doi.org/{doi}", "doi": doi, "source_id": doi,
                "citations": citations, "language": "en", "tldr": "",
                "is_oa": is_oa, "pdf_url": pdf_url,
            }
        except Exception as e:
            _diag(f"Crossref解析失败: {e}")

        if not paper or not paper.get("title"):
            paper = {
                "title": f"[DOI] {doi}", "abstract": "无法解析DOI元数据，点击链接访问原文",
                "authors": "", "year": "", "source": "DOI",
                "url": f"https://doi.org/{doi}", "doi": doi, "source_id": doi,
                "citations": 0, "language": "en", "tldr": "", "is_oa": None, "pdf_url": "",
            }

        self.all_results = [paper]
        self.engine_counts = {"DOI查询": 1}
        self.engine_status = {}
        self.search_active = False
        self.root.after(0, lambda: self._doi_ui_done(paper))

    def _doi_ui_loading(self, doi):
        for w in self.results_frame.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.results_frame, text=f"正在查找 DOI: {doi}", font=ctk.CTkFont(size=13, weight="bold"), text_color="#e0e0e0").pack(anchor=tk.W, pady=(0, 6))
        self.status_label.configure(text=f"DOI查询: {doi}")

    def _doi_ui_done(self, paper):
        self._render_results([paper])
        self._show_filter_bar()
        self.status_label.configure(text=f"DOI查询: 1篇")

    def _get(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": "PaperSearch/2.0"})
        return urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT, context=_SSL_CTX).read()

    def _do_search(self, q: str, lang_override: str, srcs: list):
        if lang_override == "中文": lang = "zh"
        elif lang_override == "English": lang = "en"
        elif lang_override == "日本語": lang = "ja"
        else: lang = detect_language(q)
        all_queries = translate_query(q)

        zh_qs = [t for t in all_queries if any('一' <= c <= '鿿' for c in t)]
        ja_qs = [t for t in all_queries if any('぀' <= c <= 'ヿ' for c in t)]
        en_qs = [t for t in all_queries if t not in set(zh_qs) and t not in set(ja_qs)]

        def _build_engine_qs(engine_name):
            prefs = self.ENGINE_LANG_PREF.get(engine_name, ['en'])
            result = []
            for pref in prefs:
                if pref == 'zh':
                    result.extend(zh_qs)
                elif pref == 'ja':
                    result.extend(ja_qs)
                elif pref == 'en':
                    result.extend(en_qs)
            seen = set()
            uniq = []
            for t in result:
                if t not in seen:
                    seen.add(t)
                    uniq.append(t)
            return uniq[:25]

        log(f"查询扩展: {len(all_queries)}词 (中{len(zh_qs)}/英{len(en_qs)}/日{len(ja_qs)}) | {len(srcs)}平台")
        self.result_queue.put(('log', f"查询扩展: {len(all_queries)}个词 | 语言: {lang} | 平台: {len(srcs)}个"))

        all_local = []
        fts_seen = set()
        for sq in all_queries[:8]:
            for r in db_search_fts(self.db, sq, FTS5_LIMIT):
                rid = hashlib.sha256(r['title'][:80].lower().encode()).hexdigest()
                if rid not in self.seen_ids:
                    self.seen_ids.add(rid)
                    fts_seen.add(rid)
                    all_local.append(r)

        for sq in all_queries[:3]:
            for r in db_search_like(self.db, sq, 80):
                rid = hashlib.sha256(r['title'][:80].lower().encode()).hexdigest()
                if rid not in self.seen_ids:
                    self.seen_ids.add(rid)
                    r['source'] = '本地'
                    all_local.append(r)

        log(f"本地: FTS5 {len(fts_seen)}篇 + LIKE补充 {len(all_local)-len(fts_seen)}篇 = {len(all_local)}篇")
        for r in all_local:
            self.result_queue.put(('result', r))
        log(f"本地缓存命中: {len(all_local)}篇")
        self.engine_status['本地'] = f"完成({len(all_local)}篇)"

        threads = []
        for engine_name in srcs:
            engine_qs = _build_engine_qs(engine_name)
            log(f"  [{engine_name}] 查询词: {engine_qs[:3]}...")
            self.engine_status[engine_name] = "搜索中..."
            t = threading.Thread(target=self._run_engine, args=(engine_name, engine_qs), daemon=True)
            t.start()
            threads.append(t)
        self.search_threads = threads

        for t in threads:
            t.join()
        self.result_queue.put(('done', None))

    ENGINE_CLASS_MAP = {
        'OpenAlex': 'OpenAlexClient',
        'Semantic Scholar': 'SemanticScholarClient',
        'arXiv': 'ArxivClient',
        'CiNii': 'CiNiiClient',
        'CORE': 'CoreClient',
        'PubMed': 'PubMedClient',
        'DOAJ': 'DOAJClient',
        '百度学术': 'BaiduScholarClient',
    }

    def _run_engine(self, name: str, queries: list):
        try:
            cls_name = self.ENGINE_CLASS_MAP.get(name, name.replace(' ','')+'Client')
            mod = __import__('engines', fromlist=[cls_name])
            cls = getattr(mod, cls_name)
            self.engine_status[name] = "搜索中..."
            cls.search(queries, self.cancel_event, self.result_queue)
            self.result_queue.put(('engine_done', name))
        except ImportError as e:
            self.engine_status[name] = "失败"
            self.result_queue.put(('log', f"[{name}] 引擎加载失败: {e}"))
        except Exception as e:
            self.engine_status[name] = "失败"
            self.result_queue.put(('log', f"[{name}] {e}"))

    def _flush_inserts(self):
        if not self._pending_inserts:
            return
        batch = self._pending_inserts[:]
        self._pending_inserts.clear()
        try:
            for paper in batch:
                db_insert_paper(self.db, paper)
        except Exception:
            pass

    def _process_results(self):
        try:
            self._process_results_inner()
        except Exception as e:
            _diag(f"_process_results 异常: {e}")
            import traceback
            _diag(traceback.format_exc())
            if not self.cancel_event.is_set():
                self.root.after(POLL_INTERVAL, self._process_results)

    def _process_results_inner(self):
        max_per_tick = 60
        processed = 0
        done_received = False
        try:
            while processed < max_per_tick:
                kind, data = self.result_queue.get_nowait()
                if kind == 'result':
                    self.all_results.append(data)
                    src = data.get('source', '')
                    self.engine_counts[src] = self.engine_counts.get(src, 0) + 1
                    self._pending_inserts.append(data)
                    processed += 1
                elif kind == 'log':
                    log(str(data))
                elif kind == 'engine_done':
                    name = data
                    cnt = self.engine_counts.get(name, 0)
                    self.engine_status[name] = f"完成({cnt}篇)" if cnt > 0 else "无结果"
                elif kind == 'done':
                    done_received = True
                    break
        except queue.Empty:
            pass

        self._update_progress()
        self._update_status_text()

        if done_received:
            self._drain_remaining()
            self._flush_inserts()
            self._on_search_done()
        else:
            self.root.after(POLL_INTERVAL, self._process_results)

    def _drain_remaining(self):
        while True:
            try:
                kind, data = self.result_queue.get_nowait()
                if kind == 'result':
                    self.all_results.append(data)
                    src = data.get('source', '')
                    self.engine_counts[src] = self.engine_counts.get(src, 0) + 1
                    self._pending_inserts.append(data)
                elif kind == 'engine_done':
                    name = data
                    cnt = self.engine_counts.get(name, 0)
                    self.engine_status[name] = f"完成({cnt}篇)" if cnt > 0 else "无结果"
                elif kind == 'log':
                    log(str(data))
            except queue.Empty:
                break

    def _on_search_done(self):
        self.search_active = False
        self._set_progress(False)
        try: self.cancel_btn.pack_forget()
        except: pass
        self._flush_inserts()
        self._render_results(self.all_results)
        self.db.commit()
        self._update_cache_label()
        self._show_filter_bar()

        parts = []
        for src in ['本地','OpenAlex','Semantic Scholar','arXiv','PubMed','DOAJ','百度学术','CiNii','CORE']:
            if src in self.engine_counts:
                parts.append(f"{src}:{self.engine_counts[src]}")
        total = len(self.all_results)
        suffix = " (已取消)" if self.cancel_event.is_set() else ""
        self.status_label.configure(text=f"显示 {min(total,MAX_RESULTS)}/{total}篇{suffix} | {' '.join(parts)}")

    def _render_results(self, source_list=None):
        """分批渐进渲染：每帧15张卡片，不阻塞UI"""
        if source_list is None:
            source_list = self.all_results

        # 排序
        q = self.search_entry.get().strip().lower()
        q_terms = set(q.split())
        def sort_key(r):
            s = 0
            title = (r.get('title','') or '').lower()
            for t in q_terms:
                if t in title: s += 100
            s += (r.get('citations', 0) or 0) // 10
            try: s += int(r.get('year', '0') or '0') // 10
            except: pass
            return s

        results = sorted(source_list, key=sort_key, reverse=True)
        if MAX_RESULTS > 0 and source_list is self.all_results:
            results = results[:MAX_RESULTS]

        # 清空旧卡片
        for w in list(self.results_frame.winfo_children())[1:]:
            w.destroy()

        if not results:
            ctk.CTkLabel(self.results_frame, text="暂无结果", font=ctk.CTkFont(size=13), text_color="#6c757d").pack(pady=20)
            return

        # 分帧渲染：每批15张，after(1)调度下一批
        self._render_queue = results
        self._render_idx = 0
        self.root.after(1, self._render_batch)

    def _render_batch(self):
        batch = 15
        end = min(self._render_idx + batch, len(self._render_queue))
        for i in range(self._render_idx, end):
            self._create_card(self._render_queue[i])
        self._render_idx = end
        self.root.update_idletasks()
        if self._render_idx < len(self._render_queue):
            self.root.after(1, self._render_batch)
        else:
            self._render_queue = None

    def _create_card(self, paper: dict):
        src = paper.get('source', '')
        is_oa = paper.get('is_oa', None)
        pdf_url = paper.get('pdf_url', '')
        url = paper.get('url', '')
        proxy = load_proxy()

        if is_oa is True:
            oa_badge = "🟢 OA"
        elif is_oa is False and proxy:
            oa_badge = "🟡 代理"
            url = self._wrap_proxy(url)
        elif is_oa is False:
            oa_badge = "🔴 付费"
        else:
            oa_badge = "⚪"

        bar_color = SRC_COLORS.get(src, "#6c757d")

        card = ctk.CTkFrame(self.results_frame, fg_color="#1a1a2e", corner_radius=6)
        card.pack(fill=tk.X, padx=2, pady=2)
        card._paper_data = paper

        # ── 左侧 3px 颜色条 ──
        color_bar = tk.Frame(card, bg=bar_color, width=3)
        color_bar.pack(side=tk.LEFT, fill=tk.Y)
        color_bar.pack_propagate(False)

        # ── 内容容器 ──
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0))

        # Row 1: 标题 + 来源badge + OA标记
        title_row = ctk.CTkFrame(content, fg_color="transparent")
        title_row.pack(fill=tk.X, pady=(6, 2))
        src_badge = ctk.CTkLabel(title_row, text=f" {src} ",
            font=ctk.CTkFont(size=9, weight="bold"),
            fg_color=bar_color, corner_radius=4, text_color="#ffffff")
        src_badge.pack(side=tk.RIGHT, padx=(4, 0))
        oa_label = ctk.CTkLabel(title_row, text=oa_badge,
            font=ctk.CTkFont(size=9), text_color="#8b949e")
        oa_label.pack(side=tk.RIGHT, padx=(4, 0))
        card._oa_label = oa_label

        title_text = paper.get('title', 'Untitled')
        click_url = pdf_url or url
        title_label = ctk.CTkLabel(title_row, text=title_text,
            font=ctk.CTkFont(size=12, weight="bold"), text_color="#4a9eff",
            cursor="hand2" if click_url else "arrow", anchor=tk.W)
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if click_url:
            title_label.bind("<Button-1>", lambda e, u=click_url: webbrowser.open(u))
            title_label.bind("<Button-3>", lambda e, u=url, t=title_text: self._context_menu(e, u, t, paper.get('abstract','')))
        card._title_label = title_label

        # Row 2: 作者 + 年份 + DOI + 引用
        meta_row = ctk.CTkFrame(content, fg_color="transparent")
        meta_row.pack(fill=tk.X, pady=(0, 2))
        meta_parts = []
        authors = paper.get('authors', '')[:80]
        if authors:
            meta_parts.append(f"{authors}")
        year = paper.get('year', '')
        if year:
            meta_parts.append(f"{year}")
        doi = paper.get('doi', '')
        if doi:
            meta_parts.append(f"DOI:{doi[:30]}")
        citations = paper.get('citations', 0)
        if citations:
            meta_parts.append(f"被引{citations}")
        if meta_parts:
            ctk.CTkLabel(meta_row, text="  |  ".join(meta_parts),
                font=ctk.CTkFont(size=10), text_color="#a0a0b0",
                anchor=tk.W).pack(fill=tk.X)

        # Row 3: 摘要 / TLDR
        abstract = paper.get('abstract', '') or ''
        tldr = paper.get('tldr', '') or ''
        if tldr:
            abstract = f"💡 {tldr}" + (f" — {abstract[:200]}" if abstract else "")
        abstract = abstract[:300] if abstract else ""
        if abstract:
            ctk.CTkLabel(content, text=abstract,
                font=ctk.CTkFont(size=10), text_color="#6c757d",
                anchor=tk.W, wraplength=1050).pack(fill=tk.X, pady=(0, 6))
        elif not meta_parts:
            ctk.CTkLabel(content, text=" ", font=ctk.CTkFont(size=10)).pack()

    def _context_menu(self, event, url, title, abstract):
        menu = Menu(self.root, tearoff=0, bg="#1e1e2e", fg="#e0e0e0", activebackground="#e94560", font=("Microsoft YaHei", 10))
        menu.add_command(label="打开原文", command=lambda: webbrowser.open(url))
        menu.add_command(label="复制标题", command=lambda: self.root.clipboard_append(title))
        if abstract:
            menu.add_command(label="复制摘要", command=lambda: self.root.clipboard_append(abstract))
        menu.add_command(label="复制链接", command=lambda: self.root.clipboard_append(url))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    PaperSearchApp().run()
