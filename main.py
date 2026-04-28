import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Файл для хранения избранного
        self.favorites_file = "favorites.json"
        self.favorites = self.load_favorites()
        
        # Создание GUI
        self.setup_ui()
        
    def setup_ui(self):
        # Верхняя панель с поиском
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="Поиск пользователя GitHub:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(top_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<Return>", lambda e: self.search_users())
        
        self.search_button = ttk.Button(top_frame, text="Найти", command=self.search_users)
        self.search_button.pack(side=tk.LEFT, padx=5)
        
        # Панель с кнопками избранного
        fav_frame = ttk.Frame(self.root, padding="10")
        fav_frame.pack(fill=tk.X)
        
        self.show_fav_button = ttk.Button(fav_frame, text="Показать избранное", command=self.show_favorites)
        self.show_fav_button.pack(side=tk.LEFT, padx=5)
        
        # Основная область с результатами поиска
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладка результатов поиска
        self.search_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.search_tab, text="Результаты поиска")
        
        # Таблица результатов
        self.result_tree = ttk.Treeview(self.search_tab, columns=("login", "id", "url"), show="tree headings")
        self.result_tree.heading("#0", text="Аватар")
        self.result_tree.heading("login", text="Логин")
        self.result_tree.heading("id", text="ID")
        self.result_tree.heading("url", text="URL профиля")
        
        self.result_tree.column("#0", width=60)
        self.result_tree.column("login", width=150)
        self.result_tree.column("id", width=80)
        self.result_tree.column("url", width=300)
        
        scrollbar = ttk.Scrollbar(self.search_tab, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Контекстное меню для результатов
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Добавить в избранное", command=self.add_to_favorites)
        self.context_menu.add_command(label="Открыть профиль в браузере", command=self.open_profile)
        
        self.result_tree.bind("<Button-3>", self.show_context_menu)
        
        # Вкладка избранного
        self.fav_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.fav_tab, text="Избранное")
        
        # Таблица избранного
        self.fav_tree = ttk.Treeview(self.fav_tab, columns=("login", "id", "url", "added"), show="tree headings")
        self.fav_tree.heading("#0", text="Аватар")
        self.fav_tree.heading("login", text="Логин")
        self.fav_tree.heading("id", text="ID")
        self.fav_tree.heading("url", text="URL профиля")
        self.fav_tree.heading("added", text="Дата добавления")
        
        self.fav_tree.column("#0", width=60)
        self.fav_tree.column("login", width=150)
        self.fav_tree.column("id", width=80)
        self.fav_tree.column("url", width=300)
        self.fav_tree.column("added", width=150)
        
        fav_scrollbar = ttk.Scrollbar(self.fav_tab, orient=tk.VERTICAL, command=self.fav_tree.yview)
        self.fav_tree.configure(yscrollcommand=fav_scrollbar.set)
        
        self.fav_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        fav_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Контекстное меню для избранного
        self.fav_context_menu = tk.Menu(self.root, tearoff=0)
        self.fav_context_menu.add_command(label="Удалить из избранного", command=self.remove_from_favorites)
        self.fav_context_menu.add_command(label="Открыть профиль в браузере", command=self.open_profile_fav)
        
        self.fav_tree.bind("<Button-3>", self.show_fav_context_menu)
        
        # Статусная строка
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def search_users(self):
        """Поиск пользователей GitHub"""
        query = self.search_entry.get().strip()
        
        # Проверка на пустое поле
        if not query:
            messagebox.showwarning("Предупреждение", "Поле поиска не может быть пустым!")
            self.status_var.set("Ошибка: поле поиска пустое")
            return
        
        self.status_var.set(f"Поиск пользователей по запросу: {query}...")
        self.search_button.config(state=tk.DISABLED)
        
        try:
            # API GitHub Search Users
            url = f"https://api.github.com/search/users?q={query}&per_page=30"
            headers = {
                "Accept": "application/vnd.github.v3+json"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get("items", [])
                
                # Очищаем таблицу
                for item in self.result_tree.get_children():
                    self.result_tree.delete(item)
                
                if users:
                    for user in users:
                        # Получаем дополнительные данные о пользователе
                        user_details = self.get_user_details(user["login"])
                        avatar_url = user.get("avatar_url", "")
                        
                        # Вставляем в таблицу
                        self.result_tree.insert("", tk.END, 
                                               text="🖼️",
                                               values=(
                                                   user["login"],
                                                   user_details.get("id", "N/A"),
                                                   user["html_url"]
                                               ))
                    
                    self.status_var.set(f"Найдено пользователей: {len(users)}")
                else:
                    self.status_var.set("Пользователи не найдены")
                    messagebox.showinfo("Результат", "Пользователи не найдены")
            else:
                self.status_var.set(f"Ошибка API: {response.status_code}")
                messagebox.showerror("Ошибка", f"Ошибка при запросе к API GitHub: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.status_var.set(f"Ошибка сети: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка сети: {str(e)}")
        finally:
            self.search_button.config(state=tk.NORMAL)
    
    def get_user_details(self, username):
        """Получение детальной информации о пользователе"""
        try:
            url = f"https://api.github.com/users/{username}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return {}
    
    def show_context_menu(self, event):
        """Показ контекстного меню для результатов поиска"""
        item = self.result_tree.identify_row(event.y)
        if item:
            self.result_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def add_to_favorites(self):
        """Добавление выбранного пользователя в избранное"""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.result_tree.item(item, "values")
        
        if values:
            login = values[0]
            user_id = values[1]
            url = values[2]
            
            # Проверяем, нет ли уже в избранном
            if login in self.favorites:
                messagebox.showinfo("Информация", f"Пользователь {login} уже в избранном")
                return
            
            # Добавляем в избранное
            self.favorites[login] = {
                "login": login,
                "id": user_id,
                "url": url,
                "added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.save_favorites()
            self.refresh_favorites_tab()
            self.status_var.set(f"Пользователь {login} добавлен в избранное")
    
    def remove_from_favorites(self):
        """Удаление пользователя из избранного"""
        selection = self.fav_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.fav_tree.item(item, "values")
        
        if values:
            login = values[0]
            if login in self.favorites:
                del self.favorites[login]
                self.save_favorites()
                self.refresh_favorites_tab()
                self.status_var.set(f"Пользователь {login} удалён из избранного")
    
    def open_profile(self):
        """Открытие профиля в браузере (результаты поиска)"""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.result_tree.item(item, "values")
        
        if values and len(values) >= 3:
            import webbrowser
            webbrowser.open(values[2])
    
    def open_profile_fav(self):
        """Открытие профиля в браузере (избранное)"""
        selection = self.fav_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.fav_tree.item(item, "values")
        
        if values and len(values) >= 3:
            import webbrowser
            webbrowser.open(values[2])
    
    def show_favorites(self):
        """Показ вкладки с избранным"""
        self.refresh_favorites_tab()
        self.notebook.select(self.fav_tab)
    
    def refresh_favorites_tab(self):
        """Обновление вкладки избранного"""
        # Очищаем таблицу
        for item in self.fav_tree.get_children():
            self.fav_tree.delete(item)
        
        # Заполняем избранным
        for login, data in self.favorites.items():
            self.fav_tree.insert("", tk.END,
                               text="⭐",
                               values=(
                                   data["login"],
                                   data["id"],
                                   data["url"],
                                   data.get("added", "N/A")
                               ))
    
    def show_fav_context_menu(self, event):
        """Показ контекстного меню для избранного"""
        item = self.fav_tree.identify_row(event.y)
        if item:
            self.fav_tree.selection_set(item)
            self.fav_context_menu.post(event.x_root, event.y_root)
    
    def load_favorites(self):
        """Загрузка избранного из JSON файла"""
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_favorites(self):
        """Сохранение избранного в JSON файл"""
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить избранное: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()
