"""
merge_dicts.py
複数の IME辞書txt を統合・整形して1つに出力するスクリプト。

使い方:
    python merge_dicts.py
    → GUIでtxtファイルを複数選択 → merged_dict.txt が出力される

オプション:
    python merge_dicts.py --min-score 3 --output my_dict.txt
"""

import os
import re
import argparse
from collections import defaultdict
from tkinter import filedialog, Tk

# ── ひらがな・カタカナ判定 ────────────────────────────────
HIRAGANA = re.compile(r'^[ぁ-ん・ー\s]+$')
KATAKANA = re.compile(r'^[ァ-ヶ・ー\s]+$')


def load_ime_txt(path: str) -> dict:
    """よみ\t単語\t品詞 形式のtxtを読み込む（カウントは1固定）"""
    entries = defaultdict(int)
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            yomi = parts[0].strip()
            word = parts[1].strip()
            if yomi and word:
                entries[(yomi, word)] += 1
    return entries


def is_garbage(yomi: str, word: str) -> bool:
    """除外すべきゴミ語の判定"""
    # 1文字以下
    if len(word) < 2:
        return True
    # 記号・数字・空白のみ
    if re.fullmatch(r'[\d\s\W]+', word):
        return True
    # 読みに漢字が残っている（GiNZAが読みを取得できなかった語）
    if re.search(r'[一-龥]', yomi):
        return True
    # 読みが空 or ひらがな・カタカナ以外
    if not yomi:
        return True
    if not (HIRAGANA.match(yomi) or KATAKANA.match(yomi)):
        return True
    # 読みと表記が完全一致（変換しても意味がない）
    if yomi == word:
        return True
    # 読みが極端に短い（1文字）
    if len(yomi) < 2:
        return True
    return False


def merge_and_clean(
        txt_files: list,
        output_file: str,
        min_score: int = 2
):
    """複数のtxtを統合・整形して出力"""

    # ── 1. 全ファイルを読み込んで出現回数を合算
    merged = defaultdict(int)
    for path in txt_files:
        print(f"  読み込み中: {os.path.basename(path)}")
        for (yomi, word), count in load_ime_txt(path).items():
            merged[(yomi, word)] += count

    total_before = len(merged)

    # ── 2. ゴミ語除去
    after_garbage = {
        k: v for k, v in merged.items()
        if not is_garbage(k[0], k[1])
    }

    # ── 3. 頻度フィルタ（複数ファイルで精度向上の核心）
    after_freq = {
        k: v for k, v in after_garbage.items()
        if v >= min_score
    }

    # ── 4. 頻度の高い順にソート
    sorted_entries = sorted(after_freq.items(), key=lambda x: -x[1])

    # ── 5. 出力
    with open(output_file, "w", encoding="utf-8", newline="\n") as f:
        for (yomi, word), _ in sorted_entries:
            f.write(f"{yomi}\t{word}\t固有名詞\n")

    # ── 6. レポート
    removed_garbage = total_before - len(after_garbage)
    removed_freq    = len(after_garbage) - len(after_freq)

    print(f"\n{'─'*44}")
    print(f"  統合前の総エントリ数   : {total_before:>6}")
    print(f"  ゴミ語除去             : -{removed_garbage:>5}  (記号・読み異常・1文字など)")
    print(f"  低頻度フィルタ (<{min_score}回) : -{removed_freq:>5}  (複数ファイル合算後)")
    print(f"  ✅ 最終エントリ数       : {len(after_freq):>6}")
    print(f"{'─'*44}")
    print(f"\n  出力先: {os.path.abspath(output_file)}")

    if sorted_entries:
        print("\n  ── 上位20件プレビュー ──")
        for (yomi, word), score in sorted_entries[:20]:
            print(f"    {yomi:<20} {word:<20} ({score}回)")

    return len(after_freq)


# ── CLI オプション ────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="IME辞書txtを統合・整形するツール")
    p.add_argument("--min-score", type=int, default=2,
                   help="最低出現回数（デフォルト: 2）")
    p.add_argument("--output", type=str, default="merged_dict.txt",
                   help="出力ファイル名（デフォルト: merged_dict.txt）")
    p.add_argument("files", nargs="*",
                   help="統合するtxtファイル（省略時はGUIで選択）")
    return p.parse_args()


# ── メイン ────────────────────────────────────────────────
if __name__ == "__main__":
    args = parse_args()

    # ファイルが引数で渡されなければGUIで選択
    if args.files:
        files = args.files
    else:
        root = Tk()
        root.withdraw()
        files = list(filedialog.askopenfilenames(
            title="統合するtxtファイルを選択（複数可）",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        ))
        root.destroy()

    if not files:
        print("ファイルが選択されませんでした。終了します。")
        exit(0)

    print(f"\n{len(files)}ファイルを統合します（最低出現回数: {args.min_score}回）\n")
    merge_and_clean(files, args.output, min_score=args.min_score)