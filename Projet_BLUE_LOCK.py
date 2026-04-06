"""
Gestionnaire de Base de Données SQLite
Application desktop Python avec Tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import csv
import os
import sys

# ─────────────────────────────────────────────
#  Palette de couleurs
# ─────────────────────────────────────────────
COLORS = {
    "bg":          "#1a1d23",
    "sidebar":     "#13151a",
    "panel":       "#21242c",
    "card":        "#292d38",
    "accent":      "#4f8ef7",
    "accent2":     "#38c4a0",
    "danger":      "#e05c5c",
    "warning":     "#f0a04a",
    "text":        "#e8eaf0",
    "text_muted":  "#7a7f94",
    "border":      "#2e3340",
    "hover":       "#333848",
    "success":     "#4cba7a",
    "input_bg":    "#1e212a",
}

FONT_TITLE  = ("Segoe UI", 13, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_MONO   = ("Consolas", 10)
FONT_H1     = ("Segoe UI", 16, "bold")


# ─────────────────────────────────────────────
#  Couche base de données
# ─────────────────────────────────────────────
class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.path = None

    # ── Connexion ──────────────────────────────
    def new(self, path: str):
        self.close()
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.path = path
        return True

    def open(self, path: str):
        return self.new(path)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            self.path = None

    def is_open(self) -> bool:
        return self.conn is not None

    # ── Tables ─────────────────────────────────
    def get_tables(self):
        cur = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [r[0] for r in cur.fetchall()]

    def create_table(self, name: str, columns: list):
        """columns = [{'name': str, 'type': str, 'pk': bool, 'notnull': bool}]"""
        col_defs = []
        for c in columns:
            definition = f'"{c["name"]}" {c["type"]}'
            if c.get("pk"):
                definition += " PRIMARY KEY AUTOINCREMENT"
            if c.get("notnull") and not c.get("pk"):
                definition += " NOT NULL"
            col_defs.append(definition)
        sql = f'CREATE TABLE IF NOT EXISTS "{name}" ({", ".join(col_defs)})'
        self.conn.execute(sql)
        self.conn.commit()

    def drop_table(self, name: str):
        self.conn.execute(f'DROP TABLE IF EXISTS "{name}"')
        self.conn.commit()

    def rename_table(self, old: str, new: str):
        self.conn.execute(f'ALTER TABLE "{old}" RENAME TO "{new}"')
        self.conn.commit()

    def get_schema(self, table: str):
        cur = self.conn.execute(f'PRAGMA table_info("{table}")')
        return cur.fetchall()

    def get_row_count(self, table: str) -> int:
        cur = self.conn.execute(f'SELECT COUNT(*) FROM "{table}"')
        return cur.fetchone()[0]

    # ── Données ────────────────────────────────
    def get_rows(self, table: str, search: str = "", limit: int = 500, offset: int = 0):
        schema = self.get_schema(table)
        if search:
            conditions = [f'CAST("{col["name"]}" AS TEXT) LIKE ?' for col in schema]
            where = " OR ".join(conditions)
            params = [f"%{search}%"] * len(schema)
            sql = f'SELECT * FROM "{table}" WHERE {where} LIMIT {limit} OFFSET {offset}'
            cur = self.conn.execute(sql, params)
        else:
            cur = self.conn.execute(
                f'SELECT * FROM "{table}" LIMIT {limit} OFFSET {offset}')
        return cur.fetchall()

    def insert_row(self, table: str, data: dict):
        cols = ", ".join(f'"{k}"' for k in data)
        placeholders = ", ".join("?" for _ in data)
        self.conn.execute(
            f'INSERT INTO "{table}" ({cols}) VALUES ({placeholders})',
            list(data.values()))
        self.conn.commit()

    def update_row(self, table: str, pk_col: str, pk_val, data: dict):
        sets = ", ".join(f'"{k}" = ?' for k in data)
        self.conn.execute(
            f'UPDATE "{table}" SET {sets} WHERE "{pk_col}" = ?',
            list(data.values()) + [pk_val])
        self.conn.commit()

    def delete_row(self, table: str, pk_col: str, pk_val):
        self.conn.execute(
            f'DELETE FROM "{table}" WHERE "{pk_col}" = ?', (pk_val,))
        self.conn.commit()

    # ── SQL brut ───────────────────────────────
    def execute_sql(self, sql: str):
        cur = self.conn.execute(sql)
        self.conn.commit()
        return cur

    # ── Import / Export CSV ────────────────────
    def export_csv(self, table: str, path: str):
        schema = self.get_schema(table)
        headers = [col["name"] for col in schema]
        rows = self.conn.execute(f'SELECT * FROM "{table}"').fetchall()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return len(rows)

    def import_csv(self, table: str, path: str):
        schema = self.get_schema(table)
        col_names = [col["name"] for col in schema]
        pk_cols = [col["name"] for col in schema if col["pk"]]
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                data = {k: v for k, v in row.items()
                        if k in col_names and k not in pk_cols}
                if data:
                    self.insert_row(table, data)
                    count += 1
        return count


# ─────────────────────────────────────────────
#  Widgets personnalisés
# ─────────────────────────────────────────────
class StyledButton(tk.Frame):
    def __init__(self, parent, text, command=None, color="accent",
                 width=None, icon="", **kwargs):
        bg = COLORS[color]
        super().__init__(parent, bg=bg, cursor="hand2", **kwargs)
        self.command = command
        self.color = color
        self.bg = bg
        label_text = f"{icon} {text}".strip() if icon else text
        self.label = tk.Label(
            self, text=label_text, bg=bg, fg=COLORS["text"],
            font=FONT_NORMAL, padx=12, pady=6)
        if width:
            self.label.config(width=width)
        self.label.pack()
        self.bind("<Button-1>", self._click)
        self.label.bind("<Button-1>", self._click)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.label.bind("<Enter>", self._enter)
        self.label.bind("<Leave>", self._leave)

    def _click(self, e=None):
        if self.command:
            self.command()

    def _enter(self, e=None):
        darker = self._darken(self.bg)
        self.config(bg=darker)
        self.label.config(bg=darker)

    def _leave(self, e=None):
        self.config(bg=self.bg)
        self.label.config(bg=self.bg)

    @staticmethod
    def _darken(hex_color):
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        factor = 0.8
        return "#{:02x}{:02x}{:02x}".format(
            int(r * factor), int(g * factor), int(b * factor))


class LabeledEntry(tk.Frame):
    def __init__(self, parent, label, placeholder="", show=None, **kwargs):
        super().__init__(parent, bg=COLORS["panel"], **kwargs)
        tk.Label(self, text=label, bg=COLORS["panel"],
                 fg=COLORS["text_muted"], font=FONT_SMALL).pack(anchor="w")
        self.var = tk.StringVar()
        self.entry = tk.Entry(
            self, textvariable=self.var, bg=COLORS["input_bg"],
            fg=COLORS["text"], font=FONT_NORMAL,
            insertbackground=COLORS["text"], relief="flat",
            bd=0, highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"])
        if show:
            self.entry.config(show=show)
        self.entry.pack(fill="x", ipady=5, padx=2)
        if placeholder:
            self.entry.insert(0, placeholder)
            self.entry.config(fg=COLORS["text_muted"])
            self.entry.bind("<FocusIn>", lambda e: self._clear_ph(placeholder))
            self.entry.bind("<FocusOut>", lambda e: self._restore_ph(placeholder))

    def _clear_ph(self, ph):
        if self.entry.get() == ph:
            self.entry.delete(0, "end")
            self.entry.config(fg=COLORS["text"])

    def _restore_ph(self, ph):
        if not self.entry.get():
            self.entry.insert(0, ph)
            self.entry.config(fg=COLORS["text_muted"])

    def get(self):
        return self.var.get()

    def set(self, val):
        self.var.set(val)


class Separator(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS["border"], height=1, **kwargs)


# ─────────────────────────────────────────────
#  Dialogue : créer une table
# ─────────────────────────────────────────────
class CreateTableDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        self.title("Nouvelle Table")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.columns = []
        self._build()
        self._center(parent)

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build(self):
        pad = {"padx": 20, "pady": 8}

        tk.Label(self, text="Créer une table", font=FONT_H1,
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(**pad, anchor="w")
        Separator(self).pack(fill="x", padx=20)

        self.name_entry = LabeledEntry(self, "Nom de la table", "ma_table")
        self.name_entry.pack(fill="x", **pad)

        tk.Label(self, text="Colonnes", font=FONT_TITLE,
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(**pad, anchor="w")

        # Liste des colonnes
        self.cols_frame = tk.Frame(self, bg=COLORS["bg"])
        self.cols_frame.pack(fill="x", padx=20)

        # Colonne ID par défaut
        self._add_column_row(default_pk=True)

        btn_frame = tk.Frame(self, bg=COLORS["bg"])
        btn_frame.pack(fill="x", **pad)
        StyledButton(btn_frame, "+ Colonne", self._add_column_row,
                     color="card").pack(side="left")

        Separator(self).pack(fill="x", padx=20, pady=8)

        footer = tk.Frame(self, bg=COLORS["bg"])
        footer.pack(fill="x", **pad)
        StyledButton(footer, "Annuler", self.destroy, color="card").pack(side="right", padx=(8, 0))
        StyledButton(footer, "Créer", self._submit, color="accent").pack(side="right")

    def _add_column_row(self, default_pk=False):
        row = tk.Frame(self.cols_frame, bg=COLORS["card"],
                       pady=6, padx=8)
        row.pack(fill="x", pady=2)

        name_var = tk.StringVar(value="id" if default_pk else "")
        type_var = tk.StringVar(value="INTEGER" if default_pk else "TEXT")
        pk_var = tk.BooleanVar(value=default_pk)
        nn_var = tk.BooleanVar(value=False)

        tk.Entry(row, textvariable=name_var, width=14,
                 bg=COLORS["input_bg"], fg=COLORS["text"],
                 insertbackground=COLORS["text"], font=FONT_NORMAL,
                 relief="flat", bd=0).pack(side="left", padx=4)

        type_cb = ttk.Combobox(row, textvariable=type_var, width=10,
                                values=["INTEGER", "TEXT", "REAL", "BLOB", "NUMERIC"],
                                state="readonly", font=FONT_NORMAL)
        type_cb.pack(side="left", padx=4)

        tk.Checkbutton(row, text="PK", variable=pk_var,
                       bg=COLORS["card"], fg=COLORS["text"],
                       selectcolor=COLORS["accent"],
                       activebackground=COLORS["card"],
                       font=FONT_SMALL).pack(side="left", padx=4)

        tk.Checkbutton(row, text="NOT NULL", variable=nn_var,
                       bg=COLORS["card"], fg=COLORS["text"],
                       selectcolor=COLORS["accent"],
                       activebackground=COLORS["card"],
                       font=FONT_SMALL).pack(side="left", padx=4)

        if not default_pk:
            def remove():
                self.columns.remove(entry)
                row.destroy()
            tk.Button(row, text="✕", command=remove,
                      bg=COLORS["danger"], fg="white",
                      font=FONT_SMALL, relief="flat", bd=0,
                      padx=6, pady=2, cursor="hand2").pack(side="right")

        entry = {"name": name_var, "type": type_var, "pk": pk_var, "notnull": nn_var}
        self.columns.append(entry)

    def _submit(self):
        table_name = self.name_entry.get().strip()
        if not table_name:
            messagebox.showwarning("Erreur", "Nom de table requis.", parent=self)
            return
        cols = []
        for c in self.columns:
            name = c["name"].get().strip()
            if not name:
                continue
            cols.append({
                "name": name,
                "type": c["type"].get(),
                "pk": c["pk"].get(),
                "notnull": c["notnull"].get(),
            })
        if not cols:
            messagebox.showwarning("Erreur", "Au moins une colonne requise.", parent=self)
            return
        self.result = {"name": table_name, "columns": cols}
        self.destroy()


# ─────────────────────────────────────────────
#  Dialogue : éditer / ajouter une ligne
# ─────────────────────────────────────────────
class RowDialog(tk.Toplevel):
    def __init__(self, parent, schema, existing=None, title="Ajouter une ligne"):
        super().__init__(parent)
        self.result = None
        self.schema = schema
        self.existing = existing
        self.title(title)
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.fields = {}
        self._build()
        self._center(parent)

    def _center(self, parent):
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _build(self):
        pad = {"padx": 20, "pady": 6}
        tk.Label(self, text=self.title(), font=FONT_H1,
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(**pad, anchor="w")
        Separator(self).pack(fill="x", padx=20)

        for col in self.schema:
            is_pk = bool(col["pk"])
            frame = tk.Frame(self, bg=COLORS["panel"], pady=4, padx=10)
            frame.pack(fill="x", padx=20, pady=3)

            badge = " [PK]" if is_pk else ""
            tk.Label(frame, text=f'{col["name"]}{badge}',
                     bg=COLORS["panel"], fg=COLORS["text_muted"],
                     font=FONT_SMALL).pack(anchor="w")

            if is_pk:
                val = str(self.existing[col["name"]]) if self.existing else "(auto)"
                tk.Label(frame, text=val, bg=COLORS["panel"],
                         fg=COLORS["text_muted"], font=FONT_MONO).pack(anchor="w")
            else:
                var = tk.StringVar()
                if self.existing and col["name"] in self.existing.keys():
                    v = self.existing[col["name"]]
                    var.set("" if v is None else str(v))
                entry = tk.Entry(frame, textvariable=var, width=36,
                                 bg=COLORS["input_bg"], fg=COLORS["text"],
                                 insertbackground=COLORS["text"],
                                 font=FONT_NORMAL, relief="flat", bd=0,
                                 highlightthickness=1,
                                 highlightbackground=COLORS["border"],
                                 highlightcolor=COLORS["accent"])
                entry.pack(fill="x", ipady=5, padx=2)
                self.fields[col["name"]] = var

        Separator(self).pack(fill="x", padx=20, pady=8)
        footer = tk.Frame(self, bg=COLORS["bg"])
        footer.pack(fill="x", padx=20, pady=(0, 14))
        StyledButton(footer, "Annuler", self.destroy, color="card").pack(side="right", padx=(8, 0))
        StyledButton(footer, "Sauvegarder", self._submit, color="accent").pack(side="right")

    def _submit(self):
        self.result = {k: (v.get() if v.get() != "" else None)
                       for k, v in self.fields.items()}
        self.destroy()


# ─────────────────────────────────────────────
#  Panneau : vue des données d'une table
# ─────────────────────────────────────────────
class DataPanel(tk.Frame):
    PAGE_SIZE = 100

    def __init__(self, parent, db: DatabaseManager, table: str,
                 on_status=None, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        self.db = db
        self.table = table
        self.on_status = on_status
        self.schema = db.get_schema(table)
        self.pk_col = next((c["name"] for c in self.schema if c["pk"]), None)
        self.search_var = tk.StringVar()
        self.offset = 0
        self._build()
        self.refresh()

    def _build(self):
        # ── Toolbar ──────────────────────────────
        toolbar = tk.Frame(self, bg=COLORS["panel"], pady=6, padx=10)
        toolbar.pack(fill="x")

        StyledButton(toolbar, "Ajouter", self.add_row,
                     color="accent2", icon="＋").pack(side="left", padx=4)
        StyledButton(toolbar, "Modifier", self.edit_row,
                     color="accent", icon="✎").pack(side="left", padx=4)
        StyledButton(toolbar, "Supprimer", self.delete_row,
                     color="danger", icon="✕").pack(side="left", padx=4)

        tk.Frame(toolbar, bg=COLORS["panel"], width=20).pack(side="left")

        StyledButton(toolbar, "Export CSV", self.export_csv,
                     color="card", icon="↓").pack(side="left", padx=4)
        StyledButton(toolbar, "Import CSV", self.import_csv,
                     color="card", icon="↑").pack(side="left", padx=4)

        # Barre de recherche
        search_frame = tk.Frame(toolbar, bg=COLORS["input_bg"],
                                highlightthickness=1,
                                highlightbackground=COLORS["border"])
        search_frame.pack(side="right", padx=8)
        tk.Label(search_frame, text="🔍", bg=COLORS["input_bg"],
                 fg=COLORS["text_muted"], font=FONT_SMALL).pack(side="left", padx=6)
        tk.Entry(search_frame, textvariable=self.search_var, width=22,
                 bg=COLORS["input_bg"], fg=COLORS["text"],
                 insertbackground=COLORS["text"], font=FONT_NORMAL,
                 relief="flat", bd=0).pack(side="left", ipady=5, padx=(0, 8))
        self.search_var.trace_add("write", lambda *a: self._on_search())

        # ── Tableau ───────────────────────────────
        table_frame = tk.Frame(self, bg=COLORS["bg"])
        table_frame.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.Treeview",
                         background=COLORS["bg"],
                         foreground=COLORS["text"],
                         rowheight=28,
                         fieldbackground=COLORS["bg"],
                         borderwidth=0,
                         font=FONT_NORMAL)
        style.configure("Dark.Treeview.Heading",
                         background=COLORS["panel"],
                         foreground=COLORS["text_muted"],
                         relief="flat",
                         font=FONT_SMALL)
        style.map("Dark.Treeview",
                  background=[("selected", COLORS["accent"])],
                  foreground=[("selected", "white")])

        cols = [c["name"] for c in self.schema]
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                  style="Dark.Treeview")

        for col in self.schema:
            width = 80 if col["type"] in ("INTEGER", "REAL") else 140
            self.tree.heading(col["name"], text=col["name"],
                              command=lambda c=col["name"]: self._sort(c))
            self.tree.column(col["name"], width=width, minwidth=60)

        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                             command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal",
                             command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", lambda e: self.edit_row())

        # ── Pagination ────────────────────────────
        pag = tk.Frame(self, bg=COLORS["panel"], pady=4)
        pag.pack(fill="x")
        self.prev_btn = StyledButton(pag, "◀ Précédent",
                                     self._prev_page, color="card")
        self.prev_btn.pack(side="left", padx=10)
        self.page_label = tk.Label(pag, text="", bg=COLORS["panel"],
                                    fg=COLORS["text_muted"], font=FONT_SMALL)
        self.page_label.pack(side="left")
        self.next_btn = StyledButton(pag, "Suivant ▶",
                                     self._next_page, color="card")
        self.next_btn.pack(side="right", padx=10)

    def _on_search(self):
        self.offset = 0
        self.refresh()

    def _sort(self, col):
        pass  # tri simplifié

    def refresh(self):
        search = self.search_var.get().strip()
        rows = self.db.get_rows(self.table, search, self.PAGE_SIZE, self.offset)
        total = self.db.get_row_count(self.table)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for row in rows:
            values = [("" if v is None else v) for v in row]
            self.tree.insert("", "end", values=values)

        page = self.offset // self.PAGE_SIZE + 1
        pages = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        self.page_label.config(text=f"Page {page}/{pages}  ({total} lignes)")
        if self.on_status:
            self.on_status(f"Table : {self.table}  |  {total} lignes")

    def _prev_page(self):
        if self.offset >= self.PAGE_SIZE:
            self.offset -= self.PAGE_SIZE
            self.refresh()

    def _next_page(self):
        total = self.db.get_row_count(self.table)
        if self.offset + self.PAGE_SIZE < total:
            self.offset += self.PAGE_SIZE
            self.refresh()

    def _selected_row(self):
        sel = self.tree.selection()
        if not sel:
            return None, None
        item = sel[0]
        values = self.tree.item(item, "values")
        row_dict = {self.schema[i]["name"]: values[i] for i in range(len(self.schema))}
        return item, row_dict

    def add_row(self):
        dlg = RowDialog(self, self.schema, title="Ajouter une ligne")
        self.wait_window(dlg)
        if dlg.result:
            try:
                self.db.insert_row(self.table, dlg.result)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Erreur", str(e), parent=self)

    def edit_row(self):
        item, row = self._selected_row()
        if not row:
            messagebox.showinfo("Info", "Sélectionnez une ligne.", parent=self)
            return
        dlg = RowDialog(self, self.schema, existing=row, title="Modifier la ligne")
        self.wait_window(dlg)
        if dlg.result and self.pk_col:
            try:
                pk_val = row[self.pk_col]
                self.db.update_row(self.table, self.pk_col, pk_val, dlg.result)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Erreur", str(e), parent=self)

    def delete_row(self):
        item, row = self._selected_row()
        if not row:
            messagebox.showinfo("Info", "Sélectionnez une ligne.", parent=self)
            return
        if not self.pk_col:
            messagebox.showwarning("Attention", "Aucune clé primaire définie.", parent=self)
            return
        if messagebox.askyesno("Confirmer", "Supprimer cette ligne ?", parent=self):
            try:
                self.db.delete_row(self.table, self.pk_col, row[self.pk_col])
                self.refresh()
            except Exception as e:
                messagebox.showerror("Erreur", str(e), parent=self)

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile=f"{self.table}.csv",
            parent=self)
        if path:
            try:
                n = self.db.export_csv(self.table, path)
                messagebox.showinfo("Export", f"{n} lignes exportées.", parent=self)
            except Exception as e:
                messagebox.showerror("Erreur", str(e), parent=self)

    def import_csv(self):
        path = filedialog.askopenfilename(
            filetypes=[("CSV", "*.csv")], parent=self)
        if path:
            try:
                n = self.db.import_csv(self.table, path)
                self.refresh()
                messagebox.showinfo("Import", f"{n} lignes importées.", parent=self)
            except Exception as e:
                messagebox.showerror("Erreur", str(e), parent=self)


# ─────────────────────────────────────────────
#  Panneau : éditeur SQL
# ─────────────────────────────────────────────
class SQLPanel(tk.Frame):
    def __init__(self, parent, db: DatabaseManager, on_refresh=None, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        self.db = db
        self.on_refresh = on_refresh
        self._history = []
        self._build()

    def _build(self):
        # Toolbar
        toolbar = tk.Frame(self, bg=COLORS["panel"], pady=6, padx=10)
        toolbar.pack(fill="x")
        StyledButton(toolbar, "▶  Exécuter", self.run,
                     color="accent2").pack(side="left", padx=4)
        StyledButton(toolbar, "Effacer", self._clear,
                     color="card").pack(side="left", padx=4)
        StyledButton(toolbar, "Historique", self._show_history,
                     color="card").pack(side="left", padx=4)
        tk.Label(toolbar, text="F5 = Exécuter",
                 bg=COLORS["panel"], fg=COLORS["text_muted"],
                 font=FONT_SMALL).pack(side="right", padx=10)

        # Zone SQL
        editor_frame = tk.Frame(self, bg=COLORS["bg"])
        editor_frame.pack(fill="both", expand=True, padx=10, pady=(8, 0))

        tk.Label(editor_frame, text="Requête SQL", font=FONT_SMALL,
                 bg=COLORS["bg"], fg=COLORS["text_muted"]).pack(anchor="w")

        self.sql_text = tk.Text(
            editor_frame, height=10, bg=COLORS["input_bg"],
            fg=COLORS["text"], font=FONT_MONO,
            insertbackground=COLORS["text"], relief="flat",
            bd=0, padx=10, pady=10,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["accent"],
            undo=True, wrap="none")
        self.sql_text.pack(fill="both", expand=True)
        self.sql_text.bind("<F5>", lambda e: self.run())
        self.sql_text.bind("<Control-Return>", lambda e: self.run())

        # Résultats
        res_frame = tk.Frame(self, bg=COLORS["bg"])
        res_frame.pack(fill="both", expand=True, padx=10, pady=8)

        self.res_label = tk.Label(res_frame, text="Résultats",
                                   font=FONT_SMALL, bg=COLORS["bg"],
                                   fg=COLORS["text_muted"])
        self.res_label.pack(anchor="w")

        self.result_tree = ttk.Treeview(res_frame, style="Dark.Treeview",
                                         show="headings")
        vsb = ttk.Scrollbar(res_frame, orient="vertical",
                             command=self.result_tree.yview)
        hsb = ttk.Scrollbar(res_frame, orient="horizontal",
                             command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=vsb.set,
                                   xscrollcommand=hsb.set)
        self.result_tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, sticky="ew")
        res_frame.rowconfigure(1, weight=1)
        res_frame.columnconfigure(0, weight=1)

        self.msg_label = tk.Label(res_frame, text="", font=FONT_SMALL,
                                   bg=COLORS["bg"], fg=COLORS["text_muted"])
        self.msg_label.grid(row=0, column=0, columnspan=2, sticky="w")

    def run(self, event=None):
        sql = self.sql_text.get("1.0", "end").strip()
        if not sql:
            return
        self._history.append(sql)
        try:
            cur = self.db.execute_sql(sql)
            if cur.description:
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()
                self._show_results(cols, rows)
                self.msg_label.config(
                    text=f"✓  {len(rows)} ligne(s) retournée(s)",
                    fg=COLORS["success"])
            else:
                self._clear_results()
                self.msg_label.config(
                    text=f"✓  Requête exécutée — {cur.rowcount} ligne(s) affectée(s)",
                    fg=COLORS["success"])
                if self.on_refresh:
                    self.on_refresh()
        except Exception as e:
            self._clear_results()
            self.msg_label.config(text=f"✗  {e}", fg=COLORS["danger"])

    def _show_results(self, cols, rows):
        self._clear_results()
        self.result_tree["columns"] = cols
        for c in cols:
            self.result_tree.heading(c, text=c)
            self.result_tree.column(c, width=120, minwidth=60)
        for row in rows:
            self.result_tree.insert("", "end",
                values=[("" if v is None else v) for v in row])

    def _clear_results(self):
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        self.result_tree["columns"] = []

    def _clear(self):
        self.sql_text.delete("1.0", "end")
        self._clear_results()
        self.msg_label.config(text="")

    def _show_history(self):
        if not self._history:
            messagebox.showinfo("Historique", "Aucune requête dans l'historique.",
                                parent=self)
            return
        win = tk.Toplevel(self)
        win.title("Historique SQL")
        win.configure(bg=COLORS["bg"])
        win.grab_set()
        lb = tk.Listbox(win, bg=COLORS["input_bg"], fg=COLORS["text"],
                        font=FONT_MONO, width=70, height=20,
                        selectbackground=COLORS["accent"])
        lb.pack(padx=12, pady=12, fill="both", expand=True)
        for q in reversed(self._history):
            lb.insert("end", q[:100])

        def use():
            sel = lb.curselection()
            if sel:
                idx = len(self._history) - 1 - sel[0]
                self.sql_text.delete("1.0", "end")
                self.sql_text.insert("1.0", self._history[idx])
                win.destroy()

        StyledButton(win, "Utiliser", use, color="accent").pack(pady=(0, 12))


# ─────────────────────────────────────────────
#  Panneau : schéma d'une table
# ─────────────────────────────────────────────
class SchemaPanel(tk.Frame):
    def __init__(self, parent, db: DatabaseManager, table: str, **kwargs):
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        self.db = db
        self.table = table
        self._build()

    def _build(self):
        schema = self.db.get_schema(self.table)
        count = self.db.get_row_count(self.table)

        # En-tête
        header = tk.Frame(self, bg=COLORS["panel"], pady=12, padx=16)
        header.pack(fill="x")
        tk.Label(header, text=f"📋  {self.table}", font=FONT_H1,
                 bg=COLORS["panel"], fg=COLORS["text"]).pack(side="left")
        tk.Label(header, text=f"{count} lignes  |  {len(schema)} colonnes",
                 bg=COLORS["panel"], fg=COLORS["text_muted"],
                 font=FONT_SMALL).pack(side="right")

        Separator(self).pack(fill="x")

        # Tableau schéma
        frame = tk.Frame(self, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ("#", "Nom", "Type", "Not Null", "Défaut", "Clé primaire")
        tree = ttk.Treeview(frame, columns=cols, show="headings",
                             style="Dark.Treeview", height=15)
        widths = [40, 160, 100, 80, 120, 100]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, minwidth=40)

        for col in schema:
            tree.insert("", "end", values=(
                col["cid"] + 1,
                col["name"],
                col["type"],
                "✓" if col["notnull"] else "—",
                col["dflt_value"] or "—",
                "★ PK" if col["pk"] else "—",
            ))
        tree.pack(fill="both", expand=True)

        # SQL de création
        try:
            res = self.db.conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                (self.table,)).fetchone()
            create_sql = res[0] if res else ""
        except Exception:
            create_sql = ""

        if create_sql:
            tk.Label(self, text="Définition SQL", font=FONT_SMALL,
                     bg=COLORS["bg"], fg=COLORS["text_muted"]).pack(
                         anchor="w", padx=12, pady=(10, 2))
            txt = tk.Text(self, height=5, bg=COLORS["input_bg"],
                          fg=COLORS["text_muted"], font=FONT_MONO,
                          relief="flat", bd=0, padx=8, pady=8,
                          state="normal", wrap="none")
            txt.insert("1.0", create_sql)
            txt.config(state="disabled")
            txt.pack(fill="x", padx=12, pady=(0, 10))


# ─────────────────────────────────────────────
#  Application principale
# ─────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DB Manager — SQLite")
        self.geometry("1100x700")
        self.minsize(800, 500)
        self.configure(bg=COLORS["bg"])

        self.db = DatabaseManager()
        self.active_table = None
        self.active_view = "data"

        self._apply_style()
        self._build_menu()
        self._build_ui()
        self._update_title()

    # ── Style global ───────────────────────────
    def _apply_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TScrollbar",
                         background=COLORS["panel"],
                         troughcolor=COLORS["bg"],
                         bordercolor=COLORS["bg"],
                         arrowcolor=COLORS["text_muted"],
                         relief="flat")
        style.configure("TCombobox",
                         fieldbackground=COLORS["input_bg"],
                         background=COLORS["input_bg"],
                         foreground=COLORS["text"],
                         arrowcolor=COLORS["text_muted"],
                         bordercolor=COLORS["border"],
                         relief="flat")

    # ── Menu ───────────────────────────────────
    def _build_menu(self):
        menubar = tk.Menu(self, bg=COLORS["panel"], fg=COLORS["text"],
                          activebackground=COLORS["accent"],
                          activeforeground="white", relief="flat")

        file_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["panel"],
                            fg=COLORS["text"],
                            activebackground=COLORS["accent"],
                            activeforeground="white")
        file_menu.add_command(label="Nouvelle base de données…",
                              command=self.new_db, accelerator="Ctrl+N")
        file_menu.add_command(label="Ouvrir…",
                              command=self.open_db, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Fermer la base", command=self.close_db)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit)
        menubar.add_cascade(label="Fichier", menu=file_menu)

        table_menu = tk.Menu(menubar, tearoff=0, bg=COLORS["panel"],
                             fg=COLORS["text"],
                             activebackground=COLORS["accent"],
                             activeforeground="white")
        table_menu.add_command(label="Nouvelle table…",
                               command=self.new_table, accelerator="Ctrl+T")
        table_menu.add_command(label="Renommer la table…",
                               command=self.rename_table)
        table_menu.add_command(label="Supprimer la table",
                               command=self.drop_table)
        menubar.add_cascade(label="Table", menu=table_menu)

        self.config(menu=menubar)
        self.bind("<Control-n>", lambda e: self.new_db())
        self.bind("<Control-o>", lambda e: self.open_db())
        self.bind("<Control-t>", lambda e: self.new_table())

    # ── Interface ──────────────────────────────
    def _build_ui(self):
        # Barre d'outils supérieure
        topbar = tk.Frame(self, bg=COLORS["sidebar"], pady=8, padx=12)
        topbar.pack(fill="x")

        StyledButton(topbar, "Nouvelle BDD", self.new_db,
                     color="accent2", icon="＋").pack(side="left", padx=4)
        StyledButton(topbar, "Ouvrir", self.open_db,
                     color="card", icon="📂").pack(side="left", padx=4)
        StyledButton(topbar, "Nouvelle table", self.new_table,
                     color="card", icon="▦").pack(side="left", padx=8)

        self.db_label = tk.Label(topbar, text="Aucune base ouverte",
                                  bg=COLORS["sidebar"],
                                  fg=COLORS["text_muted"], font=FONT_SMALL)
        self.db_label.pack(side="right", padx=10)

        # Corps principal
        body = tk.Frame(self, bg=COLORS["bg"])
        body.pack(fill="both", expand=True)

        # Sidebar (liste des tables)
        self.sidebar = tk.Frame(body, bg=COLORS["sidebar"], width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="TABLES", font=("Segoe UI", 9, "bold"),
                 bg=COLORS["sidebar"], fg=COLORS["text_muted"],
                 pady=10).pack(anchor="w", padx=12)
        Separator(self.sidebar).pack(fill="x")

        self.table_list_frame = tk.Frame(self.sidebar, bg=COLORS["sidebar"])
        self.table_list_frame.pack(fill="both", expand=True)

        # Zone principale
        self.main_area = tk.Frame(body, bg=COLORS["bg"])
        self.main_area.pack(side="left", fill="both", expand=True)

        # Onglets (Data / Schema / SQL)
        self.tab_bar = tk.Frame(self.main_area, bg=COLORS["panel"], pady=0)
        self.tab_bar.pack(fill="x")

        self.tab_btns = {}
        for tab in [("data", "Données"), ("schema", "Schéma"), ("sql", "SQL")]:
            key, label = tab
            btn = tk.Label(self.tab_bar, text=label, font=FONT_NORMAL,
                           bg=COLORS["panel"], fg=COLORS["text_muted"],
                           pady=10, padx=20, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda e, k=key: self._switch_tab(k))
            self.tab_btns[key] = btn

        self._update_tabs()

        # Contenu
        self.content_frame = tk.Frame(self.main_area, bg=COLORS["bg"])
        self.content_frame.pack(fill="both", expand=True)

        # Barre de statut
        self.status_bar = tk.Label(self, text="Prêt",
                                    bg=COLORS["sidebar"],
                                    fg=COLORS["text_muted"],
                                    font=FONT_SMALL, anchor="w", pady=4, padx=12)
        self.status_bar.pack(fill="x", side="bottom")

        self._show_welcome()

    # ── Onglets ────────────────────────────────
    def _switch_tab(self, tab):
        self.active_view = tab
        self._update_tabs()
        self._load_view()

    def _update_tabs(self):
        for key, btn in self.tab_btns.items():
            if key == self.active_view:
                btn.config(fg=COLORS["accent"],
                            font=("Segoe UI", 10, "bold"))
            else:
                btn.config(fg=COLORS["text_muted"],
                            font=FONT_NORMAL)

    # ── Vue de bienvenue ───────────────────────
    def _show_welcome(self):
        for w in self.content_frame.winfo_children():
            w.destroy()
        frame = tk.Frame(self.content_frame, bg=COLORS["bg"])
        frame.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(frame, text="🗄️", font=("Segoe UI", 48),
                 bg=COLORS["bg"], fg=COLORS["text_muted"]).pack()
        tk.Label(frame, text="DB Manager", font=("Segoe UI", 22, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(pady=4)
        tk.Label(frame, text="Créez ou ouvrez une base de données SQLite pour commencer",
                 bg=COLORS["bg"], fg=COLORS["text_muted"],
                 font=FONT_NORMAL).pack()
        tk.Frame(frame, bg=COLORS["bg"], height=16).pack()
        StyledButton(frame, "Nouvelle base de données",
                     self.new_db, color="accent2").pack(pady=4, ipadx=20)
        StyledButton(frame, "Ouvrir une base existante",
                     self.open_db, color="card").pack(ipadx=20)

    # ── Chargement de la vue courante ──────────
    def _load_view(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

        if not self.db.is_open():
            self._show_welcome()
            return

        if self.active_view == "sql":
            panel = SQLPanel(self.content_frame, self.db,
                             on_refresh=self._refresh_tables)
            panel.pack(fill="both", expand=True)
            return

        if not self.active_table:
            tk.Label(self.content_frame,
                     text="Sélectionnez une table dans la liste",
                     bg=COLORS["bg"], fg=COLORS["text_muted"],
                     font=FONT_NORMAL).place(relx=0.5, rely=0.5, anchor="center")
            return

        if self.active_view == "data":
            panel = DataPanel(self.content_frame, self.db,
                              self.active_table,
                              on_status=self._set_status)
            panel.pack(fill="both", expand=True)
        elif self.active_view == "schema":
            panel = SchemaPanel(self.content_frame, self.db, self.active_table)
            panel.pack(fill="both", expand=True)

    # ── Sidebar tables ─────────────────────────
    def _refresh_tables(self):
        for w in self.table_list_frame.winfo_children():
            w.destroy()
        if not self.db.is_open():
            return
        tables = self.db.get_tables()
        for tbl in tables:
            is_active = tbl == self.active_table
            bg = COLORS["hover"] if is_active else COLORS["sidebar"]
            fg = COLORS["text"] if is_active else COLORS["text_muted"]
            item = tk.Label(self.table_list_frame, text=f"  ▦  {tbl}",
                            bg=bg, fg=fg, font=FONT_NORMAL,
                            anchor="w", pady=8, padx=4, cursor="hand2")
            item.pack(fill="x")
            item.bind("<Button-1>", lambda e, t=tbl: self._select_table(t))
            item.bind("<Enter>",
                      lambda e, w=item: w.config(bg=COLORS["hover"]))
            item.bind("<Leave>",
                      lambda e, w=item, t=tbl: w.config(
                          bg=COLORS["hover"] if t == self.active_table
                          else COLORS["sidebar"]))

    def _select_table(self, table):
        self.active_table = table
        self._refresh_tables()
        self._load_view()

    # ── Actions BDD ────────────────────────────
    def new_db(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("SQLite", "*.db *.sqlite"), ("Tous", "*.*")],
            title="Créer une nouvelle base de données")
        if path:
            self.db.new(path)
            self.active_table = None
            self._refresh_tables()
            self._update_title()
            self._set_status(f"Base créée : {os.path.basename(path)}")
            self._show_welcome()

    def open_db(self):
        path = filedialog.askopenfilename(
            filetypes=[("SQLite", "*.db *.sqlite *.db3"), ("Tous", "*.*")],
            title="Ouvrir une base de données")
        if path:
            self.db.open(path)
            tables = self.db.get_tables()
            self.active_table = tables[0] if tables else None
            self._refresh_tables()
            self._update_title()
            self._set_status(f"Base ouverte : {os.path.basename(path)}")
            self._load_view()

    def close_db(self):
        if messagebox.askyesno("Fermer", "Fermer la base de données ?"):
            self.db.close()
            self.active_table = None
            self._refresh_tables()
            self._update_title()
            self._show_welcome()

    # ── Actions table ──────────────────────────
    def new_table(self):
        if not self.db.is_open():
            messagebox.showwarning("Info", "Ouvrez d'abord une base de données.")
            return
        dlg = CreateTableDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            try:
                self.db.create_table(dlg.result["name"], dlg.result["columns"])
                self.active_table = dlg.result["name"]
                self._refresh_tables()
                self._load_view()
                self._set_status(f"Table '{dlg.result['name']}' créée.")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    def rename_table(self):
        if not self.active_table:
            return
        new_name = simpledialog.askstring(
            "Renommer", f"Nouveau nom pour '{self.active_table}' :",
            parent=self)
        if new_name and new_name.strip():
            try:
                self.db.rename_table(self.active_table, new_name.strip())
                self.active_table = new_name.strip()
                self._refresh_tables()
                self._load_view()
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    def drop_table(self):
        if not self.active_table:
            return
        if messagebox.askyesno("Confirmer",
                                f"Supprimer définitivement la table '{self.active_table}' ?"):
            try:
                self.db.drop_table(self.active_table)
                tables = self.db.get_tables()
                self.active_table = tables[0] if tables else None
                self._refresh_tables()
                self._load_view()
                self._set_status("Table supprimée.")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

    # ── Utilitaires ────────────────────────────
    def _update_title(self):
        if self.db.is_open():
            name = os.path.basename(self.db.path)
            self.title(f"DB Manager — {name}")
            self.db_label.config(text=f"📂  {name}", fg=COLORS["text"])
        else:
            self.title("DB Manager — SQLite")
            self.db_label.config(text="Aucune base ouverte",
                                  fg=COLORS["text_muted"])

    def _set_status(self, msg: str):
        self.status_bar.config(text=f"  {msg}")


# ─────────────────────────────────────────────
#  Point d'entrée
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
