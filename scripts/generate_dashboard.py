#!/usr/bin/env python3
"""グループダッシュボード生成スクリプト — AIスキル診断シート

複数人分の診断結果JSON（data/results/）を集計し、ダッシュボードHTMLを生成する。
AI呼び出しは一切含まない（docs/simple-spec.md §4.2）。

使い方:
    python generate_dashboard.py [結果フォルダ] [出力HTMLパス]
    （省略時: data/results/ → outputs/dashboard.html）

- 重み付け合計・レベル判定はJSON内の確定値を再利用する（再計算しない）
- 同一対象者の複数JSONは評価日が最新の1件のみを集計・表示対象とする
- Python 3.11 標準ライブラリのみ使用
"""
import json
import sys
from html import escape
from pathlib import Path

VECTOR_IDS = ["V1", "V2", "V3", "V4", "V5"]
LEVELS = ["L0", "L1", "L2", "L3", "L4", "L5"]

# 集計に必要な必須フィールド（SKILL.md のJSONスキーマより）
REQUIRED_TOP_FIELDS = ["subject", "assessment_date", "total_score", "level", "vectors"]
REQUIRED_VECTOR_FIELDS = ["raw_score", "weighted_score", "evidence_grade"]


def _is_number(value):
    # bool は int のサブクラスだが点数としては不正
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_record(data):
    """必須フィールドの欠損・型不正を検査する。問題があればエラーメッセージ、なければ None を返す。"""
    for field in REQUIRED_TOP_FIELDS:
        if field not in data:
            return f"必須フィールド '{field}' がありません"
    for field in ("subject", "assessment_date", "level"):
        if not isinstance(data[field], str):
            return f"'{field}' が文字列ではありません"
    if not _is_number(data["total_score"]):
        return "'total_score' が数値ではありません"
    if not isinstance(data["vectors"], dict):
        return "'vectors' がオブジェクトではありません"
    for vid in VECTOR_IDS:
        if vid not in data["vectors"]:
            return f"ベクトル '{vid}' がありません"
        vec = data["vectors"][vid]
        if not isinstance(vec, dict):
            return f"ベクトル '{vid}' がオブジェクトではありません"
        for field in REQUIRED_VECTOR_FIELDS:
            if field not in vec:
                return f"ベクトル '{vid}' に必須フィールド '{field}' がありません"
        if not _is_number(vec["raw_score"]) or not 0 <= vec["raw_score"] <= 5:
            return f"ベクトル '{vid}' の 'raw_score' が0〜5の数値ではありません"
        if not _is_number(vec["weighted_score"]):
            return f"ベクトル '{vid}' の 'weighted_score' が数値ではありません"
    return None


def load_results(results_dir):
    """結果フォルダ内の全JSONを読み込む。

    Returns:
        (records, errors): 有効なレコードのリストと、エラーメッセージのリスト。
        壊れたファイル・欠損のあるファイルは records に含めず errors に記録する（処理は継続）。
    """
    results_dir = Path(results_dir)
    records = []
    errors = []

    if not results_dir.is_dir():
        errors.append(f"結果フォルダが見つかりません: {results_dir}")
        return records, errors

    for path in sorted(results_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            errors.append(f"{path.name}: JSONとして読み込めません（{e}）")
            continue
        problem = validate_record(data)
        if problem:
            errors.append(f"{path.name}: {problem}")
            continue
        records.append(data)

    return records, errors


def select_latest(records):
    """同一対象者は評価日が最新の1件のみを残し、合計点の降順で返す（docs/simple-spec.md §4.2）。"""
    latest = {}
    for rec in records:
        subject = rec["subject"]
        # 評価日はYYYY-MM-DD形式のため文字列比較で新旧判定できる
        if subject not in latest or rec["assessment_date"] > latest[subject]["assessment_date"]:
            latest[subject] = rec
    return sorted(latest.values(), key=lambda r: r["total_score"], reverse=True)


def level_distribution(records):
    """レベル（L0〜L5）ごとの人数を数える。"""
    dist = {level: 0 for level in LEVELS}
    for rec in records:
        if rec["level"] in dist:
            dist[rec["level"]] += 1
    return dist


# ---------------------------------------------------------------------------
# チャート生成（B2）
# デザイン方針（docs/simple-spec.md §6）: 藍 #2b3a8f の単色ファミリーのみ使用。
# グラデーション・外部chartライブラリは使わない。座標系はSKILL.mdの個人結果レーダーと同一。
# ---------------------------------------------------------------------------

# 参照HTML（genai-skill-framework-v2.html）のL0〜L5バンド色（濃→淡）
SERIES_COLORS = ["#2b3a8f", "#5d6d9c", "#8a94b5", "#404f96", "#7c88a6", "#9aa2b3"]

LEVEL_BAND_COLORS = {
    "L0": "#b9bcc4", "L1": "#9aa2b3", "L2": "#7c88a6",
    "L3": "#5d6d9c", "L4": "#404f96", "L5": "#2b3a8f",
}
LEVEL_NAMES = {
    "L0": "Entry", "L1": "Foundation", "L2": "App Builder",
    "L3": "Practitioner", "L4": "Architect", "L5": "Principal",
}

# ベクトルの説明（フレームワーク3章）。レーダー・ヒートマップの凡例に使用
VECTOR_LEGEND = {
    "V1": ("Context Engineering", "コンテキスト設計力", 25),
    "V2": ("Agentic System Design", "エージェントシステム設計力", 25),
    "V3": ("Knowledge Architecture", "知識アーキテクチャ設計力", 20),
    "V4": ("Evaluation & Observability", "評価・観測能力", 15),
    "V5": ("Production & LLMOps", "本番構築・運用能力", 15),
}


# レベル基準（フレームワーク4章より転記・変更禁止）
LEVEL_CRITERIA = [
    ("85〜100", "L5", "Principal Architect", "方法論を確立し、組織の標準を設計できる。全ベクトルで等級A証拠を持つ"),
    ("70〜84", "L4", "Architect", "複雑なシステムを一貫した設計判断のもとで構築・指揮できる"),
    ("55〜69", "L3", "Systems Practitioner", "標準的なエージェント／検索システムを自力で構築でき、一部領域で設計判断を示せる"),
    ("40〜54", "L2", "Application Builder", "既存の枠組みに沿ったAIアプリケーションを構築できる"),
    ("25〜39", "L1", "Foundation", "AI活用の基礎を実務に適用している。システム構築はこれから"),
    ("0〜24", "L0", "Entry", "評価可能な実績が未蓄積（能力の否定ではなく、証拠の不在を意味する）"),
]


def level_legend_html(current_level=None):
    """L0〜L5の評価基準解説表（控えめなデザイン）を返す。

    current_level を指定すると該当行を薄くハイライトする（個人結果向け。ダッシュボードでは未指定）。
    """
    rows = []
    for score_range, lv, name, desc in LEVEL_CRITERIA:
        cls = ' class="current"' if lv == current_level else ""
        rows.append(
            f'<tr{cls}><td class="lv-range">{score_range}</td><td class="lv-id">{lv}</td>'
            f'<td class="lv-name">{name}</td><td>{desc}</td></tr>')
    return (
        '<table class="lv-legend">'
        '<tr><th>スコア</th><th>Lv</th><th>呼称</th><th>状態の説明</th></tr>'
        + "".join(rows) + "</table>"
    )


def vector_legend_html():
    """V1〜V5の名称・和名・重みの凡例テーブルを返す。"""
    rows = "".join(
        f'<tr><td class="num">{vid}</td><td>{en}</td><td>{ja}</td><td class="num">{w}%</td></tr>'
        for vid, (en, ja, w) in VECTOR_LEGEND.items())
    return (
        '<table class="data vector-legend">'
        '<tr><th style="width:44px">V</th><th>ベクトル</th><th>内容</th><th style="width:56px">重み</th></tr>'
        + rows + "</table>"
    )

# レーダー座標: 中心(200,200)、半径28×到達度。V1が真上、時計回り
RADAR_ANGLES = {
    "V1": (0.0, -1.0),
    "V2": (0.951, -0.309),
    "V3": (0.588, 0.809),
    "V4": (-0.588, 0.809),
    "V5": (-0.951, -0.309),
}


def _radar_point(vid, score):
    cos_t, sin_t = RADAR_ANGLES[vid]
    x = 200 + 28 * score * cos_t
    y = 200 + 28 * score * sin_t
    return f"{x:.1f},{y:.1f}"


def radar_svg(records):
    """全対象者を重ね描きした比較レーダーチャートSVGを返す。"""
    grid = []
    for k in range(1, 6):
        stroke = "#b9b9b0" if k == 5 else "#dcdcd6"
        width = "1.5" if k == 5 else "1"
        points = " ".join(_radar_point(vid, k) for vid in VECTOR_IDS)
        grid.append(f'<polygon points="{points}" fill="none" stroke="{stroke}" stroke-width="{width}"/>')
    axes = []
    for vid in VECTOR_IDS:
        x2, y2 = _radar_point(vid, 5).split(",")
        axes.append(f'<line x1="200" y1="200" x2="{x2}" y2="{y2}" stroke="#dcdcd6"/>')
    labels = [
        '<text x="200" y="46" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="12" fill="#4b4f57">V1</text>',
        '<text x="348" y="152" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="12" fill="#4b4f57">V2</text>',
        '<text x="290" y="332" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="12" fill="#4b4f57">V3</text>',
        '<text x="110" y="332" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="12" fill="#4b4f57">V4</text>',
        '<text x="52" y="152" text-anchor="middle" font-family="IBM Plex Mono,monospace" font-size="12" fill="#4b4f57">V5</text>',
    ]
    polys = []
    for i, rec in enumerate(records):
        color = SERIES_COLORS[i % len(SERIES_COLORS)]
        points = " ".join(
            _radar_point(vid, rec["vectors"][vid]["raw_score"]) for vid in VECTOR_IDS)
        polys.append(
            f'<polygon class="subject-poly" data-subject="{escape(rec["subject"])}" '
            f'points="{points}" fill="none" stroke="{color}" stroke-width="2"/>')

    legend = "".join(
        f'<span class="radar-key"><i style="background:{SERIES_COLORS[i % len(SERIES_COLORS)]}"></i>'
        f'{escape(rec["subject"])}</span>'
        for i, rec in enumerate(records))

    return (
        '<svg width="400" height="380" viewBox="0 0 400 380" role="img" aria-label="比較レーダーチャート">'
        + "".join(grid) + "".join(axes) + "".join(polys) + "".join(labels)
        + "</svg>"
        + f'<div class="radar-legend">{legend}</div>'
    )


def heatmap_color(score):
    """到達度0〜5を藍の単色スケール（#e8eaf6→#2b3a8f）に線形補間する。"""
    low, high = (232, 234, 246), (43, 58, 143)
    t = score / 5
    r, g, b = (round(low[i] + (high[i] - low[i]) * t) for i in range(3))
    return f"#{r:02x}{g:02x}{b:02x}"


def heatmap_html(records):
    """対象者×ベクトルの到達度ヒートマップ（HTMLテーブル）を返す。"""
    head = "".join(f'<th class="num">{vid}</th>' for vid in VECTOR_IDS)
    rows = []
    for rec in records:
        cells = []
        for vid in VECTOR_IDS:
            score = rec["vectors"][vid]["raw_score"]
            text_color = "#fff" if score >= 3 else "#1c1e22"
            cells.append(
                f'<td class="hm-cell" style="background:{heatmap_color(score)};color:{text_color}">{score}</td>')
        rows.append(
            f'<tr><td class="hm-subject">{escape(rec["subject"])}</td>{"".join(cells)}'
            f'<td class="num">{rec["total_score"]}</td></tr>')
    return (
        '<table class="data heatmap"><tr><th>対象者</th>' + head + '<th class="num">合計</th></tr>'
        + "".join(rows) + "</table>"
    )


def level_dist_html(records):
    """レベル分布の横バー表示を返す。パーセンタイル表記は使わない（§2非ゴール）。"""
    dist = level_distribution(records)
    max_count = max(dist.values()) if any(dist.values()) else 1
    rows = []
    for level in reversed(LEVELS):
        count = dist[level]
        width = round(count / max_count * 100, 1) if max_count else 0
        rows.append(
            f'<div class="dist-row">'
            f'<span class="dist-label">{level} {LEVEL_NAMES[level]}</span>'
            f'<span class="dist-track"><i style="width:{width}%;background:{LEVEL_BAND_COLORS[level]}"></i></span>'
            f'<span class="dist-count">{count}名</span>'
            f'</div>')
    return f'<div class="level-dist">{"".join(rows)}</div>'


def position_scale_html(records):
    """スコアスケール（L0〜L5横バー）上に各対象者のマーカーを置いた社内相対位置表示を返す。"""
    markers = "".join(
        f'<div class="marker" style="left:{rec["total_score"]:.1f}%">'
        f'<span class="m-name">{escape(rec["subject"])}</span>'
        f'<span class="m-score">{rec["total_score"]}</span></div>'
        for rec in records)
    bands = (
        '<div class="band" style="flex:25;background:#b9bcc4"><span class="lv">L0</span><span class="nm">Entry</span></div>'
        '<div class="band" style="flex:15;background:#9aa2b3"><span class="lv">L1</span><span class="nm">Foundation</span></div>'
        '<div class="band" style="flex:15;background:#7c88a6"><span class="lv">L2</span><span class="nm">App Builder</span></div>'
        '<div class="band" style="flex:15;background:#5d6d9c"><span class="lv">L3</span><span class="nm">Practitioner</span></div>'
        '<div class="band" style="flex:15;background:#404f96"><span class="lv">L4</span><span class="nm">Architect</span></div>'
        '<div class="band" style="flex:16;background:#2b3a8f"><span class="lv">L5</span><span class="nm">Principal</span></div>')
    ticks = (
        '<div class="ticks"><span style="flex:25">0</span><span style="flex:15">25</span>'
        '<span style="flex:15">40</span><span style="flex:15">55</span>'
        '<span style="flex:15">70</span><span style="flex:16">85&nbsp;&nbsp;—&nbsp;&nbsp;100</span></div>')
    return (
        f'<div class="score-scale"><div class="markers">{markers}</div>'
        f'<div class="bar">{bands}</div>{ticks}</div>'
    )


# ---------------------------------------------------------------------------
# ダッシュボードHTML組み立て（B3）
# デザイン言語は genai-skill-framework-v2.html を継承（藍単色・紙背景・IBM Plex・ダークモードなし）
# ---------------------------------------------------------------------------

CSS = """
:root{
  --paper:#f6f6f3; --surface:#ffffff;
  --ink:#1c1e22; --ink-soft:#4b4f57; --ink-faint:#8a8e96;
  --rule:#dcdcd6; --rule-strong:#b9b9b0;
  --accent:#2b3a8f; --accent-soft:#e8eaf6;
  --caution:#8f5a2b; --caution-soft:#f6efe6;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
  --sans:'IBM Plex Sans JP',-apple-system,'Hiragino Kaku Gothic ProN','Noto Sans JP',sans-serif;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:var(--sans);background:var(--paper);color:var(--ink);font-size:15px;line-height:1.85;-webkit-font-smoothing:antialiased}
main{max-width:960px;margin:0 auto;background:var(--surface);border-left:1px solid var(--rule);border-right:1px solid var(--rule)}
.page{padding:56px 56px 96px}
header.doc-head{border-bottom:2px solid var(--ink);padding-bottom:32px}
.doc-head .eyebrow{display:flex;justify-content:space-between;align-items:center;font-family:var(--mono);font-size:11px;letter-spacing:.16em;color:var(--ink-faint);margin-bottom:22px}
.doc-head .eyebrow .ver{color:var(--accent);border:1px solid var(--accent);padding:3px 10px;letter-spacing:.1em;font-weight:500}
h1{font-size:26px;font-weight:700;line-height:1.45;margin-bottom:6px}
.doc-head .subtitle{font-size:14px;color:var(--ink-soft)}
table.meta{width:100%;border-collapse:collapse;margin-top:28px;font-size:13px}
table.meta th,table.meta td{text-align:left;padding:9px 14px;border:1px solid var(--rule);vertical-align:top}
table.meta th{width:132px;background:var(--paper);font-weight:500;font-family:var(--mono);font-size:11px;letter-spacing:.06em;color:var(--ink-soft)}
section{padding-top:52px}
section + section{border-top:1px solid var(--rule);margin-top:52px}
h2{display:flex;align-items:baseline;gap:14px;font-size:20px;font-weight:700;margin-bottom:22px}
h2 .sec-n{font-family:var(--mono);font-size:13px;font-weight:600;color:var(--surface);background:var(--accent);padding:2px 9px;flex-shrink:0;transform:translateY(-2px)}
p{margin-bottom:14px}
table.data{width:100%;border-collapse:collapse;margin:14px 0 20px;font-size:13px;line-height:1.7}
table.data th{background:var(--ink);color:var(--surface);font-weight:500;text-align:left;padding:8px 12px;font-size:12px}
table.data td{padding:9px 12px;border:1px solid var(--rule);vertical-align:top}
table.data td.num{font-family:var(--mono);font-size:12px;white-space:nowrap;text-align:center}
.note{border-left:3px solid var(--accent);background:var(--accent-soft);padding:14px 18px;margin:16px 0 20px;font-size:13.5px;line-height:1.8}
.note.warn{border-left-color:var(--caution);background:var(--caution-soft)}
.note .note-label{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;font-weight:600;color:var(--accent);display:block;margin-bottom:4px}
.note.warn .note-label{color:var(--caution)}
/* 社内相対位置スケール（主役要素） */
.score-scale{margin:56px 0 8px;position:relative}
.score-scale .markers{position:relative;height:0}
.score-scale .marker{position:absolute;bottom:44px;transform:translateX(-50%);text-align:center;font-family:var(--mono);font-size:11px;font-weight:600;color:var(--accent);line-height:1.3;white-space:nowrap}
.score-scale .marker::after{content:"▼";display:block;font-size:9px}
.score-scale .bar{display:flex;height:44px;border:1px solid var(--rule-strong)}
.score-scale .band{position:relative;display:flex;flex-direction:column;justify-content:center;padding:0 8px;border-right:1px solid rgba(255,255,255,.55);color:#fff;overflow:hidden}
.score-scale .band:last-child{border-right:none}
.score-scale .band .lv{font-family:var(--mono);font-size:11px;font-weight:600;line-height:1.3}
.score-scale .band .nm{font-size:10px;line-height:1.3;white-space:nowrap;opacity:.92}
.score-scale .ticks{display:flex;font-family:var(--mono);font-size:10px;color:var(--ink-faint);margin-top:4px}
/* レーダー凡例 */
.radar-wrap{display:flex;gap:32px;align-items:flex-start;flex-wrap:wrap;margin:20px 0}
.radar-legend{display:flex;flex-direction:column;gap:6px;font-size:13px;min-width:200px}
.radar-key{display:flex;align-items:center;gap:8px}
.radar-key i{display:inline-block;width:18px;height:3px;flex-shrink:0}
/* ヒートマップ */
table.heatmap td.hm-cell{font-family:var(--mono);font-size:12px;text-align:center;width:56px}
table.heatmap td.hm-subject{font-weight:600}
/* レベル基準解説（控えめな表） */
table.lv-legend{width:100%;border-collapse:collapse;margin:22px 0 8px;font-size:12px;line-height:1.7;color:var(--ink-soft)}
table.lv-legend th{background:var(--paper);color:var(--ink-faint);font-weight:500;text-align:left;padding:5px 10px;font-size:11px;font-family:var(--mono);letter-spacing:.06em;border:1px solid var(--rule)}
table.lv-legend td{padding:5px 10px;border:1px solid var(--rule);vertical-align:top}
table.lv-legend td.lv-range,table.lv-legend td.lv-id{font-family:var(--mono);font-size:11px;white-space:nowrap}
table.lv-legend td.lv-id{color:var(--accent);font-weight:600}
table.lv-legend td.lv-name{white-space:nowrap}
table.lv-legend tr.current td{background:var(--accent-soft)}
table.lv-legend tr.current td:first-child{border-left:3px solid var(--accent)}
/* レベル分布 */
.level-dist{margin:14px 0 20px}
.dist-row{display:flex;align-items:center;gap:12px;margin-bottom:6px}
.dist-label{font-family:var(--mono);font-size:12px;width:150px;flex-shrink:0;color:var(--ink-soft)}
.dist-track{flex:1;height:18px;background:var(--paper);border:1px solid var(--rule)}
.dist-track i{display:block;height:100%}
.dist-count{font-family:var(--mono);font-size:12px;width:44px;text-align:right;flex-shrink:0}
@media print{
  body{background:#fff}
  main{border:none}
  .page{padding:0}
  section{break-inside:avoid-page}
}
"""

FONT_LINKS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+JP:wght@400;500;600;700'
    '&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">'
)


def build_dashboard(records, errors):
    """集計結果からダッシュボードHTML全体を組み立てて返す。

    records は select_latest 適用済みを想定。errors は load_results のエラーメッセージ。
    """
    dates = [r["assessment_date"] for r in records]
    period = f"{min(dates)} 〜 {max(dates)}" if dates else "—"

    warn_section = ""
    if errors:
        items = "<br>".join(escape(e) for e in errors)
        warn_section = (
            '<div class="note warn"><span class="note-label">読み込みエラー</span>'
            f'以下のファイルは集計から除外した。修正して再実行すること。<br>{items}</div>')

    if not records:
        body = (
            warn_section
            + '<div class="note warn"><span class="note-label">NO DATA</span>'
              '結果ファイルがありません。個人採点スキルで診断を実施し、'
              'JSONを結果フォルダに配置してから再実行すること。</div>')
    else:
        body = warn_section + (
            '<section><h2><span class="sec-n">1</span>社内相対位置</h2>'
            '<p>各対象者の合計点（確定値）をレベルスケール上に示す。'
            '「Top X%」等の相対表記は校正完了まで使用しない（フレームワーク4章）。</p>'
            + position_scale_html(records)
            + level_legend_html()
            + '</section>'
            '<section><h2><span class="sec-n">2</span>比較レーダーチャート</h2>'
            '<p>ベクトル別到達度（0〜5）の重ね描き。外周＝到達度5。各軸（V1〜V5）の内容は下表を参照。</p>'
            '<div class="radar-wrap">' + radar_svg(records) + '</div>'
            + vector_legend_html() + '</section>'
            '<section><h2><span class="sec-n">3</span>ベクトル別ヒートマップ</h2>'
            '<p>到達度が高いほど濃い藍で示す。育成優先度の判断には最も低いベクトルを参照すること。</p>'
            + heatmap_html(records)
            + '</section>'
            '<section><h2><span class="sec-n">4</span>レベル分布</h2>'
            + level_dist_html(records)
            + '</section>')

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AIスキル診断 グループダッシュボード</title>
{FONT_LINKS}
<style>{CSS}</style>
</head>
<body>
<main>
<div class="page">
<header class="doc-head">
  <div class="eyebrow">
    <span>SKILL ASSESSMENT DASHBOARD — ARCHITECT TRACK</span>
    <span class="ver">FW v2.0</span>
  </div>
  <h1>グループダッシュボード</h1>
  <div class="subtitle">生成AI技術者スキル評価フレームワーク v2.0 — チーム集計</div>
  <table class="meta">
    <tr><th>SUBJECTS</th><td>{len(records)}名（同一対象者は評価日が最新の1件のみを採用）</td></tr>
    <tr><th>PERIOD</th><td>{escape(period)}</td></tr>
    <tr><th>SOURCE</th><td>診断結果JSON（重み付け合計・レベル判定は確定値を再利用。再計算しない）</td></tr>
  </table>
</header>
{body}
<p style="margin-top:40px;padding-top:20px;border-top:1px solid var(--rule);font-family:var(--mono);font-size:11px;color:var(--ink-faint);letter-spacing:.08em">
FW-GENAI-SKILL v2.0 ／ 結果は育成・配置の参考情報であり、昇給・査定に直接連動させない（HR運用原則）
</p>
</div>
</main>
</body>
</html>
"""


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    base = Path(__file__).resolve().parent.parent
    results_dir = Path(argv[0]) if len(argv) >= 1 else base / "data" / "results"
    output_path = Path(argv[1]) if len(argv) >= 2 else base / "outputs" / "dashboard.html"

    records, errors = load_results(results_dir)
    latest = select_latest(records)

    for message in errors:
        print(f"[警告] {message}", file=sys.stderr)

    html = build_dashboard(latest, errors)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    print(f"読み込み: {len(records)}件（対象者 {len(latest)}名） / エラー {len(errors)}件")
    print(f"出力: {output_path}")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
