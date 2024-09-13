import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk

class SimpleTextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Prosty Edytor Tekstu")
        self.root.geometry("800x600")
        self.current_file = None

        # Domyślny rozmiar czcionki
        self.font_size = 12
        self.font_family = 'TkDefaultFont'

        # Skróty klawiszowe
        self.root.bind('<Control-s>', self.save_file)
        self.root.bind('<Control-S>', self.save_file)
        self.root.bind('<Control-z>', self.undo)
        self.root.bind('<Control-Z>', self.undo)
        self.root.bind('<Control-y>', self.redo)
        self.root.bind('<Control-Y>', self.redo)
        self.root.bind('<Control-c>', self.copy)
        self.root.bind('<Control-C>', self.copy)
        self.root.bind('<Control-v>', self.paste)
        self.root.bind('<Control-V>', self.paste)
        self.root.bind('<Control-x>', self.cut)
        self.root.bind('<Control-X>', self.cut)
        self.root.bind('<Control-k>', self.delete_line)
        self.root.bind('<Control-K>', self.delete_line)
        self.root.bind('<Control-f>', self.find_text)
        self.root.bind('<Control-F>', self.find_text)
        self.root.bind('<Control-r>', self.replace_text)
        self.root.bind('<Control-R>', self.replace_text)
        self.root.bind('<Control-plus>', self.increase_font_size)
        self.root.bind('<Control-minus>', self.decrease_font_size)
        self.root.bind('<Control-=>', self.increase_font_size)  # Dla klawiatur bez klawisza plus
        self.root.bind('<Control-underscore>', self.decrease_font_size)  # Dla klawiatur bez klawisza minus

        # Menu górne
        self.menu = tk.Menu(self.root)
        self.root.config(menu=self.menu)
        self.file_menu = tk.Menu(self.menu, tearoff=False)
        self.menu.add_cascade(label="Plik", menu=self.file_menu)
        self.file_menu.add_command(label="Otwórz", command=self.open_file)
        self.file_menu.add_command(label="Zapisz", command=self.save_file)
        self.file_menu.add_command(label="Zapisz jako...", command=self.save_file_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Wyjdź", command=self.root.quit)

        # Ramka główna
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=1)

        # Podział na panel przeglądarki i edytora
        self.paned_window = tk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=1)

        # Panel przeglądarki plików
        self.browser_frame = tk.Frame(self.paned_window)
        self.tree = ttk.Treeview(self.browser_frame)
        self.tree.pack(fill=tk.BOTH, expand=1)
        self.tree.bind('<<TreeviewOpen>>', self.on_folder_open)
        self.tree.bind('<<TreeviewSelect>>', self.on_file_select)
        self.paned_window.add(self.browser_frame, minsize=200)

        # Panel edytora tekstu
        self.editor_frame = tk.Frame(self.paned_window)
        self.text_editor = ScrolledText(
            self.editor_frame,
            undo=True,
            autoseparators=True,
            maxundo=-1,
            font=(self.font_family, self.font_size)
        )
        self.text_editor.pack(fill=tk.BOTH, expand=1)
        self.paned_window.add(self.editor_frame)

        # Dodajemy obsługę kolorowania składni
        self.text_editor.bind('<KeyRelease>', self.on_key_release)

        # Definicje wzorców składni i kolorów
        self.syntax_patterns = {
            'keyword': r'\b(import|from|class|def|return|if|else|elif|while|for|in|try|except|with|as|pass|break|continue|lambda|yield|global|nonlocal|assert|async|await|True|False|None)\b',
            'string': r'(\".*?\"|\'.*?\')',
            'comment': r'\#.*',
            'number': r'\b\d+\.?\d*\b',
            'operator': r'[-+/*%=<>!&|^~]',
            'bracket': r'[\[\]\{\}\(\)]',
        }

        self.syntax_colors = {
            'keyword': '#ff7f50',   # Coral
            'string': '#daa520',    # Goldenrod
            'comment': '#7cfc00',   # LawnGreen
            'number': '#87ceeb',    # SkyBlue
            'operator': '#f08080',  # LightCoral
            'bracket': '#ffa500',   # Orange
        }

        # Tworzenie tagów dla kolorowania składni
        for tag, color in self.syntax_colors.items():
            self.text_editor.tag_configure(tag, foreground=color)

        # Załaduj drzewo plików
        self.populate_tree()

        # Ustawienia edytora
        self.text_editor.edit_modified(False)
        self.text_editor.bind('<<Modified>>', self.on_modified)

    def populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        path = os.getcwd()
        node = self.tree.insert('', 'end', text=path, open=True, values=[path])
        self.process_directory(node, path)

    def process_directory(self, parent, path):
        try:
            for p in os.listdir(path):
                abspath = os.path.join(path, p)
                isdir = os.path.isdir(abspath)
                node = self.tree.insert(parent, 'end', text=p, open=False, values=[abspath])
                if isdir:
                    self.tree.insert(node, 'end')  # Dodajemy pusty węzeł, żeby pokazać strzałkę
        except PermissionError:
            pass

    def on_folder_open(self, event):
        node = self.tree.focus()
        abspath = self.tree.item(node, 'values')[0]
        if os.path.isdir(abspath):
            # Usuń wszystkie dzieci
            self.tree.delete(*self.tree.get_children(node))
            self.process_directory(node, abspath)

    def on_file_select(self, event):
        selected = self.tree.focus()
        abspath = self.tree.item(selected, 'values')[0]
        if os.path.isfile(abspath):
            self.open_file(filepath=abspath)

    def open_file(self, event=None, filepath=None):
        if not filepath:
            filepath = filedialog.askopenfilename()
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                self.text_editor.delete('1.0', tk.END)
                self.text_editor.insert(tk.END, content)
                self.text_editor.edit_reset()  # Resetuje stos cofania
                self.text_editor.edit_modified(False)  # Resetuje flagę modyfikacji
                self.root.title(f"Prosty Edytor Tekstu - {filepath}")
                self.current_file = filepath
                self.highlight_syntax()
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można otworzyć pliku: {e}")

    def save_file(self, event=None):
        if self.current_file:
            try:
                content = self.text_editor.get('1.0', tk.END)
                with open(self.current_file, 'w', encoding='utf-8') as file:
                    file.write(content)
                self.text_editor.edit_modified(False)  # Resetuje flagę modyfikacji
                messagebox.showinfo("Informacja", "Plik został zapisany.")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać pliku: {e}")
        else:
            self.save_file_as()

    def save_file_as(self, event=None):
        filepath = filedialog.asksaveasfilename(defaultextension=".txt")
        if filepath:
            try:
                content = self.text_editor.get('1.0', tk.END)
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(content)
                self.root.title(f"Prosty Edytor Tekstu - {filepath}")
                self.current_file = filepath
                self.text_editor.edit_modified(False)  # Resetuje flagę modyfikacji
                messagebox.showinfo("Informacja", "Plik został zapisany.")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać pliku: {e}")

    def on_modified(self, event=None):
        self.text_editor.edit_modified(False)  # Resetuje flagę modyfikacji

    def undo(self, event=None):
        try:
            self.text_editor.edit_undo()
        except tk.TclError:
            pass  # Brak akcji do cofnięcia

    def redo(self, event=None):
        try:
            self.text_editor.edit_redo()
        except tk.TclError:
            pass  # Brak akcji do ponowienia

    def copy(self, event=None):
        try:
            self.root.clipboard_clear()
            selected_text = self.text_editor.get("sel.first", "sel.last")
            self.root.clipboard_append(selected_text)
        except tk.TclError:
            pass  # Brak zaznaczonego tekstu

    def paste(self, event=None):
        try:
            cursor_position = self.text_editor.index(tk.INSERT)
            clipboard_content = self.root.clipboard_get()
            self.text_editor.insert(cursor_position, clipboard_content)
            self.highlight_syntax()
        except tk.TclError:
            pass  # Schowek jest pusty

    def cut(self, event=None):
        try:
            self.copy()
            self.text_editor.delete("sel.first", "sel.last")
        except tk.TclError:
            pass  # Brak zaznaczonego tekstu

    def delete_line(self, event=None):
        cursor_line = self.text_editor.index("insert").split(".")[0]
        self.text_editor.delete(f"{cursor_line}.0", f"{cursor_line}.0 lineend")
        self.text_editor.edit_separator()  # Dodaj separator do stosu cofania

    def find_text(self, event=None):
        search_query = simpledialog.askstring("Wyszukaj", "Wprowadź tekst do wyszukania:")
        if search_query:
            start_pos = '1.0'
            self.text_editor.tag_remove('highlight', '1.0', tk.END)
            while True:
                start_pos = self.text_editor.search(search_query, start_pos, stopindex=tk.END)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(search_query)}c"
                self.text_editor.tag_add('highlight', start_pos, end_pos)
                start_pos = end_pos
            self.text_editor.tag_config('highlight', background='yellow')

    def replace_text(self, event=None):
        find_query = simpledialog.askstring("Zamień", "Znajdź:")
        replace_query = simpledialog.askstring("Zamień", "Zamień na:")
        if find_query and replace_query is not None:
            idx = '1.0'
            while True:
                idx = self.text_editor.search(find_query, idx, tk.END)
                if not idx:
                    break
                end_idx = f"{idx}+{len(find_query)}c"
                self.text_editor.delete(idx, end_idx)
                self.text_editor.insert(idx, replace_query)
                idx = end_idx
            messagebox.showinfo("Informacja", f"Zastąpiono wszystkie wystąpienia '{find_query}' na '{replace_query}'.")

    def on_key_release(self, event=None):
        self.highlight_syntax()

    def highlight_syntax(self, event=None):
        content = self.text_editor.get('1.0', tk.END)
        for tag in self.syntax_colors.keys():
            self.text_editor.tag_remove(tag, '1.0', tk.END)

        for tag, pattern in self.syntax_patterns.items():
            for match in re.finditer(pattern, content):
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.text_editor.tag_add(tag, start_index, end_index)

    def increase_font_size(self, event=None):
        self.font_size += 1
        self.text_editor.configure(font=(self.font_family, self.font_size))

    def decrease_font_size(self, event=None):
        if self.font_size > 1:
            self.font_size -= 1
            self.text_editor.configure(font=(self.font_family, self.font_size))

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleTextEditor(root)
    root.mainloop()
