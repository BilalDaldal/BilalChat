"""
ChamberChat - Modern Windows Mesajlaşma Uygulaması
Hesap sistemi, şık tasarım ve premium görünüm.
İstemci tarafı şifre politikası doğrulaması dahil.
Otomatik güncelleme sistemi dahil.
"""

import customtkinter as ctk
from tkinter import messagebox
import socket
import threading
import datetime
from PIL import Image, ImageDraw
import os
import re  # Şifre politikası kontrolü için
import webbrowser  # Güncelleme için

# Güncelleme modülünü import et
try:
    import updater
    UPDATER_AVAILABLE = True
    print("[INFO] Güncelleme modülü yüklendi.")
except ImportError as e:
    UPDATER_AVAILABLE = False
    print(f"[UYARI] updater.py bulunamadı: {e}")
except Exception as e:
    UPDATER_AVAILABLE = False
    print(f"[HATA] updater.py yüklenirken hata: {type(e).__name__}: {e}")
# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 SUNUCU AYARLARI - BU BÖLÜMÜ KENDİ SUNUCUNUZA GÖRE DEĞİŞTİRİN
# ═══════════════════════════════════════════════════════════════════════════════
DEFAULT_SERVER_IP = "3.64.55.5"  # Sunucu IP adresi (VPS IP'nizi buraya yazın)
DEFAULT_SERVER_PORT = 5555       # Sunucu port numarası
# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# 🔐 ŞİFRE POLİTİKASI DOĞRULAMA
# ═══════════════════════════════════════════════════════════════════════════════
def validate_password(password):
    """
    Şifre politikasını kontrol et
    - Minimum 8 karakter
    - En az 1 büyük harf
    - En az 1 küçük harf
    - En az 1 rakam
    """
    if len(password) < 8:
        return False, "Şifre en az 8 karakter olmalıdır!"
    
    if not re.search(r'[A-Z]', password):
        return False, "Şifre en az 1 büyük harf içermelidir!"
    
    if not re.search(r'[a-z]', password):
        return False, "Şifre en az 1 küçük harf içermelidir!"
    
    if not re.search(r'[0-9]', password):
        return False, "Şifre en az 1 rakam içermelidir!"
    
    return True, "Şifre geçerli"


def validate_username(username):
    """
    Kullanıcı adı politikasını kontrol et
    - Minimum 3 karakter
    - Sadece harf, rakam ve alt çizgi
    """
    if len(username) < 3:
        return False, "Kullanıcı adı en az 3 karakter olmalıdır!"
    
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Kullanıcı adı sadece harf, rakam ve alt çizgi içerebilir!"
    
    return True, "Kullanıcı adı geçerli"
# ═══════════════════════════════════════════════════════════════════════════════


# Tema ayarları
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MessageBubble(ctk.CTkFrame):
    """Mesaj baloncuğu"""
    def __init__(self, master, message, timestamp, sender, is_me=False, is_system=False, **kwargs):
        super().__init__(master, **kwargs)
        
        if is_system:
            self.configure(fg_color="transparent")
            label = ctk.CTkLabel(
                self,
                text=f"  {message}  ",
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color="#888888"
            )
            label.pack(pady=5)
        else:
            if is_me:
                self.configure(fg_color="#4158D0", corner_radius=15)
            else:
                self.configure(fg_color="#2d2d44", corner_radius=15)
            
            if not is_me:
                sender_label = ctk.CTkLabel(
                    self,
                    text=sender,
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color="#C850C0"
                )
                sender_label.pack(anchor="w", padx=12, pady=(8, 0))
            
            msg_label = ctk.CTkLabel(
                self,
                text=message,
                font=ctk.CTkFont(size=13),
                text_color="#ffffff",
                wraplength=350,
                justify="left"
            )
            msg_label.pack(anchor="w", padx=12, pady=(4 if not is_me else 10, 4))
            
            time_label = ctk.CTkLabel(
                self,
                text=timestamp,
                font=ctk.CTkFont(size=9),
                text_color="#aaaaaa"
            )
            time_label.pack(anchor="e", padx=12, pady=(0, 8))

class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("💬 ChamberChat")
        self.geometry("800x650")
        self.minsize(600, 550)
        
        self.colors = {
            'bg_primary': "#0f0f23",
            'bg_secondary': "#1a1a2e",
            'bg_tertiary': "#16213e",
            'accent_primary': "#4158D0",
            'accent_secondary': "#C850C0",
            'accent_gradient': "#FFCC70",
            'text_primary': "#ffffff",
            'text_secondary': "#b0b0b0",
            'success': "#00d26a",
            'error': "#ff4757",
            'warning': "#ffa502"
        }
        
        self.configure(fg_color=self.colors['bg_primary'])
        
        self.client_socket = None
        self.connected = False
        self.username = ""
        self.message_frames = []
        
        # Güncelleme kontrolü yap
        self.update_frame = None
        if UPDATER_AVAILABLE:
            self.check_for_updates()
        else:
            self.create_auth_screen()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def check_for_updates(self):
        """Güncelleme kontrolü (arka planda)"""
        self.create_checking_screen()
        thread = threading.Thread(target=self._check_updates_thread)
        thread.daemon = True
        thread.start()
    
    def create_checking_screen(self):
        """Güncelleme kontrol ekranı"""
        self.update_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.update_frame.pack(expand=True, fill="both", padx=40, pady=30)
        
        ctk.CTkLabel(
            self.update_frame,
            text="💬 ChamberChat",
            font=ctk.CTkFont(family="Segoe UI", size=42, weight="bold"),
            text_color=self.colors['accent_secondary']
        ).pack(pady=(100, 20))
        
        ctk.CTkLabel(
            self.update_frame,
            text="🔄 Güncellemeler kontrol ediliyor...",
            font=ctk.CTkFont(size=16),
            text_color=self.colors['text_secondary']
        ).pack(pady=20)
        
        self.update_progress = ctk.CTkProgressBar(
            self.update_frame,
            width=300,
            mode="indeterminate"
        )
        self.update_progress.pack(pady=20)
        self.update_progress.start()
    
    def _check_updates_thread(self):
        """Güncelleme kontrolü (thread)"""
        result = updater.check_for_updates()
        
        if result['error']:
            # Hata durumunda giriş ekranına geç
            print(f"[UPDATE] Hata: {result['error']}")
            self.after(0, self._show_auth_after_update_check)
        elif result['needs_update']:
            # Güncelleme gerekli - zorunlu güncelleme ekranı
            self.after(0, lambda: self._show_update_screen(
                result['latest_version'], 
                result['download_url']
            ))
        else:
            # Güncel - giriş ekranına geç
            self.after(0, self._show_auth_after_update_check)
    
    def _show_auth_after_update_check(self):
        """Güncelleme kontrolünden sonra giriş ekranını göster"""
        if self.update_frame:
            self.update_frame.destroy()
            self.update_frame = None
        self.create_auth_screen()
    
    def _show_update_screen(self, latest_version, download_url):
        """Zorunlu güncelleme ekranı"""
        if self.update_frame:
            self.update_frame.destroy()
        
        self.update_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.update_frame.pack(expand=True, fill="both", padx=40, pady=30)
        
        # Logo
        ctk.CTkLabel(
            self.update_frame,
            text="💬 BilalChat",
            font=ctk.CTkFont(family="Segoe UI", size=42, weight="bold"),
            text_color=self.colors['accent_secondary']
        ).pack(pady=(60, 20))
        
        # Güncelleme kartı
        card = ctk.CTkFrame(
            self.update_frame,
            fg_color=self.colors['bg_secondary'],
            corner_radius=20
        )
        card.pack(fill="x", pady=20, padx=50)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(padx=40, pady=30)
        
        ctk.CTkLabel(
            inner,
            text="🆕 Yeni Güncelleme Mevcut!",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.colors['warning']
        ).pack(pady=(0, 15))
        
        ctk.CTkLabel(
            inner,
            text=f"Mevcut: v{updater.CURRENT_VERSION}  →  Yeni: {latest_version}",
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_secondary']
        ).pack(pady=5)
        
        ctk.CTkLabel(
            inner,
            text="⚠️ Devam etmek için güncelleme zorunludur!",
            font=ctk.CTkFont(size=13),
            text_color=self.colors['error']
        ).pack(pady=(15, 20))
        
        # Progress bar (indirme için)
        self.download_progress = ctk.CTkProgressBar(
            inner,
            width=350,
            height=15,
            progress_color=self.colors['success']
        )
        self.download_progress.pack(pady=10)
        self.download_progress.set(0)
        
        self.download_status = ctk.CTkLabel(
            inner,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['text_secondary']
        )
        self.download_status.pack(pady=5)
        
        # Butonlar
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(pady=(15, 0))
        
        self.download_btn = ctk.CTkButton(
            btn_frame,
            text="📥 Güncellemeyi İndir",
            width=180,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors['success'],
            hover_color="#00b359",
            corner_radius=12,
            command=lambda: self._start_download(download_url)
        )
        self.download_btn.pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🌐 GitHub'da Aç",
            width=140,
            height=45,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors['bg_tertiary'],
            hover_color="#1e3a5f",
            corner_radius=12,
            command=lambda: webbrowser.open(download_url)
        ).pack(side="left", padx=5)
    
    def _start_download(self, download_url):
        """İndirmeyi başlat"""
        self.download_btn.configure(state="disabled", text="⏳ İndiriliyor...")
        self.download_status.configure(text="İndirme başlatılıyor...")
        
        thread = threading.Thread(
            target=self._download_thread,
            args=(download_url,)
        )
        thread.daemon = True
        thread.start()
    
    def _download_thread(self, download_url):
        """İndirme thread'i"""
        def progress_callback(downloaded, total, percent):
            progress = percent / 100.0
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            self.after(0, lambda: self.download_progress.set(progress))
            self.after(0, lambda: self.download_status.configure(
                text=f"{mb_downloaded:.1f} MB / {mb_total:.1f} MB ({percent:.0f}%)"
            ))
        
        result = updater.download_update(download_url, progress_callback)
        
        if result['success']:
            self.after(0, lambda: self._on_download_complete(result['file_path']))
        else:
            self.after(0, lambda: self._on_download_error(result['error']))
    
    def _on_download_complete(self, file_path):
        """İndirme tamamlandı"""
        self.download_status.configure(
            text="✅ İndirme tamamlandı! Yeni sürüm başlatılıyor...",
            text_color=self.colors['success']
        )
        self.download_btn.configure(text="✅ Tamamlandı")
        
        # 1 saniye bekle ve yeni sürümü başlat
        self.after(1000, lambda: updater.install_update(file_path))
    
    def _on_download_error(self, error):
        """İndirme hatası"""
        self.download_status.configure(
            text=f"❌ Hata: {error}",
            text_color=self.colors['error']
        )
        self.download_btn.configure(state="normal", text="🔄 Tekrar Dene")
    
    def create_auth_screen(self):
        """Giriş/Kayıt ekranı"""
        self.auth_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.auth_frame.pack(expand=True, fill="both", padx=40, pady=30)
        
        # Başlık
        title_frame = ctk.CTkFrame(self.auth_frame, fg_color="transparent")
        title_frame.pack(pady=(20, 10))
        
        title = ctk.CTkLabel(
            title_frame,
            text="💬 ChamberChat",
            font=ctk.CTkFont(family="Segoe UI", size=42, weight="bold"),
            text_color=self.colors['accent_secondary']
        )
        title.pack()
        
        subtitle = ctk.CTkLabel(
            title_frame,
            text="Güvenli Mesajlaşma Platformu",
            font=ctk.CTkFont(size=14),
            text_color=self.colors['text_secondary']
        )
        subtitle.pack(pady=(5, 0))
        
        # Kart
        card = ctk.CTkFrame(
            self.auth_frame,
            fg_color=self.colors['bg_secondary'],
            corner_radius=20,
            border_width=1,
            border_color="#2a2a4a"
        )
        card.pack(fill="x", pady=20, padx=30)
        
        inner_card = ctk.CTkFrame(card, fg_color="transparent")
        inner_card.pack(padx=40, pady=30, fill="x")
        
        # Tab View (Giriş / Kayıt)
        self.tab_view = ctk.CTkTabview(
            inner_card,
            fg_color=self.colors['bg_tertiary'],
            segmented_button_fg_color=self.colors['bg_primary'],
            segmented_button_selected_color=self.colors['accent_primary'],
            segmented_button_unselected_color=self.colors['bg_tertiary'],
            height=380
        )
        self.tab_view.pack(fill="x", pady=(0, 20))
        
        # Giriş Sekmesi
        login_tab = self.tab_view.add("🔑 Giriş Yap")
        self.create_login_form(login_tab)
        
        # Kayıt Sekmesi
        register_tab = self.tab_view.add("📝 Kayıt Ol")
        self.create_register_form(register_tab)
        
        # Durum mesajı
        self.auth_status = ctk.CTkLabel(
            inner_card,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['text_secondary']
        )
        self.auth_status.pack(pady=(0, 10))
        
        # Sunucu bilgisi
        server_frame = ctk.CTkFrame(inner_card, fg_color=self.colors['bg_tertiary'], corner_radius=10)
        server_frame.pack(fill="x")
        
        server_inner = ctk.CTkFrame(server_frame, fg_color="transparent")
        server_inner.pack(padx=15, pady=10, fill="x")
        
        ctk.CTkLabel(
            server_inner,
            text="🌐 Sunucu:",
            font=ctk.CTkFont(size=11),
            text_color=self.colors['text_secondary']
        ).pack(side="left")
        
        ctk.CTkLabel(
            server_inner,
            text=f"{DEFAULT_SERVER_IP}:{DEFAULT_SERVER_PORT}",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors['accent_secondary']
        ).pack(side="right")
    
    def create_login_form(self, parent):
        """Giriş formu"""
        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=20)
        
        # Kullanıcı adı
        ctk.CTkLabel(
            form,
            text="👤  Kullanıcı Adı",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors['text_primary']
        ).pack(anchor="w", pady=(0, 5))
        
        self.login_username = ctk.CTkEntry(
            form,
            height=42,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors['bg_primary'],
            border_color=self.colors['accent_primary'],
            corner_radius=10,
            placeholder_text="Kullanıcı adınız"
        )
        self.login_username.pack(fill="x", pady=(0, 15))
        
        # Şifre
        ctk.CTkLabel(
            form,
            text="🔒  Şifre",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors['text_primary']
        ).pack(anchor="w", pady=(0, 5))
        
        self.login_password = ctk.CTkEntry(
            form,
            height=42,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors['bg_primary'],
            border_color=self.colors['accent_primary'],
            corner_radius=10,
            placeholder_text="Şifreniz",
            show="•"
        )
        self.login_password.pack(fill="x", pady=(0, 20))
        
        # Giriş butonu
        self.login_btn = ctk.CTkButton(
            form,
            text="🚀  Giriş Yap",
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors['accent_primary'],
            hover_color=self.colors['accent_secondary'],
            corner_radius=12,
            command=lambda: self.authenticate("LOGIN")
        )
        self.login_btn.pack(fill="x")
        
        # Enter ile giriş
        self.login_password.bind('<Return>', lambda e: self.authenticate("LOGIN"))
    
    def create_register_form(self, parent):
        """Kayıt formu"""
        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=20)
        
        # Kullanıcı adı
        ctk.CTkLabel(
            form,
            text="👤  Kullanıcı Adı",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors['text_primary']
        ).pack(anchor="w", pady=(0, 5))
        
        self.register_username = ctk.CTkEntry(
            form,
            height=42,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors['bg_primary'],
            border_color=self.colors['success'],
            corner_radius=10,
            placeholder_text="Kullanıcı adı seçin"
        )
        self.register_username.pack(fill="x", pady=(0, 15))
        
        # Şifre
        ctk.CTkLabel(
            form,
            text="🔒  Şifre",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors['text_primary']
        ).pack(anchor="w", pady=(0, 5))
        
        self.register_password = ctk.CTkEntry(
            form,
            height=42,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors['bg_primary'],
            border_color=self.colors['success'],
            corner_radius=10,
            placeholder_text="Güçlü bir şifre belirleyin",
            show="•"
        )
        self.register_password.pack(fill="x", pady=(0, 3))
        
        # Şifre kuralları bilgisi
        password_hint = ctk.CTkLabel(
            form,
            text="ℹ️ Min 8 karakter, büyük/küçük harf ve rakam gerekli",
            font=ctk.CTkFont(size=9),
            text_color=self.colors['text_secondary']
        )
        password_hint.pack(anchor="w", pady=(0, 8))
        
        # Şifre tekrar
        ctk.CTkLabel(
            form,
            text="🔒  Şifre Tekrar",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.colors['text_primary']
        ).pack(anchor="w", pady=(0, 5))
        
        self.register_password2 = ctk.CTkEntry(
            form,
            height=42,
            font=ctk.CTkFont(size=13),
            fg_color=self.colors['bg_primary'],
            border_color=self.colors['success'],
            corner_radius=10,
            placeholder_text="Şifrenizi tekrar girin",
            show="•"
        )
        self.register_password2.pack(fill="x", pady=(0, 12))
        
        # Kayıt butonu
        self.register_btn = ctk.CTkButton(
            form,
            text="📝  Kayıt Ol",
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=self.colors['success'],
            hover_color="#00b359",
            corner_radius=12,
            command=lambda: self.authenticate("REGISTER")
        )
        self.register_btn.pack(fill="x")
        
        # Enter ile kayıt
        self.register_password2.bind('<Return>', lambda e: self.authenticate("REGISTER"))
    
    def authenticate(self, action):
        """Giriş veya kayıt işlemi (şifre politikası kontrolü ile)"""
        if action == "LOGIN":
            username = self.login_username.get().strip()
            password = self.login_password.get().strip()
            btn = self.login_btn
        else:
            username = self.register_username.get().strip()
            password = self.register_password.get().strip()
            password2 = self.register_password2.get().strip()
            btn = self.register_btn
            
            if password != password2:
                self.auth_status.configure(text="❌ Şifreler eşleşmiyor!", text_color=self.colors['error'])
                return
        
        # Boş alan kontrolü
        if not username or not password:
            self.auth_status.configure(text="❌ Tüm alanları doldurun!", text_color=self.colors['error'])
            return
        
        # Kayıt için şifre ve kullanıcı adı politikası kontrolü
        if action == "REGISTER":
            # Kullanıcı adı kontrolü
            is_valid_user, user_message = validate_username(username)
            if not is_valid_user:
                self.auth_status.configure(text=f"❌ {user_message}", text_color=self.colors['error'])
                return
            
            # Şifre politikası kontrolü
            is_valid_pass, pass_message = validate_password(password)
            if not is_valid_pass:
                self.auth_status.configure(text=f"❌ {pass_message}", text_color=self.colors['error'])
                return
        
        self.username = username
        self.auth_status.configure(text="⏳ Bağlanılıyor...", text_color=self.colors['text_secondary'])
        btn.configure(state="disabled")
        self.update()
        
        # Bağlantı thread'i
        thread = threading.Thread(target=self._authenticate, args=(action, username, password, btn))
        thread.daemon = True
        thread.start()
    
    def _authenticate(self, action, username, password, btn):
        """Kimlik doğrulama (ayrı thread)"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)
            self.client_socket.connect((DEFAULT_SERVER_IP, DEFAULT_SERVER_PORT))
            self.client_socket.settimeout(None)
            
            # Sunucudan AUTH_REQUIRED bekle
            response = self.client_socket.recv(1024).decode('utf-8')
            
            if response == "AUTH_REQUIRED":
                # Giriş/Kayıt bilgilerini gönder
                auth_data = f"{action}:{username}:{password}"
                self.client_socket.send(auth_data.encode('utf-8'))
                
                # Yanıt bekle
                result = self.client_socket.recv(1024).decode('utf-8')
                
                if result.startswith("AUTH_SUCCESS"):
                    message = result.split(":", 1)[1] if ":" in result else "Başarılı!"
                    self.after(0, lambda: self._on_auth_success(message))
                    self.connected = True
                    self.receive_messages()
                else:
                    error = result.split(":", 1)[1] if ":" in result else "Bir hata oluştu!"
                    self.after(0, lambda: self._on_auth_error(error, btn))
                    self.client_socket.close()
            else:
                self.after(0, lambda: self._on_auth_error("Sunucu yanıt vermedi!", btn))
                self.client_socket.close()
                
        except socket.timeout:
            self.after(0, lambda: self._on_auth_error("Bağlantı zaman aşımı!", btn))
        except ConnectionRefusedError:
            self.after(0, lambda: self._on_auth_error("Sunucu bulunamadı!", btn))
        except Exception as e:
            self.after(0, lambda: self._on_auth_error(str(e), btn))
    
    def _on_auth_success(self, message):
        """Kimlik doğrulama başarılı"""
        self.auth_frame.destroy()
        self.create_chat_screen()
    
    def _on_auth_error(self, error, btn):
        """Kimlik doğrulama hatası"""
        self.auth_status.configure(text=f"❌ {error}", text_color=self.colors['error'])
        btn.configure(state="normal")
    
    def create_chat_screen(self):
        """Sohbet ekranı"""
        self.chat_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.chat_frame.pack(expand=True, fill="both")
        
        # Header
        header = ctk.CTkFrame(
            self.chat_frame,
            fg_color=self.colors['bg_secondary'],
            height=70,
            corner_radius=0
        )
        header.pack(fill="x")
        header.pack_propagate(False)
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Sol: Logo
        ctk.CTkLabel(
            header_content,
            text="💬 ChamberChat",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=self.colors['accent_secondary']
        ).pack(side="left")
        
        # Sağ: Durum ve Çıkış
        right_header = ctk.CTkFrame(header_content, fg_color="transparent")
        right_header.pack(side="right", fill="y")
        
        # Online durumu
        status_indicator = ctk.CTkFrame(right_header, fg_color="transparent")
        status_indicator.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(
            status_indicator,
            text="●",
            font=ctk.CTkFont(size=12),
            text_color=self.colors['success']
        ).pack(side="left")
        
        ctk.CTkLabel(
            status_indicator,
            text=f" {self.username}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=self.colors['text_primary']
        ).pack(side="left")
        
        # Çıkış butonu
        ctk.CTkButton(
            right_header,
            text="✕ Çıkış",
            width=80,
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color=self.colors['error'],
            hover_color="#ff6b7a",
            corner_radius=8,
            command=self.disconnect
        ).pack(side="right")
        
        # Mesaj alanı
        chat_container = ctk.CTkFrame(
            self.chat_frame,
            fg_color=self.colors['bg_primary'],
            corner_radius=0
        )
        chat_container.pack(expand=True, fill="both")
        
        self.messages_scroll = ctk.CTkScrollableFrame(
            chat_container,
            fg_color="transparent",
            corner_radius=0
        )
        self.messages_scroll.pack(expand=True, fill="both", padx=15, pady=10)
        
        # Mesaj giriş alanı
        input_container = ctk.CTkFrame(
            self.chat_frame,
            fg_color=self.colors['bg_secondary'],
            height=80,
            corner_radius=0
        )
        input_container.pack(fill="x", side="bottom")
        input_container.pack_propagate(False)
        
        input_inner = ctk.CTkFrame(input_container, fg_color="transparent")
        input_inner.pack(fill="both", expand=True, padx=20, pady=15)
        
        self.message_entry = ctk.CTkEntry(
            input_inner,
            height=45,
            font=ctk.CTkFont(size=14),
            fg_color=self.colors['bg_tertiary'],
            border_color=self.colors['accent_primary'],
            corner_radius=20,
            placeholder_text="Mesajınızı yazın..."
        )
        self.message_entry.pack(side="left", expand=True, fill="x", padx=(0, 15))
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        self.message_entry.focus()
        
        self.send_btn = ctk.CTkButton(
            input_inner,
            text="📤",
            width=50,
            height=45,
            font=ctk.CTkFont(size=20),
            fg_color=self.colors['accent_primary'],
            hover_color=self.colors['accent_secondary'],
            corner_radius=20,
            command=self.send_message
        )
        self.send_btn.pack(side="right")
        
        self.add_message("Sohbete hoş geldiniz! 🎉", "", "", is_system=True)
    
    def add_message(self, message, sender, timestamp="", is_me=False, is_system=False):
        """Mesaj ekle"""
        if not timestamp:
            timestamp = datetime.datetime.now().strftime("%H:%M")
        
        msg_container = ctk.CTkFrame(self.messages_scroll, fg_color="transparent")
        msg_container.pack(fill="x", pady=3)
        
        bubble = MessageBubble(
            msg_container,
            message=message,
            timestamp=timestamp,
            sender=sender,
            is_me=is_me,
            is_system=is_system,
            fg_color="transparent" if is_system else (self.colors['accent_primary'] if is_me else self.colors['bg_secondary'])
        )
        
        if is_system:
            bubble.pack(anchor="center")
        elif is_me:
            bubble.pack(anchor="e", padx=(50, 0))
        else:
            bubble.pack(anchor="w", padx=(0, 50))
        
        self.message_frames.append(msg_container)
        self.after(50, lambda: self.messages_scroll._parent_canvas.yview_moveto(1.0))
    
    def receive_messages(self):
        """Mesaj al"""
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message and not message.startswith("AUTH"):
                    self.after(0, lambda m=message: self.parse_and_display(m))
            except:
                if self.connected:
                    self.after(0, lambda: self.add_message("Bağlantı kesildi!", "", "", is_system=True))
                    self.connected = False
                break
    
    def parse_and_display(self, message):
        """Mesajı parse et ve göster"""
        message = message.strip()
        if not message:
            return
        
        if message.startswith("[") and "]" in message:
            try:
                time_end = message.index("]")
                timestamp = message[1:time_end]
                rest = message[time_end+1:].strip()
                
                if ":" in rest:
                    sender, content = rest.split(":", 1)
                    sender = sender.strip()
                    content = content.strip()
                    
                    if "🟢" in rest or "🔴" in rest:
                        self.add_message(rest, "", timestamp, is_system=True)
                    else:
                        self.add_message(content, sender, timestamp.split(":")[0] + ":" + timestamp.split(":")[1], is_me=False)
                else:
                    self.add_message(rest, "", timestamp, is_system=True)
            except:
                self.add_message(message, "Sistem", "", is_system=True)
        else:
            self.add_message(message, "", "", is_system=True)
    
    def send_message(self):
        """Mesaj gönder"""
        if not self.connected:
            return
        
        message = self.message_entry.get().strip()
        if not message:
            return
        
        try:
            self.client_socket.send(message.encode('utf-8'))
            self.add_message(message, "Ben", "", is_me=True)
            self.message_entry.delete(0, 'end')
            
            if message.lower() == 'quit':
                self.disconnect()
                
        except Exception as e:
            self.add_message(f"Hata: {e}", "", "", is_system=True)
    
    def disconnect(self):
        """Bağlantıyı kes"""
        self.connected = False
        if self.client_socket:
            try:
                self.client_socket.send('quit'.encode('utf-8'))
                self.client_socket.close()
            except:
                pass
        
        if hasattr(self, 'chat_frame'):
            self.chat_frame.destroy()
        self.message_frames = []
        self.create_auth_screen()
    
    def on_closing(self):
        """Pencere kapanırken"""
        if self.connected:
            self.disconnect()
        self.destroy()

if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()
