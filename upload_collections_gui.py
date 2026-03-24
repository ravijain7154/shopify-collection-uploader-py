import csv
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

from upload_collections import (
    COLUMN_NAME,
    CSV_PATH,
    build_url,
    normalize_shop_domain,
    parse_row_payload,
    upload_payload,
)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Shopify Smart Collection Uploader")
        self.geometry("760x520")
        self.resizable(True, True)

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.worker_thread: threading.Thread | None = None

        self._build_ui()
        self._poll_log()

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 6}

        frm = tk.Frame(self)
        frm.pack(fill="x", **pad)

        tk.Label(frm, text="Shopify Store URL or Domain").grid(row=0, column=0, sticky="w")
        self.shop_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.shop_var, width=60).grid(row=1, column=0, sticky="w")

        tk.Label(frm, text="API Key (X-Shopify-Access-Token)").grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.api_var = tk.StringVar()
        tk.Entry(frm, textvariable=self.api_var, width=60, show="*").grid(row=3, column=0, sticky="w")

        tk.Label(frm, text="CSV File").grid(row=4, column=0, sticky="w", pady=(12, 0))
        file_row = tk.Frame(frm)
        file_row.grid(row=5, column=0, sticky="w")
        self.csv_var = tk.StringVar(value=CSV_PATH)
        tk.Entry(file_row, textvariable=self.csv_var, width=52).pack(side="left")
        tk.Button(file_row, text="Browse", command=self._browse).pack(side="left", padx=(6, 0))

        self.start_btn = tk.Button(frm, text="Upload Collections", command=self._start_upload)
        self.start_btn.grid(row=6, column=0, sticky="w", pady=(12, 0))

        log_frame = tk.Frame(self)
        log_frame.pack(fill="both", expand=True, **pad)
        tk.Label(log_frame, text=f"Logs (column: {COLUMN_NAME})").pack(anchor="w")
        self.log = tk.Text(log_frame, wrap="word", height=18)
        self.log.pack(fill="both", expand=True)

    def _browse(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.csv_var.set(path)

    def _start_upload(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("In Progress", "Upload is already running.")
            return

        shop = self.shop_var.get().strip()
        api_key = self.api_var.get().strip()
        csv_path = self.csv_var.get().strip()

        if not shop or not api_key or not csv_path:
            messagebox.showerror("Missing Info", "Store URL, API key, and CSV file are required.")
            return

        self.log.delete("1.0", tk.END)
        self.start_btn.config(state="disabled")

        self.worker_thread = threading.Thread(
            target=self._run_upload, args=(shop, api_key, csv_path), daemon=True
        )
        self.worker_thread.start()

    def _run_upload(self, shop: str, api_key: str, csv_path: str) -> None:
        shop_domain = normalize_shop_domain(shop)
        url = build_url(shop_domain)

        try:
            with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                if COLUMN_NAME not in reader.fieldnames:
                    self.log_queue.put(
                        f"Error: column '{COLUMN_NAME}' not found in {csv_path}.\n"
                        f"Available columns: {reader.fieldnames}\n"
                    )
                    self._finish()
                    return

                success_count = 0
                fail_count = 0
                for idx, row in enumerate(reader, start=2):
                    payload, err = parse_row_payload(row.get(COLUMN_NAME, ""), idx)
                    if err:
                        self.log_queue.put(f"[SKIP] {err}\n")
                        fail_count += 1
                        continue

                    ok, msg = upload_payload(url, api_key, payload)
                    if ok:
                        success_count += 1
                        title = payload.get("smart_collection", {}).get("title", "Untitled")
                        self.log_queue.put(f"[OK] Row {idx}: {title} -> {msg}\n")
                    else:
                        fail_count += 1
                        self.log_queue.put(f"[FAIL] Row {idx}: {msg}\n")

                self.log_queue.put(f"\nDone. Success: {success_count}, Failed: {fail_count}\n")
        except FileNotFoundError:
            self.log_queue.put(f"Error: {csv_path} not found.\n")
        finally:
            self._finish()

    def _finish(self) -> None:
        self.log_queue.put("__DONE__")

    def _poll_log(self) -> None:
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg == "__DONE__":
                    self.start_btn.config(state="normal")
                    continue
                self.log.insert(tk.END, msg)
                self.log.see(tk.END)
        except queue.Empty:
            pass
        self.after(100, self._poll_log)


if __name__ == "__main__":
    app = App()
    app.mainloop()
