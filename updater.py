"""
BilalChat Auto Updater v2.0
GitHub Releases üzerinden tam otomatik güncelleme sistemi.

Özellikler:
- GitHub API ile versiyon kontrolü
- Otomatik indirme ve kurulum
- SSL sertifika sorunlarını bypass
- Progress callback desteği
- Detaylı hata yönetimi
"""

import urllib.request
import urllib.error
import json
import os
import sys
import subprocess
import time
import ssl
import tempfile

# ═══════════════════════════════════════════════════════════════════════════════
# � VERSİYON BİLGİLERİ
# ═══════════════════════════════════════════════════════════════════════════════
CURRENT_VERSION = "1.0.5"
APP_NAME = "BilalChat"

# ═══════════════════════════════════════════════════════════════════════════════
# 📌 GITHUB AYARLARI
# ═══════════════════════════════════════════════════════════════════════════════
GITHUB_OWNER = "BilalDaldal"
GITHUB_REPO = "BilalChat"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
EXE_NAME = "BilalChat.exe"

# ═══════════════════════════════════════════════════════════════════════════════
# 📌 DEBUG MODU
# ═══════════════════════════════════════════════════════════════════════════════
DEBUG = True


def log(message: str, level: str = "INFO"):
    """Log mesajı yazdır"""
    if DEBUG or level in ("ERROR", "WARNING"):
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")


def get_ssl_context():
    """
    Güvenli SSL context oluştur.
    Sertifika doğrulama hatalarını bypass eder.
    """
    try:
        # Önce normal context dene
        context = ssl.create_default_context()
        return context
    except:
        pass
    
    # Sorun varsa unverified context kullan
    context = ssl._create_unverified_context()
    log("SSL sertifika doğrulama devre dışı", "WARNING")
    return context


def parse_version(version_str: str) -> tuple:
    """
    Versiyon stringini tuple'a çevir.
    "v1.2.3" veya "1.2.3" -> (1, 2, 3)
    """
    try:
        # 'v' prefix'ini kaldır
        clean = version_str.strip().lstrip('vV')
        # Parçalara ayır ve int'e çevir
        parts = [int(x) for x in clean.split('.')]
        # 3 parçaya tamamla
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts[:3])
    except (ValueError, AttributeError):
        return (0, 0, 0)


def compare_versions(current: str, latest: str) -> int:
    """
    İki versiyonu karşılaştır.
    Returns:
        -1: current < latest (güncelleme gerekli)
         0: current == latest (güncel)
         1: current > latest (daha yeni)
    """
    cur = parse_version(current)
    lat = parse_version(latest)
    
    if cur < lat:
        return -1
    elif cur > lat:
        return 1
    return 0


def check_for_updates() -> dict:
    """
    GitHub'dan son sürümü kontrol et.
    
    Returns:
        dict: {
            'success': bool,
            'needs_update': bool,
            'current_version': str,
            'latest_version': str,
            'download_url': str,
            'release_notes': str,
            'error': str or None
        }
    """
    result = {
        'success': False,
        'needs_update': False,
        'current_version': CURRENT_VERSION,
        'latest_version': '',
        'download_url': '',
        'release_notes': '',
        'error': None
    }
    
    log(f"Güncelleme kontrolü başlatılıyor... (Mevcut: v{CURRENT_VERSION})")
    
    try:
        # Request oluştur
        request = urllib.request.Request(
            GITHUB_API_URL,
            headers={
                'User-Agent': f'{APP_NAME}-Updater/2.0',
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        
        # SSL context al
        ssl_context = get_ssl_context()
        
        # API çağrısı
        log(f"GitHub API'ye bağlanılıyor: {GITHUB_API_URL}")
        with urllib.request.urlopen(request, timeout=15, context=ssl_context) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        # Versiyon bilgisi
        latest_version = data.get('tag_name', '').strip()
        result['latest_version'] = latest_version
        log(f"Son sürüm: {latest_version}")
        
        # Release notları
        result['release_notes'] = data.get('body', '') or ''
        
        # İndirme URL'si bul
        download_url = None
        assets = data.get('assets', [])
        
        log(f"Toplam {len(assets)} asset bulundu")
        
        for asset in assets:
            asset_name = asset.get('name', '')
            log(f"  Asset: {asset_name}")
            
            if asset_name.lower() == EXE_NAME.lower():
                download_url = asset.get('browser_download_url', '')
                log(f"  -> Indirme URL'si bulundu!")
                break
        
        if not download_url:
            # Asset bulunamadı, releases sayfasını kullan
            download_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
            log("EXE asset bulunamadı, releases sayfası kullanılacak", "WARNING")
        
        result['download_url'] = download_url
        
        # Versiyon karşılaştırma
        comparison = compare_versions(CURRENT_VERSION, latest_version)
        
        if comparison < 0:
            result['needs_update'] = True
            log(f"[*] Guncelleme mevcut: v{CURRENT_VERSION} -> {latest_version}")
        else:
            log(f"[OK] Uygulama guncel (v{CURRENT_VERSION})")
        
        result['success'] = True
        
    except urllib.error.HTTPError as e:
        result['error'] = f"GitHub API hatası: HTTP {e.code}"
        log(result['error'], "ERROR")
        
    except urllib.error.URLError as e:
        result['error'] = f"Bağlantı hatası: {e.reason}"
        log(result['error'], "ERROR")
        
    except json.JSONDecodeError:
        result['error'] = "GitHub API yanıtı geçersiz"
        log(result['error'], "ERROR")
        
    except Exception as e:
        result['error'] = f"Beklenmeyen hata: {type(e).__name__}: {e}"
        log(result['error'], "ERROR")
    
    return result


def get_exe_path() -> str:
    """Çalışan EXE'nin tam yolunu döndür"""
    if getattr(sys, 'frozen', False):
        # PyInstaller ile derlenmiş
        return sys.executable
    else:
        # Python scripti
        return os.path.abspath(sys.argv[0])


def download_update(download_url: str, progress_callback=None) -> dict:
    """
    Güncellemeyi indir.
    
    Args:
        download_url: İndirme linki
        progress_callback: func(downloaded_bytes, total_bytes, percent)
    
    Returns:
        dict: {
            'success': bool,
            'file_path': str,
            'error': str or None
        }
    """
    result = {
        'success': False,
        'file_path': '',
        'error': None
    }
    
    log(f"İndirme başlatılıyor: {download_url}")
    
    try:
        # Mevcut EXE'nin klasörünü al
        exe_path = get_exe_path()
        exe_dir = os.path.dirname(exe_path)
        
        # Yeni dosya için geçici isim
        new_file = os.path.join(exe_dir, f"{APP_NAME}_update_{os.getpid()}.exe")
        
        log(f"İndirme hedefi: {new_file}")
        
        # Request oluştur
        request = urllib.request.Request(
            download_url,
            headers={'User-Agent': f'{APP_NAME}-Updater/2.0'}
        )
        
        # SSL context
        ssl_context = get_ssl_context()
        
        # İndirme
        with urllib.request.urlopen(request, timeout=120, context=ssl_context) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 16384  # 16KB chunks
            
            log(f"Dosya boyutu: {total_size / (1024*1024):.2f} MB")
            
            with open(new_file, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        percent = (downloaded / total_size) * 100
                        progress_callback(downloaded, total_size, percent)
        
        # Dosya boyutu kontrolü
        actual_size = os.path.getsize(new_file)
        if total_size > 0 and actual_size != total_size:
            result['error'] = f"Dosya boyutu uyuşmuyor: {actual_size} != {total_size}"
            log(result['error'], "ERROR")
            os.remove(new_file)
            return result
        
        log(f"✅ İndirme tamamlandı: {actual_size / (1024*1024):.2f} MB")
        
        result['success'] = True
        result['file_path'] = new_file
        
    except urllib.error.URLError as e:
        result['error'] = f"İndirme hatası: {e.reason}"
        log(result['error'], "ERROR")
        
    except PermissionError:
        result['error'] = "Yazma izni yok! Uygulamayı yönetici olarak çalıştırın."
        log(result['error'], "ERROR")
        
    except Exception as e:
        result['error'] = f"İndirme başarısız: {type(e).__name__}: {e}"
        log(result['error'], "ERROR")
    
    return result


def install_update(new_exe_path: str) -> dict:
    """
    Güncellemeyi kur ve uygulamayı yeniden başlat.
    
    Standalone updater EXE kullanarak:
    1. BilalChatUpdater.exe'yi başlat (parametrelerle)
    2. Ana uygulamayı kapat
    3. Updater bekler, günceller, yeni versiyonu başlatır
    
    Returns:
        dict: {
            'success': bool,
            'error': str or None
        }
    """
    result = {
        'success': False,
        'error': None
    }
    
    log("Kurulum başlatılıyor...")
    
    try:
        if not os.path.exists(new_exe_path):
            result['error'] = "Güncelleme dosyası bulunamadı!"
            log(result['error'], "ERROR")
            return result
        
        # Mevcut EXE bilgileri
        current_exe = get_exe_path()
        exe_dir = os.path.dirname(current_exe)
        
        log(f"Mevcut EXE: {current_exe}")
        log(f"Yeni EXE: {new_exe_path}")
        
        # Updater EXE'nin yolunu bul
        updater_exe = os.path.join(exe_dir, "BilalChatUpdater.exe")
        
        # Eğer updater yoksa, PyInstaller bundle'dan çıkar
        if not os.path.exists(updater_exe):
            # PyInstaller ile paketlenmişse, _MEIPASS'ten kopyala
            if getattr(sys, 'frozen', False):
                bundle_dir = getattr(sys, '_MEIPASS', exe_dir)
                bundled_updater = os.path.join(bundle_dir, "BilalChatUpdater.exe")
                
                if os.path.exists(bundled_updater):
                    import shutil
                    shutil.copy2(bundled_updater, updater_exe)
                    log(f"Updater çıkarıldı: {updater_exe}")
        
        # Updater hala yoksa, indirmeyi dene
        if not os.path.exists(updater_exe):
            log("Updater EXE bulunamadı, GitHub'dan indiriliyor...", "WARNING")
            
            # GitHub'dan updater'ı indir
            updater_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest/download/BilalChatUpdater.exe"
            
            try:
                request = urllib.request.Request(
                    updater_url,
                    headers={'User-Agent': f'{APP_NAME}-Updater/2.0'}
                )
                ssl_context = get_ssl_context()
                
                with urllib.request.urlopen(request, timeout=30, context=ssl_context) as response:
                    with open(updater_exe, 'wb') as f:
                        f.write(response.read())
                
                log(f"Updater indirildi: {updater_exe}")
                
            except Exception as e:
                log(f"Updater indirilemedi: {e}", "ERROR")
                # Fallback: Batch script kullan
                return install_update_fallback(new_exe_path, current_exe, exe_dir)
        
        # Updater'ı başlat
        log("Updater başlatılıyor...")
        
        subprocess.Popen(
            [updater_exe, new_exe_path, current_exe],
            cwd=exe_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        log("Updater başlatıldı, uygulama kapatılıyor...")
        
        result['success'] = True
        
        # Uygulamayı kapat (updater devam edecek)
        time.sleep(0.5)
        sys.exit(0)
        
    except Exception as e:
        result['error'] = f"Kurulum hatası: {type(e).__name__}: {e}"
        log(result['error'], "ERROR")
    
    return result


def install_update_fallback(new_exe_path: str, current_exe: str, exe_dir: str) -> dict:
    """
    Fallback: Batch script ile güncelleme.
    Updater EXE bulunamazsa bu kullanılır.
    """
    result = {
        'success': False,
        'error': None
    }
    
    log("Fallback: Batch script ile güncelleme...")
    
    exe_name = os.path.basename(current_exe)
    batch_path = os.path.join(exe_dir, f"_update_{os.getpid()}.bat")
    
    batch_script = f'''@echo off
chcp 65001 >nul 2>&1
title {APP_NAME} Updater
echo.
echo  Guncelleme kuruluyor...
echo.

:wait_loop
timeout /t 2 /nobreak >nul
tasklist /FI "IMAGENAME eq {exe_name}" 2>NUL | find /I /N "{exe_name}" >NUL
if "%ERRORLEVEL%"=="0" goto wait_loop

timeout /t 3 /nobreak >nul

del /f /q "{current_exe}" >nul 2>&1
move /y "{new_exe_path}" "{current_exe}" >nul 2>&1

if exist "{current_exe}" (
    echo  Guncelleme tamamlandi!
    start "" "{current_exe}"
) else (
    echo  HATA: Guncelleme basarisiz!
    pause
)

del /f /q "%~f0" >nul 2>&1
'''
    
    with open(batch_path, 'w', encoding='utf-8') as f:
        f.write(batch_script)
    
    subprocess.Popen(
        ['cmd', '/c', 'start', '/min', '', batch_path],
        shell=True,
        cwd=exe_dir
    )
    
    result['success'] = True
    time.sleep(0.5)
    sys.exit(0)
    
    return result


def get_current_version() -> str:
    """Mevcut versiyonu döndür"""
    return CURRENT_VERSION


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 50)
    print(f"  {APP_NAME} Updater v2.0 - Test")
    print("=" * 50)
    print(f"\n  Mevcut Versiyon: v{CURRENT_VERSION}")
    print(f"  GitHub: {GITHUB_OWNER}/{GITHUB_REPO}")
    print()
    
    # Guncelleme kontrolu
    result = check_for_updates()
    
    print()
    if result['error']:
        print(f"  [HATA] {result['error']}")
    elif result['needs_update']:
        print(f"  [*] Yeni surum mevcut: {result['latest_version']}")
        print(f"  [>] Indirme: {result['download_url']}")
        
        # Test modunda indirme yapma
        user_input = input("\n  Indirmek ister misiniz? (e/h): ").strip().lower()
        if user_input == 'e':
            def progress(downloaded, total, percent):
                bar = '#' * int(percent / 5) + '-' * (20 - int(percent / 5))
                print(f"\r  [{bar}] {percent:.1f}%", end='', flush=True)
            
            print()
            dl_result = download_update(result['download_url'], progress)
            print()
            
            if dl_result['success']:
                print(f"\n  [OK] Indirildi: {dl_result['file_path']}")
                
                install_input = input("  Kurmak ister misiniz? (e/h): ").strip().lower()
                if install_input == 'e':
                    install_update(dl_result['file_path'])
            else:
                print(f"\n  [HATA] Indirme hatasi: {dl_result['error']}")
    else:
        print(f"  [OK] Uygulama guncel!")
    
    print()
