import sqlite3
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog
from PIL import ImageTk, Image


def get_user_name():
    user_name = simpledialog.askstring("hi!", "Enter your name:")
    return user_name


def see_notes():
    notes_window = tk.Toplevel(root)
    notes_window.title("My Notes")
    notes_window.configure(bg="white")

    title_style = ttk.Style()
    title_style.configure("Title.TLabel", font=("Arial", 18, "bold"),
                          foreground="#008199", background="white")

    notes_frame = ttk.Frame(notes_window, padding=100, height=800, width=600)
    notes_frame.pack(fill=tk.BOTH, expand=True)

    notes_frame_style = ttk.Style()
    notes_frame_style.configure("Notes.TFrame", background="white")
    notes_frame.configure(style="Notes.TFrame")

    notes_label = ttk.Label(notes_frame, text="My Notes")
    notes_label.configure(style="Title.TLabel", font=("Arial", 24, "bold"), foreground="#0097B2")
    notes_label.pack(side=tk.TOP, pady=(10, 30))

    cursor.execute("SELECT id, title, date_modified FROM notes2 WHERE user_name=? ORDER BY date_modified", (user_name,))
    notes = cursor.fetchall()

    tree = ttk.Treeview(notes_frame, columns=("Title", "Last Modified:"), show="headings")
    tree.heading("Title", text="   Title   ")
    tree.heading("Last Modified:", text="   Last Modified:   ")
    tree.pack(fill=tk.BOTH, expand=True)

    style = ttk.Style()
    style.configure("Treeview", font=("Arial", 12), background="white")
    style.configure("Treeview.Heading", font=("Arial", 14))
    for note in notes:
        tree.insert("", 0, values=(note[1], note[2], note[0]))

    def display_note(event):
        selected_items = tree.selection()
        if not selected_items:
            return
        selected_item = selected_items[0]
        note_id = tree.item(selected_item, "values")[2]

        cursor.execute("SELECT title, content, date_modified, note_type FROM notes2 WHERE id=?", (note_id,))
        note_data = cursor.fetchone()
        print('Note data: ', note_data)

        note_popup = tk.Toplevel(notes_window)
        note_popup.title(note_data[0])
        note_popup.geometry("800x600")

        title_label = ttk.Label(note_popup, text=f"{note_data[0]}", font=("Arial", 20, "bold"), foreground="#0097B2")
        title_label.pack(padx=10, pady=(10, 20))

        print('Last Modified:', note_data[2])
        date_label = ttk.Label(note_popup, text=f"Last Modified: {note_data[2]}", font=("Arial", 12, "italic"),
                               foreground="#0097B2", background="#D9D9D9")
        date_label.pack(pady=10)

        content_frame = ttk.Frame(note_popup, borderwidth=2, relief="solid", width=600, height=800, padding=10)
        content_frame.pack(padx=10, pady=10)

        if note_data[3] == 'list':
            cursor.execute("SELECT id, content, checked FROM list_items WHERE note_id=?", (note_id,))
            note_items = cursor.fetchall()
            canvas = tk.Canvas(content_frame)
            canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

            scroll_frame = ttk.Frame(canvas)
            canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
            checkboxes = []

            def make_delete_item(item_id):
                def delete_item(event):
                    result = messagebox.askquestion("Delete item", "Are you sure you want to delete this?",
                                                    icon='warning')
                    if result == 'yes':
                        cursor.execute("DELETE FROM list_items WHERE id = ?", (item_id,))
                        conn.commit()
                        cursor.execute("SELECT COUNT(*) FROM list_items WHERE note_id = ?", (note_id,))
                        count = cursor.fetchone()[0]
                        if count == 0:
                            cursor.execute("DELETE FROM notes2 WHERE id = ?", (note_id,))
                            conn.commit()
                        refresh_treeview()
                        note_popup.destroy()
                        display_note(event)

                return delete_item

            for item_id, item_content, checked in note_items:
                var = tk.IntVar(value=checked)
                style = ttk.Style()
                style.configure("CustomCheckbutton.TCheckbutton", font=("Arial", 13))
                checkbox = ttk.Checkbutton(scroll_frame, text=item_content, variable=var,
                                           style="CustomCheckbutton.TCheckbutton")
                checkbox.pack(anchor='w', padx=10, pady=10)
                checkboxes.append((checkbox, var, item_id))
                checkbox.bind("<Button-3>", make_delete_item(item_id))

            def update_list():
                updated_items = [checkbox.cget('text') for checkbox, var, item_id in checkboxes if var.get() == 0]
                updated_checked_states = {item_id: var.get() for checkbox, var, item_id in checkboxes}
                new_items = [entry.get() for entry, var in entries if entry.get().strip() != '']
                updated_content = '\n'.join(updated_items + new_items)

                cursor.execute(
                    "UPDATE notes2 SET content = ?, date_modified = datetime('now', '+2 hours') WHERE id = ?",
                    (updated_content, note_id))
                for item_id, checked_state in updated_checked_states.items():
                    cursor.execute("UPDATE list_items SET checked = ? WHERE id = ?", (checked_state, item_id))

                for new_item in new_items:
                    cursor.execute("INSERT INTO list_items (note_id, content, checked) VALUES (?, ?, 0)",
                                   (note_id, new_item))

                conn.commit()
                note_popup.destroy()
                refresh_treeview()
                display_note(event)

            button_frame = ttk.Frame(note_popup)
            button_frame.pack(pady=(10, 20), padx=(20, 20))

            update_button = ttk.Button(button_frame, text="Update List", command=update_list)
            update_button.grid(row=0, column=0, padx=(0, 20))

            entries = []
            def add_item():
                item_var = tk.StringVar()
                item_entry = ttk.Entry(scroll_frame, textvariable=item_var)
                item_entry.pack()
                entries.append((item_entry, item_var))
                scroll_frame.update()
                canvas.configure(scrollregion=canvas.bbox('all'))
                canvas.yview_moveto(1)
                canvas.update_idletasks()

            add_item_button = ttk.Button(button_frame, text="Add Item", command=add_item)
            add_item_button.grid(row=0, column=1)

        else:
            content_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD,
                                                     width=40, height=10, font=("Arial", 16))
            content_text.insert(tk.END, note_data[1])
            content_text.pack(fill=tk.BOTH, expand=True)
            content_text.bind("<Button-1>", lambda e: edit_label(note_id, content_text, "Content"))

        def close_note():
            note_popup.destroy()
            refresh_treeview()

        def delete_note():
            confirm_delete = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this note?")
            if confirm_delete:
                cursor.execute("DELETE FROM notes2 WHERE id=?", (note_id,))
                conn.commit()
                note_popup.destroy()
                refresh_treeview()

        button_frame = ttk.Frame(note_popup)
        button_frame.pack(pady=(10, 20), padx=(20, 20))

        close_button = ttk.Button(button_frame, text="Close", command=close_note)
        close_button.grid(row=0, column=0, padx=(0, 20))

        delete_button = ttk.Button(button_frame, text="Delete", command=delete_note)
        delete_button.grid(row=0, column=1)

        delete_button_style = ttk.Style()
        delete_button_style.configure("Red.TButton", foreground="red", background="red")
        delete_button.configure(style="Red.TButton")

        title_label.bind("<Button-1>", lambda e: edit_label(note_id, title_label, "Title"))

        def edit_label(note_id, widget, label_type):
            edit_window = tk.Toplevel()
            edit_window.title(f"Edit {label_type}")

            if isinstance(widget, ttk.Label):
                edit_entry = ttk.Entry(edit_window, font=("Arial", 16))
                edit_entry.insert(0, widget.cget("text"))
            elif isinstance(widget, scrolledtext.ScrolledText):
                edit_entry = scrolledtext.ScrolledText(edit_window, wrap=tk.WORD, width=40, height=10,
                                                       font=("Arial", 16))
                edit_entry.insert(tk.END, widget.get("1.0", tk.END))
            else:
                edit_entry = None

            if edit_entry:
                edit_entry.pack(padx=10, pady=10)
                save_button = ttk.Button(edit_window, text="Save Changes",
                                         command=lambda: save_changes(note_id, widget, label_type, edit_entry,
                                                                      edit_window))
                save_button.pack(pady=10)

        def save_changes(note_id, widget, label_type, new_text_widget, edit_window):
            new_text = ""
            if isinstance(new_text_widget, ttk.Entry):
                new_text = new_text_widget.get()
            elif isinstance(new_text_widget, scrolledtext.ScrolledText):
                new_text = new_text_widget.get("1.0", "end-1c")

            if label_type == "Title":
                widget.config(text=new_text)
                update_database(note_id, label_type, new_text)
            elif label_type == "Content":
                widget.delete("1.0", tk.END)
                widget.insert(tk.END, new_text)
                update_database(note_id, label_type, new_text)

            edit_window.destroy()
            refresh_treeview()

        def update_database(note_id, label_type, new_text):
            if label_type == "Title":
                cursor.execute("UPDATE notes2 SET title=?, date_modified=datetime('now', '+2 hours') WHERE id=?",
                               (new_text, note_id))
            elif label_type == "Content":
                cursor.execute("UPDATE notes2 SET content=?, date_modified=datetime('now', '+2 hours') WHERE id=?",
                               (new_text, note_id))
            conn.commit()

    tree.bind("<Double-1>", display_note)   # user face double click pe un element din tree => display_note()

    def close_notes():
        notes_window.destroy()
        refresh_treeview()

    close_button = ttk.Button(notes_window, text="Close", command=close_notes)
    close_button.pack(pady=(10, 20), padx=(20, 20))

    def refresh_treeview():
        if tree.winfo_exists():
            for item in tree.get_children():
                tree.delete(item)
            cursor.execute("SELECT id, title, date_modified FROM notes2 WHERE user_name=? ORDER BY date_modified DESC",
                           (user_name,))
            notes = cursor.fetchall()

            for note in notes:
                tree.insert("", "end", values=(note[1], note[2], note[0]))


def create_note():
    create_note_window = tk.Toplevel(root)
    create_note_window.title("New Note")

    create_note_window.geometry("500x300")
    create_note_window.configure(bg="#008199")

    label = ttk.Label(create_note_window, text="Choose the type of note:",
                      font=("Arial", 16), foreground="white", background="#008199")
    label.pack(padx=10, pady=30)

    text_note_button = ttk.Button(create_note_window, text="Text Note",
                                  command=lambda: create_text_note(create_note_window))
    text_note_button.pack(padx=10, pady=20)

    list_note_button = ttk.Button(create_note_window, text="List",
                                  command=lambda: create_list_note(create_note_window))
    list_note_button.pack(padx=10, pady=20)


def create_text_note(text_note_window):
    text_note_window.destroy()
    text_note_window = tk.Toplevel()
    text_note_window.title("New Text Note")

    text_note_window.configure(bg="#008199")

    title_label = ttk.Label(text_note_window, text="Title:",
                            font=("Arial", 18, "bold"), foreground="white", background="#008199")
    title_label.grid(row=0, column=0, padx=20, pady=20, sticky="W")

    title_entry = ttk.Entry(text_note_window, width=60, font=("Arial", 16))
    title_entry.grid(row=0, column=1, padx=20, pady=20)

    content_label = ttk.Label(text_note_window, text="Content:",
                              font=("Arial", 18, "bold"), foreground="white", background="#008199")
    content_label.grid(row=1, column=0, padx=20, pady=20, sticky="W")

    content_entry = tk.Text(text_note_window, width=60, height=15, font=("Arial", 16))
    content_entry.grid(row=1, column=1, padx=20, pady=20)

    def save_note():
        title = title_entry.get()
        content = content_entry.get("1.0", tk.END)

        cursor.execute("INSERT INTO notes2 (title, content, date_modified, note_type, user_name)"
                       " VALUES (?, ?, datetime('now', '+2 hours'), 'text', ?)",
                       (title, content, user_name))
        conn.commit()

        text_note_window.destroy()

    save_button = ttk.Button(text_note_window, text="Save", command=save_note, width=20)
    save_button.grid(row=2, column=1, padx=(20, 0), pady=(0, 20), sticky="W")

    close_button = ttk.Button(text_note_window, text="Close", command=text_note_window.destroy)
    close_button.grid(row=2, column=2, padx=(0, 50), pady=(20, 20), sticky="W")


def create_list_note(create_note_window):
    create_note_window.destroy()
    list_note_window = tk.Toplevel()
    list_note_window.title("New List Note")

    list_note_window.geometry("800x600")

    main_frame = ttk.Frame(list_note_window)
    main_frame.pack(fill='both', expand=True)

    canvas = tk.Canvas(main_frame)
    canvas.pack(side='left', fill='both', expand=True)

    scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=canvas.yview)
    scrollbar.pack(side='right', fill='y')
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

    scrollable_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=scrollable_frame, anchor='nw')

    title_label = ttk.Label(scrollable_frame, text="Title:",
                            font=("Arial", 18, "bold"), foreground="#FFFFFF", background="#008199")
    title_label.grid(row=0, column=0, padx=20, pady=20, sticky="W")

    title_entry = ttk.Entry(scrollable_frame, width=60, font=("Arial", 16))
    title_entry.grid(row=0, column=1, padx=20, pady=20)

    list_items = []

    def add_item():
        item = ttk.Entry(scrollable_frame, width=60, font=("Arial", 16))
        item.grid(row=len(list_items)+2, column=1, padx=20, pady=20)
        list_items.append(item)
        scrollable_frame.update()  # update cadru scrollable sa vad ultimu elem
        canvas.configure(scrollregion=canvas.bbox('all'))  # update canva pt scroll

    button_frame = ttk.Frame(list_note_window)
    button_frame.pack(fill='x', side='top')

    add_item_button = ttk.Button(button_frame, text="Add Item", command=add_item)
    add_item_button.pack(padx=20, pady=20)

    def save_list_note():
        title = title_entry.get()
        if not title.strip():  # verif daca e gol
            title = "No title"
        list_content = "\n".join([item.get() for item in list_items])

        cursor.execute(
            "INSERT INTO notes2 (title, content, date_modified, note_type, user_name) "
            "VALUES (?, ?, datetime('now', '+2 hours'), 'list', ?)",
            (title, "", user_name))
        conn.commit()
        note_id = cursor.lastrowid  # ultima inreg adaugata

        for item in list_items:
            item_content = item.get().strip()
            if item_content:  # verif sa nu fie gol elem
                cursor.execute(
                    "INSERT INTO list_items (note_id, content, checked) VALUES (?, ?, 0)",
                    (note_id, item_content)
                )
        conn.commit()
        list_note_window.destroy()

    button_frame = ttk.Frame(list_note_window)
    button_frame.pack(fill='x', side='bottom')

    close_button = ttk.Button(button_frame, text="Close", command=list_note_window.destroy)
    close_button.pack(side='left', padx=20, pady=20)

    save_button = ttk.Button(button_frame, text="Save List", command=save_list_note, width=20)
    save_button.pack(side='right', padx=20, pady=20)


conn = sqlite3.connect('notes2.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes2 (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        date_modified TEXT,
        note_type TEXT
    )
''')
conn.commit()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS list_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER,
        content TEXT,
        checked INTEGER DEFAULT 0,
        FOREIGN KEY(note_id) REFERENCES notes2(id)
    )
''')
conn.commit()
user_name = get_user_name()
print(user_name)
root = tk.Tk()
root.title("Memo App")
root.geometry("800x600")
root.configure(bg="white")

main_page_frame = ttk.Frame(root, padding="10", style="Main.TFrame")
main_page_frame.pack()

style = ttk.Style()
style.configure("Main.TFrame", background="white")
style.configure("TLabel", background="white")

logo = Image.open('logo.jpg')
resized_logo = logo.resize((250, 250), Image.BILINEAR)
logo_image = ImageTk.PhotoImage(resized_logo)

logo_label = ttk.Label(main_page_frame, image=logo_image)
logo_label.grid(row=0, column=0, columnspan=2, pady=(10, 20))

title_label = ttk.Label(main_page_frame, text="Memo App", font=("Arial", 24, "bold"), foreground="#0097B2")
title_label.grid(row=1, column=0, columnspan=2, pady=(10, 20))

button_style = ttk.Style()
button_style.configure("TButton", font=("Arial", 14), width=15, foreground="#0097B2", background="#008199")

see_notes_button = ttk.Button(main_page_frame, text="See My Notes", command=see_notes, style="TButton")
see_notes_button.grid(row=2, column=0, pady=20)

create_note_button = ttk.Button(main_page_frame, text="Create a Note", command=create_note, style="TButton")
create_note_button.grid(row=2, column=1, pady=20, padx=10)

root.mainloop()
conn.close()
