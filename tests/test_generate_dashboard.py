# 集計スクリプト（scripts/generate_dashboard.py）の単体テスト
# 参照仕様: docs/simple-spec.md §4.2・§5・§7
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import generate_dashboard as gd


def make_result(subject="yamada-taro", date="2026-07-18", total=62.0, level="L3",
                raw_scores=(3, 3, 3, 2, 2), grades=("A", "A", "B", "B", "C")):
    """SKILL.md のJSONスキーマに沿ったダミー結果を作る。"""
    weights = {"V1": 25, "V2": 25, "V3": 20, "V4": 15, "V5": 15}
    names = {
        "V1": "Context Engineering",
        "V2": "Agentic System Design",
        "V3": "Knowledge Architecture",
        "V4": "Evaluation & Observability",
        "V5": "Production & LLMOps",
    }
    vectors = {}
    for i, vid in enumerate(["V1", "V2", "V3", "V4", "V5"]):
        vectors[vid] = {
            "name": names[vid],
            "raw_score": raw_scores[i],
            "weight": weights[vid],
            "weighted_score": round(raw_scores[i] * weights[vid] / 5, 1),
            "evidence_grade": grades[i],
            "freshness": "within_12m",
            "freshness_exception": {"applied": False, "reason": ""},
            "mandatory_checks": None,
            "deep_dive_done": False,
            "rationale": "test",
            "evidence": ["https://example.com"],
        }
    return {
        "framework_version": "2.0",
        "subject": subject,
        "assessment_date": date,
        "evaluator_type": "self",
        "total_score": total,
        "level": level,
        "level_name": "Systems Practitioner",
        "vectors": vectors,
        "notes": "",
    }


def write_json(dir_path, filename, data):
    path = dir_path / filename
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


# ---------- load_results: 正常系 ----------

class TestLoadResults:
    def test_loads_valid_files(self, tmp_path):
        write_json(tmp_path, "yamada-taro_2026-07-18.json", make_result())
        write_json(tmp_path, "sato-hanako_2026-07-18.json",
                   make_result(subject="sato-hanako", total=75.0, level="L4"))

        records, errors = gd.load_results(tmp_path)

        assert len(records) == 2
        assert errors == []
        subjects = {r["subject"] for r in records}
        assert subjects == {"yamada-taro", "sato-hanako"}

    def test_ignores_non_json_files(self, tmp_path):
        write_json(tmp_path, "yamada-taro_2026-07-18.json", make_result())
        (tmp_path / "memo.txt").write_text("not json", encoding="utf-8")

        records, errors = gd.load_results(tmp_path)

        assert len(records) == 1
        assert errors == []

    def test_empty_dir_returns_empty(self, tmp_path):
        records, errors = gd.load_results(tmp_path)
        assert records == []
        assert errors == []

    def test_missing_dir_is_error(self, tmp_path):
        records, errors = gd.load_results(tmp_path / "nonexistent")
        assert records == []
        assert len(errors) == 1


# ---------- load_results: 異常系（§5: JSON欠損・形式不正時のエラー表示） ----------

class TestLoadResultsErrors:
    def test_broken_json_is_reported_not_raised(self, tmp_path):
        write_json(tmp_path, "ok_2026-07-18.json", make_result(subject="ok"))
        (tmp_path / "broken_2026-07-18.json").write_text("{not valid json", encoding="utf-8")

        records, errors = gd.load_results(tmp_path)

        assert len(records) == 1
        assert len(errors) == 1
        assert "broken_2026-07-18.json" in errors[0]

    def test_missing_required_field_is_reported(self, tmp_path):
        bad = make_result(subject="bad")
        del bad["total_score"]
        write_json(tmp_path, "bad_2026-07-18.json", bad)

        records, errors = gd.load_results(tmp_path)

        assert records == []
        assert len(errors) == 1
        assert "total_score" in errors[0]

    def test_missing_vector_is_reported(self, tmp_path):
        bad = make_result(subject="bad")
        del bad["vectors"]["V3"]
        write_json(tmp_path, "bad_2026-07-18.json", bad)

        records, errors = gd.load_results(tmp_path)

        assert records == []
        assert len(errors) == 1
        assert "V3" in errors[0]

    def test_missing_vector_field_is_reported(self, tmp_path):
        bad = make_result(subject="bad")
        del bad["vectors"]["V2"]["raw_score"]
        write_json(tmp_path, "bad_2026-07-18.json", bad)

        records, errors = gd.load_results(tmp_path)

        assert records == []
        assert len(errors) == 1
        assert "raw_score" in errors[0]

    # 型不正はクラッシュではなくエラー報告で除外する（コードレビュー指摘 2026-07-18）

    def test_string_raw_score_is_reported(self, tmp_path):
        bad = make_result(subject="bad")
        bad["vectors"]["V1"]["raw_score"] = "3"
        write_json(tmp_path, "bad_2026-07-18.json", bad)

        records, errors = gd.load_results(tmp_path)

        assert records == []
        assert len(errors) == 1 and "raw_score" in errors[0]

    def test_out_of_range_raw_score_is_reported(self, tmp_path):
        bad = make_result(subject="bad")
        bad["vectors"]["V1"]["raw_score"] = 9
        write_json(tmp_path, "bad_2026-07-18.json", bad)

        records, errors = gd.load_results(tmp_path)

        assert records == []
        assert len(errors) == 1 and "raw_score" in errors[0]

    def test_string_total_score_is_reported(self, tmp_path):
        bad = make_result(subject="bad")
        bad["total_score"] = "62"
        write_json(tmp_path, "bad_2026-07-18.json", bad)

        records, errors = gd.load_results(tmp_path)

        assert records == []
        assert len(errors) == 1 and "total_score" in errors[0]

    def test_non_string_subject_is_reported(self, tmp_path):
        bad = make_result(subject="bad")
        bad["subject"] = 123
        write_json(tmp_path, "bad_2026-07-18.json", bad)

        records, errors = gd.load_results(tmp_path)

        assert records == []
        assert len(errors) == 1 and "subject" in errors[0]

    def test_non_dict_vectors_is_reported(self, tmp_path):
        bad = make_result(subject="bad")
        bad["vectors"] = "broken"
        write_json(tmp_path, "bad_2026-07-18.json", bad)

        records, errors = gd.load_results(tmp_path)

        assert records == []
        assert len(errors) == 1 and "vectors" in errors[0]


# ---------- select_latest: 同一対象者は評価日最新の1件のみ（§4.2） ----------

class TestSelectLatest:
    def test_latest_per_subject(self):
        records = [
            make_result(subject="yamada-taro", date="2026-04-01", total=55.0, level="L3"),
            make_result(subject="yamada-taro", date="2026-07-18", total=62.0, level="L3"),
            make_result(subject="sato-hanako", date="2026-07-01", total=75.0, level="L4"),
        ]
        latest = gd.select_latest(records)

        assert len(latest) == 2
        yamada = next(r for r in latest if r["subject"] == "yamada-taro")
        assert yamada["assessment_date"] == "2026-07-18"
        assert yamada["total_score"] == 62.0

    def test_single_record_kept(self):
        records = [make_result()]
        assert gd.select_latest(records) == records

    def test_empty_input(self):
        assert gd.select_latest([]) == []

    def test_result_sorted_by_score_desc(self):
        records = [
            make_result(subject="low", total=30.0, level="L1"),
            make_result(subject="high", total=80.0, level="L4"),
        ]
        latest = gd.select_latest(records)
        assert [r["subject"] for r in latest] == ["high", "low"]


# ---------- 集計: レベル分布（§4.2） ----------

class TestLevelDistribution:
    def test_counts_all_levels(self):
        records = [
            make_result(subject="a", total=80.0, level="L4"),
            make_result(subject="b", total=75.0, level="L4"),
            make_result(subject="c", total=30.0, level="L1"),
        ]
        dist = gd.level_distribution(records)

        assert dist == {"L0": 0, "L1": 1, "L2": 0, "L3": 0, "L4": 2, "L5": 0}

    def test_empty(self):
        assert gd.level_distribution([]) == {
            "L0": 0, "L1": 0, "L2": 0, "L3": 0, "L4": 0, "L5": 0}


# ---------- B2: 比較レーダーチャートSVG（§4.2・§6） ----------

class TestRadarSvg:
    def test_polygon_per_subject(self):
        records = [
            make_result(subject="a", total=80.0),
            make_result(subject="b", total=60.0),
        ]
        svg = gd.radar_svg(records)

        assert svg.count('class="subject-poly"') == 2
        assert "a" in svg and "b" in svg

    def test_polygon_points_math(self):
        # V1〜V5 全て到達度5 → 各軸の外周端点になる
        records = [make_result(subject="max", raw_scores=(5, 5, 5, 5, 5))]
        svg = gd.radar_svg(records)

        assert "200.0,60.0" in svg      # V1: 200, 200-140
        assert "333.1,156.7" in svg     # V2: 200+140*0.951, 200-140*0.309
        assert "282.3,313.3" in svg     # V3
        assert "117.7,313.3" in svg     # V4
        assert "66.9,156.7" in svg      # V5

    def test_zero_score_at_center(self):
        records = [make_result(subject="zero", raw_scores=(0, 0, 0, 0, 0))]
        svg = gd.radar_svg(records)
        assert "200.0,200.0" in svg

    def test_no_gradient(self):
        svg = gd.radar_svg([make_result()])
        assert "gradient" not in svg.lower()


# ---------- B2: ヒートマップ（§4.2・§6） ----------

class TestHeatmap:
    def test_contains_subjects_and_vectors(self):
        records = [
            make_result(subject="a", raw_scores=(5, 4, 3, 2, 1)),
            make_result(subject="b", raw_scores=(0, 1, 2, 3, 4)),
        ]
        html = gd.heatmap_html(records)

        assert "a" in html and "b" in html
        for vid in ["V1", "V2", "V3", "V4", "V5"]:
            assert vid in html
        # 到達度がセルに表示される
        assert html.count("<td") >= 10

    def test_color_scale_is_single_hue(self):
        # 藍単色のスケール: 0点は accent-soft、5点は accent
        assert gd.heatmap_color(0) == "#e8eaf6"
        assert gd.heatmap_color(5) == "#2b3a8f"

    def test_high_score_uses_light_text(self):
        html = gd.heatmap_html([make_result(subject="a", raw_scores=(5, 5, 5, 5, 5))])
        assert "#fff" in html


# ---------- B2: レベル分布バー（§4.2） ----------

class TestLevelDistHtml:
    def test_shows_counts(self):
        records = [
            make_result(subject="a", level="L4"),
            make_result(subject="b", level="L4"),
            make_result(subject="c", level="L1"),
        ]
        html = gd.level_dist_html(records)

        for level in ["L0", "L1", "L2", "L3", "L4", "L5"]:
            assert level in html
        assert "2名" in html and "1名" in html

    def test_no_percentile(self):
        # パーセンタイル表示は非ゴール（§2）
        html = gd.level_dist_html([make_result()])
        assert "%tile" not in html and "Top" not in html


# ---------- B2: 社内相対位置スケール（§4.2） ----------

class TestPositionScale:
    def test_marker_per_subject(self):
        records = [
            make_result(subject="a", total=80.0),
            make_result(subject="b", total=30.0),
        ]
        html = gd.position_scale_html(records)

        assert html.count('class="marker"') == 2
        assert "left:80.0%" in html
        assert "left:30.0%" in html
        assert "a" in html and "b" in html


# ---------- B3: ダッシュボードHTML組み立て（§4.2・§6） ----------

class TestBuildDashboard:
    def test_contains_all_sections(self):
        records = [
            make_result(subject="yamada-taro", total=62.0, level="L3"),
            make_result(subject="sato-hanako", total=75.0, level="L4"),
        ]
        html = gd.build_dashboard(records, [])

        assert html.startswith("<!DOCTYPE html>")
        assert "社内相対位置" in html
        assert "比較レーダー" in html
        assert "ヒートマップ" in html
        assert "レベル分布" in html
        assert "yamada-taro" in html and "sato-hanako" in html
        assert "IBM Plex" in html
        assert "2名" in html  # 対象者数

    def test_error_warnings_displayed(self):
        html = gd.build_dashboard([make_result()], ["bad.json: 壊れています"])
        assert "bad.json" in html
        assert "note warn" in html

    def test_no_warning_section_without_errors(self):
        html = gd.build_dashboard([make_result()], [])
        assert "読み込みエラー" not in html

    def test_empty_records_message(self):
        html = gd.build_dashboard([], [])
        assert "結果ファイルがありません" in html

    def test_subject_is_escaped(self):
        rec = make_result(subject="<script>alert(1)</script>")
        html = gd.build_dashboard([rec], [])
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

    def test_no_gradient_no_darkmode(self):
        html = gd.build_dashboard([make_result()], [])
        assert "linear-gradient" not in html
        assert "prefers-color-scheme" not in html

    def test_vector_names_explained(self):
        # V1〜V5の記号だけでなくベクトル名の説明が含まれる（2026-07-18 ユーザー指摘）
        html = gd.build_dashboard([make_result()], [])
        for name in ["Context Engineering", "Agentic System Design",
                     "Knowledge Architecture", "Evaluation", "Production"]:
            assert name in html
        assert "コンテキスト設計力" in html

    def test_level_criteria_explained(self):
        # L0〜L5の評価基準解説が含まれる（2026-07-18 ユーザー指摘）
        html = gd.build_dashboard([make_result()], [])
        assert "Principal Architect" in html
        assert "評価可能な実績が未蓄積" in html
        assert "85〜100" in html and "0〜24" in html


# ---------- B3: main（ファイル出力・終了コード） ----------

class TestMain:
    def test_writes_dashboard_file(self, tmp_path, capsys):
        results = tmp_path / "results"
        results.mkdir()
        write_json(results, "yamada-taro_2026-07-18.json", make_result())
        out = tmp_path / "out" / "dashboard.html"

        code = gd.main([str(results), str(out)])

        assert code == 0
        assert out.exists()
        assert "yamada-taro" in out.read_text(encoding="utf-8")

    def test_exit_code_1_with_errors_but_still_writes(self, tmp_path):
        results = tmp_path / "results"
        results.mkdir()
        write_json(results, "ok_2026-07-18.json", make_result(subject="ok"))
        (results / "broken_2026-01-01.json").write_text("{bad", encoding="utf-8")
        out = tmp_path / "dashboard.html"

        code = gd.main([str(results), str(out)])

        assert code == 1
        assert out.exists()
        html = out.read_text(encoding="utf-8")
        assert "ok" in html
        assert "broken_2026-01-01.json" in html
