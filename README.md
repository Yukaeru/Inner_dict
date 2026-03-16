## 目標
最終目標は
CSVファイルから社内用語（高PMIの連続名詞）を抽出し、PCのIME（Google日本語入力やMS-IME）にインポートできる形式の辞書ファイルを出力する

```shell
pip install -U spacy ginza ja-ginza pandas
pip install pdfminer.six
```


### 注意事項
GiNZAのバージョンによって読み取得の方法が異なります。現在のGiNZAでは token.morph.get("Reading") を使います。
修正箇所 
#### 修正前
```python
yomi = "".join([token._.reading for token in nc])

```

#### 修正後
```python
yomi = "".join([
token.morph.get("Reading")[0] if token.morph.get("Reading") else token.text
for token in nc
])
```

token.morph.get("Reading") はリストを返すので [0] で取得し、読みがない場合は token.text をそのまま使うようにしています。