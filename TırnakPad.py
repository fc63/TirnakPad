import tkinter as tk
import sys
import os
from tkinter import messagebox, filedialog

class TırnakPad(tk.Tk):
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.saved_text = ""

        self.title("TırnakPad")
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, 'icon.ico')
        else:
            icon_path = 'icon.ico'

        self.iconbitmap(icon_path)
        self.geometry("800x600")
        self.configure(bg="black")

        self.text = tk.Text(self, wrap="word", bg="black", fg="white", insertbackground="white", undo=True)
        self.text.pack(expand=True, fill="both")

        self.text.bind("\"", self.insert_quotes)
        self.text.bind("<Control-a>", self.select_all)
        self.text.bind("<Control-s>", self.ctrl_save)
        self.text.bind("<BackSpace>", self.confirm_delete)
        self.text.bind("<Delete>", self.confirm_delete)
        self.text.bind("<KeyRelease>", self.on_key_release)

        self.quote_pairs = []

        self.text.tag_configure("active_quote", foreground="red")
        self.text.tag_configure("active_text", foreground="yellow")
        self.text.tag_configure("inactive_text", foreground="gray")
        self.text.tag_configure("normal_text", foreground="white")

        self.create_menu()

    def create_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Aç", command=self.open_file)
        file_menu.add_command(label="Kaydet", command=self.save_file)
        file_menu.add_command(label="Farklı Kaydet", command=self.save_as_file)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        self.config(menu=menubar)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
                self.text.delete("1.0", "end")
                self.text.insert("1.0", content)
                self.current_file = file_path
                self.saved_text = content
                self.update_title()
                self.highlight_quotes()

    def save_file(self):
        if self.current_file:
            with open(self.current_file, "w", encoding="utf-8") as file:
                file.write(self.text.get("1.0", "end-1c"))
            self.saved_text = self.text.get("1.0", "end-1c")
            self.update_title()
        else:
            self.save_as_file()

    def ctrl_save(self, event=None):
        self.save_file()
        return "break"

    def save_as_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.current_file = file_path
            self.save_file()

    def insert_quotes(self, event=None):
        self.text.insert("insert", '"\n\n"')
        self.text.mark_set("insert", "insert -1 lines")
        self.update_quote_pairs()
        self.highlight_quotes()
        return "break"

    def update_quote_pairs(self):
        content = self.text.get("1.0", "end-1c")
        positions = []
        idx = 0
        while idx < len(content):
            if content[idx] == '"':
                positions.append(self.index_to_position(idx))
            idx += 1

        self.quote_pairs = []
        temp_positions = positions.copy()
        while len(temp_positions) >= 2:
            first = temp_positions.pop(0)
            last = temp_positions.pop(-1)
            self.quote_pairs.append((first, last))

    def index_to_position(self, index):
        lines = self.text.get("1.0", "end-1c").split("\n")
        total = 0
        for line_number, line in enumerate(lines, start=1):
            if total + len(line) >= index:
                return f"{line_number}.{index - total}"
            total += len(line) + 1
        return "end"

    def select_all(self, event=None):
        self.update_quote_pairs()
        cursor = self.text.index("insert")
        for start, end in reversed(self.quote_pairs):
            if self.text.compare(start, "<=", cursor) and self.text.compare(cursor, "<=", end):
                self.text.tag_remove("sel", "1.0", "end")
                self.text.tag_add("sel", start, f"{end} +1c")
                return "break"
        self.text.tag_add("sel", "1.0", "end-1c")
        return "break"

    def confirm_delete(self, event=None):
        cursor = self.text.index("insert")
        if cursor == "1.0" and event.keysym == "BackSpace":
            return None
        prev_cursor = self.text.index(f"{cursor} -1c")
        self.update_quote_pairs()
        for start, end in self.quote_pairs:
            if (event.keysym == "BackSpace" and self.text.compare(prev_cursor, "==", start)) or \
               (event.keysym == "Delete" and self.text.compare(cursor, "==", start)) or \
               (event.keysym == "BackSpace" and self.text.compare(prev_cursor, "==", end)) or \
               (event.keysym == "Delete" and self.text.compare(cursor, "==", end)):
                if not messagebox.askyesno("Onay", "Bu tırnak ve bağlı tırnağı silmek istiyor musun?"):
                    return "break"
                else:
                    self.text.delete(start)
                    self.text.delete(end)
                    self.update_quote_pairs()
                    self.highlight_quotes()
                    return "break"
        return None

    def highlight_quotes(self, event=None):
        self.update_quote_pairs()
        self.text.tag_remove("active_quote", "1.0", "end")
        self.text.tag_remove("active_text", "1.0", "end")
        self.text.tag_remove("inactive_text", "1.0", "end")
        self.text.tag_remove("normal_text", "1.0", "end")

        cursor = self.text.index("insert")
        active_found = False
        for start, end in reversed(self.quote_pairs):
            if self.text.compare(start, "<=", cursor) and self.text.compare(cursor, "<=", end):
                self.text.tag_add("active_quote", start, f"{start} +1c")
                self.text.tag_add("active_quote", end, f"{end} +1c")
                self.text.tag_add("active_text", f"{start} +1c", end)
                self.text.tag_add("inactive_text", "1.0", start)
                self.text.tag_add("inactive_text", f"{end} +1c", "end")
                active_found = True
                break
        if not active_found:
            self.text.tag_add("normal_text", "1.0", "end-1c")

    def on_key_release(self, event=None):
        self.highlight_quotes()
        self.update_title()

    def update_title(self):
        filename = self.current_file.split("/")[-1] if self.current_file else "(İsimsiz)"
        current_text = self.text.get("1.0", "end-1c")
        if current_text == self.saved_text:
            self.title(f"TırnakPad ({filename})")
        else:
            self.title(f"TırnakPad ({filename}*)")

if __name__ == "__main__":
    app = TırnakPad()
    app.mainloop()