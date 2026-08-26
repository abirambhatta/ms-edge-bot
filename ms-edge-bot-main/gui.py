"""
Microsoft Edge Search Automator - GUI Application with Modern UI
"""

import customtkinter as ctk
import tkinter.messagebox as messagebox
import threading
import sys
import os
import subprocess
import time
from edge_search_bot import EdgeSearchBot, load_word_list_from_file
from keyword_fetcher import WikipediaKeywordFetcher, update_words_file
from search_history import SearchHistoryTracker
from settings import SettingsManager
from profile_manager import ProfileManager

# Set Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class LogRedirector:
    """Redirect stdout to the GUI log widget in a thread-safe way."""
    def __init__(self, text_widget, root):
        self.text_widget = text_widget
        self.root = root
        
    def write(self, message):
        self.root.after(0, self._write_safe, message)
        
    def _write_safe(self, message):
        self.text_widget.insert("end", message)
        self.text_widget.see("end")
        
    def flush(self):
        pass


class EdgeBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Microsoft Edge Search Automator")
        self.root.geometry("1200x850")
        self.root.minsize(1000, 700)
        
        # Control flags
        self.stop_flag = False
        self.running = False
        
        # Setup paths and managers
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        cache_file = os.path.join(script_dir, 'search_cache.json')
        self.keyword_fetcher = WikipediaKeywordFetcher(cache_file=cache_file)
        
        history_file = os.path.join(script_dir, 'search_history.json')
        self.history_tracker = SearchHistoryTracker(history_file)
        
        settings_file = os.path.join(script_dir, 'settings.json')
        self.settings = SettingsManager(settings_file)
        
        profiles_file = os.path.join(script_dir, 'profiles.json')
        self.profile_manager = ProfileManager(profiles_file)
        self.profiles = self.profile_manager.get_profiles()
        
        self.word_list = load_word_list_from_file(os.path.join(script_dir, 'words.txt')) or []
        self.pc_search_count = self.settings.get_global_pc_count()
        self.mobile_search_count = self.settings.get_global_mobile_count()
        
        self.setup_ui()
        self.root.after(100, self.check_and_update_keywords)

    def setup_ui(self):
        """Setup the modern GUI layout using CustomTkinter."""
        # Main grid layout
        self.root.grid_columnconfigure(0, weight=4) # Left Panel
        self.root.grid_columnconfigure(1, weight=6) # Right Panel
        self.root.grid_rowconfigure(2, weight=1)    # Main Body
        
        # HEADER
        self.header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(self.header_frame, text="Microsoft Edge Search Automator", 
                                   font=ctk.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        btn_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e")
        
        ctk.CTkButton(btn_frame, text="Close Edge", fg_color="#ef4444", hover_color="#dc2626", 
                      width=110, command=self.close_edge_click).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Check Profiles", fg_color="#3b82f6", hover_color="#2563eb", 
                      width=130, command=self.check_profiles_click).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Clear History", fg_color="#f59e0b", hover_color="#d97706", 
                      width=120, command=self.clear_history_click).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Add Profile", fg_color="#10b981", hover_color="#059669", 
                      width=120, command=self.add_profile_click).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Update Keywords", fg_color="#8b5cf6", hover_color="#7c3aed", 
                      width=150, command=self.update_keywords_click).pack(side="left", padx=5)
        
        # INFO CARD
        self.info_card = ctk.CTkFrame(self.root)
        self.info_card.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        
        info_text = f"Keywords: {len(self.word_list)}  |  PC: {self.pc_search_count} defaults  |  Mobile: {self.mobile_search_count} defaults"
        self.info_label = ctk.CTkLabel(self.info_card, text=info_text, font=ctk.CTkFont(size=14))
        self.info_label.pack(pady=10)
        
        # LEFT SIDE - Controls & Profiles
        self.left_panel = ctk.CTkScrollableFrame(self.root, corner_radius=10)
        self.left_panel.grid(row=2, column=0, sticky="nsew", padx=(20, 10), pady=(0, 20))
        
        # Controls
        ctrl_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        ctrl_frame.pack(fill="x", pady=(0, 15))
        
        self.stop_btn = ctk.CTkButton(ctrl_frame, text="Stop Run", fg_color="#ef4444", hover_color="#dc2626", 
                                      state="disabled", command=self.stop_search, width=120)
        self.stop_btn.pack(side="left")
        
        self.status_indicator = ctk.CTkLabel(ctrl_frame, text="Ready", text_color="#10b981", 
                                             font=ctk.CTkFont(weight="bold"))
        self.status_indicator.pack(side="right", padx=10)
        
        # Run All
        ctk.CTkLabel(self.left_panel, text="Run All Profiles", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(10, 5))
        
        run_all_frame = ctk.CTkFrame(self.left_panel)
        run_all_frame.pack(fill="x", pady=5, padx=5)
        ctk.CTkButton(run_all_frame, text="Run All (PC + Mobile)", fg_color="#ec4899", hover_color="#db2777", 
                      command=lambda: self.run_all_profiles('both')).pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(run_all_frame, text="Run All (PC Only)", fg_color="#f97316", hover_color="#ea580c", 
                      command=lambda: self.run_all_profiles('pc')).pack(fill="x", pady=5, padx=10)
        ctk.CTkButton(run_all_frame, text="Run All (Mobile Only)", fg_color="#eab308", hover_color="#ca8a04", 
                      command=lambda: self.run_all_profiles('mobile')).pack(fill="x", pady=5, padx=10)
        
        ctk.CTkLabel(self.left_panel, text="Individual Profiles", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(20, 5))
        
        # Profile list container
        self.profiles_container = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.profiles_container.pack(fill="x", expand=True)
        self.refresh_home_profiles()
        
        # RIGHT SIDE - Tabs
        self.right_panel = ctk.CTkTabview(self.root, corner_radius=10)
        self.right_panel.grid(row=2, column=1, sticky="nsew", padx=(10, 20), pady=(0, 20))
        self.right_panel.add("Activity Log")
        self.right_panel.add("Settings")
        
        # Tab 1: Log
        log_tab = self.right_panel.tab("Activity Log")
        log_tab.grid_columnconfigure(0, weight=1)
        log_tab.grid_rowconfigure(1, weight=1)
        
        log_header = ctk.CTkFrame(log_tab, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        ctk.CTkLabel(log_header, text="Activity Log", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(log_header, text="Clear", width=80, fg_color="transparent", border_width=1, 
                      command=self.clear_log).pack(side="right")
        
        self.log_text = ctk.CTkTextbox(log_tab, font=ctk.CTkFont(family="Consolas", size=12), wrap="word")
        self.log_text.grid(row=1, column=0, sticky="nsew")
        self.log_redirector = LogRedirector(self.log_text, self.root)
        
        self.log("Microsoft Edge Search Automator initialized")
        self.log(f"Loaded {len(self.word_list)} search terms")
        self.log("Select a profile and search mode to begin\n")
        
        # Tab 2: Settings
        settings_tab = self.right_panel.tab("Settings")
        settings_tab.grid_columnconfigure(0, weight=1)
        settings_tab.grid_rowconfigure(0, weight=1)
        
        self.settings_scroll = ctk.CTkScrollableFrame(settings_tab, fg_color="transparent")
        self.settings_scroll.grid(row=0, column=0, sticky="nsew")
        
        self.setup_settings_tab()

    def refresh_home_profiles(self):
        """Dynamically redraw the profiles on the left panel."""
        for widget in self.profiles_container.winfo_children():
            widget.destroy()
            
        for profile in self.profiles:
            card = ctk.CTkFrame(self.profiles_container)
            card.pack(fill="x", pady=5)
            
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=10, pady=(10, 5))
            ctk.CTkLabel(top_row, text=profile, font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkButton(top_row, text="Remove", width=60, fg_color="#ef4444", hover_color="#dc2626",
                          command=lambda p=profile: self.remove_profile_click(p)).pack(side="right")
            
            btn_row = ctk.CTkFrame(card, fg_color="transparent")
            btn_row.pack(fill="x", padx=10, pady=(5, 10))
            
            ctk.CTkButton(btn_row, text="Both", fg_color="#8b5cf6", hover_color="#7c3aed",
                          command=lambda p=profile: self.run_search(p, 'both')).pack(side="left", expand=True, padx=2)
            ctk.CTkButton(btn_row, text="PC", fg_color="#3b82f6", hover_color="#2563eb",
                          command=lambda p=profile: self.run_search(p, 'pc')).pack(side="left", expand=True, padx=2)
            ctk.CTkButton(btn_row, text="Mobile", fg_color="#6366f1", hover_color="#4f46e5",
                          command=lambda p=profile: self.run_search(p, 'mobile')).pack(side="left", expand=True, padx=2)

    def setup_settings_tab(self):
        """Draw the fixed parts of the settings tab."""
        # Global Settings
        global_frame = ctk.CTkFrame(self.settings_scroll)
        global_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(global_frame, text="Global Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        def make_global_row(parent, label_text, var_val, save_cmd):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(row, text=label_text, width=180, anchor="w").pack(side="left")
            var = ctk.StringVar(value=str(var_val))
            entry = ctk.CTkEntry(row, textvariable=var, width=80)
            entry.pack(side="left", padx=10)
            ctk.CTkButton(row, text="Save", width=80, command=lambda: save_cmd(var)).pack(side="left")
            return var
            
        self.api_count_var = make_global_row(global_frame, "Wikipedia API Keywords:", self.settings.get_api_keyword_count(), self.save_api_count)
        self.global_pc_var = make_global_row(global_frame, "PC Searches per Profile:", self.settings.get_global_pc_count(), self.save_global_pc)
        self.global_mobile_var = make_global_row(global_frame, "Mobile Searches per Profile:", self.settings.get_global_mobile_count(), self.save_global_mobile)
        ctk.CTkFrame(global_frame, height=10, fg_color="transparent").pack()
        
        # Profile Settings container
        self.settings_profiles_container = ctk.CTkFrame(self.settings_scroll, fg_color="transparent")
        self.settings_profiles_container.pack(fill="x", padx=0, pady=10)
        self.refresh_settings_profiles()

    def refresh_settings_profiles(self):
        """Dynamically redraw the profile settings."""
        for widget in self.settings_profiles_container.winfo_children():
            widget.destroy()
            
        header_frame = ctk.CTkFrame(self.settings_profiles_container, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(header_frame, text="Per-Profile Settings", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Override global settings for specific profiles", text_color="gray").pack(anchor="w")
        
        self.profile_pc_vars = {}
        self.profile_mobile_vars = {}
        
        for profile in self.profiles:
            card = ctk.CTkFrame(self.settings_profiles_container)
            card.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(card, text=profile, font=ctk.CTkFont(weight="bold"), text_color="#3b82f6").pack(anchor="w", padx=15, pady=(10, 5))
            
            # PC Row
            pc_row = ctk.CTkFrame(card, fg_color="transparent")
            pc_row.pack(fill="x", padx=15, pady=2)
            ctk.CTkLabel(pc_row, text="PC Searches:", width=120, anchor="w").pack(side="left")
            pc_var = ctk.StringVar(value=str(self.settings.get_profile_pc_count(profile)))
            self.profile_pc_vars[profile] = pc_var
            ctk.CTkEntry(pc_row, textvariable=pc_var, width=60).pack(side="left", padx=10)
            ctk.CTkButton(pc_row, text="Save", width=60, command=lambda p=profile: self.save_profile_pc(p)).pack(side="left")
            
            # Mobile Row
            mob_row = ctk.CTkFrame(card, fg_color="transparent")
            mob_row.pack(fill="x", padx=15, pady=(2, 10))
            ctk.CTkLabel(mob_row, text="Mobile Searches:", width=120, anchor="w").pack(side="left")
            mob_var = ctk.StringVar(value=str(self.settings.get_profile_mobile_count(profile)))
            self.profile_mobile_vars[profile] = mob_var
            ctk.CTkEntry(mob_row, textvariable=mob_var, width=60).pack(side="left", padx=10)
            ctk.CTkButton(mob_row, text="Save", width=60, command=lambda p=profile: self.save_profile_mobile(p)).pack(side="left")

    def save_api_count(self, var):
        try:
            count = int(var.get())
            if count < 10: raise ValueError
            if messagebox.askyesno("Confirm", f"Update API keyword count to {count}?"):
                self.settings.set_api_keyword_count(count)
                self.log(f"API keyword count set to {count}")
                messagebox.showinfo("Success", f"API keyword count set to {count}")
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number (minimum 10)")

    def save_global_pc(self, var):
        try:
            count = int(var.get())
            if count < 1: raise ValueError
            if messagebox.askyesno("Confirm", f"Update Global PC Searches to {count}?"):
                self.settings.set_global_pc_count(count)
                self.pc_search_count = count
                self.update_info_label()
                self.log(f"Global PC count set to {count}")
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number")

    def save_global_mobile(self, var):
        try:
            count = int(var.get())
            if count < 1: raise ValueError
            if messagebox.askyesno("Confirm", f"Update Global Mobile Searches to {count}?"):
                self.settings.set_global_mobile_count(count)
                self.mobile_search_count = count
                self.update_info_label()
                self.log(f"Global mobile count set to {count}")
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number")

    def save_profile_pc(self, profile):
        try:
            count = int(self.profile_pc_vars[profile].get())
            if count < 1: raise ValueError
            if messagebox.askyesno("Confirm", f"Update PC Searches for {profile} to {count}?"):
                self.settings.set_profile_pc_count(profile, count)
                self.log(f"{profile} PC count set to {count}")
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number")

    def save_profile_mobile(self, profile):
        try:
            count = int(self.profile_mobile_vars[profile].get())
            if count < 1: raise ValueError
            if messagebox.askyesno("Confirm", f"Update Mobile Searches for {profile} to {count}?"):
                self.settings.set_profile_mobile_count(profile, count)
                self.log(f"{profile} mobile count set to {count}")
        except ValueError:
            messagebox.showerror("Error", "Enter a valid number")

    def update_info_label(self):
        info_text = f"Keywords: {len(self.word_list)}  |  PC: {self.pc_search_count} defaults  |  Mobile: {self.mobile_search_count} defaults"
        self.info_label.configure(text=info_text)

    def check_and_update_keywords(self):
        try:
            if self.keyword_fetcher.load_cache() is None:
                self.log("Keywords cache expired. Updating...")
                threading.Thread(target=self._initial_update_thread, daemon=True).start()
        except Exception as e:
            self.log(f"Note: {e}")

    def _initial_update_thread(self):
        old_stdout = sys.stdout
        sys.stdout = self.log_redirector
        try:
            update_words_file(force_refresh=True)
            self.word_list = load_word_list_from_file(os.path.join(os.path.dirname(__file__), 'words.txt')) or []
            self.update_info_label()
            self.log(f"Keywords loaded: {len(self.word_list)} terms\n")
        except:
            self.log("Note: Using existing keywords\n")
        finally:
            sys.stdout = old_stdout

    def update_keywords_click(self):
        if self.running:
            messagebox.showwarning("Automator Running", "Cannot update while running!")
            return
        threading.Thread(target=self._update_keywords_thread, daemon=True).start()

    def _update_keywords_thread(self):
        old_stdout = sys.stdout
        sys.stdout = self.log_redirector
        try:
            self.set_status("Updating...", '#f59e0b')
            update_words_file(force_refresh=True)
            self.word_list = load_word_list_from_file(os.path.join(os.path.dirname(__file__), 'words.txt')) or []
            self.update_info_label()
            self.log(f"Keywords updated: {len(self.word_list)} terms\n")
            self.set_status("Ready", '#10b981')
        except Exception as e:
            self.log(f"Update failed: {e}\n")
            self.set_status("Update failed", '#ef4444')
        finally:
            sys.stdout = old_stdout

    def clear_history_click(self):
        if self.running: return
        if messagebox.askyesno("Clear History", "Clear search history for all profiles?"):
            self.history_tracker.clear_all_history()
            self.log("Search history cleared")
            messagebox.showinfo("Success", "History cleared!")

    def close_edge_click(self):
        if messagebox.askyesno("Close Edge", "Force close all Microsoft Edge windows?"):
            try:
                self.log("Closing Edge...")
                subprocess.run(['taskkill', '/F', '/IM', 'msedge.exe'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(['taskkill', '/F', '/IM', 'msedgedriver.exe'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
                self.log("Edge closed")
            except Exception as e:
                self.log(f"Error: {e}")

    def check_profiles_click(self):
        if self.running: return
        if messagebox.askyesno("Check Profiles", "Close Edge and check all profiles?"):
            threading.Thread(target=self._check_profiles_thread, daemon=True).start()

    def _check_profiles_thread(self):
        old_stdout = sys.stdout
        sys.stdout = self.log_redirector
        try:
            self.log("\nStarting Profile Checker...")
            subprocess.run(['taskkill', '/F', '/IM', 'msedge.exe'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
            from check_profile import check_profile
            for p in self.profiles: check_profile(p)
            self.log("Profile check complete!\n")
        except Exception as e:
            self.log(f"Error: {e}")
        finally:
            sys.stdout = old_stdout

    def add_profile_click(self):
        if self.running: return
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Add Profile")
        dialog.geometry("400x180")
        dialog.attributes('-topmost', True)
        
        ctk.CTkLabel(dialog, text="Enter Profile Name:").pack(pady=20)
        entry = ctk.CTkEntry(dialog, width=250)
        entry.pack(pady=10)
        entry.focus()
        
        def save_profile():
            p_name = entry.get().strip()
            if not p_name: return
            if self.profile_manager.add_profile(p_name):
                self.profiles = self.profile_manager.get_profiles()
                self.refresh_home_profiles()
                self.refresh_settings_profiles()
                self.log(f"Profile '{p_name}' added dynamically")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Profile already exists!")
                
        ctk.CTkButton(dialog, text="Add", command=save_profile).pack(pady=10)

    def remove_profile_click(self, profile):
        if self.running: return
        if messagebox.askyesno("Remove Profile", f"Remove profile '{profile}'?"):
            if self.profile_manager.remove_profile(profile):
                self.profiles = self.profile_manager.get_profiles()
                self.refresh_home_profiles()
                self.refresh_settings_profiles()
                self.log(f"Profile '{profile}' removed")

    def log(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def clear_log(self):
        self.log_text.delete("1.0", "end")

    def set_status(self, message, color='#10b981'):
        self.root.after(0, lambda: self.status_indicator.configure(text=message, text_color=color))

    def stop_search(self):
        self.stop_flag = True
        self.log("Stop requested...")
        self.root.after(0, lambda: self.stop_btn.configure(state="disabled"))
        self.set_status("Stopping...", "#f59e0b")

    def run_search(self, profile, mode):
        if self.running: return
        if not self.word_list: return self.log("No words loaded!")
        threading.Thread(target=self._execute_search, args=(profile, mode), daemon=True).start()

    def run_all_profiles(self, mode):
        if self.running: return
        if not self.word_list: return self.log("No words loaded!")
        threading.Thread(target=self._execute_all_profiles, args=(mode,), daemon=True).start()

    def _execute_search(self, profile, mode):
        self.running = True
        self.stop_flag = False
        self.root.after(0, lambda: self.stop_btn.configure(state="normal"))
        old_stdout = sys.stdout
        sys.stdout = self.log_redirector
        
        try:
            self.set_status(f"{profile} - {mode.upper()}", '#8b5cf6')
            
            def run_bot(is_mobile):
                if self.stop_flag: return
                self.log(f"\n--- {'Mobile' if is_mobile else 'PC'} Search : {profile} ---")
                bot = EdgeSearchBot(headless=False, profile_name=profile, mobile=is_mobile, stop_callback=lambda: self.stop_flag)
                bot.run(word_list=self.word_list, delay_between_searches=3)

            if mode in ['both', 'pc']: run_bot(False)
            if mode in ['both', 'mobile']: run_bot(True)

            if self.stop_flag:
                self.log("\nStopped by user")
                self.set_status("Stopped", '#f59e0b')
            else:
                self.log("\nCompleted!")
                self.set_status("Completed", '#10b981')
        except Exception as e:
            self.log(f"\nError: {e}")
            self.set_status("Error", '#ef4444')
        finally:
            sys.stdout = old_stdout
            self.running = False
            self.root.after(0, lambda: self.stop_btn.configure(state="disabled"))

    def _execute_all_profiles(self, mode):
        self.running = True
        self.stop_flag = False
        self.root.after(0, lambda: self.stop_btn.configure(state="normal"))
        old_stdout = sys.stdout
        sys.stdout = self.log_redirector
        
        try:
            self.set_status(f"All Profiles - {mode.upper()}", '#8b5cf6')
            self.log(f"\n--- Starting All Profiles ({mode.upper()}) ---")
            
            for profile in self.profiles:
                if self.stop_flag: break
                
                def run_bot(is_mobile):
                    if self.stop_flag: return
                    self.log(f"\n--- {'Mobile' if is_mobile else 'PC'} Search : {profile} ---")
                    bot = EdgeSearchBot(headless=False, profile_name=profile, mobile=is_mobile, stop_callback=lambda: self.stop_flag)
                    bot.run(word_list=self.word_list, delay_between_searches=3)

                if mode in ['both', 'pc']: run_bot(False)
                if mode in ['both', 'mobile']: run_bot(True)

            if self.stop_flag:
                self.log(f"\nAll profiles stopped")
                self.set_status("Stopped", '#f59e0b')
            else:
                self.log(f"\nAll profiles completed!")
                self.set_status("All Completed", '#10b981')
        except Exception as e:
            self.log(f"\nError: {e}")
            self.set_status("Error", '#ef4444')
        finally:
            sys.stdout = old_stdout
            self.running = False
            self.root.after(0, lambda: self.stop_btn.configure(state="disabled"))

def main():
    root = ctk.CTk()
    app = EdgeBotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
