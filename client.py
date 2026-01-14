"""
CMD Chat Client - Mesajlaşma İstemcisi
Sunucuya bağlanıp mesaj gönderip almayı sağlar.
"""

import socket
import threading
import sys

def receive_messages(client_socket):
    """Sunucudan gelen mesajları dinler"""
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message:
                # Kullanıcı adı isteği değilse ekrana yaz
                if not message.startswith("KULLANICI_ADI_GIRIN:"):
                    print(message, end='')
            else:
                print("\n[!] Sunucu ile bağlantı kesildi.")
                break
        except ConnectionResetError:
            print("\n[!] Sunucu bağlantısı koptu.")
            break
        except Exception as e:
            print(f"\n[!] Bağlantı hatası: {e}")
            break
    
    # Programı kapat
    sys.exit(0)

def main():
    """Ana istemci fonksiyonu"""
    print("""
╔══════════════════════════════════════════════════════╗
║           CMD CHAT CLIENT - MESAJLAŞMA İSTEMCİSİ     ║
╚══════════════════════════════════════════════════════╝
    """)
    
    # Sunucu bilgilerini al
    server_ip = input("📍 Sunucu IP adresi: ").strip()
    if not server_ip:
        server_ip = "127.0.0.1"
    
    server_port = input("🔌 Sunucu portu (varsayılan 5555): ").strip()
    if not server_port:
        server_port = 5555
    else:
        server_port = int(server_port)
    
    # Sunucuya bağlan
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        print(f"\n⏳ {server_ip}:{server_port} adresine bağlanılıyor...")
        client_socket.connect((server_ip, server_port))
        print("✅ Bağlantı başarılı!")
        
        # Kullanıcı adı isteğini bekle
        response = client_socket.recv(1024).decode('utf-8')
        if "KULLANICI_ADI_GIRIN:" in response:
            username = input("\n👤 Kullanıcı adınız: ").strip()
            if not username:
                username = "Anonim"
            client_socket.send(username.encode('utf-8'))
        
        # Mesaj alma thread'ini başlat
        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
        receive_thread.daemon = True
        receive_thread.start()
        
        # Mesaj gönderme döngüsü
        while True:
            try:
                message = input()
                
                if message.lower() == 'quit':
                    client_socket.send('quit'.encode('utf-8'))
                    print("\n👋 Görüşmek üzere!")
                    break
                
                if message.strip():
                    client_socket.send(message.encode('utf-8'))
                    
            except KeyboardInterrupt:
                client_socket.send('quit'.encode('utf-8'))
                print("\n👋 Görüşmek üzere!")
                break
            except:
                break
                
    except ConnectionRefusedError:
        print(f"\n❌ Bağlantı reddedildi! Sunucu ({server_ip}:{server_port}) çalışmıyor olabilir.")
    except socket.timeout:
        print("\n❌ Bağlantı zaman aşımına uğradı!")
    except Exception as e:
        print(f"\n❌ Bağlantı hatası: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    main()
