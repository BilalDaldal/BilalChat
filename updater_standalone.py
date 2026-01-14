"""
BilalChat Standalone Updater
Ana uygulamadan bağımsız çalışan güncelleme aracı.

Kullanım: BilalChatUpdater.exe <yeni_exe_yolu> <hedef_exe_yolu>

Bu program:
1. Ana uygulamanın kapanmasını bekler
2. Eski EXE'yi siler
3. Yeni EXE'yi yerine koyar
4. Yeni uygulamayı başlatır
5. Kendini temizler
"""

import sys
import os
import time
import shutil
import subprocess

def log(msg):
    """Konsola log yaz"""
    print(f"[Updater] {msg}")

def wait_for_process(exe_name, timeout=60):
    """Belirtilen process'in kapanmasını bekle"""
    import ctypes
    
    log(f"'{exe_name}' kapanması bekleniyor...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        # tasklist ile kontrol et
        try:
            result = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {exe_name}'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            if exe_name.lower() not in result.stdout.lower():
                log("Uygulama kapandı.")
                return True
        except:
            pass
        
        time.sleep(1)
    
    log("Timeout - uygulama hala çalışıyor olabilir.")
    return False

def safe_delete(file_path, max_retries=30):
    """Dosyayı güvenli şekilde sil, gerekirse bekle"""
    log(f"Siliniyor: {file_path}")
    
    for i in range(max_retries):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if not os.path.exists(file_path):
                log("Dosya silindi.")
                return True
        except PermissionError:
            log(f"Dosya kilitli, bekleniyor... ({i+1}/{max_retries})")
            time.sleep(2)
        except Exception as e:
            log(f"Silme hatası: {e}")
            time.sleep(1)
    
    return False

def safe_move(src, dst, max_retries=30):
    """Dosyayı güvenli şekilde taşı"""
    log(f"Taşınıyor: {src} -> {dst}")
    
    for i in range(max_retries):
        try:
            shutil.move(src, dst)
            if os.path.exists(dst):
                log("Dosya taşındı.")
                return True
        except PermissionError:
            log(f"Hedef kilitli, bekleniyor... ({i+1}/{max_retries})")
            time.sleep(2)
        except Exception as e:
            log(f"Taşıma hatası: {e}")
            time.sleep(1)
    
    return False

def main():
    print("=" * 50)
    print("  BilalChat Updater")
    print("=" * 50)
    print()
    
    # Argümanları kontrol et
    if len(sys.argv) < 3:
        log("Kullanım: BilalChatUpdater.exe <yeni_exe> <hedef_exe>")
        input("Devam etmek için Enter'a basın...")
        sys.exit(1)
    
    new_exe = sys.argv[1]
    target_exe = sys.argv[2]
    target_name = os.path.basename(target_exe)
    
    log(f"Yeni dosya: {new_exe}")
    log(f"Hedef: {target_exe}")
    print()
    
    # Yeni dosya var mı?
    if not os.path.exists(new_exe):
        log(f"HATA: Yeni dosya bulunamadı: {new_exe}")
        input("Devam etmek için Enter'a basın...")
        sys.exit(1)
    
    # 1. Ana uygulamanın kapanmasını bekle
    print("[1/4] Uygulama kapatılıyor...")
    time.sleep(2)  # Uygulamanın kapanma işlemini başlatmasına izin ver
    wait_for_process(target_name, timeout=60)
    
    # Ekstra bekleme (dosya kilidi için)
    print("[2/4] Dosya kilidi bekleniyor...")
    time.sleep(3)
    
    # 2. Eski dosyayı sil
    print("[3/4] Eski sürüm siliniyor...")
    if os.path.exists(target_exe):
        if not safe_delete(target_exe):
            log("HATA: Eski dosya silinemedi!")
            log("Lütfen uygulamayı manuel olarak kapatın ve tekrar deneyin.")
            input("Devam etmek için Enter'a basın...")
            sys.exit(1)
    
    # 3. Yeni dosyayı taşı
    print("[4/4] Yeni sürüm kuruluyor...")
    if not safe_move(new_exe, target_exe):
        log("HATA: Yeni dosya taşınamadı!")
        input("Devam etmek için Enter'a basın...")
        sys.exit(1)
    
    print()
    print("=" * 50)
    print("  Güncelleme tamamlandı!")
    print("=" * 50)
    print()
    
    # 4. Yeni uygulamayı başlat
    log("Uygulama yeniden başlatılıyor...")
    time.sleep(1)
    
    try:
        subprocess.Popen([target_exe], cwd=os.path.dirname(target_exe))
    except Exception as e:
        log(f"Başlatma hatası: {e}")
    
    # 5. Kendimizi temizle (batch ile)
    self_exe = sys.executable if getattr(sys, 'frozen', False) else __file__
    
    if getattr(sys, 'frozen', False):
        # PyInstaller ile derlenmişse, kendimizi silmek için batch kullan
        batch_content = f'''@echo off
timeout /t 2 /nobreak >nul
del /f /q "{self_exe}" >nul 2>&1
del /f /q "%~f0" >nul 2>&1
'''
        batch_path = os.path.join(os.path.dirname(self_exe), "_cleanup.bat")
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        
        subprocess.Popen(
            ['cmd', '/c', batch_path],
            creationflags=subprocess.CREATE_NO_WINDOW
        )
    
    sys.exit(0)

if __name__ == "__main__":
    main()
