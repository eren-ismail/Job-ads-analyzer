__version__ = "0.1.0"

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import sqlite3
import pandas as pd
import re
from collections import Counter



# --- CONFIG ---
DB_PATH = "job_ads.db"
STOPWORDS = set(["and", "or", "in", "at", "https://", "ein", "sowie", "bzw", "etc", "mit", "with", "experience"])

# --- DATABASE FUNCTIONS ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS job_ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def insert_job_ad(content):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO job_ads (content) VALUES (?)", (content,))
    conn.commit()
    conn.close()


def fetch_all_ads():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM job_ads", conn)
    conn.close()
    return df

# --- TEXT PROCESSING FUNCTIONS ---
def tokenize(text):
    text = re.sub(r"[^a-zA-Z+#]", " ", text)
    tokens = text.lower().split()
    return [t for t in tokens if t not in STOPWORDS]


def count_keywords(texts, top_n=20):
    all_tokens = []
    for text in texts:
        tokens = tokenize(text)
        all_tokens.extend(tokens)

    counts = Counter(all_tokens)
    return counts.most_common(top_n)


def keyword_match_ratio(texts, keyword):
    keyword = keyword.lower()
    match_count = sum(1 for t in texts if keyword in t.lower())
    total = len(texts)
    return match_count, total

# --- GUI SETUP ---
class JobAdAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Job Ad Keyword Analyzer")

        self.tabControl = ttk.Notebook(root)

        self.tab1 = ttk.Frame(self.tabControl)
        self.tab2 = ttk.Frame(self.tabControl)

        self.tabControl.add(self.tab1, text='Add Job Ad')
        self.tabControl.add(self.tab2, text='Analyze Job Ads')
        self.tabControl.pack(expand=1, fill="both")

        self.setup_tab1()
        self.setup_tab2()

    def setup_tab1(self):
        self.text_area = scrolledtext.ScrolledText(self.tab1, wrap=tk.WORD, width=80, height=20)
        self.text_area.pack(padx=10, pady=10)

        self.save_button = tk.Button(self.tab1, text="Save to Database", command=self.save_to_db)
        self.save_button.pack(pady=10)

    def save_to_db(self):
        content = self.text_area.get("1.0", tk.END).strip()
        if content:
            insert_job_ad(content)
            messagebox.showinfo("Success", "Job ad saved successfully.")
            self.text_area.delete("1.0", tk.END)
        else:
            messagebox.showwarning("Warning", "Please enter some content.")

    def setup_tab2(self):
        self.left_frame = tk.Frame(self.tab2)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.Y)

        self.right_frame = tk.Frame(self.tab2)
        self.right_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.analysis_mode = tk.StringVar(value="Top Keywords")

        tk.Label(self.left_frame, text="Select Analysis Mode:").pack(anchor=tk.W)
        tk.Radiobutton(self.left_frame, text="Top Keywords", variable=self.analysis_mode, value="Top Keywords", command=self.toggle_analysis_inputs).pack(anchor=tk.W)
        tk.Radiobutton(self.left_frame, text="Single Keyword Match", variable=self.analysis_mode, value="Single Keyword Match", command=self.toggle_analysis_inputs).pack(anchor=tk.W)

        self.n_select = ttk.Combobox(self.left_frame, values=[10, 20, 50], state="readonly")
        self.n_select.current(0)

        self.keyword_entry = tk.Entry(self.left_frame)

        self.analyze_button = tk.Button(self.left_frame, text="Analyze", command=self.analyze_keywords)
        self.analyze_button.pack(pady=10)

        self.result_text = scrolledtext.ScrolledText(self.right_frame, wrap=tk.WORD, width=80, height=30)
        self.result_text.pack(fill=tk.BOTH, expand=True)

        self.toggle_analysis_inputs()

    def toggle_analysis_inputs(self):
        mode = self.analysis_mode.get()
        if mode == "Top Keywords":
            self.keyword_entry.pack_forget()
            self.n_select.pack(pady=5)
        elif mode == "Single Keyword Match":
            self.n_select.pack_forget()
            self.keyword_entry.pack(pady=5)

    def analyze_keywords(self):
        df = fetch_all_ads()
        if df.empty:
            messagebox.showinfo("Info", "No job ads in the database.")
            return

        mode = self.analysis_mode.get()
        self.result_text.delete("1.0", tk.END)

        if mode == "Top Keywords":
            n = int(self.n_select.get())
            results = count_keywords(df['content'].tolist(), top_n=n)
            if results:
                for kw, count in results:
                    self.result_text.insert(tk.END, f"{kw}: {count}\n")
            else:
                self.result_text.insert(tk.END, "No matching keywords found.\n")

        elif mode == "Single Keyword Match":
            keyword = self.keyword_entry.get().strip()
            if keyword:
                match, total = keyword_match_ratio(df['content'].tolist(), keyword)
                self.result_text.insert(tk.END, f"{match} / {total} Match found\n")
            else:
                messagebox.showwarning("Warning", "Enter a keyword to search.")

# --- RUN APP ---
if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = JobAdAnalyzerApp(root)
    root.mainloop()
