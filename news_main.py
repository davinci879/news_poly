# -*- coding: utf-8 -*-
"""
中文新闻聚合客户端
门户首页抓取 + 详情页正文提取，按关键词分子分类，本地 JSON 存储。
"""
import sys
import os
import re
import json
import html as html_mod
from datetime import datetime, timedelta

os.environ["QT_LOGGING_RULES"] = "*=false;*.debug=false;*.warning=false"

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QListWidget, QListWidgetItem, QStackedWidget, QLabel, QLineEdit,
    QScrollArea, QPushButton, QDialog, QTextBrowser, QFrame,
    QMessageBox, QGridLayout, QButtonGroup, QStatusBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QUrl, QObject, QTimer
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt5.QtGui import QFont, QCursor, QDesktopServices


# ============== 路径 ==============
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)


# ============== 门户首页 ==============
# 每项: (显示名, URL, 归属分类)
PORTALS = [
    ("中国知识产权报", "https://www.iprchn.com",            "知产"),
    ("中国保护知识产权网", "https://ipr.mofcom.gov.cn",     "知产"),
    ("国家知识产权局", "https://www.cnipa.gov.cn",         "知产"),
    ("中国知识产权网", "https://www.cnipr.com",            "知产"),
    ("知产法网",      "https://chinaiprlaw.cn",            "知产"),
    ("IPRdaily",     "https://www.iprdaily.com",           "知产"),
    ("智南针",       "https://www.zhinanzhen.com",         "知产"),
    ("WIPO",        "https://www.wipo.int",               "知产"),
    ("World IP Review","https://www.worldipreview.com",    "知产"),
    ("IPWatchdog",   "https://www.ipwatchdog.com",         "知产"),
    ("IAM",         "https://www.iam-media.com",          "知产"),
    ("知产力",     "https://www.zhichanli.com",         "知产"),
    ("知宝网",     "https://www.zhibaip.com",          "知产"),
    ("最高法知产庭","https://ipc.court.gov.cn",        "知产"),
    ("智慧芽资讯", "https://www.zhihuiya.com/news",    "知产"),
    ("思博论坛",   "https://www.mysipo.com",           "知产"),
    ("知产宝",     "https://www.iprdb.com",            "知产"),
    ("中国商标网", "https://sbj.cnipa.gov.cn",         "知产"),
    ("中国版权保护中心","https://www.ccopyright.com.cn","知产"),
    ("中国经济网", "http://www.ce.cn",               "财经门户"),
    ("财联社",     "https://www.cls.cn",             "财经门户"),
    ("中国证券报", "https://www.cs.com.cn",          "财经门户"),
    ("证券时报",   "https://www.stcn.com",          "财经门户"),
    ("上海证券报", "https://www.cnstock.com",        "财经门户"),
    ("证券日报",   "https://www.zqrb.cn",           "财经门户"),
    ("经济参考网", "https://www.jjckb.cn",          "财经门户"),
    ("新浪财经",   "https://finance.sina.com.cn",   "财经门户"),
    ("腾讯财经",   "https://finance.qq.com",        "财经门户"),
    ("网易财经",   "https://money.163.com",         "财经门户"),
    ("搜狐财经",   "https://business.sohu.com",     "财经门户"),
    ("财新网",     "https://www.caixin.com.cn",     "财经门户"),
    ("第一财经",   "https://www.yicai.com",         "财经门户"),
    ("界面新闻",   "https://www.jiemian.com",       "财经门户"),
    ("21财经",    "https://www.21jingji.com",       "财经门户"),
    ("每日经济新闻","https://www.nbd.com.cn",       "财经门户"),
    ("和讯网",     "https://www.hexun.com",         "财经门户"),
    ("东方财富",   "https://www.eastmoney.com",     "财经门户"),
    ("金融界",     "https://www.jrj.com",           "财经门户"),
    ("雪球",       "https://xueqiu.com",           "财经门户"),
    ("Yahoo Finance","https://finance.yahoo.com",   "财经门户"),
    ("华尔街见闻", "https://wallstreetcn.com",        "财经门户"),
    ("金十数据",   "https://www.jin10.com",           "财经门户"),
    ("新浪新闻",   "https://news.sina.com.cn",       "综合门户"),
    ("网易新闻",   "https://news.163.com",           "综合门户"),
    ("腾讯新闻",   "https://news.qq.com",            "综合门户"),
    ("搜狐新闻",   "https://news.sohu.com",          "综合门户"),
    ("环球网",     "https://www.huanqiu.com",          "国际"),
    ("海外网",     "https://www.haiwainet.cn",         "国际"),
    ("新华网国际", "https://www.xinhuanet.com/world/", "国际"),
    ("人民网国际", "https://www.people.com.cn/world/", "国际"),
    ("中新网国际", "https://www.chinanews.com.cn/world/", "国际"),
    ("观察者网",   "https://www.guancha.cn",           "国际"),
    ("参考消息",   "https://www.cankaoxiaoxi.com",     "国际"),
    ("环球时报英文版","https://www.globaltimes.cn",   "国际"),
    ("澎湃国际",   "https://www.thepaper.cn/world",    "国际"),
    ("凤凰国际",   "https://news.ifeng.com/world",     "国际"),
    ("国防部网",   "http://www.mod.gov.cn",            "国际"),
    ("解放军报",   "http://www.81.cn",                 "国际"),
    ("环球军事",   "https://mil.huanqiu.com",          "国际"),
    ("观察者军事", "https://www.guancha.cn/military",  "国际"),
    ("防务新闻",   "https://www.defensenews.com",      "国际"),
    ("BBC",       "https://www.bbc.com/news",          "国际"),
    ("Foreign Policy","https://foreignpolicy.com",    "国际"),
    ("CSIS",      "https://www.csis.org",             "国际"),
    ("Al Jazeera","https://www.aljazeera.com",         "国际"),
    ("Fox News",   "https://www.foxnews.com",        "国际"),
    ("ABC News",   "https://abcnews.go.com",         "国际"),
    ("CNBC",       "https://www.cnbc.com",           "国际"),
    # 科技垂直门户
    ("中国科技网", "https://www.stdaily.com",       "科技"),
    ("科学网",     "https://www.sciencenet.cn",     "科技"),
    ("人民网科技", "https://scitech.people.com.cn", "科技"),
    ("腾讯科技",   "https://tech.qq.com",           "科技"),
    ("网易科技",   "https://tech.163.com",          "科技"),
    ("中关村在线", "https://www.zol.com.cn",        "科技"),
    ("IT之家",     "https://www.ithome.com",       "科技"),
    ("太平洋电脑", "https://www.pconline.com.cn",  "科技"),
    ("快科技",     "https://www.kknews.cc",        "科技"),
    ("天极网",     "https://www.yesky.com",         "科技"),
    ("36氪",      "https://36kr.com",              "科技"),
    ("钛媒体",     "https://www.tmtpost.com",      "科技"),
    ("虎嗅",       "https://www.huxiu.com",        "科技"),
    ("爱范儿",     "https://www.ifanr.com",        "科技"),
    ("雷锋网",     "https://www.leiphone.com",     "科技"),
    ("OFweek",    "https://www.ofweek.com",        "科技"),
    ("TechCrunch","https://techcrunch.com",        "科技"),
    ("The Verge", "https://www.theverge.com",      "科技"),
    ("CNET",      "https://www.cnet.com",          "科技"),
    ("WIRED",     "https://www.wired.com",         "科技"),
    ("Engadget",  "https://www.engadget.com",      "科技"),
    ("MIT Tech Review", "https://www.technologyreview.com", "科技"),
    ("量子位",     "https://www.qbitai.com",           "科技"),
    ("机器之心",   "https://www.jiqizhixin.com",       "科技"),
    ("芯智讯",     "https://www.zhidx.com",            "科技"),
    ("中国储能网", "https://www.escn.com.cn",          "科技"),
    # ===== 补充：主要门户网站 =====
    # 综合门户
    ("人民网",       "http://www.people.com.cn",        "综合门户"),
    ("新华网",       "http://www.xinhuanet.com",        "综合门户"),
    ("央视网",       "https://www.cctv.com",            "综合门户"),
    ("光明网",       "https://www.gmw.cn",             "综合门户"),
    ("中国网",       "http://www.china.com.cn",         "综合门户"),
    ("中国日报网",   "https://www.chinadaily.com.cn",   "综合门户"),
    ("中青在线",     "https://cyol.com",                "综合门户"),
    ("央广网",       "https://www.cnr.cn",              "综合门户"),
    ("凤凰网",       "https://www.ifeng.com",           "综合门户"),
    # 财经门户补充
    ("同花顺",       "http://www.10jqka.com.cn",        "财经门户"),
    ("证券之星",     "http://www.stockstar.com",        "财经门户"),
    ("中国金融新闻网","https://www.financialnews.com.cn","财经门户"),
    ("FT中文网",     "https://www.ftchinese.com",       "财经门户"),
    ("英为财情",     "https://cn.investing.com",        "财经门户"),
    # 国际补充
    ("路透中文",     "https://cn.reuters.com",         "国际"),
    ("联合早报",     "https://www.zaobao.com.sg",       "国际"),
    ("德国之声",     "https://www.dw.com/zh",           "国际"),
    ("BBC中文",      "https://www.bbc.com/zhongwen/simp","国际"),
    ("纽约时报中文", "https://cn.nytimes.com",          "国际"),
    ("朝鲜日报中文", "https://chinese.chosun.com",      "国际"),
    ("中央社",       "https://www.cna.com.tw",          "国际"),
    # 科技补充
    ("TechWeb",     "http://www.techweb.com.cn",       "科技"),
    ("cnbeta",      "https://www.cnbeta.com",          "科技"),
    ("品玩",         "https://www.pingwest.com",        "科技"),
    ("智东西",       "https://zhidx.com",              "科技"),
    ("EET China",   "https://www.eet-china.com",      "科技"),
    ("DeepTech",    "https://www.mittrchina.com",     "科技"),
    # ===== 补充：权威/官方信源 =====
    # 政务与官媒
    ("中国政府网",   "http://www.gov.cn",              "综合门户"),
    ("求是网",       "http://www.qstheory.cn",         "综合门户"),
    ("法治网",       "http://www.legaldaily.com.cn",   "综合门户"),
    ("人民政协网",   "http://www.rmzxb.com.cn",        "综合门户"),
    ("国际在线",     "https://www.cri.cn",             "综合门户"),
    ("澎湃新闻",     "https://www.thepaper.cn",        "综合门户"),
    ("中国新闻网",   "https://www.chinanews.com.cn",   "综合门户"),
    # 财经监管与专业报
    ("中国经营报",   "http://www.cb.com.cn",           "财经门户"),
    ("经济观察网",   "http://www.eeo.com.cn",          "财经门户"),
    ("商务部",       "http://www.mofcom.gov.cn",       "财经门户"),
    ("人民银行",     "http://www.pbc.gov.cn",          "财经门户"),
    ("国家统计局",   "http://www.stats.gov.cn",        "财经门户"),
    ("证监会",       "http://www.csrc.gov.cn",         "财经门户"),
    # 科技主管部门与科研机构
    ("中国科学院",   "https://www.cas.cn",             "科技"),
    ("科技部",       "https://www.most.gov.cn",        "科技"),
    ("工信部",       "https://www.miit.gov.cn",        "科技"),
    ("中国工程院",   "https://www.cae.cn",             "科技"),
    # 知产主管部门
    ("国家版权局",   "https://www.ncac.gov.cn",        "知产"),
    # 专利诉讼专项信源（国内）
    ("中国法院网",   "https://www.chinacourt.org",      "知产"),
    ("裁判文书网",   "https://wenshu.court.gov.cn",     "知产"),
    ("北京知产法院", "https://www.bjzhichanfy.gov.cn",  "知产"),
    ("上海知产法院", "https://www.shzcfy.gov.cn",       "知产"),
    ("广州知产法院", "https://www.gzlfy.gov.cn",        "知产"),
    ("深圳知识产权法庭","https://www.szcourt.gov.cn",   "知产"),
    ("无讼",         "https://www.itslaw.com",          "知产"),
    ("北大法宝",     "https://www.pkulaw.com",          "知产"),
    # 专利诉讼专项信源（国外）
    ("PatentlyO",   "https://patentlyo.com",            "知产"),
    ("Managing IP",  "https://www.managingip.com",      "知产"),
    ("The IP Kat",   "https://ipkitten.blogspot.com",   "知产"),
    ("Juve Patent",  "https://www.juve-patent.com",    "知产"),
    # 专利诉讼/海外IP 专门栏目
    ("知产力-诉讼",   "https://www.zhichanli.com/category/lawsuit", "知产"),
    ("IPRdaily-诉讼", "https://www.iprdaily.com/category/lawsuit", "知产"),
    ("知产宝-案例",   "https://www.iprdb.com/CourtCase",          "知产"),
    ("中国法院网-知产","https://www.chinacourt.org/index.shtml",  "知产"),
    ("FOSS Patents", "https://fosspatents.blogspot.com",         "知产"),
    ("Reuters Legal-IP","https://www.reuters.com/legal/legalindustry/", "知产"),
    # 国际组织
    ("联合国新闻",   "https://news.un.org/zh/",        "国际"),
    # GitHub 社区/开源资讯（国内可达）
    ("HelloGitHub",   "https://hellogithub.com",       "gh"),
    ("CSDN",        "https://www.csdn.net",           "gh"),
    ("InfoQ",       "https://www.infoq.cn",          "gh"),
    ("开源中国",    "https://www.oschina.net",       "gh"),
    ("小众软件",    "https://www.appinn.com",       "gh"),
]


# ============== Mock 数据 ==============

# 科技子分类关键词匹配
TECH_KEYWORDS = {
    "信息技术":  ["软件", "操作系统", "数据库", "云计算", "大数据", "5G", "6G", "通信", "网络安全", "开源",
                  "SaaS", "PaaS", "IaaS", "微服务", "容器", "K8s", "Docker", "分布式", "中间件",
                  "物联网", "IoT", "边缘计算", "云原生", "Serverless", "DevOps", "CI/CD",
                  "信创", "国产软件", "国产替代", "ERP", "CRM", "API网关",
                  "Linux", "安卓", "鸿蒙", "HarmonyOS",
                  "VPN", "防火墙", "区块链", "算法", "Apache",
                  "MySQL", "PostgreSQL", "MongoDB", "Redis",
                  "数据仓库", "数据中台", "ETL", "数据治理",
                  "入侵检测", "DDoS", "零信任", "运维", "监控"],
    "硬件":     ["硬件", "PC", "笔记本", "服务器", "GPU", "CPU", "处理器", "主板", "显示器",
                  "显卡", "独立显卡", "内存", "固态硬盘", "SSD", "NVMe", "硬盘", "机箱", "电源",
                  "键盘", "鼠标", "打印机", "3D打印机", "扫描仪", "投影仪", "智能投影",
                  "路由器", "交换机", "网卡", "声卡", "采集卡",
                  "传感器", "MEMS", "激光雷达", "毫米波雷达", "摄像头模组",
                  "快充", "充电桩", "AI服务器", "工控机", "单片机", "开发板", "树莓派",
                  "台式机", "一体机", "工作站", "外设", "DIY",
                  "4K显示器", "便携屏", "边缘计算盒子", "SD卡", "扩展坞"],
    "互联网":   ["互联网", "平台", "社交", "电商", "游戏", "短视频", "直播", "外卖", "出行",
                  "微信", "抖音", "快手", "B站", "小红书", "微博", "知乎", "豆瓣",
                  "淘宝", "京东", "拼多多", "美团", "饿了么", "滴滴",
                  "在线教育", "网课", "知识付费", "长视频", "网剧",
                  "直播带货", "MCN", "私域流量", "元宇宙", "Web3",
                  "网约车", "内容付费", "网红经济", "社区团购",
                  "公众号", "小程序", "视频号", "共享经济", "共享单车",
                  "携程", "在线旅游", "OTA", "贴吧", "虎扑", "论坛", "社区",
                  "虚拟人", "数字藏品", "NFT"],
    "人工智能": ["AI", "人工智能", "大模型", "GPT", "ChatGPT", "LLM", "机器学习", "深度学习", "智能体", "Agent",
                  "AIGC", "生成式AI", "多模态", "文生图", "文生视频", "Sora",
                  "Claude", "Gemini", "豆包", "文心一言", "通义千问", "盘古", "讯飞星火",
                  "LLaMA", "Mistral", "Qwen", "DeepSeek", "MoE", "混合专家",
                  "Transformer", "扩散模型", "强化学习", "RLHF", "SFT", "微调",
                  "计算机视觉", "NLP", "自然语言处理", "语音识别",
                  "PyTorch", "TensorFlow", "自动驾驶", "具身智能", "机器人",
                  "RAG", "检索增强", "prompt", "提示词", "Embedding",
                  "向量数据库", "LangChain", "AI助手", "智能客服"],
    "半导体":   ["半导体", "芯片", "晶圆", "代工", "光刻", "存储", "芯片制造", "封测", "EDA",
                  "台积电", "TSMC", "中芯国际", "SMIC", "华虹", "英特尔", "三星",
                  "ASML", "光刻胶", "HBM", "DRAM", "NAND", "Chiplet", "先进封装",
                  "RISC-V", "IGBT", "碳化硅", "SiC", "氮化镓", "GaN", "功率半导体",
                  "Fabless", "芯片法案", "出口管制", "中微公司", "北方华创",
                  "长鑫存储", "长江存储", "先进制程", "成熟制程", "7nm", "5nm", "3nm",
                  "EUV", "DUV", "第三代半导体", "化合物半导体", "射频芯片", "模拟芯片",
                  "存储芯片", "功率器件", "MEMS传感器", "光电子"],
    "前沿科学": ["量子", "航天", "核聚变", "生物科技", "脑机接口", "新材料", "基因", "深空",
                  "量子计算", "量子通信", "量子卫星", "量子纠缠", "量子比特",
                  "北斗", "空间站", "神舟", "嫦娥", "天问",
                  "火星探测", "月球采样", "可控核聚变", "人造太阳",
                  "CRISPR", "基因编辑", "mRNA", "干细胞", "基因治疗",
                  "超导", "石墨烯", "碳纳米管", "纳米材料", "钙钛矿",
                  "深空探测", "暗物质", "暗能量", "黑洞", "引力波",
                  "脑机", "脑科学", "神经科学", "合成生物学", "类器官",
                  "系外行星", "詹姆斯韦伯", "FAST", "中国天眼", "AGI", "中子星", "引力波探测", "离子阱", "拓扑量子", "超导体"],
    "储能":     ["储能", "电池", "锂电池", "钠电池", "固态电池", "电解液", "光伏储能", "储能电站", "BMS",
                  "宁德时代", "比亚迪", "磷酸铁锂", "三元锂",
                  "隔膜", "正极材料", "负极材料", "碳酸锂",
                  "氢能", "燃料电池", "钒电池", "液流电池", "钠硫电池",
                  "储能系统", "抽水蓄能", "户用储能", "工商业储能",
                  "电池回收", "梯次利用", "充电桩", "换电",
                  "氢能汽车", "钙钛矿电池", "储能柜", "储能电池",
                  "半固态电池", "液冷", "储能温控", "PCS", "逆变器",
                  "储能变流器", "虚拟电厂", "微电网", "智能电网",
                  "特高压", "电网调峰", "长时储能", "构网型储能",
                  "共享储能", "储能安全", "钠硫电池", "储能电站并网", "储能变流器", "电池管理系统"],
    "消费电子": ["手机", "折叠屏", "平板", "耳机", "手表", "智能穿戴", "VR", "AR", "MR", "TWS", "笔记本",
                  "iPhone", "华为手机", "小米手机", "智能手机",
                  "智能手表", "智能眼镜", "AR眼镜", "降噪耳机", "游戏手机",
                  "智能音箱", "扫地机器人", "扫地机", "洗地机", "智能家居",
                  "无人机", "相机", "微单", "Kindle", "电子墨水屏",
                  "家用机器人", "空气净化器", "电竞手机", "智能戒指", "手环",
                  "智能门锁", "破壁机", "咖啡机", "电动牙刷", "吹风机",
                  "按摩仪", "VR头显", "AI学习机", "翻译机", "录音笔",
                  "游戏掌机", "Switch", "PS5", "智能窗帘", "颈椎仪", "电竞显示器", "剃须刀"],
}

# 财经子分类关键词匹配
FIN_KEYWORDS = {
    "宏观经济": ["GDP", "CPI", "PMI", "美联储", "财政政策", "PPI", "财政", "宏观", "缩表", "加息", "降息", "工业增加值", "社会消费品零售", "固定资产投资", "出口", "进口", "贸易顺差", "外汇储备", "失业率", "就业", "财政赤字", "专项债", "地方债", "减税降费", "通胀", "通缩", "经济数据", "GDP增速", "制造业PMI", "非制造业PMI", "经济复苏", "消费复苏", "GDP总量", "经济增长", "三驾马车", "社会融资规模", "M1", "核心CPI", "GDP平减指数", "财新PMI", "宏观杠杆率", "居民杠杆率", "政府杠杆率", "企业杠杆率", "L型复苏", "V型反弹", "硬着陆", "软着陆", "滞胀", "宏观数据", "经济基本面", "复苏动能", "内需", "外需", "降准", "LPR", "MLF", "逆回购", "人民银行", "央行", "PBOC", "SLF", "再贷款", "再贴现", "公开市场操作", "货币政策", "M2", "社融", "信贷", "存款准备金率", "基准利率", "LPR报价", "流动性", "净投放", "净回笼", "资金面", "OMO", "PSL", "抵押补充贷款", "碳减排支持工具", "央行行长", "货币政策委员会", "贷款市场报价利率", "结构性货币政策工具", "MLF利率", "7天逆回购", "央行票据", "国库现金定存", "中期借贷便利", "贷款基准利率", "存款基准利率", "降息周期", "加息周期", "量化宽松", "QE", "央行资产负债表", "适度宽松", "稳健货币政策", "MLF操作", "MLF投放", "逆回购操作", "7天期逆回购", "14天逆回购", "央行票据互换"],
    "股市资讯": ["A股", "沪深300", "上证指数", "创业板", "北向资金", "港股", "美股", "上证", "深证", "纳斯达克", "股票", "涨停", "跌停", "牛市", "熊市", "中证500", "科创50", "沪指", "深成指", "南向资金", "主力资金", "龙虎榜", "两融", "融资融券", "熔断", "打新", "ST股", "板块", "概念股", "回调", "反弹", "深证成指", "创业板指", "北证50", "北交所", "港股通", "沪股通", "深股通", "A50", "富时A50", "MSCI", "标普500", "道琼斯", "恒生指数", "券商股", "银行股", "白酒股", "新能源股", "医药股", "蓝筹股", "白马股", "题材股", "妖股", "次新股", "破发"],
    "债券基金": ["国债", "10年期国债", "国债收益率", "可转债", "城投债", "债券", "收益率", "利率债", "信用债", "发债", "国债期货", "地方政府债", "违约", "展期", "债市", "债基", "国债逆回购", "地方债", "政策性金融债", "国开债", "短融", "中票", "公司债", "企业债", "ABS", "资产证券化", "十年期国债", "收益率曲线", "信用利差", "城投债违约", "金融债", "信用违约", "央票", "国库券", "永续债", "可交换债", "PPN", "MBS", "ABN", "银行二级资本债", "30年期国债", "DR007", "R007", "SHIBOR", "逆回购", "浮息债", "定向工具", "资产支持证券", "次级债", "TLAC", "国债ETF", "可转债基金", "ETF", "公募", "基金净值", "股票型基金", "基金经理", "基金", "私募", "净值", "定投", "债券型基金", "混合型基金", "货币基金", "QDII", "基金重仓", "宽基ETF", "行业ETF", "REITs", "估值", "基金发行", "基金定投", "基金申购", "基金赎回", "指数基金", "主动基金", "被动基金", "基金重仓股", "公募基金", "私募基金", "货币市场基金", "股票基金", "债券基金", "基金分红", "FOF", "MOM", "养老目标基金", "社保基金", "企业年金", "爆款基金", "日光基", "百亿基金", "顶流基金经理", "QDII基金", "RQFII", "私募基金备案", "养老基金", "职业年金", "FOF基金", "MOM基金", "雪球基金", "基金季报", "基金四季报"],
    "外汇期货": ["原油", "黄金", "股指期货", "螺纹钢", "大宗商品", "期货", "铁矿石", "焦煤", "焦炭", "沪铜", "沪金", "沪银", "沪深300期货", "白银", "贵金属", "豆粕", "玉米", "期货价格", "沪铝", "沪锌", "沪镍", "沪铅", "玻璃", "纯碱", "甲醇", "PTA", "PVC", "棕榈油", "棉花", "白糖", "鸡蛋", "生猪", "工业硅", "碳酸锂", "多晶硅", "尿素", "花生", "橡胶", "沥青", "LPG", "燃料油", "中证500期货", "中证1000期货", "股指期权", "沪锡", "沪锰", "工业硅期货", "多晶硅期货", "苹果", "红枣", "纸浆", "人民币汇率", "美元指数", "离岸人民币", "升值", "贬值", "汇率", "美元", "人民币", "欧元", "日元", "外汇", "英镑", "在岸人民币", "DXY", "汇率中间价", "结售汇", "美元汇率", "欧元汇率", "日元汇率", "英镑汇率", "澳元", "加元", "瑞郎", "港币", "汇率波动", "汇率风险", "外汇占款", "结汇", "售汇", "QFII", "人民币结算", "跨境支付", "CNH", "CNY", "NDF", "外汇掉期", "货币互换", "SDR", "人民币国际化", "CIPS", "人民币跨境支付", "美联储议息", "点阵图", "卢布", "泰铢", "欧元区", "人民币汇率中间价", "外汇远期", "货币掉期", "外汇市场", "人民币指数", "CFETS"],
    "企业研报": ["制造业", "新能源", "数字经济", "供应链", "外贸", "产业", "服务业", "产业链", "光伏", "风电", "汽车", "新能源汽车", "消费", "白酒", "医药", "跨境电商", "高端制造", "专精特新", "工业互联网", "智能制造", "工业母机", "机器人", "人形机器人", "低空经济", "eVTOL", "商业航天", "合成生物", "卫星互联网", "工业4.0", "生物医药", "医疗器械", "新能源产业", "数据要素", "数据资产", "东数西算", "算力", "小巨人", "单项冠军", "自主可控", "卡脖子", "新质生产力", "战略性新兴产业", "绿色低碳", "循环经济", "数字产业化", "产业数字化", "数据交易所", "算力中心", "工业机器人", "服务机器人", "绿色制造", "房地产", "楼市", "房价", "房企", "保交楼", "土地", "物业", "商品房", "二手房", "新房", "土地出让", "土拍", "房贷", "首付比例", "公积金", "烂尾楼", "库存", "城中村改造", "保障房", "商品房销售", "二手房成交", "土地市场", "房贷利率", "限购", "限贷", "限售", "救市", "地产新政", "房企债务", "恒大", "碧桂园", "万科", "预售资金", "网签备案", "70城房价", "一线城市", "二线城市", "北上广深", "开发贷", "按揭贷款", "首套房", "二套房", "房产税", "房地产税", "土地财政", "商业地产", "商品房预售", "二手房挂牌", "一线城市房价", "二线城市房价", "养老地产", "业绩预告", "年报", "并购", "回购", "增持", "公告", "季报", "重组", "减持", "定增", "业绩快报", "分红", "派息", "停牌", "复牌", "股权收购", "资产注入", "借壳", "商誉减值", "资产减值", "退市", "风险警示", "业绩预增", "业绩预减", "股权质押", "股东减持", "高管增持", "员工持股", "股权激励", "重大资产重组", "破产重整", "业绩扭亏", "配股", "分拆上市", "私有化", "*ST", "限售股解禁", "大宗交易", "要约收购", "实际控制人变更", "董事长辞职", "董事会换届", "可转债发行", "股份回购", "业绩首亏", "业绩续亏", "业绩预告修正", "董事会决议", "监事会决议", "股东大会", "股东大会决议", "分红预案"],
}

# 知产子分类关键词匹配
IP_KEYWORDS = {
    "行业快讯":      ["快讯", "今日", "最新", "通报", "公告", "通知", "发布", "印发",
                  "办法", "规定", "条例", "国知局", "国家知识产权局",
                  "最高法", "最高人民法院", "知识产权法庭", "WIPO", "世界知识产权组织",
                  "专利法", "商标法", "著作权法", "反不正当竞争法",
                  "商标法修订", "版权", "集成电路布图设计",
                  "地理标志", "植物新品种", "知识产权强国", "专利转化运用",
                  "国知局公告", "专利法实施细则", "数据知识产权",
                  "专利局", "商标局", "版权局", "惩罚性赔偿",
                  "专利审查", "商标异议", "驰名商标", "行政保护",
                  "知识产权司法保护", "专利转化专项", "专利产业化",
                  "知识产权强国纲要", "海外维权援助", "知识产权局", "专利复审", "专利无效", "商标评审", "版权局", "知识产权司法", "知识产权行政", "专利预审"],
    "专利诉讼":  ["专利侵权", "专利诉讼", "无效宣告", "判赔", "专利战",
                  "诉讼", "侵权", "起诉", "败诉", "胜诉", "索赔",
                  "判决", "裁定", "二审", "一审", "终审", "高院", "中院", "知产法庭",
                  "停止侵权", "赔偿", "举证", "管辖", "临时禁令", "行为保全",
                  "知产法院", "知识产权法庭", "侵权纠纷", "复审", "无效",
                  "证据保全", "应诉", "反诉", "管辖异议", "无效请求", "复审委",
                  "等同原则", "现有技术抗辩", "损害赔偿", "法定赔偿",
                  "诉前禁令", "财产保全", "技术调查官", "司法鉴定",
                  "再审", "诉讼时效", "举证责任", "合法来源抗辩", "等同侵权", "全面覆盖", "禁止反悔", "捐献原则", "现有设计抗辩"],
    "海外IP": ["USPTO", "337调查", "PCT", "UPC", "海外维权",
                  "海外", "美国", "欧盟", "日本", "韩国", "WIPO", "EPO", "国际",
                  "ITC", "PTAB", "上诉法院", "联邦巡回",
                  "专利合作条约", "海牙", "马德里", "CAFC", "统一专利法院",
                  "DPMA", "UKIPO", "JPO", "涉外", "海外布局",
                  "美国专利商标局", "欧洲专利局", "日本特许厅",
                  "PCT申请", "马德里商标",
                  "KIPO", "EUIPO", "CNIPA", "CIPO加拿大",
                  "印度专利局", "以色列专利局", "Rospatent",
                  "海外专利申请", "PCT国际申请", "海牙体系",
                  "专利审查高速路", "PPH", "UPOV", "布达佩斯条约", "澳大利亚IP", "新西兰专利", "巴西专利局", "墨西哥专利局", "土耳其专利局", "瑞士专利局"],
    "专利运营":  ["专利运营", "专利转让", "专利池", "质押融资", "高价值专利",
                  "运营", "转化", "交易", "许可费", "质押", "评估", "定价",
                  "专利收购", "专利联盟",
                  "质押贷款", "专利导航", "开放许可", "作价入股",
                  "专利组合", "IP运营",
                  "专利转让合同", "专利交易", "专利拍卖",
                  "专利运用", "专利评议", "专利预警", "专利分析", "专利情报",
                  "专利密集型产业", "高价值专利培育", "专利运营公司", "专利池许可",
                  "专利保险", "专利价值评估", "专利估值",
                  "知识产权证券化", "知识产权质押",
                  "知识产权运营中心", "专利代理", "专利代理师", "专利质押", "专利保险", "专利价值", "知识产权运营", "知识产权交易", "知识产权服务", "专利代理", "专利代理人", "专利情报分析", "专利导航工程", "高价值专利组合", "专利转化项目"],
    "许可":      ["SEP", "FRAND", "标准必要专利", "专利许可", "交叉许可",
                  "许可", "授权", "标准必要",
                  "独家许可", "普通许可", "许可谈判", "费率", "和解金",
                  "技术许可", "实施许可", "和解",
                  "不侵权", "反垄断", "垄断协议",
                  "SEP许可", "交叉许可协议", "默示许可", "强制许可", "当然许可",
                  "专利许可合同", "许可费率", "专利和解", "反垄断调查",
                  "FRAND费率", "专利许可谈判", "标准组织", "专利联盟许可",
                  "标准制定组织", "SSO", "专利劫持", "hold-up",
                  "打包许可", "组件许可", "累积royalty", "禁令滥用", "标准必要", "FRAND承诺", "许可金", "许可模式", "许可组合", "许可争议", "专利池管理", "专利许可运营", "标准制定", "SSO标准", "许可费率裁决", "反垄断许可"],
    "企业IP": ["管理", "战略", "布局", "企业", "IPR", "研发", "护城河",
                  "知识产权管理", "专利布局", "专利战略", "知识产权战略",
                  "知识产权管理体系", "贯标", "知识产权贯标",
                  "IPR部门", "首席知识产权官", "CIPO", "研发投入",
                  "专利申请", "专利申请量", "发明专利", "实用新型", "外观设计",
                  "商标注册", "品牌保护", "商业秘密", "竞业限制",
                  "FTO", "自由实施分析", "专利风险", "侵权风险",
                  "知识产权保护", "知识产权培训",
                  "知识产权考核", "知识产权预算", "专利工程师",
                  "知识产权律师", "知识产权法务", "保密协议", "NDA",
                  "职务发明", "中国专利奖", "创新管理", "技术秘密", "知识产权战略", "专利策略", "研发创新", "技术创新", "知识产权团队", "知识产权专员", "专利工程师", "知识产权法务"],
}
# 国际子分类关键词匹配
INTL_KEYWORDS = {
    "大国博弈": ["中美", "中俄", "美俄", "G7", "金砖", "大国", "霸权", "崛起", "修昔底德", "G2", "中美关系", "中美贸易", "中美元首", "习拜会", "中俄合作", "中美博弈", "大国竞争", "脱钩", "去风险", "小院高墙", "修昔底德陷阱", "中美高层", "中美元首会晤", "中俄天然气", "美欧关系", "美日关系", "中美经贸", "大国关系", "国际秩序", "多极化", "单极化", "中美战略竞争", "中俄关系", "中欧关系", "中日关系", "中印关系", "上合组织", "SCO", "白宫", "国务院", "五角大楼", "外交部发言人", "国防部", "国家安全顾问", "地缘政治", "地缘经济", "美元霸权", "石油美元", "去美元化", "一带一路", "人类命运共同体", "制裁", "SWIFT", "出口管制", "实体清单", "长臂管辖", "禁运", "冻结", "关税", "贸易战", "二级制裁", "不可靠实体清单", "冻结资产", "外汇储备", "技术封锁", "贸易壁垒", "制裁名单", "反制裁", "反制", "出口管制清单", "金融制裁", "能源制裁", "个人制裁", "次级制裁", "制裁俄罗斯", "制裁伊朗", "贸易限制", "投资限制", "芯片出口管制", "技术出口", "制裁中国", "制裁朝鲜", "制裁叙利亚", "经济制裁", "G7制裁", "对俄制裁", "对华关税", "对等关税", "301关税", "232关税", "钢铝关税", "UFLPA", "涉疆法案", "OFAC", "SDN清单", "芯片与科学法案", "IRA", "欧盟制裁", "英国制裁", "日本制裁", "韩国制裁", "个人资产冻结", "关税壁垒"],
    "地缘冲突": ["俄乌", "加沙", "停火", "空袭", "导弹袭击", 
             "战争", "冲突", "开战", "前线", "炮击", "哈马斯", "以色列", 
             "军事行动", "参战", "阵亡", "伤亡", "无人机", "战机", "坦克", "装甲", "战线", "攻势", "反攻", "占领", "黎巴嫩", "也门", "胡塞", "苏丹", "海地", "缅甸", "克里米亚", 
             "顿巴斯", "赫尔松", "扎波罗热", "库尔斯克", "约旦河西岸", "真主党", "红海", "曼德海峡", "停火协议", "和平谈判", "撤军", "增兵", "巴以冲突", 
             "以哈冲突", "俄乌冲突", "中东", "核打击", "停火谈判", "瓦格纳", "车臣", "格鲁乌", "军事基地", "军演", "核武器", "核潜艇", "反导", "部署", 
             "导弹", "军舰", "驻军", "萨德", "宙斯盾", "航母战斗群", "航母编队", "海外基地", "军事存在", "中程导弹", "洲际导弹", "ICBM", "战略轰炸机", 
             "美韩军演", "美日军演", "核威慑", "核力量", "导弹防御", "中导条约", "新削减战略武器条约", "美国驻军", "三位一体核", "NMD", "TMD", "START条约", 
             "北约东扩", "北约军演", "北约峰会", "驻日美军", "驻韩美军", "驻德美军", "冲绳基地", "横须贺", "嘉手纳", "QUAD", "AUKUS", "奥库斯", "太平洋威慑", 
             "EDCA", "菲律宾美军", "北约盟国", "欧洲驻军", "驻欧美军", "澳大利亚驻军", "四国机制"],
    "资源": ["OPEC", "天然气", "石油", "稀土", "粮食", "原油", "能源", "粮食", "小麦", "大豆", "管道", "航线", "LNG", "液化天然气", 
           "北溪", "OPEC+", "能源危机", "关键矿产", "锂", "钴", "镍", "粮价", "油市", "页岩油", "油价", "俄气", "俄油", "稀土出口", "黑海粮食协议", 
           "能源价格", "能源转型", "粮食安全", "能源安全", "能源独立", "沙特阿美", "Gazprom", "化肥", "能源武器", "石油武器", "苏伊士运河", "霍尔木兹海峡", 
           "马六甲海峡", "铀", "核电", "核能", "委内瑞拉石油", "石油输出国组织", "欧佩克", "沙特", "俄罗斯石油", "伊朗石油", "能源出口"],
    "海洋地缘": ["南海", "台海", "台湾海峡", "第一岛链", "航母", "东海", "黄海", "海峡", "岛屿", "海军", "舰队", "航行自由", "南海仲裁", "南海岛礁", "九段线", "台海局势", "台湾", "第二岛链", "钓鱼岛", "黄岩岛", "自由航行", "南海巡航", "台湾问题", "中美海军", "抵近侦察", "航行自由行动", "关岛", "南海岛礁建设", "台海军事", "中美军舰", "迪戈加西亚", "第一岛链封锁", "第三岛链", "仁爱礁", "仙宾礁", "台海中线", "环台军演", "围台军演", "联合利剑", "永暑礁", "美济礁", "西沙", "南沙", "东沙", "金门", "马祖", "南海岛礁", "台湾海峡巡航", "台海周边", "中沙", "东沙岛", "太平岛"],
}

INDUSTRY_SECTIONS = {k: [] for k in IP_KEYWORDS}
INTERNATIONAL_SECTIONS = {k: [] for k in INTL_KEYWORDS}
INTERNATIONAL_SECTIONS["外媒报道"] = []

# 历史数据归组映射（避免在多处 _regroup 调用里重复写）
FIN_RENAME = {
    "央行政策": "宏观经济",
    "产业": "企业研报", "地产": "企业研报", "公司公告": "企业研报",
    "债券": "债券基金", "基金": "债券基金",
    "期货": "外汇期货", "外汇": "外汇期货",
}
FIN_DROP = ("其他",)
INTL_RENAME = {
    "能源/粮食地缘": "资源",
    "区域战争": "地缘冲突", "军事部署": "地缘冲突",
    "制裁": "大国博弈",
}
INTL_DROP = ("全球治理",)
IP_DROP = ("其他", "行业访谈")
TECH_DROP = ("其他",)

# Git 热榜 - Skill 热榜关键词（从 Trending 仓库里按 name/desc 过滤）
SKILL_KEYWORDS = [
    "agent", "Agent", "AI Agent", "LLM Agent", "autonomous", "multi-agent",
    "Claude Skill", "Claude Skills", "GPTs", "GPT Store", "GPT Builder",
    "MCP", "Model Context Protocol", "mcp server", "mcp client",
    "tool use", "function calling", "tool calling",
    "prompt", "prompt engineering", "prompt library", "prompt hub",
    "few-shot", "chain-of-thought", "CoT",
    "RAG", "retrieval augmented", "vector database", "vector db",
    "LangChain", "LlamaIndex", "LangGraph", "AutoGPT", "CrewAI",
    "AutoGen", "Semantic Kernel",
    "Dify", "Coze", "n8n", "Flowise", "Zapier",
    "Copilot", "Cursor", "Claude Code", "Devin", "GitHub Copilot",
    "Chatbot", "chatbot", "AI assistant",
    "AI workflow", "AI automation", "workflow automation",
    "agent framework", "agent sdk", "agent toolkit",
    "OpenAI API", "Anthropic API", "Gemini API",
    "code interpreter", "AI coding", "AI code assistant",
]

# 补搜时对特定子分类追加的精准 query（每条单独发一次搜索）
SPECIAL_QUERIES = {
    "行业快讯": [
        '"国家知识产权局" 公告',
        '"专利法" 修订',
        '"知识产权" 政策 发布',
    ],
    "专利诉讼": [
        '"专利侵权" 判决',
        '"专利侵权" 起诉',
        '"专利无效" 宣告',
        '"知识产权法院" 一审',
        '"专利" 赔偿 判决',
        '"专利纠纷" 终审',
        '"标准必要专利" 诉讼',
        '"patent infringement" ruling',
        '"Section 337" ITC',
    ],
    "海外IP": [
        '"337调查" 立案',
        '"USPTO" 专利',
        '"ITC" 专利调查',
        '"UPC" 统一专利法院',
        '"PCT" 国际专利申请',
        '"USPTO" patent',
        '"ITC" Section 337',
        '"UPC" patent court ruling',
        '"EPO" opposition patent',
        '"WIPO" 专利申请',
        '"海外维权" 企业',
        '"专利" 美国 起诉',
    ],
    "专利运营": [
        '"专利转让" 交易',
        '"专利质押" 融资',
        '"高价值专利" 培育',
        '"专利池" 许可',
        '"专利运营" 平台',
        '"知识产权证券化"',
        '"专利导航"',
        '"开放许可" 专利',
        '"专利转化" 运用',
        '"知识产权运营中心"',
    ],
    "许可": [
        '"标准必要专利" 许可',
        '"FRAND" 费率',
        '"SEP" 许可谈判',
        '"专利交叉许可"',
        '"反垄断" 专利',
        '"专利许可" 合同',
        '"标准必要专利" 费率',
        '"专利和解" 协议',
        '"FRAND" 判决',
    ],
    "企业IP": [
        '"专利布局" 企业',
        '"知识产权战略"',
        '"FTO" 自由实施',
        '"商业秘密" 保护',
        '"知识产权管理" 体系',
        '"知识产权贯标"',
        '"专利申请" 企业',
        '"知识产权" 风险',
        '"品牌保护" 商标',
        '"研发" 专利',
    ],
    # 国际时讯
    "地缘冲突": [
        '"俄乌冲突" 最新',
        '"巴以冲突" 停火',
        '"红海" 胡塞 袭击',
        '"北约" 军演',
        '"美军" 基地',
        '"Russia Ukraine" war',
        '"Israel Gaza" ceasefire',
        '"Houthi" Red Sea',
        "俄乌", "加沙", "停火", "空袭", "导弹袭击", 
        "战争", "冲突", "开战", "前线", "炮击", "哈马斯", "以色列", 
        "军事行动", "参战", "阵亡", "伤亡", "无人机", "战机", "坦克", "装甲", "战线", "攻势", "反攻", "占领", "黎巴嫩", "也门", "胡塞", "苏丹", "海地", "缅甸", "克里米亚", 
        "顿巴斯", "赫尔松", "扎波罗热", "库尔斯克", "约旦河西岸", "真主党", "红海", "曼德海峡", "停火协议", "和平谈判", "撤军", "增兵", "巴以冲突", 
        "以哈冲突", "俄乌冲突", "中东", "核打击", "停火谈判", "瓦格纳", "车臣", "格鲁乌", "军事基地", "军演", "核武器", "核潜艇", "反导", "部署", 
        "导弹", "军舰", "驻军", "萨德", "宙斯盾", "航母战斗群", "航母编队", "海外基地", "军事存在", "中程导弹", "洲际导弹", "ICBM", "战略轰炸机", 
        "美韩军演", "美日军演", "核威慑", "核力量", "导弹防御", "中导条约", "新削减战略武器条约", "美国驻军", "三位一体核", "NMD", "TMD", "START条约", 
        "北约东扩", "北约军演", "北约峰会", "驻日美军", "驻韩美军", "驻德美军", "冲绳基地", "横须贺", "嘉手纳", "QUAD", "AUKUS", "奥库斯", "太平洋威慑", 
        "EDCA", "菲律宾美军", "北约盟国", "欧洲驻军", "驻欧美军", "澳大利亚驻军", "四国机制",
    ],
    "资源": [
        '"OPEC" 减产',
        '"天然气" 价格',
        '"稀土" 出口',
        '"石油" 油价',
        '"粮食" 危机',
        '"OPEC" production cut',
        '"rare earth" export',
        '"natural gas" price',
        "OPEC", "天然气", "石油", "稀土", "粮食", "原油", "能源", "粮食", "小麦", "大豆", "管道", "航线", "LNG", "液化天然气", 
        "北溪", "OPEC+", "能源危机", "关键矿产", "锂", "钴", "镍", "粮价", "油市", "页岩油", "油价", "俄气", "俄油", "稀土出口", "黑海粮食协议", 
        "能源价格", "能源转型", "粮食安全", "能源安全", "能源独立", "沙特阿美", "Gazprom", "化肥", "能源武器", "石油武器", "苏伊士运河", "霍尔木兹海峡", 
        "马六甲海峡", "铀", "核电", "核能", "委内瑞拉石油", "石油输出国组织", "欧佩克", "沙特", "俄罗斯石油", "伊朗石油", "能源出口"
    ],
    # 科技资讯
    "信息技术": [
        '"云计算" 平台',
        '"开源" 软件',
        '"数据中台" 建设',
        '"网络安全" 漏洞',
        '"AI cloud" platform',
    ],
    "硬件": [
        '"GPU" 服务器',
        '"AI芯片" 发布',
        '"消费电子" 新品',
        '"半导体设备"',
        '"AI server" launch',
    ],
    "互联网": [
        '"短视频" 平台',
        '"电商" 直播',
        '"大模型" 应用',
        '"AI应用" 落地',
        '"AI app" launch',
    ],
    "人工智能": [
        '"大模型" 发布',
        '"GPT" 新版本',
        '"AI Agent" 智能体',
        '"多模态" 模型',
        '"LLM" release',
        "AI", "人工智能", "大模型", "GPT", "ChatGPT", "LLM", "机器学习", "深度学习", "智能体", "Agent",
        "AIGC", "生成式AI", "多模态", "文生图", "文生视频", "Sora",
        "Claude", "Gemini", "豆包", "文心一言", "通义千问", "盘古", "讯飞星火",
        "LLaMA", "Mistral", "Qwen", "DeepSeek", "MoE", "混合专家",
        "Transformer", "扩散模型", "强化学习", "RLHF", "SFT", "微调",
        "计算机视觉", "NLP", "自然语言处理", "语音识别",
        "PyTorch", "TensorFlow", "自动驾驶", "具身智能", "机器人",
        "RAG", "检索增强", "prompt", "提示词", "Embedding",
        "向量数据库", "LangChain", "AI助手", "智能客服",
    ],
    "半导体": [
        '"台积电" 制程',
        '"中芯国际" 代工',
        '"EUV" 光刻',
        '"芯片" 出口管制',
        '"TSMC" process',
    ],
    "前沿科学": [
        '"量子计算" 突破',
        '"可控核聚变" 实验',
        '"脑机接口" 临床',
        '"基因编辑" 疗法',
        '"quantum computing" breakthrough',
        "量子", "航天", "核聚变", "生物科技", "脑机接口", "新材料", "基因", "深空",
        "量子计算", "量子通信", "量子卫星", "量子纠缠", "量子比特",
        "北斗", "空间站", "神舟", "嫦娥", "天问",
        "火星探测", "月球采样", "可控核聚变", "人造太阳",
        "CRISPR", "基因编辑", "mRNA", "干细胞", "基因治疗",
        "超导", "石墨烯", "碳纳米管", "纳米材料", "钙钛矿",
        "深空探测", "暗物质", "暗能量", "黑洞", "引力波",
        "脑机", "脑科学", "神经科学", "合成生物学", "类器官",
        "系外行星", "詹姆斯韦伯", "FAST", "中国天眼", "AGI", "中子星", "引力波探测", "离子阱", "拓扑量子", "超导体",
    ],
    "储能": [
        '"宁德时代" 电池',
        '"固态电池" 量产',
        '"虚拟电厂" 上线',
        '"光伏" 装机',
        '"solid state battery"',
        "储能", "电池", "锂电池", "钠电池", "固态电池", "电解液", "光伏储能", "储能电站", "BMS",
        "宁德时代", "比亚迪", "磷酸铁锂", "三元锂",
        "隔膜", "正极材料", "负极材料", "碳酸锂",
        "氢能", "燃料电池", "钒电池", "液流电池", "钠硫电池",
        "储能系统", "抽水蓄能", "户用储能", "工商业储能",
        "电池回收", "梯次利用", "充电桩", "换电",
        "氢能汽车", "钙钛矿电池", "储能柜", "储能电池",
        "半固态电池", "液冷", "储能温控", "PCS", "逆变器",
        "储能变流器", "虚拟电厂", "微电网", "智能电网",
        "特高压", "电网调峰", "长时储能", "构网型储能",
        "共享储能", "储能安全", "钠硫电池", "储能电站并网", "储能变流器", "电池管理系统",
    ],
    "消费电子": [
        '"iPhone" 发布',
        '"折叠屏" 手机',
        '"AI眼镜" 新品',
        '"智能穿戴"',
        '"smart glasses" launch',
    ],
}


# ============== 可点击 QLabel ==============
class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self.clicked.emit()
        super().mousePressEvent(e)
    def enterEvent(self, e):
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet("color:#60a5fa; background:transparent; text-decoration:underline;")
        super().enterEvent(e)
    def leaveEvent(self, e):
        self.setStyleSheet("color:#e5e7eb; background:transparent;")
        super().leaveEvent(e)


# ============== 门户抓取 ==============
class FeedFetcher(QObject):
    portals_done = pyqtSignal(dict)
    github_done = pyqtSignal(dict)
    hot_done = pyqtSignal(list)
    details_done = pyqtSignal()
    search_done = pyqtSignal(str, list)  # save_key, items
    progress = pyqtSignal(int, int, str)  # done, total, current_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.nam = QNetworkAccessManager(self)
        self.nam.finished.connect(self._on_reply)
        self._pending = {}
        self._portal_results = {}
        self._pending_portals = set()
        self._pending_details = set()
        self._pending_search = {}  # reply -> (save_key, subcat, engine)
        self._baidu_fail_streak = 0  # 百度连续失败次数，>=3 就暂时跳过

    def fetch_all(self, target_cat=None):
        """target_cat: None=全部, 或指定分类标签（知产/财经门户/综合门户/国际/科技/gh）"""
        # 取消所有未完成请求
        for r in list(self._pending.keys()):
            r.abort()
            r.deleteLater()
        self._pending.clear()
        self._portal_results = {}
        self._pending_portals = set()
        self._url_index = {}
        self._detail_queue = []
        self._pending_details = set()
        self._gh_results = {}
        self._pending_gh = set()
        cats_to_fetch = [target_cat] if target_cat else None
        # 科技页要同时抓综合门户+科技
        if target_cat == "科技":
            cats_to_fetch = ["综合门户", "科技"]
        portals = [(n, u, c) for n, u, c in PORTALS
                   if not cats_to_fetch or c in cats_to_fetch]
        self._total = len(portals)
        self._done = 0
        for name, url, cat in portals:
            req = QNetworkRequest(QUrl(url))
            req.setHeader(QNetworkRequest.UserAgentHeader, "Mozilla/5.0 NewsAggregator/1.0")
            req.setTransferTimeout(6000)
            self._pending[self.nam.get(req)] = ("portal", name, cat)
            self._pending_portals.add(name)
        # GitHub Trending
        if target_cat in (None, "gh"):
            for since, label in [("daily", "日榜"), ("weekly", "周榜"), ("monthly", "月榜")]:
                url = f"https://github.com/trending?since={since}"
                req = QNetworkRequest(QUrl(url))
                req.setHeader(QNetworkRequest.UserAgentHeader, "Mozilla/5.0 NewsAggregator/1.0")
                req.setTransferTimeout(15000)
                self._pending[self.nam.get(req)] = ("gh", label)
                self._pending_gh.add(label)
                self._total += 1
        # 热搜：百度热搜（微博 API 匿名已失效）
        if target_cat in (None, "hot"):
            req = QNetworkRequest(QUrl("https://top.baidu.com/api/board?platform=wise&tab=realtime"))
            req.setHeader(QNetworkRequest.UserAgentHeader, "Mozilla/5.0 NewsAggregator/1.0")
            req.setRawHeader(b"Accept-Language", b"zh-CN")
            req.setTransferTimeout(6000)
            self._pending[self.nam.get(req)] = ("hot", "baidu")
            self._total += 1

    def _on_reply(self, reply):
        tag = self._pending.pop(reply, None)
        if tag is None:
            reply.deleteLater(); return
        err = reply.error()
        body = bytes(reply.readAll()) if err == QNetworkReply.NoError else b""
        reply.deleteLater()
        if tag[0] == "portal":
            _, name, cat = tag
            self._handle_portal(name, cat, err, body)
        elif tag[0] == "detail":
            self._handle_detail(tag[1], err, body)
        elif tag[0] == "gh":
            self._handle_gh(tag[1], err, body)
        elif tag[0] == "hot":
            self._handle_hot(err, body)
        elif tag[0] == "search":
            self._pending_search.pop(reply, None)
            self._handle_search(tag[1], tag[2], tag[3], err, body)

    def _handle_portal(self, name, cat, err, body):
        self._pending_portals.discard(name)
        self._done += 1
        self.progress.emit(self._done, self._total, name)
        if err == QNetworkReply.NoError and body:
            try:
                html = None
                for enc in ("utf-8", "gbk", "gb2312"):
                    try: html = body.decode(enc); break
                    except UnicodeDecodeError: continue
                if html is None: html = body.decode("utf-8", errors="ignore")
                # 抓所有 <a href="...">...</a>，再从内部提取纯文本
                link_re = re.compile(
                    r'(.{0,500})<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>(.{0,500})', re.S)
                # 时间模式：ISO / 中文日期 / 相对时间 / <time datetime>
                time_re = re.compile(
                    r'<time[^>]+datetime="([^"]+)"'
                    r'|(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}[^"<]*)'
                    r'|(\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:\s+\d{1,2}:\d{2})?)'
                    r'|(\d{1,2}-\d{1,2}(?:\s+\d{1,2}:\d{2})?)'
                    r'|(\d+\s*(?:分钟|小时|天)前)'
                    r'|(今天\s*\d{0,2}:\d{0,2})'
                    r'|(昨天(?:\s*\d{0,2}:\d{0,2})?)'
                    r'|(\d{1,2}:\d{2})')
                ad_kw = ["javascript:", "#", "login", "register", "about", "contact",
                         ".jpg", ".png", ".css", ".js", ".ico", ".svg", ".gif",
                         "/ad/", "/ads/", "/advert", "/promo", "/sponsor",
                         "taobao.com", "jd.com", "pinduoduo", "tmall",
                         "vip.jrj", "24h.jrj", "jrjagent", "dataCenter",
                         "s.weibo", "passport.", "logout", "feedback"]
                ad_text = {"首页", "更多", "登录", "注册", "下载", "APP", "客户端",
                           "关于我们", "联系方式", "广告", "投稿", "举报", "版权",
                           "VIP", "VIP会员", "登录/注册", "免费注册", "立即下载"}
                seen = set(); items = []
                for m in link_re.finditer(html):
                    before, url, raw_inner, after = m.group(1), m.group(2), m.group(3), m.group(4)
                    txt = re.sub(r'<[^>]+>', '', raw_inner).strip()
                    txt = re.sub(r'\s+', ' ', txt)
                    if len(txt) < 6 or len(txt) > 100 or url in seen: continue
                    if txt in ad_text: continue
                    if any(x in url for x in ad_kw): continue
                    seen.add(url)
                    # 同时在前后文里找时间
                    tm = time_re.search(before + after)
                    pub = ""
                    if tm:
                        pub = next(g for g in tm.groups() if g)
                    items.append({"title": txt, "url": url, "source": name,
                                  "summary": "", "content": txt,
                                  "pub_date": pub,
                                  "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M")})
                    if len(items) >= 8: break
                self._portal_results.setdefault(cat, []).extend(items)
            except Exception:
                pass
        if not self._pending_portals:
            self._start_detail_fetch()

    def _start_detail_fetch(self):
        """首页全部完成后，先更新界面，再限流并发请求详情页。"""
        self.portals_done.emit(self._portal_results)
        self._detail_queue = []
        self._url_index = {}  # url -> (save_key, index)
        # 门户分类 key -> JSON 文件名
        cat_map = {"知产": "ip", "国际": "intl", "财经门户": "fin",
                   "综合门户": "tech", "科技": "tech"}
        # 重组：把 _portal_results 按 save_key 合并
        merged = {}
        for cat, lst in self._portal_results.items():
            sk = cat_map.get(cat, cat)
            merged.setdefault(sk, []).extend(lst)
        self._portal_results = merged
        per_site = {}
        for cat, lst in self._portal_results.items():
            for i, it in enumerate(lst):
                if not it.get("url"): continue
                src = it.get("source", "")
                per_site[src] = per_site.get(src, 0) + 1
                if per_site[src] <= 3:  # 每站最多抓 3 条详情页
                    self._detail_queue.append((cat, it["url"]))
                    self._url_index[it["url"]] = (cat, i)
        if not self._detail_queue:
            # 没有详情页要抓，也要通知主窗口走后续补搜逻辑
            self.details_done.emit()
            return
        self._total += len(self._detail_queue)
        self._detail_max = 10  # 并发降到 10
        for _ in range(min(self._detail_max, len(self._detail_queue))):
            self._fire_one_detail()

    def fetch_details_only(self, urls):
        """只请求详情页补正文，不走首页抓取。"""
        # 取消所有未完成请求
        for r in list(self._pending.keys()):
            r.abort()
            r.deleteLater()
        self._pending.clear()
        self._portal_results = {}
        self._url_index = {}  # url -> (cat, index)
        for fname in ["ip", "intl", "fin", "tech"]:
            data = JSONStore.load(fname)
            if data:
                self._portal_results[fname] = data
                for i, it in enumerate(data):
                    if it.get("url"):
                        self._url_index[it["url"]] = (fname, i)
        self._detail_queue = [(None, u) for u in urls]
        self._total = len(urls)
        self._done = 0
        self._detail_max = 10
        for _ in range(min(self._detail_max, len(self._detail_queue))):
            self._fire_one_detail()

    def _fire_one_detail(self):
        if not self._detail_queue: return
        cat, url = self._detail_queue.pop(0)
        req = QNetworkRequest(QUrl(url))
        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
        req.setHeader(QNetworkRequest.UserAgentHeader, ua)
        req.setRawHeader(b"Accept-Language", b"zh-CN,zh;q=0.9")
        req.setTransferTimeout(10000)
        r = self.nam.get(req)
        self._pending[r] = ("detail", url)
        self._pending_details.add(url)

    def _handle_detail(self, url, err, body):
        self._pending_details.discard(url)
        self._done += 1
        self.progress.emit(self._done, self._total, f"日期 {url[:40]}")
        pub = ""; content = ""
        if err == QNetworkReply.NoError and body:
            try:
                # 编码检测：先扫前 2KB 找 charset
                head = body[:2048].decode("ascii", errors="ignore").lower()
                enc = "utf-8"
                m = re.search(r'charset=["\']?\s*(gb\d+|gbk|gb2312|gb18030)', head)
                if m:
                    enc = m.group(1)
                html = body.decode(enc, errors="ignore")
                for pat in [r'<meta[^>]+property="article:published_time"[^>]+content="([^"]+)"',
                            r'<meta[^>]+name="pubdate"[^>]+content="([^"]+)"',
                            r'<meta[^>]+name="publishdate"[^>]+content="([^"]+)"',
                            r'<time[^>]+datetime="([^"]+)"']:
                    m = re.search(pat, html, re.I)
                    if m:
                        pub = m.group(1).strip().replace("T", " ").replace("Z", "")[:16]; break
                # 正文：优先常见容器，再退化到 <article>，最后所有 <p>
                scope = html
                # 凤凰网特殊处理：正文在 allData JSON 里
                if "ifeng.com" in url:
                    m_json = re.search(r'var\s+allData\s*=\s*(\{.*?\});\s*\n', html, re.S)
                    if m_json:
                        try:
                            ad = json.loads(m_json.group(1))
                            c = ad.get("content") or ad.get("mainContent") or ""
                            if c:
                                c = re.sub(r'<[^>]+>', '', c)
                                c = re.sub(r'\s+', ' ', c).strip()
                                if len(c) > 50:
                                    content = c[:3000]
                        except Exception:
                            pass
                if not content:
                    for pat in [r'<div[^>]+class="[^"]*(?:text_con|article-content|main-content|post-content|content_body|article_content|news-content|detail-content|articleMain|article-main|content-inner|TRS_Editor|TRS_UEDITOR|view TRS|custom_union|kr-article|post_content|entry-content|article__content|news_content|paragraph|article-detail|g-articl-text|show_text|content_text|index_main|main-text|detail|artical|articleContent|contentBox|end_article|article_text|article-content-left|left_zw|cont_news|news_txt|detail_txt|TRS|article_content_main|content w1000|main_content|text|detail_content|art_content|article_content|showcontent|contentbox|article_body|entry-content|post_content|single-content|entry|content-area|post__content|rich_media_content|page-article|articleBody|article__body|story-body|story_content|article_body_content|entryBody|articleBodyText|article-html)[^"]*"[^>]*>(.*?)</div>',
                                r'<article[^>]*>(.*?)</article>',
                                r'<main[^>]*>(.*?)</main>',
                                r'<div[^>]+id="[^"]*(?:article|content|detail|main|text|post)[^"]*"[^>]*>(.*?)</div>']:
                        m = re.search(pat, html, re.S | re.I)
                        if m:
                            scope = m.group(1); break
                    ps = re.findall(r'<p[^>]*>(.*?)</p>', scope, re.S | re.I)
                    paras = []
                    for p in ps:
                        t = re.sub(r'<[^>]+>', '', p).strip()
                        t = re.sub(r'\s+', ' ', t)
                        if len(t) > 30:
                            paras.append(t)
                    content = "\n\n".join(paras[:20])
            except Exception:
                pass
        # 用索引 O(1) 找这条 URL（标记删除，避免索引错位）
        entry = self._url_index.get(url)
        if entry and entry[0] in self._portal_results:
            cat, i = entry
            if i >= len(self._portal_results[cat]):
                pass
            elif err != QNetworkReply.NoError:
                self._portal_results[cat][i]["_deleted"] = True
            else:
                it = self._portal_results[cat][i]
                if pub: it["pub_date"] = pub
                if content:
                    it["content"] = content
                else:
                    it["_no_content"] = True  # 标记提取失败，下次不重试
        # 发下一个
        if self._detail_queue:
            self._fire_one_detail()
        elif not self._pending_details:
            # 保存更新后的各分类（过滤标记删除，保留 _no_content 的条目）
            for fname in ["ip", "intl", "fin", "tech"]:
                if fname in self._portal_results:
                    alive = [x for x in self._portal_results[fname] if not x.get("_deleted")]
                    cleaned = MainWindow._clean_items(alive)
                    JSONStore.save(fname, cleaned)
            self.details_done.emit()

    def _handle_gh(self, label, err, body):
        self._pending_gh.discard(label)
        self._done += 1
        self.progress.emit(self._done, self._total, f"GitHub {label}")
        if err == QNetworkReply.NoError and body:
            try:
                # 编码检测：先扫前 2KB 找 charset
                head = body[:2048].decode("ascii", errors="ignore").lower()
                enc = "utf-8"
                m = re.search(r'charset=["\']?\s*(gb\d+|gbk|gb2312|gb18030)', head)
                if m:
                    enc = m.group(1)
                html = body.decode(enc, errors="ignore")
                # 宽松匹配：<article> 块内含 Box-row
                blocks = re.findall(r'<article[^>]*>(.*?)</article>', html, re.S)
                items = []
                for blk in blocks:
                    m = re.search(r'<h2[^>]*>\s*<a[^>]+href="/([^"]+)"', blk)
                    if not m: continue
                    name = m.group(1).strip()
                    # 描述：h2 之后第一段文本，依次试 <p> / <div>
                    desc = ""
                    dm = re.search(r'</h2>\s*<p[^>]*>(.*?)</p>', blk, re.S)
                    if not dm:
                        dm = re.search(r'<p[^>]*class="[^"]*color-fg-muted[^"]*"[^>]*>(.*?)</p>', blk, re.S)
                    if not dm:
                        dm = re.search(r'</h2>\s*<div[^>]*>(.*?)</div>', blk, re.S)
                    if dm:
                        desc = re.sub(r'<[^>]+>', '', dm.group(1)).strip()
                        desc = re.sub(r'\s+', ' ', desc)
                    # 总星数：从 article 块里找所有数字，排除周期增量，最大那个就是总星数
                    stars_total = "-"
                    # 先抓周期增量
                    sm = re.search(r'([\d,]+)\s*stars?\s*(?:today|this week|this month)?', blk)
                    stars_period = sm.group(0) if sm else ""
                    period_num = sm.group(1) if sm else ""
                    # 找块里所有数字
                    txt = re.sub(r'<[^>]+>', ' ', blk)
                    txt = html_mod.unescape(txt)
                    all_nums = re.findall(r'(\d{1,3}(?:,\d{3})+)', txt)
                    # 转成整数，排除周期增量
                    cands = []
                    for n in all_nums:
                        if n == period_num: continue
                        try:
                            v = int(n.replace(',', ''))
                            if v >= 100:  # 总星数一般 >=100
                                cands.append((v, n))
                        except: pass
                    if cands:
                        # 最大的数字通常是总星数（forks 一般小一个数量级）
                        cands.sort(reverse=True)
                        stars_total = cands[0][1]
                    items.append({"name": name, "desc": desc,
                                  "stars_total": stars_total, "stars_period": stars_period})
                    if len(items) >= 15: break
                self._gh_results[label] = items
            except Exception:
                pass
        if not self._pending_gh:
            wk = self._gh_results.get("周榜", [])
            mo = self._gh_results.get("月榜", [])
            # skill 热榜：把日/周/月所有仓库合并，按 SKILL_KEYWORDS 过滤去重
            seen = set()
            skill_hits = []
            for lbl in ("日榜", "周榜", "月榜"):
                for it in self._gh_results.get(lbl, []):
                    nm = it.get("name", "")
                    if nm in seen: continue
                    blob = (nm + " " + it.get("desc", "")).lower()
                    if any(kw.lower() in blob for kw in SKILL_KEYWORDS):
                        seen.add(nm)
                        skill_hits.append(it)
            out = {"周榜": wk, "月榜": mo,
                   "skill热榜": skill_hits}
            if wk or mo:
                # 抓到新数据，写盘
                self._save_json("github_trending.json", out)
            else:
                # GitHub 连不上/超时：保留旧数据，不写空文件
                old = JSONStore.load("github_trending")
                if isinstance(old, dict) and (old.get("周榜") or old.get("月榜")):
                    out = old
            self.github_done.emit(out)

    def _handle_hot(self, err, body):
        self._done += 1
        self.progress.emit(self._done, self._total, "百度热搜")
        if err != QNetworkReply.NoError or not body:
            return
        try:
            data = json.loads(body.decode("utf-8", errors="ignore"))
            cards = data.get("data", {}).get("cards", [])
            out = []
            for card in cards:
                for block in card.get("content", []):
                    items = block.get("content", []) if isinstance(block, dict) else []
                    for it in items:
                        w = it.get("word", "")
                        u = it.get("url", "")
                        if w:
                            out.append({"word": w, "url": u or f"https://www.baidu.com/s?wd={w}"})
                    if out: break
                if out: break
            out = out[:50]
            if out:
                self._save_json("hot.json", out)
                self.hot_done.emit(out)
        except Exception:
            pass

    # ---------- 新闻搜索补全：360 / 百度 / 必应 三引擎 ----------
    def fetch_search(self, queries):
        """queries: [(save_key, subcat, query_str), ...]"""
        self._pending_search = {}
        self._search_results = {}  # save_key -> items
        if not queries:
            return
        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
        # 每个 query 并发发引擎；百度连续失败 3 次以上就跳过
        engines = [
            ("so360",  lambda enc: f"https://news.so.com/ns?q={enc}&pn=1&rn=10"),
            ("bing",   lambda enc: f"https://www.bing.com/news/search?q={enc}&setlang=zh-CN"),
        ]
        if self._baidu_fail_streak < 3:
            engines.insert(1, ("baidu", lambda enc: f"https://www.baidu.com/s?rtt=1&bsst=1&cl=2&tn=news&word={enc}"))
        self._total = len(queries) * len(engines)
        self._done = 0
        for save_key, subcat, q in queries:
            enc = bytes(QUrl.toPercentEncoding(q)).decode("utf-8")
            for engine, url_fn in engines:
                url = url_fn(enc)
                req = QNetworkRequest(QUrl(url))
                req.setHeader(QNetworkRequest.UserAgentHeader, ua)
                req.setRawHeader(b"Accept-Language", b"zh-CN,zh;q=0.9")
                req.setTransferTimeout(8000)
                r = self.nam.get(req)
                self._pending[r] = ("search", save_key, subcat, engine)
                self._pending_search[r] = (save_key, subcat, engine)

    def _handle_search(self, save_key, subcat, engine, err, body):
        self._done += 1
        self.progress.emit(self._done, self._total, f"搜索[{engine}]:{subcat}")
        # 百度失败熔断：连续失败计数
        if engine == "baidu":
            if err != QNetworkReply.NoError or not body:
                self._baidu_fail_streak += 1
            else:
                self._baidu_fail_streak = 0
        items = []
        if err == QNetworkReply.NoError and body:
            try:
                if engine == "so360":
                    items = self._parse_so360(body.decode("utf-8", errors="ignore"), subcat)
                elif engine == "baidu":
                    items = self._parse_baidu(body.decode("utf-8", errors="ignore"), subcat)
                elif engine == "bing":
                    items = self._parse_bing(body.decode("utf-8", errors="ignore"), subcat)
            except Exception:
                pass
        self._search_results.setdefault(save_key, []).extend(items)
        # 所有搜索请求都回来后，按 save_key 批量 emit
        if len(self._pending_search) == 0:
            for sk, lst in self._search_results.items():
                self.search_done.emit(sk, lst)
            self._search_results = {}

    @staticmethod
    def _mk_item(title, url, source, summary, pub, subcat):
        return {"title": title, "url": url, "source": source,
                "summary": summary, "content": summary,
                "pub_date": pub, "subcategory": subcat,
                "fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M")}

    def _parse_so360(self, html, subcat):
        out = []
        block_re = re.compile(
            r'<li[^>]*class="[^"]*res-list[^"]*"[^>]*data-from="news"[^>]*data-url="([^"]+)"[^>]*>(.*?)</li>',
            re.S)
        for m in block_re.finditer(html):
            url, block = m.group(1), m.group(2)
            tm = re.search(r'<a[^>]*title="([^"]+)"', block)
            title = html_mod.unescape(re.sub(r'<[^>]+>', '', tm.group(1)).strip()) if tm else ""
            if not title or not url: continue
            sm = re.search(r'<p[^>]*class="[^"]*summary[^"]*"[^>]*>(.*?)</p>', block, re.S)
            summary = re.sub(r'<[^>]+>', '', sm.group(1)).strip() if sm else ""
            summary = html_mod.unescape(re.sub(r'\s+', ' ', summary))
            cm = re.search(r'<cite[^>]*class="sitename"[^>]*>(.*?)</cite>', block, re.S)
            source = html_mod.unescape(re.sub(r'<[^>]+>', '', cm.group(1)).strip()) if cm else "360新闻"
            pm = re.search(r'<span[^>]*class="[^"]*time[^"]*"[^>]*>(.*?)</span>', block, re.S)
            pub = html_mod.unescape(re.sub(r'<[^>]+>', '', pm.group(1)).strip()) if pm else ""
            out.append(self._mk_item(title, url, source, summary, pub, subcat))
            if len(out) >= 10: break
        return out

    def _parse_baidu(self, html, subcat):
        # 百度新闻搜索结果：<h3 class="...news-title..."><a href="...">title</a></h3>
        out = []
        block_re = re.compile(
            r'<h3[^>]*class="[^"]*news-title[^"]*"[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            re.S)
        for m in block_re.finditer(html):
            url, block = m.group(1), m.group(2)
            title = html_mod.unescape(re.sub(r'<[^>]+>', '', block).strip())
            if not title or not url: continue
            out.append(self._mk_item(title, url, "百度新闻", "", "", subcat))
            if len(out) >= 10: break
        return out

    def _parse_bing(self, html, subcat):
        # 必应新闻：<li class="b_algo"> 里的 <a href="...">title</a>
        out = []
        block_re = re.compile(
            r'<li[^>]*class="b_algo"[^>]*>(.*?)</li>', re.S)
        for m in block_re.finditer(html):
            block = m.group(1)
            am = re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
            if not am: continue
            url, block = am.group(1), am.group(2)
            title = html_mod.unescape(re.sub(r'<[^>]+>', '', block).strip())
            if not title or not url or url.startswith("https://www.bing.com"): continue
            sm = re.search(r'<p[^>]*>(.*?)</p>', block, re.S)
            summary = re.sub(r'<[^>]+>', '', sm.group(1)).strip() if sm else ""
            summary = html_mod.unescape(re.sub(r'\s+', ' ', summary))
            out.append(self._mk_item(title, url, "必应新闻", summary, "", subcat))
            if len(out) >= 10: break
        return out

    @staticmethod
    def _save_json(fname, data):
        with open(os.path.join(DATA_DIR, fname), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


# ============== JSON 存储（替代 SQLite） ==============
class JSONStore:
    """每个分类一个 JSON 文件，存 data/{cat}.json"""
    @staticmethod
    def _path(cat):
        # 文件名安全化
        safe = cat.replace("/", "_").replace("\\", "_")
        return os.path.join(DATA_DIR, f"{safe}.json")

    @staticmethod
    def save(cat, items):
        with open(JSONStore._path(cat), "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load(cat):
        p = JSONStore._path(cat)
        if not os.path.exists(p):
            return []
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []


# ============== 新闻卡片 ==============
class NewsCard(QFrame):
    def __init__(self, news, on_open, on_fav):
        super().__init__()
        self.news = news
        self.setStyleSheet("""NewsCard{background:#262633;border:1px solid #3a3a4a;border-radius:8px;}
                              NewsCard:hover{border:1px solid #60a5fa;}""")
        self.setFixedHeight(120)
        lay = QVBoxLayout(self); lay.setContentsMargins(14,10,14,10); lay.setSpacing(5)
        t = ClickableLabel(news["title"])
        t.setFont(QFont("Microsoft YaHei", 11, QFont.Bold)); t.setWordWrap(True)
        t.setStyleSheet("color:#e5e7eb; background:transparent;")
        t.clicked.connect(lambda: on_open(news))
        m = QLabel(f"{news.get('source','')} · {news.get('pub_date') or news.get('fetched_at') or ''}")
        m.setStyleSheet("color:#6b7280; background:transparent; font-size:11px;")
        row = QHBoxLayout(); row.addStretch(1)
        fav = QPushButton("☆ 收藏"); fav.setCursor(QCursor(Qt.PointingHandCursor))
        fav.setStyleSheet("QPushButton{background:#33334a;color:#d1d5db;border:1px solid #4a4a5e;padding:4px 12px;border-radius:4px;}"
                          "QPushButton:hover{background:#3f3f58;color:#fff;}")
        fav.clicked.connect(lambda: on_fav(news))
        det = QPushButton("查看详情"); det.setCursor(QCursor(Qt.PointingHandCursor))
        det.setStyleSheet("QPushButton{background:#33334a;color:#d1d5db;border:1px solid #4a4a5e;padding:4px 12px;border-radius:4px;}"
                          "QPushButton:hover{background:#3f3f58;color:#fff;}")
        det.clicked.connect(lambda: on_open(news))
        op = QPushButton("打开原文 ↗"); op.setCursor(QCursor(Qt.PointingHandCursor))
        op.setStyleSheet("QPushButton{background:#3b82f6;color:#fff;border:none;padding:4px 12px;border-radius:4px;}"
                         "QPushButton:hover{background:#2563eb;}")
        op.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(news["url"])))
        row.addWidget(fav); row.addWidget(det); row.addWidget(op)
        lay.addWidget(t); lay.addWidget(m); lay.addLayout(row)


# ============== 详情弹窗 ==============
class DetailDialog(QDialog):
    def __init__(self, news):
        super().__init__()
        self.setWindowTitle(news["title"]); self.resize(640, 480)
        lay = QVBoxLayout(self); lay.setContentsMargins(20,18,20,18)
        t = QLabel(news["title"]); t.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        t.setWordWrap(True); t.setStyleSheet("color:#e5e7eb;")
        m = QLabel(f"{news.get('source','')} · {news.get('pub_date') or news.get('fetched_at') or ''}")
        m.setStyleSheet("color:#9ca3af;")
        body = QTextBrowser(); body.setFont(QFont("Microsoft YaHei", 10))
        body.setStyleSheet("QTextBrowser{background:#1f1f2b;color:#d1d5db;border:1px solid #3a3a4a;border-radius:6px;padding:8px;}")
        body.setText(news.get("content") or news.get("summary") or "")
        link = QLabel(f'原文：<a href="{news["url"]}" style="color:#60a5fa;">{news["url"]}</a>')
        link.setOpenExternalLinks(False); link.setTextFormat(Qt.RichText); link.setWordWrap(True)
        link.setStyleSheet("color:#9ca3af;font-size:11px;")
        link.linkActivated.connect(self._open_link_and_close)
        close = QPushButton("关闭"); close.setStyleSheet("QPushButton{background:#3b82f6;color:#fff;border:none;padding:6px 18px;border-radius:4px;}")
        close.clicked.connect(self.accept)
        lay.addWidget(t); lay.addWidget(m); lay.addWidget(body,1); lay.addWidget(link)
        lay.addWidget(close, alignment=Qt.AlignRight)

    def _open_link_and_close(self, url):
        QDesktopServices.openUrl(QUrl(url))
        self.accept()


# ============== 列表页（支持子分类） ==============
class NewsPage(QWidget):
    def __init__(self, sections=None, empty_text="暂无内容"):
        super().__init__()
        self.sections = sections or {}
        self.empty_text = empty_text
        self.on_open = None; self.on_fav = None
        outer = QVBoxLayout(self); outer.setContentsMargins(16,14,16,14); outer.setSpacing(8)
        self.btn_row = QHBoxLayout()
        self._btngrp = QButtonGroup(self)
        outer.addLayout(self.btn_row)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        self.container = QWidget(); self.container.setStyleSheet("background:transparent;")
        self.vbox = QVBoxLayout(self.container); self.vbox.setContentsMargins(0,0,0,0); self.vbox.setSpacing(10)
        self.vbox.addStretch(1)
        scroll.setWidget(self.container)
        outer.addWidget(scroll, 1)
        if self.sections: self._build_btns()

    def _build_btns(self):
        for i in reversed(range(self.btn_row.count())):
            w = self.btn_row.itemAt(i).widget()
            if w: w.deleteLater()
        allb = QPushButton("全部"); allb.setCheckable(True)
        self._style(allb); allb.clicked.connect(lambda: self._render("__all__"))
        self._btngrp.addButton(allb); self.btn_row.addWidget(allb)
        for k in self.sections:
            b = QPushButton(k); b.setCheckable(True)
            self._style(b); b.clicked.connect(lambda _, x=k: self._render(x))
            self._btngrp.addButton(b); self.btn_row.addWidget(b)
        self.btn_row.addStretch(1); allb.setChecked(True); self._render("__all__")

    @staticmethod
    def _style(b):
        b.setCursor(QCursor(Qt.PointingHandCursor))
        b.setStyleSheet("QPushButton{background:#2a2a3d;color:#d1d5db;border:1px solid #4a4a5e;padding:5px 12px;border-radius:12px;}"
                        "QPushButton:checked{background:#3b82f6;color:#fff;}")

    def set_data(self, sections, on_open, on_fav):
        self.sections = sections; self.on_open = on_open; self.on_fav = on_fav
        self._build_btns()

    def set_flat(self, items, on_open, on_fav):
        self.on_open = on_open; self.on_fav = on_fav
        while self.vbox.count() > 1:
            it = self.vbox.takeAt(0); w = it.widget()
            if w: w.deleteLater()
        if not items:
            tip = QLabel(self.empty_text); tip.setAlignment(Qt.AlignCenter)
            tip.setStyleSheet("color:#6b7280;padding:40px;"); self.vbox.insertWidget(0, tip); return
        for n in items:
            self.vbox.insertWidget(self.vbox.count()-1, NewsCard(n, on_open, on_fav))

    def _render(self, key):
        items = [n for lst in self.sections.values() for n in lst] if key == "__all__" else self.sections.get(key, [])
        # 按时间倒序：优先 pub_date，其次 fetched_at
        def _t(n):
            s = n.get("pub_date") or n.get("fetched_at") or ""
            return str(s)
        items = sorted(items, key=_t, reverse=True)
        self.set_flat(items, self.on_open, self.on_fav)


# ============== 热搜页 ==============
class HotPage(QWidget):
    def __init__(self):
        super().__init__()
        self.items = []
        self.lay = QVBoxLayout(self); self.lay.setContentsMargins(20,16,20,16); self.lay.setSpacing(10)
        self.h = QLabel("🔥 热搜词条"); self.h.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        self.h.setStyleSheet("color:#e5e7eb;"); self.lay.addWidget(self.h)
        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        self.lay.addWidget(self.scroll, 1)
        self._render()

    def set_data(self, items):
        self.items = items
        self._render()

    def _render(self):
        c = QWidget(); c.setStyleSheet("background:transparent;")
        g = QGridLayout(c); g.setSpacing(10)
        for i, item in enumerate(self.items):
            b = QPushButton(f"{i+1}. {item['word']}")
            b.setCursor(QCursor(Qt.PointingHandCursor))
            b.setStyleSheet("QPushButton{background:#2a2a3d;color:#fcd34d;border:1px solid #4a4a5e;border-radius:14px;padding:8px 14px;text-align:left;}"
                            "QPushButton:hover{border:1px solid #fcd34d;}")
            b.clicked.connect(lambda _, u=item["url"]: QDesktopServices.openUrl(QUrl(u)))
            g.addWidget(b, i//2, i%2)
        self.scroll.setWidget(c)


# ============== GitHub 页 ==============
class GitHubPage(QWidget):
    def __init__(self):
        super().__init__()
        self.data = {"周榜": [], "月榜": [], "skill热榜": []}
        outer = QVBoxLayout(self); outer.setContentsMargins(20,16,20,16); outer.setSpacing(10)
        h = QLabel("🐙 GitHub 热门"); h.setFont(QFont("Microsoft YaHei", 13, QFont.Bold))
        h.setStyleSheet("color:#e5e7eb;"); outer.addWidget(h)
        self.g = QButtonGroup(self); row = QHBoxLayout()
        for txt in ["周榜","月榜","skill热榜"]:
            b = QPushButton(txt); b.setCheckable(True); b.setCursor(QCursor(Qt.PointingHandCursor))
            b.setStyleSheet("QPushButton{background:#2a2a3d;color:#d1d5db;border:1px solid #4a4a5e;padding:5px 12px;border-radius:12px;}"
                            "QPushButton:checked{background:#3b82f6;color:#fff;}")
            b.clicked.connect(lambda _, x=txt: self._render(x))
            self.g.addButton(b); row.addWidget(b)
        row.addStretch(1); outer.addLayout(row)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        self.c = QWidget(); self.c.setStyleSheet("background:transparent;")
        self.v = QVBoxLayout(self.c); self.v.setContentsMargins(0,0,0,0); self.v.setSpacing(10); self.v.addStretch(1)
        scroll.setWidget(self.c); outer.addWidget(scroll, 1)
        row.itemAt(0).widget().setChecked(True); self._render("周榜")

    def set_data(self, data):
        """data: {"周榜":[...], "月榜":[...], "季榜":[...], "冲榜最快":[...]}"""
        self.data = data
        self._render(self._current_tab())

    def _current_tab(self):
        btn = self.g.checkedButton()
        return btn.text() if btn else "周榜"

    def _render(self, mode):
        while self.v.count() > 1:
            it = self.v.takeAt(0); w = it.widget()
            if w: w.deleteLater()
        rows = self.data.get(mode, [])
        if not rows:
            tip = QLabel("暂无数据，点刷新抓取 GitHub Trending")
            tip.setAlignment(Qt.AlignCenter); tip.setStyleSheet("color:#6b7280;padding:40px;")
            self.v.insertWidget(0, tip); return
        for r in rows:
            card = QFrame(); card.setStyleSheet("QFrame{background:#262633;border:1px solid #3a3a4a;border-radius:8px;}"
                                                "QFrame:hover{border:1px solid #60a5fa;}")
            card.setFixedHeight(110)
            cl = QVBoxLayout(card); cl.setContentsMargins(12,8,12,8); cl.setSpacing(4)
            # 上：项目名
            if r.get("is_article"):
                url = r.get("url", "#")
                nm = ClickableLabel(f"📰 {r['name']} ↗")
                nm.setFont(QFont("Microsoft YaHei", 10, QFont.Bold)); nm.setStyleSheet("color:#7dd3fc;")
            else:
                url = f"https://github.com/{r['name']}"
                nm = ClickableLabel(f"📦 {r['name']} ↗")
                nm.setFont(QFont("Consolas", 11, QFont.Bold)); nm.setStyleSheet("color:#7dd3fc;")
            nm.clicked.connect(lambda u=url: QDesktopServices.openUrl(QUrl(u)))
            cl.addWidget(nm)
            # 中：项目介绍
            d = QLabel(r.get("desc","") or "（该仓库暂无简介）")
            d.setWordWrap(True); d.setStyleSheet("color:#b0b3bc;font-size:12px;background:transparent;")
            ds = QScrollArea(); ds.setFixedHeight(36); ds.setWidgetResizable(True)
            ds.setStyleSheet("QScrollArea{border:none;background:transparent;} QScrollBar:vertical{width:4px;background:#3a3a4a;}")
            ds.setWidget(d)
            cl.addWidget(ds)
            # 下：星数详情
            total = r.get("stars_total", "-")
            period = r.get("stars_period", "")
            if mode == "skill热榜":
                star_txt = f"⭐ {total}"
            else:
                star_txt = f"⭐ 总 {total}    📈 {period}" if period else f"⭐ 总 {total}"
            sl = QLabel(star_txt)
            sl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            sl.setStyleSheet("color:#fbbf24;font-size:12px;background:transparent;")
            cl.addWidget(sl)
            self.v.insertWidget(self.v.count()-1, card)


# ============== 主窗口 ==============
class MainWindow(QMainWindow):
    MENU = ["🔥 热搜", "🏛️ 知产新闻", "💻 科技资讯", "🐙 Git热榜",
            "🌍 国际时讯", "💰 财经导航", "⭐ 收藏", "⚙️ 设置"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("新闻聚合")
        screen = QApplication.primaryScreen().geometry()
        self.resize(screen.width()//2, int(screen.height()*0.8))
        self.setMinimumSize(800, 600)
        self.favorites = []
        self.fetcher = FeedFetcher(self)
        self.fetcher.portals_done.connect(self._on_portals)
        self.fetcher.github_done.connect(self._on_github)
        self.fetcher.hot_done.connect(self._on_hot)
        self.fetcher.details_done.connect(self._on_details_done)
        self.fetcher.search_done.connect(self._on_search_done)
        self.fetcher.progress.connect(self._on_progress)
        self._current_target = None
        self._build_ui()
        self._load_mock()

    def _build_ui(self):
        central = QWidget(); root = QHBoxLayout(central)
        root.setContentsMargins(0,0,0,0); root.setSpacing(0)
        self.sb = QListWidget(); self.sb.setFixedWidth(170)
        self.sb.setStyleSheet("QListWidget{background:#15151f;color:#d1d5db;border:none;font-size:13px;}"
                              "QListWidget::item{padding:13px 16px;}"
                              "QListWidget::item:hover{background:#26263a;}"
                              "QListWidget::item:selected{background:#3b82f6;color:#fff;}")
        for n in self.MENU: QListWidgetItem(n, self.sb)
        root.addWidget(self.sb)
        right = QVBoxLayout(); right.setContentsMargins(0,0,0,0); right.setSpacing(0)
        top = QWidget(); top.setStyleSheet("background:#181824;border-bottom:1px solid #3a3a4a;")
        top.setFixedHeight(48)
        tb = QHBoxLayout(top); tb.setContentsMargins(14,8,14,8)
        self.search = QLineEdit(); self.search.setPlaceholderText("搜索标题…")
        self.search.setStyleSheet("QLineEdit{padding:6px 10px;background:#262633;color:#e5e7eb;border:1px solid #3a3a4a;border-radius:6px;}")
        self.search.returnPressed.connect(self._do_search)
        rb = QPushButton("刷新"); rb.setCursor(QCursor(Qt.PointingHandCursor))
        rb.setStyleSheet("QPushButton{background:#3b82f6;color:#fff;border:none;padding:6px 14px;border-radius:6px;}")
        rb.clicked.connect(self.refresh)
        tb.addWidget(self.search,1); tb.addWidget(rb); right.addWidget(top)
        self.stack = QStackedWidget()
        self.p_hot = HotPage()
        self.p_ind = NewsPage(INDUSTRY_SECTIONS, "暂无知产新闻")
        self.p_tech = NewsPage({k: [] for k in TECH_KEYWORDS}, "暂无科技新闻")
        self.p_gh = GitHubPage()
        self.p_intl = NewsPage(INTERNATIONAL_SECTIONS, "暂无国际新闻")
        self.p_fin = NewsPage({k: [] for k in FIN_KEYWORDS}, "暂无财经新闻")
        self.p_fav = NewsPage(empty_text="还没有收藏")
        self.p_set = self._setting()
        for p in (self.p_hot, self.p_ind, self.p_tech, self.p_gh,
                  self.p_intl, self.p_fin, self.p_fav, self.p_set):
            self.stack.addWidget(p)
        right.addWidget(self.stack, 1)
        root.addLayout(right, 1)
        self.setCentralWidget(central)
        self.status = QStatusBar(); self.setStatusBar(self.status)
        self.sb.currentRowChanged.connect(lambda i: self.stack.setCurrentIndex(i))
        self.sb.setCurrentRow(0)

    def _setting(self):
        p = QWidget(); lay = QVBoxLayout(p); lay.setContentsMargins(24,20,24,20)
        t = QLabel("设置"); t.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        t.setStyleSheet("color:#e5e7eb;")
        info = QLabel(
            "数据源（门户首页实时抓取）：\n"
            "  · 知产：15 个 IP 专业站\n"
            "  · 财经：26 个财经门户\n"
            "  · 科技：28 个科技门户\n"
            "  · 国际：24 个地缘/国际站\n"
            "  · GitHub：Trending + 13 个开源社区\n"
            "  · 热搜：微博热搜 API\n\n"
            "点刷新抓取当前分类，详情页限流 10 并发\n"
            "数据存 data/ 文件夹下 JSON 文件")
        info.setStyleSheet("color:#b0b3bc;font-size:12px;"); info.setWordWrap(True)
        lay.addWidget(t); lay.addWidget(info); lay.addStretch(1)
        return p

    def _load_mock(self):
        # 从按大类分的 JSON 加载
        self._missing_urls = []
        ip = JSONStore.load("ip")
        if ip:
            sections = self._regroup(ip, IP_KEYWORDS, drop=IP_DROP)
            self.p_ind.set_data(sections, self._open, self._fav)
            self._collect_missing(ip)
        else:
            self.p_ind.set_data(INDUSTRY_SECTIONS, self._open, self._fav)
        intl = JSONStore.load("intl")
        if intl:
            sections = self._regroup(intl, INTL_KEYWORDS, extra="外媒报道", rename=INTL_RENAME, drop=INTL_DROP)
            self.p_intl.set_data(sections, self._open, self._fav)
            self._collect_missing(intl)
        else:
            self.p_intl.set_data(INTERNATIONAL_SECTIONS, self._open, self._fav)
        fin = JSONStore.load("fin")
        if fin:
            self._fin_sections = self._regroup(fin, FIN_KEYWORDS, drop=FIN_DROP, rename=FIN_RENAME)
            self.p_fin.set_data(self._fin_sections, self._open, self._fav)
            self._collect_missing(fin)
        tech = JSONStore.load("tech")
        if tech:
            self._tech_sections = self._regroup(tech, TECH_KEYWORDS, drop=TECH_DROP)
            self.p_tech.set_data(self._tech_sections, self._open, self._fav)
            self._collect_missing(tech)
        gh = JSONStore.load("github_trending")
        if gh: self.p_gh.set_data(gh)
        hot = JSONStore.load("hot")
        if hot: self.p_hot.set_data(hot)
        fav = JSONStore.load("favorites")
        if fav:
            self.favorites = fav
            self.p_fav.set_flat(self.favorites, self._open, self._fav)
        # 后台补全缺失正文
        if self._missing_urls:
            QTimer.singleShot(500, self._fetch_missing)

    def _collect_missing(self, items):
        """收集需要补全正文的 URL：content 字数 < 100，且 url 不空。
           排除列表页/首页（这些本来就没正文）。"""
        skip_pat = re.compile(r'(index\.html?|/index|list|NewsList|forum-|/category/|/tag/|/$)', re.I)
        for it in items:
            c = (it.get("content") or "").strip()
            u = (it.get("url") or "").strip()
            if not u: continue
            if skip_pat.search(u): continue
            if len(c) < 100:
                self._missing_urls.append(it["url"])

    def _fetch_missing(self):
        """对 content==title 的条目，后台请求 URL 补正文。"""
        if not self._missing_urls: return
        self.fetcher.fetch_details_only(self._missing_urls)

    @staticmethod
    def _clean_items(items):
        """过滤：title < 10 字删除；ICP备案号删除；content==title 清空；
           content 空且 url 空删除；非中文标注。"""
        out = []
        for it in items:
            t = (it.get("title") or "").strip()
            if len(t) < 10: continue
            if ("ICP" in t and "备" in t) or ("备" in t and "[" in t and "]" in t) or "备案号" in t or "下载" in t: continue
            c = (it.get("content") or "").strip()
            u = (it.get("url") or "").strip()
            if not u: continue  # 无链接，删除
            if c and c == t:
                it["content"] = ""
                c = ""
            if not c and not u: continue  # 无正文且无链接，删除
            if not re.search(r'[\u4e00-\u9fff]', t):
                it["title"] = "[EN] " + t
            out.append(it)
        return out

    @staticmethod
    def _regroup(items, keywords, extra=None, drop=(), rename=None):
        """从扁平列表按 subcategory 重新分组。drop 里的不渲染；rename 把旧子分类名映射成新名。"""
        items = MainWindow._clean_items(items)
        sections = {k: [] for k in keywords}
        if extra: sections[extra] = []
        drop_set = set(drop)
        rename = rename or {}
        for it in items:
            sub = it.get("subcategory", "其他")
            sub = rename.get(sub, sub)
            if sub in drop_set:
                continue
            if sub not in sections:
                if sub == "其他":
                    sections["其他"] = []
                else:
                    continue  # 已删除的子分类，历史条目不显示
            sections[sub].append(it)
        return sections

    def refresh(self):
        row = self.sb.currentRow()
        mapping = {0: "hot", 1: "知产", 2: "科技", 3: "gh",
                   4: "国际", 5: "财经门户"}
        target = mapping.get(row)
        self._current_target = target
        self.status.showMessage(f"正在刷新 {'全部' if target is None else self.MENU[row][2:]}…")
        self.fetcher.fetch_all(target_cat=target)

    def _on_progress(self, done, total, name):
        self.status.showMessage(f"抓取中 {done}/{total} · {name}")

    def _on_details_done(self):
        """详情页补完正文后，重新从 JSON 加载刷新界面。"""
        ip = JSONStore.load("ip")
        if ip:
            self.p_ind.set_data(self._regroup(ip, IP_KEYWORDS, drop=IP_DROP), self._open, self._fav)
        intl = JSONStore.load("intl")
        if intl:
            self.p_intl.set_data(self._regroup(intl, INTL_KEYWORDS, extra="外媒报道", rename=INTL_RENAME, drop=INTL_DROP),
                                 self._open, self._fav)
        fin = JSONStore.load("fin")
        if fin:
            self._fin_sections = self._regroup(fin, FIN_KEYWORDS, drop=FIN_DROP, rename=FIN_RENAME)
            self.p_fin.set_data(self._fin_sections, self._open, self._fav)
        tech = JSONStore.load("tech")
        if tech:
            self._tech_sections = self._regroup(tech, TECH_KEYWORDS, drop=TECH_DROP)
            self.p_tech.set_data(self._tech_sections, self._open, self._fav)
        self.status.showMessage("正文补全完成", 3000)
        # 补空子分类：用 360 新闻搜索
        self._find_empty_and_search()

    # 当前大类 -> (keywords_dict, save_key)
    _CAT_MAP = {
        "知产":   (IP_KEYWORDS,    "ip"),
        "科技":   (TECH_KEYWORDS,  "tech"),
        "国际":   (INTL_KEYWORDS,  "intl"),
        "财经门户":(FIN_KEYWORDS,   "fin"),
    }

    @staticmethod
    def _parse_pub_date(s):
        """把杂乱的 pub_date 字符串解析成 datetime，失败返回 None。"""
        if not s:
            return None
        s = s.strip()
        now = datetime.now()
        m = re.match(r'(\d+)\s*分钟前', s)
        if m: return now - timedelta(minutes=int(m.group(1)))
        m = re.match(r'(\d+)\s*小时前', s)
        if m: return now - timedelta(hours=int(m.group(1)))
        m = re.match(r'(\d+)\s*天前', s)
        if m: return now - timedelta(days=int(m.group(1)))
        if s.startswith('今天'):
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        if s.startswith('昨天'):
            return now - timedelta(days=1)
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d',
                    '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M', '%Y/%m/%d'):
            try:
                return datetime.strptime(s[:19], fmt)
            except ValueError:
                continue
        m = re.match(r'(\d{1,2})-(\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?', s)
        if m:
            try:
                mo, d = int(m.group(1)), int(m.group(2))
                hh = int(m.group(3)) if m.group(3) else 0
                mm = int(m.group(4)) if m.group(4) else 0
                return now.replace(month=mo, day=d, hour=hh, minute=mm,
                                   second=0, microsecond=0)
            except ValueError:
                return None
        return None

    def _find_empty_and_search(self):
        """点刷新后，对当前大类所有子分类都补搜新新闻，按 URL 去重合并。"""
        cat = self._current_target
        if cat not in self._CAT_MAP:
            return
        keywords_dict, save_key = self._CAT_MAP[cat]
        queries = []
        for sub in keywords_dict:
            kws = keywords_dict[sub][:5]
            q = " OR ".join(f'"{k}"' for k in kws)
            queries.append((save_key, sub, q))
            # 专利诉讼 / 海外IP动态：额外发几个精准 query，多抓结果
            extra = SPECIAL_QUERIES.get(sub, [])
            for eq in extra:
                queries.append((save_key, sub, eq))
        if not queries:
            return
        self.status.showMessage(f"补搜 {len(queries)} 个子分类的最新新闻…")
        self.fetcher.fetch_search(queries)

    def _on_search_done(self, save_key, new_items):
        """搜索结果回来：按 url 去重合并进 JSON，刷新对应页。"""
        if not new_items:
            self.status.showMessage("搜索无结果", 3000)
            return
        existing = JSONStore.load(save_key)
        seen = {it.get("url") for it in existing if it.get("url")}
        added = 0
        for it in new_items:
            u = it.get("url")
            if not u or u in seen:
                continue
            seen.add(u)
            existing.append(it)
            added += 1
        cleaned = self._clean_items(existing)
        JSONStore.save(save_key, cleaned)
        # 刷新对应页面
        if save_key == "ip":
            self.p_ind.set_data(self._regroup(cleaned, IP_KEYWORDS, drop=IP_DROP), self._open, self._fav)
        elif save_key == "tech":
            self._tech_sections = self._regroup(cleaned, TECH_KEYWORDS, drop=TECH_DROP)
            self.p_tech.set_data(self._tech_sections, self._open, self._fav)
        elif save_key == "intl":
            self.p_intl.set_data(self._regroup(cleaned, INTL_KEYWORDS, extra="外媒报道", rename=INTL_RENAME, drop=INTL_DROP),
                                 self._open, self._fav)
        elif save_key == "fin":
            self._fin_sections = self._regroup(cleaned, FIN_KEYWORDS, drop=FIN_DROP, rename=FIN_RENAME)
            self.p_fin.set_data(self._fin_sections, self._open, self._fav)
        self.status.showMessage(f"搜索补入 {added} 条", 4000)

    def _do_search(self):
        kw = self.search.text().strip()
        if not kw: return
        # 收集所有页面的新闻
        all_news = []
        for sections in [getattr(self, "_tech_sections", {}),
                         getattr(self, "_fin_sections", {}),
                         getattr(self.p_ind, "sections", {}),
                         getattr(self.p_intl, "sections", {})]:
            for lst in sections.values():
                all_news.extend(lst)
        m = [n for n in all_news if kw in n.get("title", "")]
        if not m:
            QMessageBox.information(self, "搜索", f"未找到「{kw}」")
        else:
            QMessageBox.information(self, f"搜索：{kw}",
                                    f"{len(m)} 条：\n" + "\n".join(f"· {n['title']}" for n in m[:20]))

    @staticmethod
    def _classify_tech(items):
        """按关键词把新闻分到科技子分类。匹配不上的丢弃（不要"其他"）。"""
        sections = {k: [] for k in TECH_KEYWORDS}
        for n in items:
            title = n.get("title", "")
            matched = False
            for sub, kws in TECH_KEYWORDS.items():
                if any(kw in title for kw in kws):
                    sections[sub].append(n); matched = True; break
            # 不设"其他"，匹配不上直接丢
        return sections

    @staticmethod
    def _classify_fin(items):
        sections = {k: [] for k in FIN_KEYWORDS}
        for n in items:
            title = n.get("title", "")
            matched = False
            for sub, kws in FIN_KEYWORDS.items():
                if any(kw in title for kw in kws):
                    sections[sub].append(n); matched = True; break
            # 不设"其他"，匹配不上直接丢
        return sections

    @staticmethod
    def _classify_ip(items):
        sections = {k: [] for k in IP_KEYWORDS}
        for n in items:
            title = n.get("title", "")
            matched = False
            for sub, kws in IP_KEYWORDS.items():
                if any(kw in title for kw in kws):
                    sections[sub].append(n); matched = True; break
            # 不设"其他"，匹配不上直接丢
        return sections

    @staticmethod
    def _classify_intl(items):
        sections = {k: [] for k in INTL_KEYWORDS}
        sections["外媒报道"] = []
        for n in items:
            title = n.get("title", "")
            matched = False
            for sub, kws in INTL_KEYWORDS.items():
                if any(kw in title for kw in kws):
                    sections[sub].append(n); matched = True; break
            if not matched:
                sections["外媒报道"].append(n)
        return sections

    def _on_portals(self, sections):
        """把门户抓取结果分类，按大类保存到独立 JSON。"""
        n = 0
        if sections.get("知产"):
            classified = self._classify_ip(sections["知产"])
            flat = self._clean_items(self._flatten(classified))
            JSONStore.save("ip", flat)
            self.p_ind.set_data(self._regroup(flat, IP_KEYWORDS, drop=IP_DROP), self._open, self._fav)
            n += len(flat)
        if sections.get("国际"):
            classified = self._classify_intl(sections["国际"])
            flat = self._clean_items(self._flatten(classified))
            JSONStore.save("intl", flat)
            self.p_intl.set_data(self._regroup(flat, INTL_KEYWORDS, extra="外媒报道", rename=INTL_RENAME, drop=INTL_DROP),
                                 self._open, self._fav)
            n += len(flat)
        if sections.get("财经门户"):
            classified = self._classify_fin(sections["财经门户"])
            flat = self._clean_items(self._flatten(classified))
            JSONStore.save("fin", flat)
            self._fin_sections = self._regroup(flat, FIN_KEYWORDS, drop=FIN_DROP, rename=FIN_RENAME)
            self.p_fin.set_data(self._fin_sections, self._open, self._fav)
            n += len(flat)
        tech_items = sections.get("综合门户", []) + sections.get("科技", [])
        if tech_items:
            classified = self._classify_tech(tech_items)
            flat = self._clean_items(self._flatten(classified))
            JSONStore.save("tech", flat)
            self._tech_sections = self._regroup(flat, TECH_KEYWORDS, drop=TECH_DROP)
            self.p_tech.set_data(self._tech_sections, self._open, self._fav)
            n += len(flat)
        if sections.get("gh"):
            items = [{"name": it["title"], "desc": it["source"],
                      "stars_total": "-", "stars_period": "",
                      "url": it["url"], "is_article": True} for it in sections["gh"]]
            existing = dict(getattr(self.p_gh, "data", {}))
            existing["社区推荐"] = items
            self.p_gh.set_data(existing)
            n += len(items)
        self.status.showMessage(f"已更新 {n} 条", 3000)

    @staticmethod
    def _flatten(sections):
        """把子分类字典压平成列表，每条加 subcategory 字段。"""
        out = []
        for sub, lst in sections.items():
            for it in lst:
                it["subcategory"] = sub
                if it.get("content") == it.get("title"):
                    it["content"] = ""
                out.append(it)
        return out

    def _on_github(self, data):
        self.p_gh.set_data(data)
        n = sum(len(v) for v in data.values())
        self.status.showMessage(f"GitHub Trending {n} 条，存 data/github_trending.json", 6000)

    def _on_hot(self, items):
        self.p_hot.set_data(items)
        self.status.showMessage(f"微博热搜 {len(items)} 条已更新", 5000)

    def _open(self, news):
        DetailDialog(news).exec_()

    def _fav(self, news):
        for n in self.favorites:
            if n["url"] == news["url"]:
                QMessageBox.information(self, "提示", "已在收藏夹"); return
        self.favorites.append(news)
        JSONStore.save("favorites", self.favorites)
        self.p_fav.set_flat(self.favorites, self._open, self._fav)
        QMessageBox.information(self, "成功", "已收藏")


def _hide():
    if sys.platform != "win32": return
    import ctypes
    h = ctypes.windll.kernel32.GetConsoleWindow()
    if h: ctypes.windll.user32.ShowWindow(h, 0)


def main():
    _hide()
    app = QApplication(sys.argv); app.setStyle("Fusion")
    app.setStyleSheet("""QMainWindow,QDialog,QWidget{background:#1e1e2a;color:#e5e7eb;}
                         QScrollBar:vertical{background:#1e1e2a;width:10px;}
                         QScrollBar::handle:vertical{background:#4a4a5e;border-radius:5px;}""")
    w = MainWindow(); w.show(); sys.exit(app.exec_())


if __name__ == "__main__":
    main()
