"""
CMD Chat - Windows GUI İstemcisi
Modern ve şık bir arayüz ile mesajlaşma uygulaması.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import socket
import threading
import datetime

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("💬 CMD Chat - Mesajlaşma")
        self.root.geometry("700x550")
        self.root.minsize(500, 400)
        
        # Renk teması
        self.colors = {
            'bg_dark': '#1a1a2e',
            'bg_medium': '#16213e',
            'bg_light': '#0f3460',
            'accent': '#e94560',
            'text': '#ffffff',
            'text_dim': '#a0a0a0',
            'success': '#4ecca3',
            'input_bg': '#2d2d44'
        }
        
        self.root.configure(bg=self.colors['bg_dark'])
        
        self.client_socket = None
        self.connected = False
        self.username = ""
        
        self.setup_styles()
        self.create_login_screen()
        
        # Pencere kapatıldığında bağlantıyı kes
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_styles(self):
        """Tema stillerini ayarla"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Button stili
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground=self.colors['text'],
                       padding=(20, 10),
                       font=('Segoe UI', 11, 'bold'))
        style.map('Accent.TButton',
                 background=[('active', '#ff6b6b')])
        
        # Entry stili
        style.configure('Dark.TEntry',
                       fieldbackground=self.colors['input_bg'],
                       foreground=self.colors['text'],
                       padding=10)
        
        # Label stili
        style.configure('Dark.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10))
        
        style.configure('Title.TLabel',
                       background=self.colors['bg_dark'],
                       foreground=self.colors['accent'],
                       font=('Segoe UI', 24, 'bold'))
    
    def create_login_screen(self):
        """Giriş ekranını oluştur"""
        self.login_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        self.login_frame.pack(expand=True, fill='both', padx=50, pady=30)
        
        # Başlık
        title = tk.Label(self.login_frame, text="💬 CMD Chat",
                        font=('Segoe UI', 32, 'bold'),
                        fg=self.colors['accent'],
                        bg=self.colors['bg_dark'])
        title.pack(pady=(30, 5))
        
        subtitle = tk.Label(self.login_frame, text="Uzak Mesajlaşma Uygulaması",
                           font=('Segoe UI', 12),
                           fg=self.colors['text_dim'],
                           bg=self.colors['bg_dark'])
        subtitle.pack(pady=(0, 40))
        
        # Giriş formu container
        form_frame = tk.Frame(self.login_frame, bg=self.colors['bg_medium'],
                             padx=30, pady=30)
        form_frame.pack(fill='x')
        
        # Sunucu IP
        tk.Label(form_frame, text="🌐 Sunucu IP Adresi",
                font=('Segoe UI', 10, 'bold'),
                fg=self.colors['text'],
                bg=self.colors['bg_medium']).pack(anchor='w', pady=(0, 5))
        
        self.ip_entry = tk.Entry(form_frame, font=('Segoe UI', 12),
                                bg=self.colors['input_bg'],
                                fg=self.colors['text'],
                                insertbackground=self.colors['text'],
                                relief='flat', bd=0)
        self.ip_entry.pack(fill='x', pady=(0, 15), ipady=10)
        self.ip_entry.insert(0, "127.0.0.1")
        
        # Port
        tk.Label(form_frame, text="🔌 Port Numarası",
                font=('Segoe UI', 10, 'bold'),
                fg=self.colors['text'],
                bg=self.colors['bg_medium']).pack(anchor='w', pady=(0, 5))
        
        self.port_entry = tk.Entry(form_frame, font=('Segoe UI', 12),
                                  bg=self.colors['input_bg'],
                                  fg=self.colors['text'],
                                  insertbackground=self.colors['text'],
                                  relief='flat', bd=0)
        self.port_entry.pack(fill='x', pady=(0, 15), ipady=10)
        self.port_entry.insert(0, "5555")
        
        # Kullanıcı Adı
        tk.Label(form_frame, text="👤 Kullanıcı Adınız",
                font=('Segoe UI', 10, 'bold'),
                fg=self.colors['text'],
                bg=self.colors['bg_medium']).pack(anchor='w', pady=(0, 5))
        
        self.username_entry = tk.Entry(form_frame, font=('Segoe UI', 12),
                                       bg=self.colors['input_bg'],
                                       fg=self.colors['text'],
                                       insertbackground=self.colors['text'],
                                       relief='flat', bd=0)
        self.username_entry.pack(fill='x', pady=(0, 25), ipady=10)
        self.username_entry.insert(0, "Kullanıcı")
        
        # Bağlan butonu
        self.connect_btn = tk.Button(form_frame, text="🚀 Bağlan",
                                    font=('Segoe UI', 12, 'bold'),
                                    bg=self.colors['accent'],
                                    fg=self.colors['text'],
                                    activebackground='#ff6b6b',
                                    activeforeground=self.colors['text'],
                                    relief='flat',
                                    cursor='hand2',
                                    command=self.connect_to_server)
        self.connect_btn.pack(fill='x', ipady=12)
        
        # Durum mesajı
        self.status_label = tk.Label(form_frame, text="",
                                    font=('Segoe UI', 10),
                                    fg=self.colors['text_dim'],
                                    bg=self.colors['bg_medium'])
        self.status_label.pack(pady=(15, 0))
        
        # Enter tuşu ile bağlan
        self.username_entry.bind('<Return>', lambda e: self.connect_to_server())
    
    def create_chat_screen(self):
        """Sohbet ekranını oluştur"""
        self.chat_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        self.chat_frame.pack(expand=True, fill='both')
        
        # Üst bar
        header = tk.Frame(self.chat_frame, bg=self.colors['bg_medium'], height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg=self.colors['bg_medium'])
        header_content.pack(expand=True, fill='both', padx=15)
        
        tk.Label(header_content, text="💬 CMD Chat",
                font=('Segoe UI', 14, 'bold'),
                fg=self.colors['accent'],
                bg=self.colors['bg_medium']).pack(side='left', pady=15)
        
        # Bağlantı durumu
        self.connection_status = tk.Label(header_content,
                                         text=f"● Bağlı: {self.username}",
                                         font=('Segoe UI', 10),
                                         fg=self.colors['success'],
                                         bg=self.colors['bg_medium'])
        self.connection_status.pack(side='right', pady=15)
        
        # Çıkış butonu
        disconnect_btn = tk.Button(header_content, text="✕ Çıkış",
                                  font=('Segoe UI', 10),
                                  bg=self.colors['accent'],
                                  fg=self.colors['text'],
                                  relief='flat',
                                  cursor='hand2',
                                  command=self.disconnect)
        disconnect_btn.pack(side='right', padx=(0, 15), pady=15)
        
        # Mesaj alanı
        chat_container = tk.Frame(self.chat_frame, bg=self.colors['bg_dark'])
        chat_container.pack(expand=True, fill='both', padx=15, pady=10)
        
        self.chat_display = scrolledtext.ScrolledText(
            chat_container,
            font=('Consolas', 11),
            bg=self.colors['bg_medium'],
            fg=self.colors['text'],
            insertbackground=self.colors['text'],
            relief='flat',
            wrap='word',
            state='disabled',
            padx=15,
            pady=10
        )
        self.chat_display.pack(expand=True, fill='both')
        
        # Mesaj giriş alanı
        input_frame = tk.Frame(self.chat_frame, bg=self.colors['bg_dark'])
        input_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        self.message_entry = tk.Entry(input_frame,
                                     font=('Segoe UI', 12),
                                     bg=self.colors['input_bg'],
                                     fg=self.colors['text'],
                                     insertbackground=self.colors['text'],
                                     relief='flat')
        self.message_entry.pack(side='left', expand=True, fill='x', ipady=12, padx=(0, 10))
        self.message_entry.bind('<Return>', lambda e: self.send_message())
        self.message_entry.focus()
        
        self.send_btn = tk.Button(input_frame, text="📤 Gönder",
                                 font=('Segoe UI', 11, 'bold'),
                                 bg=self.colors['accent'],
                                 fg=self.colors['text'],
                                 activebackground='#ff6b6b',
                                 relief='flat',
                                 cursor='hand2',
                                 command=self.send_message)
        self.send_btn.pack(side='right', ipady=10, ipadx=15)
        
        # Hoş geldin mesajı
        self.add_system_message(f"🎉 Hoş geldiniz, {self.username}! Mesajlaşmaya başlayabilirsiniz.")
    
    def connect_to_server(self):
        """Sunucuya bağlan"""
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        self.username = self.username_entry.get().strip()
        
        if not ip or not port or not self.username:
            self.status_label.config(text="❌ Lütfen tüm alanları doldurun!", fg=self.colors['accent'])
            return
        
        try:
            port = int(port)
        except ValueError:
            self.status_label.config(text="❌ Geçersiz port numarası!", fg=self.colors['accent'])
            return
        
        self.status_label.config(text="⏳ Bağlanılıyor...", fg=self.colors['text_dim'])
        self.connect_btn.config(state='disabled')
        self.root.update()
        
        # Bağlantıyı ayrı thread'de yap
        thread = threading.Thread(target=self._connect, args=(ip, port))
        thread.daemon = True
        thread.start()
    
    def _connect(self, ip, port):
        """Bağlantı işlemi (ayrı thread'de)"""
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.settimeout(10)
            self.client_socket.connect((ip, port))
            self.client_socket.settimeout(None)
            
            # Kullanıcı adı isteğini bekle
            response = self.client_socket.recv(1024).decode('utf-8')
            if "KULLANICI_ADI_GIRIN:" in response:
                self.client_socket.send(self.username.encode('utf-8'))
            
            self.connected = True
            
            # UI'ı güncelle (ana thread'de)
            self.root.after(0, self._on_connected)
            
            # Mesaj alma döngüsünü başlat
            self.receive_messages()
            
        except socket.timeout:
            self.root.after(0, lambda: self._on_connection_error("Bağlantı zaman aşımı!"))
        except ConnectionRefusedError:
            self.root.after(0, lambda: self._on_connection_error("Sunucu bulunamadı!"))
        except Exception as e:
            self.root.after(0, lambda: self._on_connection_error(str(e)))
    
    def _on_connected(self):
        """Bağlantı başarılı"""
        self.login_frame.destroy()
        self.create_chat_screen()
    
    def _on_connection_error(self, error):
        """Bağlantı hatası"""
        self.status_label.config(text=f"❌ {error}", fg=self.colors['accent'])
        self.connect_btn.config(state='normal')
    
    def receive_messages(self):
        """Sunucudan mesaj al"""
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message and not message.startswith("KULLANICI_ADI_GIRIN:"):
                    # UI'ı güncelle (ana thread'de)
                    self.root.after(0, lambda m=message: self.display_message(m))
            except:
                if self.connected:
                    self.root.after(0, lambda: self.add_system_message("❌ Sunucu bağlantısı kesildi!"))
                    self.connected = False
                break
    
    def display_message(self, message):
        """Mesajı ekranda göster"""
        self.chat_display.config(state='normal')
        self.chat_display.insert('end', message)
        self.chat_display.config(state='disabled')
        self.chat_display.see('end')
    
    def add_system_message(self, message):
        """Sistem mesajı ekle"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted = f"\n[{timestamp}] {message}\n"
        self.display_message(formatted)
    
    def send_message(self):
        """Mesaj gönder"""
        if not self.connected:
            return
        
        message = self.message_entry.get().strip()
        if not message:
            return
        
        try:
            self.client_socket.send(message.encode('utf-8'))
            
            # Kendi mesajımızı göster
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.display_message(f"\n[{timestamp}] Ben: {message}\n")
            
            self.message_entry.delete(0, 'end')
            
            if message.lower() == 'quit':
                self.disconnect()
                
        except Exception as e:
            self.add_system_message(f"❌ Mesaj gönderilemedi: {e}")
    
    def disconnect(self):
        """Bağlantıyı kes"""
        self.connected = False
        if self.client_socket:
            try:
                self.client_socket.send('quit'.encode('utf-8'))
                self.client_socket.close()
            except:
                pass
        
        # Giriş ekranına dön
        if hasattr(self, 'chat_frame'):
            self.chat_frame.destroy()
        self.create_login_screen()
    
    def on_closing(self):
        """Pencere kapatılırken"""
        if self.connected:
            self.disconnect()
        self.root.destroy()

def main():
    root = tk.Tk()
    
    # Windows için DPI ölçekleme
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    app = ChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
