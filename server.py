"""
ChamberChat Server - Hesap Sistemli Mesajlaşma Sunucusu
SQLite veritabanı ve gelişmiş şifre güvenliği ile kullanıcı yönetimi.
- bcrypt ile güvenli şifre hashleme
- Otomatik rastgele salt
- Şifre politikası kontrolü
"""

import socket
import threading
import datetime
import sqlite3
import os
import re

# bcrypt için - eğer yüklü değilse hashlib kullan
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
    print("[SECURITY] ✅ bcrypt modülü yüklü - Güvenli şifreleme aktif")
except ImportError:
    import hashlib
    BCRYPT_AVAILABLE = False
    print("[SECURITY] ⚠️ bcrypt yüklü değil! 'pip install bcrypt' ile yükleyin.")
    print("[SECURITY] Geçici olarak SHA-256 kullanılıyor.")


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

# Sunucu ayarları
HOST = '0.0.0.0'
PORT = 5555

# Veritabanı dosyası
DB_FILE = 'users.db'

# Bağlı istemcileri takip et
clients = {}
clients_lock = threading.Lock()

def init_database():
    """Veritabanını başlat"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("[DB] Veritabanı hazır: users.db")


def save_message(sender, message):
    """Mesajı veritabanına kaydet"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        timestamp = get_timestamp()
        cursor.execute(
            'INSERT INTO messages (sender, message, timestamp) VALUES (?, ?, ?)',
            (sender, message, timestamp)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB] Mesaj kaydetme hatası: {e}")


def get_recent_messages(limit=50):
    """Son N mesajı getir"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            'SELECT sender, message, timestamp FROM messages ORDER BY id DESC LIMIT ?',
            (limit,)
        )
        messages = cursor.fetchall()
        conn.close()
        return list(reversed(messages))
    except Exception as e:
        print(f"[DB] Mesaj getirme hatası: {e}")
        return []

def hash_password(password):
    """
    Şifreyi bcrypt ile hashle (otomatik rastgele salt dahil)
    bcrypt yoksa SHA-256 + salt kullan
    """
    if BCRYPT_AVAILABLE:
        # bcrypt otomatik olarak rastgele salt üretir ve hash'e dahil eder
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)  # 2^12 iterasyon - güvenli ve hızlı
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    else:
        # Fallback: SHA-256 + sabit salt (daha az güvenli)
        salt = "BilalChat_Secret_Salt_2024"
        return hashlib.sha256((password + salt).encode()).hexdigest()


def verify_password(password, stored_hash):
    """
    Şifreyi doğrula
    """
    if BCRYPT_AVAILABLE:
        try:
            password_bytes = password.encode('utf-8')
            stored_hash_bytes = stored_hash.encode('utf-8')
            return bcrypt.checkpw(password_bytes, stored_hash_bytes)
        except Exception:
            return False
    else:
        # Fallback: SHA-256 kontrolü
        return hash_password(password) == stored_hash

def register_user(username, password):
    """Yeni kullanıcı kaydet (şifre politikası kontrolü ile)"""
    try:
        # Şifre politikasını kontrol et
        is_valid, policy_message = validate_password(password)
        if not is_valid:
            return False, policy_message
        
        # Kullanıcı adı kontrolü
        if len(username) < 3:
            return False, "Kullanıcı adı en az 3 karakter olmalıdır!"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Kullanıcı adı sadece harf, rakam ve alt çizgi içerebilir!"
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        password_hash = hash_password(password)
        cursor.execute(
            'INSERT INTO users (username, password_hash) VALUES (?, ?)',
            (username, password_hash)
        )
        conn.commit()
        conn.close()
        return True, "Kayıt başarılı! 🎉"
    except sqlite3.IntegrityError:
        return False, "Bu kullanıcı adı zaten kullanılıyor!"
    except Exception as e:
        return False, f"Kayıt hatası: {str(e)}"

def login_user(username, password):
    """Kullanıcı girişi doğrula (bcrypt ile güvenli karşılaştırma)"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Kullanıcının hash'ini al
        cursor.execute(
            'SELECT id, password_hash FROM users WHERE username = ?',
            (username,)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            user_id, stored_hash = result
            # bcrypt ile güvenli şifre doğrulama
            if verify_password(password, stored_hash):
                return True, "Giriş başarılı! 🎉"
            else:
                return False, "Yanlış şifre!"
        else:
            return False, "Kullanıcı bulunamadı!"
    except Exception as e:
        return False, f"Giriş hatası: {str(e)}"

def get_timestamp():
    """Zaman damgası döndürür"""
    return datetime.datetime.now().strftime("%H:%M:%S")

def broadcast(message, sender_socket=None):
    """Mesajı tüm bağlı istemcilere gönderir"""
    with clients_lock:
        for client_socket, username in list(clients.items()):
            if client_socket != sender_socket:
                try:
                    client_socket.send(message.encode('utf-8'))
                except:
                    remove_client(client_socket)

def remove_client(client_socket):
    """İstemciyi listeden kaldırır"""
    with clients_lock:
        if client_socket in clients:
            username = clients[client_socket]
            del clients[client_socket]
            return username
    return None

def handle_client(client_socket, address):
    """Her istemci için ayrı thread'de çalışır"""
    username = None
    authenticated = False
    
    try:
        # Kimlik doğrulama döngüsü
        while not authenticated:
            client_socket.send("AUTH_REQUIRED".encode('utf-8'))
            
            try:
                auth_data = client_socket.recv(1024).decode('utf-8').strip()
                
                if not auth_data:
                    break
                
                # REGISTER:username:password veya LOGIN:username:password
                parts = auth_data.split(':', 2)
                
                if len(parts) != 3:
                    client_socket.send("AUTH_ERROR:Geçersiz format!".encode('utf-8'))
                    continue
                
                action, username, password = parts
                
                if action == "REGISTER":
                    success, message = register_user(username, password)
                    if success:
                        client_socket.send(f"AUTH_SUCCESS:{message}".encode('utf-8'))
                        authenticated = True
                        print(f"[+] Yeni kayıt: {username}")
                    else:
                        client_socket.send(f"AUTH_ERROR:{message}".encode('utf-8'))
                        
                elif action == "LOGIN":
                    success, message = login_user(username, password)
                    if success:
                        client_socket.send(f"AUTH_SUCCESS:{message}".encode('utf-8'))
                        authenticated = True
                        print(f"[+] Giriş: {username}")
                    else:
                        client_socket.send(f"AUTH_ERROR:{message}".encode('utf-8'))
                else:
                    client_socket.send("AUTH_ERROR:Bilinmeyen komut!".encode('utf-8'))
                    
            except ConnectionResetError:
                break
        
        if not authenticated:
            client_socket.close()
            return
        
        # Kullanıcı listesine ekle
        with clients_lock:
            clients[client_socket] = username
        
        # Hoş geldin mesajı
        welcome_msg = f"\n{'='*50}\n🎉 Hoş geldiniz, {username}!\n💬 Mesaj yazmaya başlayabilirsiniz.\n📤 Çıkmak için 'quit' yazın.\n{'='*50}\n"
        client_socket.send(welcome_msg.encode('utf-8'))
        
        # Mesaj geçmişini gönder
        history = get_recent_messages(50)
        if history:
            client_socket.send("\n📜 Son mesajlar:\n".encode('utf-8'))
            for sender, msg, ts in history:
                history_msg = f"[{ts}] {sender}: {msg}\n"
                client_socket.send(history_msg.encode('utf-8'))
            client_socket.send(("─" * 40 + "\n").encode('utf-8'))
        
        # Diğer kullanıcılara bildir
        join_msg = f"\n[{get_timestamp()}] 🟢 {username} sohbete katıldı!\n"
        broadcast(join_msg, client_socket)
        print(f"[CHAT] {username} ({address[0]}:{address[1]}) sohbete katıldı")
        
        # Mesaj döngüsü
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                
                if not message:
                    break
                
                message = message.strip()
                
                if message.lower() == 'quit':
                    break
                
                if message:
                    formatted_msg = f"[{get_timestamp()}] {username}: {message}"
                    print(formatted_msg)
                    save_message(username, message)  # Mesajı kaydet
                    broadcast(f"\n{formatted_msg}\n", client_socket)
                    
            except ConnectionResetError:
                break
            except Exception as e:
                print(f"[!] Mesaj hatası: {e}")
                break
                
    except Exception as e:
        print(f"[!] İstemci hatası: {e}")
    finally:
        # İstemci ayrıldığında
        removed_user = remove_client(client_socket)
        if removed_user:
            leave_msg = f"\n[{get_timestamp()}] 🔴 {removed_user} sohbetten ayrıldı.\n"
            broadcast(leave_msg)
            print(f"[-] {removed_user} ayrıldı")
        client_socket.close()

def main():
    """Ana sunucu fonksiyonu"""
    init_database()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen(10)
        
        print(f"""
╔══════════════════════════════════════════════════════╗
║         BILALCHAT SERVER - HESAP SİSTEMİ AKTİF       ║
╠══════════════════════════════════════════════════════╣
║  🌐 Sunucu başlatıldı!                               ║
║  📍 IP: {HOST}                                     ║
║  🔌 Port: {PORT}                                      ║
║  🔐 Hesap sistemi: AKTİF                             ║
║  💾 Veritabanı: {DB_FILE}                            ║
║                                                      ║
║  ⏹️  Durdurmak için Ctrl+C                           ║
╚══════════════════════════════════════════════════════╝
        """)
        
        while True:
            client_socket, address = server.accept()
            thread = threading.Thread(target=handle_client, args=(client_socket, address))
            thread.daemon = True
            thread.start()
            
    except KeyboardInterrupt:
        print("\n[!] Sunucu kapatılıyor...")
    except Exception as e:
        print(f"[!] Sunucu hatası: {e}")
    finally:
        server.close()

if __name__ == "__main__":
    main()
