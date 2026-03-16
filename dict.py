import os
import pandas as pd
import spacy
from collections import Counter
from pdfminer.high_level import extract_text

class CompanyDictionaryBuilder:
    def __init__(self):
        print("モデルをロード中（初回は時間がかかります）...")
        self.nlp = spacy.load("ja_ginza")
        self.term_counts = Counter()

    # --- 1. データ読み込みメソッド群 ---
    def load_pdf(self, file_path):
        """PDFからテキストを抽出する"""
        print(f"PDF読み込み中: {file_path}")
        try:
            text = extract_text(file_path)
            return text
        except Exception as e:
            print(f"PDF抽出エラー: {e}")
            return ""

    def load_csv(self, file_path, column_name='text'):
        """CSVの特定カラムからテキストを抽出する"""
        print(f"CSV読み込み中: {file_path}")
        df = pd.read_csv(file_path)
        return " ".join(df[column_name].astype(str).tolist())

    def analyze_text(self, text, chunk_size=40000):
        """テキストをチャンクに分割して解析する"""
        if not text: return

        # テキストをバイト数ベースで分割
        encoded = text.encode("utf-8")
        chunks = []
        start = 0
        while start < len(encoded):
            end = start + chunk_size
            # 文字の途中で切らないよう調整
            chunk_bytes = encoded[start:end]
            chunks.append(chunk_bytes.decode("utf-8", errors="ignore"))
            start = end

        for chunk in chunks:
            doc = self.nlp(chunk)
            for nc in doc.noun_chunks:
                if len(nc.text) >= 2:
                    yomi = "".join([
                        token.morph.get("Reading")[0] if token.morph.get("Reading") else token.text
                        for token in nc
                    ])
                    yomi_hira = "".join([
                        chr(ord(c) - 96) if ('ァ' <= c <= 'ン') else c
                        for c in yomi
                    ])
                    self.term_counts[(nc.text, yomi_hira)] += 1
    # # --- 2. 解析メソッド ---
    # def analyze_text(self, text):
    #     """テキストから名詞句を抽出してカウントする"""
    #     if not text: return
    #
    #     doc = self.nlp(text)
    #     for chunk in doc.noun_chunks:
    #         if len(chunk.text) >= 2:
    #             # 読みの取得とひらがな変換
    #             yomi = "".join([token._.reading for token in chunk])
    #             yomi_hira = "".join([chr(ord(c) - 96) if ('ァ' <= c <= 'ン') else c for c in yomi])
    #
    #             # (単語, 読み) のタプルでカウント
    #             self.term_counts[(chunk.text, yomi_hira)] += 1

    # --- 3. 保存メソッド ---
    def save_google_ime_dict(self, output_file, min_freq=2):
        """Google日本語入力形式で保存する"""
        with open(output_file, "w", encoding="utf-8") as f:
            for (word, yomi), count in self.term_counts.items():
                if count >= min_freq:
                    # 優先度を上げるために「固有名詞」として出力
                    f.write(f"{yomi}\t{word}\t固有名詞\n")
        print(f"辞書作成完了: {output_file} (登録語数: {len(self.term_counts)})")

# --- メイン処理 ---
if __name__ == "__main__":
    builder = CompanyDictionaryBuilder()

    # 外部ファイルのロード（PDFでもCSVでもOK）
    # 例: カレントディレクトリにあるPDFファイルをすべて処理
    # target_files = ["internal_doc.pdf", "project_notes.csv"]
    target_files = ["curriculum_map.pdf", "project_notes.csv"]

    for file in target_files:
        if not os.path.exists(file): continue

        if file.endswith(".pdf"):
            content = builder.load_pdf(file)
        elif file.endswith(".csv"):
            content = builder.load_csv(file)

        builder.analyze_text(content)

    # 辞書の書き出し
    builder.save_google_ime_dict("company_expert_dict.txt", min_freq=1)