import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk

class SimpleTextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Prosty Edytor Tekstu")
        self.root.geometry("800x600")
        self.current_file = None

        # Skróty klawiszowe
        self.root.bind('<Control-s>', self.save_file)
        self.root.bind('<Control-S>', self.save_file)
        self.root.bind('<Control-z>', self.undo)
        self.root.bind('<Control-Z>', self.undo)
        self.root.bind('<Control-c>', self.copy)
        self.root.bind('<Control-C>', self.copy)
        self.root.bind('<Control-v>', self.paste)
        self.root.bind('<Control-V>', self.paste)

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
        self.text_editor = ScrolledText(self.editor_frame, undo=True, autoseparators=True, maxundo=-1)
        self.text_editor.pack(fill=tk.BOTH, expand=1)
        self.paned_window.add(self.editor_frame)

        # Załaduj drzewo plików
        self.populate_tree()

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
            try:
                with open(abspath, 'r', encoding='utf-8') as file:
                    content = file.read()
                self.text_editor.delete('1.0', tk.END)
                self.text_editor.insert(tk.END, content)
                self.root.title(f"Prosty Edytor Tekstu - {abspath}")
                self.current_file = abspath
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można otworzyć pliku: {e}")

    def open_file(self, event=None):
        filepath = filedialog.askopenfilename()
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                self.text_editor.delete('1.0', tk.END)
                self.text_editor.insert(tk.END, content)
                self.root.title(f"Prosty Edytor Tekstu - {filepath}")
                self.current_file = filepath
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można otworzyć pliku: {e}")

    def save_file(self, event=None):
        if self.current_file:
            try:
                content = self.text_editor.get('1.0', tk.END)
                with open(self.current_file, 'w', encoding='utf-8') as file:
                    file.write(content)
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
                messagebox.showinfo("Informacja", "Plik został zapisany.")
            except Exception as e:
                messagebox.showerror("Błąd", f"Nie można zapisać pliku: {e}")

    def undo(self, event=None):
        try:
            self.text_editor.edit_undo()
        except tk.TclError:
            pass  # Brak akcji do cofnięcia

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
        except tk.TclError:
            pass  # Schowek jest pusty

if __name__ == "__main__":
    root = tk.Tk()
    app = SimpleTextEditor(root)
    root.mainloop()



