"""
generate.py - Claude APIを使って各サービスのSEO記事を生成する
"""
import os
import sys
import yaml
import random
import anthropic
from datetime import datetime
from pathlib import Path

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def pick_keyword(config, service_name):
    """キーワードをローテーションで選ぶ（毎日違うものを選択）"""
    today = datetime.now()
    day_of_year = today.timetuple().tm_yday

    if service_name == "localnavi":
        return pick_localnavi_keyword(config, day_of_year)
    elif service_name == "nishiki":
        return pick_nishiki_keyword(config, day_of_year)
    else:
        # キーワードリストを全部フラットに並べてローテーション
        all_keywords = []
        kw_dict = config.get("keywords", {})
        for group in kw_dict.values():
            if isinstance(group, list):
                all_keywords.extend(group)
        idx = day_of_year % len(all_keywords)
        return all_keywords[idx], {}

def pick_localnavi_keyword(config, day_of_year):
    """LocalNavi用：業種×地域のマトリクスからキーワードを生成"""
    categories = config.get("categories", {})
    active_cats = {k: v for k, v in categories.items() if v.get("active", True)}

    # アクティブな業種をローテーション
    cat_keys = list(active_cats.keys())
    cat_key = cat_keys[day_of_year % len(cat_keys)]
    cat = active_cats[cat_key]

    regions = cat.get("regions", [])
    templates = cat.get("article_templates", [])
    work_types = cat.get("work_types", cat.get("specialties", cat.get("genres", [""])))

    region = regions[day_of_year % len(regions)]
    work_type = work_types[(day_of_year // len(regions)) % len(work_types)]
    template = templates[day_of_year % len(templates)]

    keyword = template.format(
        region=region,
        work_type=work_type,
        specialty=work_type,
        genre=work_type,
        year=datetime.now().year,
        N=5
    )
    return keyword, {
        "category": cat.get("label", cat_key),
        "region": region,
        "posts_dir": cat.get("posts_dir", "_posts")
    }

def pick_nishiki_keyword(config, day_of_year):
    """NISHIKI用：日英・軸A/Bをローテーション"""
    # 日本語軸A → 日本語軸B → 英語軸A の順でローテーション
    slots = [
        ("axis_a_ja", "ja", "A"),
        ("axis_b_ja", "ja", "B"),
        ("axis_a_en", "en", "A"),
    ]
    slot_key, lang, axis = slots[day_of_year % len(slots)]
    kw_list = config["keywords"].get(slot_key, [])
    keyword = kw_list[day_of_year % len(kw_list)]
    return keyword, {"language": lang, "axis": axis}

def generate_article(service_name, keyword, prompt_template, extra_params=None):
    """Claude APIで記事を生成"""
    extra_params = extra_params or {}
    year = datetime.now().year

    # プロンプトに変数を埋め込む
    prompt = prompt_template.replace("{keyword}", keyword)
    prompt = prompt.replace("{year}", str(year))
    for k, v in extra_params.items():
        prompt = prompt.replace("{" + k + "}", str(v))

    print(f"[{service_name}] 記事生成中: {keyword}")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

def parse_article(raw_text):
    """生成されたテキストからTITLE・META・CONTENTを抽出"""
    lines = raw_text.strip().split("\n")
    title = ""
    meta = ""
    lang = "ja"
    content_lines = []
    in_content = False

    for line in lines:
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        elif line.startswith("META_DESCRIPTION:"):
            meta = line.replace("META_DESCRIPTION:", "").strip()
        elif line.startswith("LANG:"):
            lang = line.replace("LANG:", "").strip()
        elif line.startswith("CONTENT:"):
            in_content = True
        elif in_content and line.strip() not in ("---", ""):
            content_lines.append(line)
        elif in_content and line.strip() == "---":
            break

    content = "\n".join(content_lines).strip()
    return {"title": title, "meta": meta, "lang": lang, "content": content}

def run_service(service_name, config_path, prompt_path):
    """1サービス分の記事生成を実行し、結果を返す"""
    config = load_yaml(config_path)
    prompt_template = load_prompt(prompt_path)

    keyword, extra = pick_keyword(config, service_name)
    raw = generate_article(service_name, keyword, prompt_template, extra)
    article = parse_article(raw)
    article["keyword"] = keyword
    article["extra"] = extra
    article["config"] = config

    print(f"[{service_name}] 生成完了: {article['title']}")
    return article

# ========== メイン ==========
if __name__ == "__main__":
    base = Path(__file__).parent.parent

    services = {
        "fromzero": ("config/fromzero.yaml", "prompts/fromzero_prompt.md"),
        "mimosa":   ("config/mimosa.yaml",   "prompts/mimosa_prompt.md"),
        "localnavi":("config/localnavi.yaml","prompts/localnavi_prompt.md"),
        "nishiki":  ("config/nishiki.yaml",  "prompts/nishiki_prompt.md"),
    }

    # 引数でサービスを絞れる（例: python generate.py fromzero）
    target = sys.argv[1] if len(sys.argv) > 1 else None

    results = {}
    for name, (cfg, pmt) in services.items():
        if target and name != target:
            continue
        try:
            results[name] = run_service(name, base / cfg, base / pmt)
        except Exception as e:
            print(f"[{name}] エラー: {e}")
            results[name] = None

    # 結果をJSONで出力（後続スクリプトが読み込む）
    import json
    output_path = base / "generated_articles.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 生成完了 → {output_path}")
