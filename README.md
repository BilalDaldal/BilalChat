# 💬 CMD Chat - Komut Satırı Mesajlaşma Uygulaması

Uzaktaki bilgisayarlarla CMD üzerinden mesajlaşmanızı sağlayan basit ve etkili bir Python uygulaması.

## 🚀 Kurulum

Python 3.x yüklü olması yeterlidir. Ek kütüphane gerekmez!

## 📖 Kullanım

### 1. Sunucu Başlatma

Bir bilgisayarda sunucuyu başlatın:

```bash
cd C:\Users\Bilal\.gemini\antigravity\scratch\cmd-chat
python server.py
```

### 2. İstemci Bağlantısı

Diğer bilgisayarlarda istemciyi çalıştırın:

```bash
python client.py
```

Daha sonra:
- Sunucunun IP adresini girin
- Port numarasını girin (varsayılan: 5555)
- Kullanıcı adınızı belirleyin

## 🌐 Uzak Bağlantı için Ayarlar

### Aynı Ağda (LAN)
Sunucu bilgisayarının yerel IP adresini kullanın (örn: `192.168.1.x`)

Yerel IP'nizi öğrenmek için:
```bash
ipconfig
```

### Farklı Ağlarda (İnternet Üzerinden)

1. **Port Yönlendirme**: Modem/router'da 5555 portunu sunucu bilgisayarına yönlendirin
2. **Public IP**: [whatismyip.com](https://whatismyip.com) adresinden public IP'nizi öğrenin
3. **Firewall**: Windows Güvenlik Duvarı'nda 5555 portuna izin verin

## 🎮 Komutlar

| Komut | Açıklama |
|-------|----------|
| `quit` | Sohbetten çıkış yapar |
| `Ctrl+C` | Programı sonlandırır |

## 🔒 Güvenlik Notları

- Bu uygulama eğitim amaçlıdır
- ⚠️ Mesajlar şifrelenmemiştir
- Hassas bilgiler paylaşmayın
- Güvenilir ağlarda kullanın

### 🔐 Şifre Güvenliği (Yeni!)

BilalChat artık **bcrypt** ile güvenli şifre hashleme kullanıyor:

- **bcrypt algoritması**: Her şifre için otomatik rastgele salt
- **2^12 iterasyon**: Brute-force saldırılarına karşı koruma

**Şifre Politikası:**
| Gereksinim | Açıklama |
|------------|----------|
| Minimum uzunluk | 8 karakter |
| Büyük harf | En az 1 adet (A-Z) |
| Küçük harf | En az 1 adet (a-z) |
| Rakam | En az 1 adet (0-9) |

**Kullanıcı Adı Kuralları:**
- Minimum 3 karakter
- Sadece harf, rakam ve alt çizgi (_) içerebilir

## 📁 Dosyalar

- `server.py` - Sunucu uygulaması
- `client.py` - İstemci uygulaması
- `chat_pro.py` - Modern GUI istemcisi (CustomTkinter)
- `chat_gui.py` - Standart GUI istemcisi (Tkinter)

## 📦 Gereksinimler

```bash
pip install bcrypt customtkinter pillow
```
