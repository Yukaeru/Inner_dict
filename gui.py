import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import os
import sys

# dict.py と同じディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dict import CompanyDictionaryBuilder


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("社内辞書ビルダー")
        self.geometry("620x520")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")

        self.files = []       # 追加されたファイルパスのリスト
        self._build_ui()

    # ── UI構築 ──────────────────────────────────────────
    def _build_ui(self):
        BG     = "#1e1e2e"
        PANEL  = "#2a2a3d"
        ACCENT = "#7c6af7"
        FG     = "#e0e0f0"
        MUTED  = "#6b6b8a"
        ENTRY  = "#12121f"

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TProgressbar",
                        troughcolor=PANEL, background=ACCENT,
                        bordercolor=PANEL, lightcolor=ACCENT, darkcolor=ACCENT)

        # ── タイトル
        tk.Label(self, text="社内辞書ビルダー",
                 bg=BG, fg=FG,
                 font=("Helvetica Neue", 18, "bold")).pack(pady=(24, 2))
        tk.Label(self, text="PDF / CSV → IME辞書（Google日本語入力 / MS-IME）",
                 bg=BG, fg=MUTED, font=("Helvetica Neue", 10)).pack()

        # ── ファイルリスト
        list_frame = tk.Frame(self, bg=PANEL, bd=0)
        list_frame.pack(fill="x", padx=24, pady=(18, 0))

        tk.Label(list_frame, text="入力ファイル",
                 bg=PANEL, fg=MUTED,
                 font=("Helvetica Neue", 9, "bold")).pack(anchor="w", padx=10, pady=(8, 2))

        self.listbox = tk.Listbox(
            list_frame, bg=ENTRY, fg=FG,
            selectbackground=ACCENT, selectforeground="#fff",
            relief="flat", bd=0,
            font=("Menlo", 10), height=6,
            activestyle="none"
        )
        self.listbox.pack(fill="x", padx=10, pady=(0, 8))

        btn_row = tk.Frame(list_frame, bg=PANEL)
        btn_row.pack(fill="x", padx=10, pady=(0, 10))

        self._btn(btn_row, "＋ PDF追加", ACCENT, self._add_pdf).pack(side="left", padx=(0, 6))
        self._btn(btn_row, "＋ CSV追加", "#4a9eff", self._add_csv).pack(side="left", padx=(0, 6))
        self._btn(btn_row, "✕ 削除",    "#e05a7a", self._remove_file).pack(side="left")

        # ── 設定行
        cfg_frame = tk.Frame(self, bg=BG)
        cfg_frame.pack(fill="x", padx=24, pady=(16, 0))

        # 最低出現回数
        tk.Label(cfg_frame, text="最低出現回数",
                 bg=BG, fg=MUTED, font=("Helvetica Neue", 10)).grid(row=0, column=0, sticky="w")
        self.min_freq = tk.IntVar(value=1)
        tk.Spinbox(cfg_frame, from_=1, to=20,
                   textvariable=self.min_freq, width=5,
                   bg=PANEL, fg=FG, buttonbackground=PANEL,
                   relief="flat", font=("Helvetica Neue", 11)).grid(row=0, column=1, padx=(8, 24), sticky="w")

        # 出力ファイル名
        tk.Label(cfg_frame, text="出力ファイル名",
                 bg=BG, fg=MUTED, font=("Helvetica Neue", 10)).grid(row=0, column=2, sticky="w")
        self.out_var = tk.StringVar(value="company_dict_1.txt")
        tk.Entry(cfg_frame, textvariable=self.out_var, width=22,
                 bg=PANEL, fg=FG, insertbackground=FG,
                 relief="flat", font=("Helvetica Neue", 11)).grid(row=0, column=3, padx=(8, 0))

        # ── プログレスバー
        self.progress = ttk.Progressbar(self, mode="indeterminate", style="TProgressbar")
        self.progress.pack(fill="x", padx=24, pady=(18, 0))

        # ── ログエリア
        log_frame = tk.Frame(self, bg=PANEL, bd=0)
        log_frame.pack(fill="both", expand=True, padx=24, pady=(12, 0))

        self.log = tk.Text(
            log_frame, bg=ENTRY, fg=FG,
            font=("Menlo", 9), relief="flat", bd=0,
            state="disabled", wrap="word", height=7
        )
        self.log.pack(fill="both", expand=True, padx=6, pady=6)

        # ── 実行ボタン
        self._btn(self, "▶  辞書を生成する", ACCENT, self._run,
                  font=("Helvetica Neue", 13, "bold"),
                  pady=10).pack(fill="x", padx=24, pady=(12, 20))

    def _btn(self, parent, text, color, cmd, **kw):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=color, fg="#fff", activebackground=color,
            relief="flat", bd=0, cursor="hand2",
            font=kw.pop("font", ("Helvetica Neue", 10, "bold")),
            padx=kw.pop("padx", 14),
            pady=kw.pop("pady", 6),
            **kw
        )

    # ── ファイル操作 ──────────────────────────────────────
    def _add_pdf(self):
        paths = filedialog.askopenfilenames(
            title="PDFファイルを選択",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.listbox.insert("end", os.path.basename(p))

    def _add_csv(self):
        paths = filedialog.askopenfilenames(
            title="CSVファイルを選択",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.listbox.insert("end", os.path.basename(p))

    def _remove_file(self):
        sel = self.listbox.curselection()
        if sel:
            idx = sel[0]
            self.listbox.delete(idx)
            self.files.pop(idx)

    # ── ログ出力 ──────────────────────────────────────────
    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    # ── 辞書生成（別スレッド） ────────────────────────────
    def _run(self):
        if not self.files:
            messagebox.showwarning("ファイル未選択", "ファイルを1つ以上追加してください。")
            return

        # UI を無効化
        self.progress.start(10)
        self._log("─" * 40)
        self._log("処理を開始します...")

        thread = threading.Thread(target=self._worker, daemon=True)
        thread.start()

    def _worker(self):
        try:
            # printをGUIログにリダイレクト
            import builtins
            orig_print = builtins.print
            def gui_print(*args, **kwargs):
                msg = " ".join(str(a) for a in args)
                self.after(0, self._log, msg)
            builtins.print = gui_print

            builder = CompanyDictionaryBuilder()

            for path in self.files:
                if path.endswith(".pdf"):
                    content = builder.load_pdf(path)
                elif path.endswith(".csv"):
                    content = builder.load_csv(path)
                else:
                    continue
                builder.analyze_text(content)

            out_file = self.out_var.get() or "company_dict_1.txt"
            builder.save_ime_dict(out_file, min_freq=self.min_freq.get())

            builtins.print = orig_print
            self.after(0, self._done, out_file)

        except Exception as e:
            import builtins
            builtins.print = __builtins__["print"] if isinstance(__builtins__, dict) else print
            self.after(0, self._error, str(e))

    def _done(self, out_file):
        self.progress.stop()
        self._log(f"\n✅ 完了！→ {os.path.abspath(out_file)}")
        messagebox.showinfo("完了", f"辞書ファイルを出力しました:\n{os.path.abspath(out_file)}")

    def _error(self, msg):
        self.progress.stop()
        self._log(f"\n❌ エラー: {msg}")
        messagebox.showerror("エラー", msg)


if __name__ == "__main__":
    app = App()
    app.mainloop()