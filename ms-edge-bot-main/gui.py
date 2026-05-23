"""
Microsoft Edge Search Bot - GUI Application with Modern UI
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
from io import StringIO
from edge_search_bot import EdgeSearchBot, load_word_list_from_file
from keyword_fetcher import WikipediaKeywordFetcher, update_words_file
from search_history import SearchHistoryTracker
import os


class LogRedirector:
    """Redirect stdout to the GUI log widget."""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        
    def write(self, message):
        self.text_widget.insert(tk.END, message)
        self.text_widget.see(tk.END)
        self.text_widget.update()
        
    def flush(self):
        pass


class EdgeBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Microsoft Edge Search Bot - Modern UI")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # Modern color scheme
        self.bg_color = "#1e1e2e"
        self.card_bg = "#2a2a3e"
        self.accent_color = "#6c63ff"
        self.text_color = "#ffffff"
        self.secondary_text = "#a0a0b0"
        
        self.root.configure(bg=self.bg_color)
        
        # Control flags
        self.stop_flag = False
        
        # Initialize keyword fetcher
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cache_file = os.path.join(script_dir, 'search_cache.json')
        self.keyword_fetcher = WikipediaKeywordFetcher(cache_file=cache_file)
        
        # Initialize search history tracker
        history_file = os.path.join(script_dir, 'search_history.json')
        self.history_tracker = SearchHistoryTracker(history_file)
        
        # Load word list first
        self.word_list = load_word_list_from_file(os.path.join(script_dir, 'words.txt'))
        
        if not self.word_list:
            self.word_list = []
        
        self.profiles = ['Default', 'Profile 1', 'Profile 2']
        self.running = False
        self.pc_search_count = 34
        self.mobile_search_count = 24
        
        self.setup_ui()
        
        # Check and update keywords after UI is ready
        self.root.after(100, self.check_and_update_keywords)
        
    def setup_ui(self):
        """Setup the modern GUI layout with left-right split."""
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Card.TFrame', background=self.card_bg)
        style.configure('Main.TFrame', background=self.bg_color)
        style.configure('Title.TLabel', background=self.bg_color, foreground=self.text_color, 
                       font=('Segoe UI', 20, 'bold'))
        style.configure('Info.TLabel', background=self.card_bg, foreground=self.secondary_text, 
                       font=('Segoe UI', 10))
        style.configure('Header.TLabel', background=self.card_bg, foreground=self.text_color, 
                       font=('Segoe UI', 11, 'bold'))
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="20", style='Main.TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for 50-50 split
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Header Section (spans both columns)
        header_frame = ttk.Frame(main_frame, style='Main.TFrame')
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        title_label = ttk.Label(header_frame, text="🚀 Microsoft Edge Search Bot", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)
        
        # Right side buttons
        btn_container = tk.Frame(header_frame, bg=self.bg_color)
        btn_container.pack(side=tk.RIGHT)
        
        tk.Button(btn_container, text="🗑️ Clear History", 
                 command=self.clear_history_click,
                 bg="#ff4757", fg="white", 
                 font=('Segoe UI', 9, 'bold'),
                 relief=tk.FLAT, padx=15, pady=10,
                 cursor="hand2", activebackground="#ee5a6f").pack(side=tk.LEFT, padx=5)
        
        update_btn = tk.Button(btn_container, text="🔄 Update Keywords", 
                              command=self.update_keywords_click,
                              bg=self.accent_color, fg="white", 
                              font=('Segoe UI', 10, 'bold'),
                              relief=tk.FLAT, padx=20, pady=10,
                              cursor="hand2", activebackground="#5a52d5")
        update_btn.pack(side=tk.LEFT)
        
        # Info Card (spans both columns)
        info_card = ttk.Frame(main_frame, style='Card.TFrame', padding="15")
        info_card.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        info_text = f"📊 Keywords: {len(self.word_list)} | 🖥️ PC: {self.pc_search_count} searches | 📱 Mobile: {self.mobile_search_count} searches"
        self.info_label = ttk.Label(info_card, text=info_text, style='Info.TLabel')
        self.info_label.pack(side=tk.LEFT)
        
        # LEFT SIDE - Controls
        left_frame = ttk.Frame(main_frame, style='Card.TFrame', padding="20")
        left_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Control buttons (Stop only)
        control_frame = tk.Frame(left_frame, bg=self.card_bg)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.stop_btn = tk.Button(control_frame, text="⏸️ Stop", 
                                 command=self.stop_search,
                                 bg="#ff4757", fg="white", 
                                 font=('Segoe UI', 10, 'bold'),
                                 relief=tk.FLAT, padx=20, pady=10,
                                 cursor="hand2", state=tk.DISABLED,
                                 activebackground="#ee5a6f")
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_indicator = tk.Label(control_frame, text="● Ready", 
                                        bg=self.card_bg, fg="#2ed573",
                                        font=('Segoe UI', 10, 'bold'))
        self.status_indicator.pack(side=tk.RIGHT, padx=10)
        
        # Run All Section (at top)
        all_label = ttk.Label(left_frame, text="Run All Profiles", style='Header.TLabel')
        all_label.pack(anchor=tk.W, pady=(5, 10))
        
        btn_all_both = tk.Button(left_frame, text="▶▶ Run All (PC + Mobile)",
                               command=lambda: self.run_all_profiles('both'),
                               bg="#ff6348", fg="white", font=('Segoe UI', 10, 'bold'),
                               relief=tk.FLAT, pady=12, cursor="hand2",
                               activebackground="#ff4757")
        btn_all_both.pack(fill=tk.X, pady=3)
        
        btn_all_pc = tk.Button(left_frame, text="▶▶ Run All (PC Only)",
                             command=lambda: self.run_all_profiles('pc'),
                             bg="#ff9f43", fg="white", font=('Segoe UI', 10, 'bold'),
                             relief=tk.FLAT, pady=12, cursor="hand2",
                             activebackground="#ff8c2f")
        btn_all_pc.pack(fill=tk.X, pady=3)
        
        btn_all_mobile = tk.Button(left_frame, text="▶▶ Run All (Mobile Only)",
                                 command=lambda: self.run_all_profiles('mobile'),
                                 bg="#ffa502", fg="white", font=('Segoe UI', 10, 'bold'),
                                 relief=tk.FLAT, pady=12, cursor="hand2",
                                 activebackground="#ff9500")
        btn_all_mobile.pack(fill=tk.X, pady=3)
        
        # Separator
        separator = tk.Frame(left_frame, height=2, bg=self.bg_color)
        separator.pack(fill=tk.X, pady=15)
        
        # Individual Profiles Section
        profiles_label = ttk.Label(left_frame, text="Individual Profiles", style='Header.TLabel')
        profiles_label.pack(anchor=tk.W, pady=(5, 10))
        
        # Profile buttons
        for profile in self.profiles:
            profile_frame = tk.Frame(left_frame, bg=self.card_bg)
            profile_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(profile_frame, text=profile, bg=self.card_bg, fg=self.text_color,
                    font=('Segoe UI', 10, 'bold')).pack(anchor=tk.W, pady=(0, 5))
            
            btn_frame = tk.Frame(profile_frame, bg=self.card_bg)
            btn_frame.pack(fill=tk.X)
            
            tk.Button(btn_frame, text="▶ Both",
                     command=lambda p=profile: self.run_search(p, 'both'),
                     bg="#6c63ff", fg="white", font=('Segoe UI', 9, 'bold'),
                     relief=tk.FLAT, padx=12, pady=8, cursor="hand2",
                     activebackground="#5a52d5").pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
            
            tk.Button(btn_frame, text="🖥️ PC",
                     command=lambda p=profile: self.run_search(p, 'pc'),
                     bg="#3742fa", fg="white", font=('Segoe UI', 9, 'bold'),
                     relief=tk.FLAT, padx=12, pady=8, cursor="hand2",
                     activebackground="#2f3ae0").pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
            
            tk.Button(btn_frame, text="📱 Mobile",
                     command=lambda p=profile: self.run_search(p, 'mobile'),
                     bg="#5f27cd", fg="white", font=('Segoe UI', 9, 'bold'),
                     relief=tk.FLAT, padx=12, pady=8, cursor="hand2",
                     activebackground="#4a1fa8").pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        # RIGHT SIDE - Log
        log_frame = ttk.Frame(main_frame, style='Card.TFrame', padding="20")
        log_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)
        
        log_header = tk.Frame(log_frame, bg=self.card_bg)
        log_header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(log_header, text="📝 Activity Log", style='Header.TLabel').pack(side=tk.LEFT)
        
        tk.Button(log_header, text="🗑️ Clear", command=self.clear_log,
                 bg=self.bg_color, fg=self.secondary_text, 
                 font=('Segoe UI', 9),
                 relief=tk.FLAT, padx=15, pady=5, cursor="hand2",
                 activebackground="#3a3a4e").pack(side=tk.RIGHT)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, 
                                                   height=25, font=('Consolas', 9),
                                                   bg="#1a1a2e", fg="#e0e0e0",
                                                   insertbackground="white",
                                                   relief=tk.FLAT,
                                                   padx=10, pady=10)
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure log tags
        self.log_text.tag_config("success", foreground="#2ed573")
        self.log_text.tag_config("error", foreground="#ff4757")
        self.log_text.tag_config("warning", foreground="#ffa502")
        self.log_text.tag_config("info", foreground="#6c63ff")
        
        self.log_redirector = LogRedirector(self.log_text)
        
        # Initial messages
        self.log("✨ Microsoft Edge Search Bot initialized", "success")
        self.log(f"📊 Loaded {len(self.word_list)} search terms", "info")
        self.log(f"🖥️ PC: {self.pc_search_count} | 📱 Mobile: {self.mobile_search_count}", "info")
        self.log("🚀 Select a profile and search mode to begin\n")
    
    def check_and_update_keywords(self):
        """Check if keywords need updating."""
        try:
            cached = self.keyword_fetcher.load_cache()
            if cached is None:
                self.log("Keywords cache expired. Updating...", "warning")
                thread = threading.Thread(target=self._initial_update_thread, daemon=True)
                thread.start()
        except Exception as e:
            self.log(f"Note: {e}")
    
    def _initial_update_thread(self):
        """Initial keyword update."""
        old_stdout = sys.stdout
        sys.stdout = self.log_redirector
        
        try:
            update_words_file(force_refresh=True)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.word_list = load_word_list_from_file(os.path.join(script_dir, 'words.txt'))
            info_text = f"📊 Keywords: {len(self.word_list)} | 🖥️ PC: {self.pc_search_count} | 📱 Mobile: {self.mobile_search_count}"
            self.info_label.config(text=info_text)
            self.log(f"✓ Keywords loaded: {len(self.word_list)} terms\n", "success")
        except:
            self.log("Note: Using existing keywords\n")
        finally:
            sys.stdout = old_stdout
    
    def update_keywords_click(self):
        """Handle update button click."""
        if self.running:
            messagebox.showwarning("Bot Running", "Cannot update while bot is running!")
            return
        thread = threading.Thread(target=self._update_keywords_thread, daemon=True)
        thread.start()
    
    def _update_keywords_thread(self):
        """Update keywords in background."""
        old_stdout = sys.stdout
        sys.stdout = self.log_redirector
        
        try:
            self.set_status("Updating...", '#ffa502')
            update_words_file(force_refresh=True)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.word_list = load_word_list_from_file(os.path.join(script_dir, 'words.txt'))
            info_text = f"📊 Keywords: {len(self.word_list)} | 🖥️ PC: {self.pc_search_count} | 📱 Mobile: {self.mobile_search_count}"
            self.info_label.config(text=info_text)
            self.log(f"✓ Keywords updated: {len(self.word_list)} terms\n", "success")
            self.set_status("Ready", '#2ed573')
        except Exception as e:
            self.log(f"✗ Update failed: {e}\n", "error")
            self.set_status("Update failed", '#ff4757')
        finally:
            sys.stdout = old_stdout
    
    def clear_history_click(self):
        """Handle clear history button click."""
        if self.running:
            messagebox.showwarning("Bot Running", "Cannot clear history while bot is running!")
            return
        
        result = messagebox.askyesno(
            "Clear Search History",
            "Clear search history for all profiles?\n\nThis will allow searching the same keywords again."
        )
        
        if result:
            self.history_tracker.clear_all_history()
            self.log("✓ Search history cleared for all profiles", "success")
            messagebox.showinfo("Success", "Search history cleared!")
        
    def log(self, message, tag=None):
        """Add message to log."""
        if tag:
            self.log_text.insert(tk.END, message + "\n", tag)
        else:
            self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        
    def clear_log(self):
        """Clear log."""
        self.log_text.delete(1.0, tk.END)
        
    def set_status(self, message, color='#2ed573'):
        """Update status."""
        self.status_indicator.config(text=f"● {message}", fg=color)
    
    def stop_search(self):
        """Stop search."""
        self.stop_flag = True
        self.log("⏸️ Stop requested...", "warning")
        self.stop_btn.config(state=tk.DISABLED)
        self.set_status("Stopping...", "#ffa502")
        
    def run_search(self, profile, mode):
        """Run search for profile."""
        if self.running:
            self.log("⚠ Bot already running!", "warning")
            return
        if not self.word_list:
            self.log("✗ No words loaded!", "error")
            return
        thread = threading.Thread(target=self._execute_search, args=(profile, mode), daemon=True)
        thread.start()
        
    def run_all_profiles(self, mode):
        """Run all profiles."""
        if self.running:
            self.log("⚠ Bot already running!", "warning")
            return
        if not self.word_list:
            self.log("✗ No words loaded!", "error")
            return
        thread = threading.Thread(target=self._execute_all_profiles, args=(mode,), daemon=True)
        thread.start()
        
    def _execute_search(self, profile, mode):
        """Execute search."""
        self.running = True
        self.stop_flag = False
        self.stop_btn.config(state=tk.NORMAL)
        old_stdout = sys.stdout
        sys.stdout = self.log_redirector
        
        try:
            self.set_status(f"{profile} - {mode.upper()}", '#6c63ff')
            
            if mode == 'both':
                if not self.stop_flag:
                    self.log(f"\n{'='*60}")
                    self.log(f"PC Search - {profile}")
                    self.log(f"{'='*60}\n")
                    bot = EdgeSearchBot(headless=False, profile_name=profile, mobile=False, 
                                       stop_callback=lambda: self.stop_flag)
                    bot.run(word_list=self.word_list, delay_between_searches=3, 
                           pc_count=self.pc_search_count, mobile_count=self.mobile_search_count)
                
                if not self.stop_flag:
                    self.log(f"\n{'='*60}")
                    self.log(f"Mobile Search - {profile}")
                    self.log(f"{'='*60}\n")
                    bot = EdgeSearchBot(headless=False, profile_name=profile, mobile=True,
                                       stop_callback=lambda: self.stop_flag)
                    bot.run(word_list=self.word_list, delay_between_searches=3, 
                           pc_count=self.pc_search_count, mobile_count=self.mobile_search_count)
                
            elif mode == 'pc':
                if not self.stop_flag:
                    self.log(f"\n{'='*60}")
                    self.log(f"PC Search - {profile}")
                    self.log(f"{'='*60}\n")
                    bot = EdgeSearchBot(headless=False, profile_name=profile, mobile=False,
                                       stop_callback=lambda: self.stop_flag)
                    bot.run(word_list=self.word_list, delay_between_searches=3, 
                           pc_count=self.pc_search_count, mobile_count=self.mobile_search_count)
                
            elif mode == 'mobile':
                if not self.stop_flag:
                    self.log(f"\n{'='*60}")
                    self.log(f"Mobile Search - {profile}")
                    self.log(f"{'='*60}\n")
                    bot = EdgeSearchBot(headless=False, profile_name=profile, mobile=True,
                                       stop_callback=lambda: self.stop_flag)
                    bot.run(word_list=self.word_list, delay_between_searches=3, 
                           pc_count=self.pc_search_count, mobile_count=self.mobile_search_count)
            
            if self.stop_flag:
                self.log("\n⏹️ Stopped by user", "warning")
                self.set_status("Stopped", '#ffa502')
            else:
                self.log("\n✓ Completed!", "success")
                self.set_status("Completed", '#2ed573')
            
        except Exception as e:
            self.log(f"\n✗ Error: {e}", "error")
            self.set_status("Error", '#ff4757')
        finally:
            sys.stdout = old_stdout
            self.running = False
            self.stop_btn.config(state=tk.DISABLED)
            
    def _execute_all_profiles(self, mode):
        """Execute all profiles."""
        self.running = True
        self.stop_flag = False
        self.stop_btn.config(state=tk.NORMAL)
        old_stdout = sys.stdout
        sys.stdout = self.log_redirector
        
        try:
            self.set_status(f"All Profiles - {mode.upper()}", '#6c63ff')
            self.log(f"\n{'='*60}")
            self.log(f"Starting All Profiles - {mode.upper()}")
            self.log(f"{'='*60}\n")
            
            for profile in self.profiles:
                if self.stop_flag:
                    break
                    
                if mode == 'both':
                    if not self.stop_flag:
                        self.log(f"\n{profile} - PC Search")
                        bot = EdgeSearchBot(headless=False, profile_name=profile, mobile=False,
                                           stop_callback=lambda: self.stop_flag)
                        bot.run(word_list=self.word_list, delay_between_searches=3, 
                               pc_count=self.pc_search_count, mobile_count=self.mobile_search_count)
                    
                    if not self.stop_flag:
                        self.log(f"\n{profile} - Mobile Search")
                        bot = EdgeSearchBot(headless=False, profile_name=profile, mobile=True,
                                           stop_callback=lambda: self.stop_flag)
                        bot.run(word_list=self.word_list, delay_between_searches=3, 
                               pc_count=self.pc_search_count, mobile_count=self.mobile_search_count)
                    
                elif mode == 'pc':
                    if not self.stop_flag:
                        self.log(f"\n{profile} - PC Search")
                        bot = EdgeSearchBot(headless=False, profile_name=profile, mobile=False,
                                           stop_callback=lambda: self.stop_flag)
                        bot.run(word_list=self.word_list, delay_between_searches=3, 
                               pc_count=self.pc_search_count, mobile_count=self.mobile_search_count)
                    
                elif mode == 'mobile':
                    if not self.stop_flag:
                        self.log(f"\n{profile} - Mobile Search")
                        bot = EdgeSearchBot(headless=False, profile_name=profile, mobile=True,
                                           stop_callback=lambda: self.stop_flag)
                        bot.run(word_list=self.word_list, delay_between_searches=3, 
                               pc_count=self.pc_search_count, mobile_count=self.mobile_search_count)
            
            if self.stop_flag:
                self.log(f"\n⏹️ All profiles stopped", "warning")
                self.set_status("Stopped", '#ffa502')
            else:
                self.log(f"\n✓ All profiles completed!", "success")
                self.set_status("All Completed", '#2ed573')
            
        except Exception as e:
            self.log(f"\n✗ Error: {e}", "error")
            self.set_status("Error", '#ff4757')
        finally:
            sys.stdout = old_stdout
            self.running = False
            self.stop_btn.config(state=tk.DISABLED)


def main():
    root = tk.Tk()
    app = EdgeBotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
