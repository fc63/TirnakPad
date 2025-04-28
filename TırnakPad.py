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
        text_frame = tk.Frame(self, bg="black")
        text_frame.pack(expand=True, fill="both")
        
        self.line_numbers = tk.Canvas(text_frame, width=40, bg="black", highlightthickness=0)
        self.line_numbers.pack(side="left", fill="y")

        self.scrollbar = tk.Scrollbar(text_frame)
        self.scrollbar.pack(side="right", fill="y")

        self.text = tk.Text(
            text_frame,
            wrap="word",
            yscrollcommand=self.scrollbar.set,
            bg="black",
            fg="white",
            insertbackground="white",
            undo=True
        )
        self.text.pack(expand=True, fill="both")
        self.scrollbar.config(command=self.text.yview)
        self.text.pack(expand=True, fill="both")
        self.text.bind("<Button-2>", self.start_scroll)
        self.text.bind("<B2-Motion>", self.do_scroll)
        self.text.bind("\"", self.insert_quotes)
        self.text.bind("<Control-a>", self.select_all)
        self.text.bind("<Control-s>", self.ctrl_save)
        self.text.bind("<BackSpace>", self.confirm_delete)
        self.text.bind("<Delete>", self.confirm_delete)
        self.text.bind("<KeyRelease>", self.on_key_release)
        self.text.bind("<Button-1>", self.update_line_numbers)
        self.text.bind("<MouseWheel>", self.update_line_numbers)
        self.text.bind("<Configure>", self.update_line_numbers)
        self.text.bind("<Button-1>", self.on_mouse_click)
        self.text.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.text.bind("<ButtonRelease-2>", self.stop_scroll)
        self.text.bind("<Left>", self.on_left_key)
        self.text.bind("<Right>", self.on_right_key)
        self.text.bind("<Control-Key-1>", self.insert_region_splitter)

        self.quote_pairs = []

        self.text.tag_configure("active_quote", foreground="red")
        self.text.tag_configure("active_text", foreground="yellow")
        self.text.tag_configure("inactive_text", foreground="gray")
        self.text.tag_configure("normal_text", foreground="white")

        self.create_menu()
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    self.text.delete("1.0", "end")
                    self.text.insert("1.0", content)
                    self.current_file = file_path
                    self.saved_text = content
                    self.update_title()
                    self.highlight_quotes()

        self.update_line_numbers()

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
                self.update_line_numbers()

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
        if event.state & 0x0004:
            self.text.insert("insert", '"/<\n\n>\\"')
            self.text.mark_set("insert", "insert -1l linestart")
        else:
            self.text.insert("insert", '"')
        self.update_quote_pairs()
        self.highlight_quotes()
        return "break"

    def update_quote_pairs(self):
        self.update_regions()
        self.quote_pairs = []

        content = self.text.get("1.0", "end-1c")
        for region_start, region_end in self.regions:
            region_text = self.text.get(region_start, region_end)

            start_positions = []
            end_positions = []
            idx = 0
            while idx < len(region_text) - 2:
                if region_text[idx:idx+3] == '"/<':
                    start_positions.append(self.index_to_position_in_region(region_start, idx))
                    idx += 3
                elif region_text[idx:idx+3] == '>\\"':
                    end_positions.append(self.index_to_position_in_region(region_start, idx))
                    idx += 3
                else:
                    idx += 1

            temp_starts = start_positions.copy()
            temp_ends = end_positions.copy()

            while temp_starts and temp_ends:
                start = temp_starts.pop(0)
                end = temp_ends.pop(-1)
                self.quote_pairs.append((start, end))

    def on_left_key(self, event=None):
        cursor = self.text.index("insert")
        region_index = self.get_current_region_index(cursor)
        if region_index is None:
            return None
        region_start, region_end = self.regions[region_index]

        for start, end in self.quote_pairs:
            if self.text.compare(start, ">=", region_start) and self.text.compare(end, "<=", region_end):
                if self.text.compare(cursor, "==", f"{end} +3c"):
                    self.text.mark_set("insert", end)
                    return "break"
                if self.text.compare(cursor, "==", f"{start} +3c"):
                    self.text.mark_set("insert", start)
                    return "break"
                if self.text.compare(cursor, ">", start) and self.text.compare(cursor, "<", f"{start} +3c"):
                    self.text.mark_set("insert", start)
                    return "break"
                if self.text.compare(cursor, ">", end) and self.text.compare(cursor, "<", f"{end} +3c"):
                    self.text.mark_set("insert", end)
                    return "break"
        return None

    def on_right_key(self, event=None):
        cursor = self.text.index("insert")
        region_index = self.get_current_region_index(cursor)
        if region_index is None:
            return None
        region_start, region_end = self.regions[region_index]

        for start, end in self.quote_pairs:
            if self.text.compare(start, ">=", region_start) and self.text.compare(end, "<=", region_end):
                if self.text.compare(cursor, "==", start):
                    self.text.mark_set("insert", f"{start} +3c")
                    return "break"
                if self.text.compare(cursor, "==", end):
                    self.text.mark_set("insert", f"{end} +3c")
                    return "break"
                if self.text.compare(cursor, ">", start) and self.text.compare(cursor, "<", f"{start} +3c"):
                    self.text.mark_set("insert", f"{start} +3c")
                    return "break"
                if self.text.compare(cursor, ">", end) and self.text.compare(cursor, "<", f"{end} +3c"):
                    self.text.mark_set("insert", f"{end} +3c")
                    return "break"
        return None
        
    def index_to_position(self, index):
        lines = self.text.get("1.0", "end-1c").split("\n")
        total = 0
        for line_number, line in enumerate(lines, start=1):
            if total + len(line) >= index:
                return f"{line_number}.{index - total}"
            total += len(line) + 1
        return "end"
        
    def index_to_position_in_region(self, region_start, relative_idx):
        line, col = map(int, region_start.split("."))
        content = self.text.get("1.0", "end-1c")
        absolute_idx = self.position_to_absolute_index(region_start) + relative_idx
        lines = content.split("\n")
        total = 0
        for line_number, line_content in enumerate(lines, start=1):
            if total + len(line_content) >= absolute_idx:
                return f"{line_number}.{absolute_idx - total}"
            total += len(line_content) + 1
        return "end"
        
    def position_to_absolute_index(self, index):
        content = self.text.get("1.0", "end-1c")
        lines = content.split("\n")
        line, col = map(int, index.split("."))
        absolute = sum(len(lines[i]) + 1 for i in range(line - 1)) + col
        return absolute

    def select_all(self, event=None):
        self.update_quote_pairs()
        cursor = self.text.index("insert")
        region_index = self.get_current_region_index(cursor)
        if region_index is None:
            return "break"
        region_start, region_end = self.regions[region_index]

        for start, end in reversed(self.quote_pairs):
            if self.text.compare(start, ">=", region_start) and self.text.compare(end, "<=", region_end):
                if self.text.compare(f"{start} +1c", "<", cursor) and self.text.compare(cursor, "<=", end):
                    self.text.tag_remove("sel", "1.0", "end")
                    self.text.tag_add("sel", start, f"{end} +3c")
                    return "break"

        self.text.tag_remove("sel", "1.0", "end")
        self.text.tag_add("sel", region_start, region_end)
        return "break"

    def confirm_delete(self, event=None):
        cursor = self.text.index("insert")
        selection = self.text.tag_ranges("sel")
        region_index = self.get_current_region_index(cursor)
        if region_index is None:
            return None
        region_start, region_end = self.regions[region_index]

        if selection:
            start, end = selection
            self.update_quote_pairs()
            for q_start, q_end in self.quote_pairs:
                if self.text.compare(q_start, ">=", region_start) and self.text.compare(q_end, "<=", region_end):
                    if self.text.compare(start, "==", q_start) and self.text.compare(end, "==", f"{q_end} +3c"):
                        if not messagebox.askyesno("Onay", "Bu blok ve içeriği silinsin mi?"):
                            return "break"
                        else:
                            self.text.delete(q_start, f"{q_end} +3c")
                            self.update_quote_pairs()
                            self.highlight_quotes()
                            return "break"

        if cursor == "1.0" and event.keysym == "BackSpace":
            return None

        prev_cursor = self.text.index(f"{cursor} -1c")
        self.update_quote_pairs()
        for start, end in self.quote_pairs:
            if self.text.compare(start, ">=", region_start) and self.text.compare(end, "<=", region_end):
                if (event.keysym == "BackSpace" and (
                        self.text.compare(prev_cursor, ">=", start) and self.text.compare(prev_cursor, "<", f"{start} +3c")
                    )) or (event.keysym == "Delete" and (
                        self.text.compare(cursor, ">=", start) and self.text.compare(cursor, "<", f"{start} +3c")
                    )) or (event.keysym == "BackSpace" and (
                        self.text.compare(prev_cursor, ">=", end) and self.text.compare(prev_cursor, "<", f"{end} +3c")
                    )) or (event.keysym == "Delete" and (
                        self.text.compare(cursor, ">=", end) and self.text.compare(cursor, "<", f"{end} +3c")
                    )):
                    
                    if not messagebox.askyesno("Onay", "Bu blok ve içeriği silinsin mi?"):
                        return "break"
                    else:
                        self.text.delete(start, f"{end} +3c")
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
        region_index = self.get_current_region_index(cursor)

        if region_index is None:
            self.text.tag_add("normal_text", "1.0", "end-1c")
            return

        region_start, region_end = self.regions[region_index]

        active_found = False
        for start, end in reversed(self.quote_pairs):
            if self.text.compare(start, ">=", region_start) and self.text.compare(end, "<=", region_end):
                if self.text.compare(start, "<", cursor) and self.text.compare(cursor, "<=", end):
                    self.text.tag_add("active_quote", start, f"{start} +3c")
                    self.text.tag_add("active_quote", end, f"{end} +3c")
                    self.text.tag_add("active_text", f"{start} +3c", end)
                    if self.text.compare(region_start, "<", start):
                        self.text.tag_add("inactive_text", region_start, start)
                    if self.text.compare(f"{end} +3c", "<", region_end):
                        self.text.tag_add("inactive_text", f"{end} +3c", region_end)
                    active_found = True
                    break

        if not active_found:
            self.text.tag_add("normal_text", region_start, region_end)
            
    def get_current_region_index(self, cursor):
        for idx, (region_start, region_end) in enumerate(self.regions):
            if self.text.compare(cursor, ">=", region_start) and self.text.compare(cursor, "<=", region_end):
                return idx
        return None

    def on_key_release(self, event=None):
        self.highlight_quotes()
        self.update_title()
        self.update_line_numbers()
        
    def on_mouse_click(self, event=None):
        self.after(1, self.highlight_quotes)

    def on_mouse_release(self, event=None):
        self.after(1, self.highlight_quotes)
    
    def start_scroll(self, event):
        self.scroll_start_y = event.y
        self.text.config(cursor="fleur")

    def do_scroll(self, event):
        delta = event.y - self.scroll_start_y
        self.text.yview_scroll(int(delta / 2), "units")
        self.scroll_start_y = event.y
        self.update_line_numbers()
        
    def stop_scroll(self, event):
        self.text.config(cursor="xterm")

    def update_title(self):
        filename = self.current_file.split("/")[-1] if self.current_file else "(İsimsiz)"
        current_text = self.text.get("1.0", "end-1c")
        if current_text == self.saved_text:
            self.title(f"TırnakPad ({filename})")
        else:
            self.title(f"TırnakPad ({filename}*)")
            
    def update_line_numbers(self, event=None):
        self.line_numbers.delete("all")
        i = self.text.index("@0,0")
        while True:
            dline = self.text.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.line_numbers.create_text(2, y, anchor="nw", text=linenum, fill="gray", font=("Consolas", 10))
            i = self.text.index(f"{i}+1line")
            
    def update_regions(self):
        content = self.text.get("1.0", "end-1c")
        self.regions = []
        split_marker = "_<>_"
        start_idx = 0
        while True:
            marker_idx = content.find(split_marker, start_idx)
            if marker_idx == -1:
                break
            region_start = self.index_to_position(start_idx)
            region_end = self.index_to_position(marker_idx)
            self.regions.append((region_start, region_end))
            start_idx = marker_idx + len(split_marker)
        if start_idx <= len(content):
            region_start = self.index_to_position(start_idx)
            self.regions.append((region_start, "end-1c"))
           
    def insert_region_splitter(self, event=None):
        self.text.insert("insert", "_<>_")
        self.update_quote_pairs()
        self.highlight_quotes()
        return "break"

if __name__ == "__main__":
    app = TırnakPad()
    app.mainloop()