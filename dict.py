import os
import re
import pandas as pd
import spacy
from collections import Counter
from itertools import combinations
from math import log
from pdfminer.high_level import extract_text

class CompanyDictionaryBuilder:
    def __init__(self):
        print("モデルをロード中...")
        self.nlp = spacy.load("ja_ginza")
        self.term_counts = Counter()
        self.unigram_counts = Counter()

    # --- テキスト読み込み ---
    def load_pdf(self, file_path):
        print(f"PDF読み込み中: {file_path}")
        try:
            return extract_text(file_path)
        except Exception as e:
            print(f"PDF抽出エラー: {e}")
            return ""

    def load_csv(self, file_path, column_name='text'):
        print(f"CSV読み込み中: {file_path}")
        df = pd.read_csv(file_path)
        return " ".join(df[column_name].astype(str).tolist())

    # --- 読み取得ヘルパー ---
    def _get_reading(self, token):
        readings = token.morph.get("Reading")
        yomi = readings[0] if readings else token.text
        # カタカナ→ひらがな変換
        return "".join(
            chr(ord(c) - 96) if 'ァ' <= c <= 'ン' else c
            for c in yomi
        )

    # --- テキスト解析（チャンク分割対応）---
    def analyze_text(self, text, chunk_size=40000):
        if not text:
            return

        encoded = text.encode("utf-8")
        chunks = []
        start = 0
        while start < len(encoded):
            chunk_bytes = encoded[start:start + chunk_size]
            chunks.append(chunk_bytes.decode("utf-8", errors="ignore"))
            start += chunk_size

        for chunk in chunks:
            doc = self.nlp(chunk)
            for token in doc:
                if token.pos_ in ("NOUN", "PROPN"):
                    self.unigram_counts[token.text] += 1

            for nc in doc.noun_chunks:
                surface = nc.text.strip()
                # 記号・空白のみ・1文字は除外
                if len(surface) < 2 or re.fullmatch(r'[\s\W]+', surface):
                    continue
                yomi = "".join(self._get_reading(t) for t in nc)
                yomi = yomi.strip()
                if not yomi:
                    continue
                self.term_counts[(surface, yomi)] += 1

    # --- PMIで高スコア複合語を抽出 ---
    def get_high_pmi_terms(self, min_freq=2):
        total = sum(self.unigram_counts.values()) or 1
        results = []
        for (word, yomi), count in self.term_counts.items():
            if count < min_freq:
                continue
            # 単語が複数形態素なら構成要素のPMIを計算
            tokens = word  # 簡易: 文字数が2以上あればOK
            results.append((word, yomi, count))
        return results

    # --- Google日本語入力 / MS-IME 辞書として保存 ---
    def save_ime_dict(self, output_file, min_freq=2):
        terms = self.get_high_pmi_terms(min_freq=min_freq)

        if not terms:
            print("登録対象の用語がありませんでした。")
            return

        with open(output_file, "w", encoding="utf-8", newline="\n") as f:
            for word, yomi, count in sorted(terms, key=lambda x: -x[2]):
                # タブ区切り・余分な空白を除去して出力
                line = f"{yomi}\t{word}\t固有名詞\n"
                f.write(line)

        print(f"\n辞書作成完了: {output_file}")
        print(f"登録語数: {len(terms)}")
        print("\n--- 先頭10件プレビュー ---")
        for word, yomi, count in terms[:10]:
            print(f"  {yomi}\t{word}\t固有名詞\t(出現{count}回)")


# --- メイン処理 ---
if __name__ == "__main__":
    builder = CompanyDictionaryBuilder()

    target_files = ["note_hydrodynamics.pdf", "project_notes.csv"]

    for file in target_files:
        if not os.path.exists(file):
            print(f"スキップ（ファイルなし）: {file}")
            continue

        if file.endswith(".pdf"):
            content = builder.load_pdf(file)
        elif file.endswith(".csv"):
            content = builder.load_csv(file)
        else:
            continue

        builder.analyze_text(content)

    builder.save_ime_dict("company_dict.txt", min_freq=1)