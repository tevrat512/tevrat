
#GÜVENLİK SİSTEMİ v14.0 - TAM VERSiYON
#=======================================
import customtkinter as ctk
import cv2, os, sys, json, threading, time, subprocess, atexit, ctypes
import numpy as np
from PIL import Image, ImageTk
from datetime import datetime
from tkinter import messagebox, Menu, simpledialog, filedialog
import tkinter as tk
import ctypes.wintypes

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


#  YOLLAR -----
DESKTOP    = os.path.join(os.path.expanduser("~"), "Desktop")
ANA        = os.path.join(DESKTOP, "güvenlik")
YON_KL     = os.path.join(ANA, "YÖNETİCİLER")
SESLER     = os.path.join(ANA, "SESLER")
IZLENEN    = os.path.join(ANA, "izlenen kullanıcılar")
YON_RESIM  = os.path.join(YON_KL, "resimler")

# FFmpeg — sabit klasör adı (dir/s'den alındı)
FFMPEG = os.path.join(ANA,
    "ffmpeg-2026-03-15-git-6ba0b59d8b-full_build", "bin", "ffmpeg.exe")
if not os.path.exists(FFMPEG):
    # Yedek: klasör listesinden bul
    FFMPEG = "ffmpeg"
    if os.path.exists(ANA):
        for _d in os.listdir(ANA):
            _p = os.path.join(ANA, _d, "bin", "ffmpeg.exe")
            if os.path.exists(_p):
                FFMPEG = _p; break
YON_DOSYA  = os.path.join(YON_KL, "yönetici.txt")
SIFRE_DOSYA= os.path.join(YON_KL, "şifre.txt")
ESKI_DOSYA = os.path.join(YON_KL, "eski_sifreler.txt")
TEST_DOSYA = os.path.join(YON_KL, "test.txt")
AYAR_DOSYA = os.path.join(ANA, "ayarlar.json")

MP3_AN     = os.path.join(SESLER, "an.mp3")
MP3_SISTEM = os.path.join(SESLER, "SISTEM.mp3")
MP3_UYARI  = os.path.join(SESLER, "uyarı .mp3")

DEFAULT_SIFRE = "tevrat55"

for _d in [ANA, YON_KL, SESLER, IZLENEN, YON_RESIM]:
    os.makedirs(_d, exist_ok=True)

for _f, _i in [
    (SIFRE_DOSYA,  DEFAULT_SIFRE),
    (ESKI_DOSYA,   ""),
    (TEST_DOSYA,   "güvenlik testi"),
    (YON_DOSYA,    "=== YÖNETİCİ LİSTESİ ===\n"),
]:
    if not os.path.exists(_f):
        with open(_f, "w", encoding="utf-8") as f: f.write(_i)


#  TEMALAR ============
TEMA_RENK = {
    "Koyu":       ("#0a0a0f", "#0d0d14", "#00d4ff"),
    "Acik":       ("#f0f0f5", "#e8e8f0", "#0055aa"),
    "Yesil":      ("#0a0f0a", "#0d140d", "#00ff88"),
    "Sari":       ("#0f0f00", "#141400", "#ffdd00"),
    "Kirmizi":    ("#0f0a0a", "#140d0d", "#ff4444"),
    "Mavi":       ("#0a0a14", "#0d0d1e", "#4488ff"),
    "Acik Mavi":  ("#eef2ff", "#e0e8ff", "#0044cc"),
    "Koyu Mavi":  ("#000814", "#001128", "#00aaff"),
}

_aktif_tema = "Koyu"

def ayar_yukle():
    try:
        with open(AYAR_DOSYA,"r",encoding="utf-8") as f: return json.load(f)
    except: return {"tema":"Koyu"}

def ayar_kaydet(d):
    try:
        with open(AYAR_DOSYA,"w",encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
    except: pass

#  MP3 ===========
_pg = None

def _mp3_init():
    global _pg
    try:
        import pygame
        pygame.mixer.init()
        _pg = pygame
    except: pass

def _mp3_cal(dosya):
    if _pg and os.path.exists(dosya):
        try: _pg.mixer.music.load(dosya); _pg.mixer.music.play()
        except: pass

def _mp3_durdur():
    if _pg:
        try: _pg.mixer.music.stop()
        except: pass

_mp3_init()


#  YÖNETici FONKSIYONLARI ===========
def _yon_dosyalari():
    """Hem YÖNETİCİLER hem YONETICILER klasörlerini kontrol et"""
    dosyalar = [YON_DOSYA]
    # Eski klasör (Türkçe) varsa onu da ekle
    eski = os.path.join(ANA, "YÖNETİCİLER", "yönetici.txt")
    if os.path.exists(eski) and eski != YON_DOSYA:
        dosyalar.append(eski)
    return dosyalar

def yonetici_listesi():
    liste = []
    goruldu = set()
    for dosya in _yon_dosyalari():
        try:
            with open(dosya,"r",encoding="utf-8") as f: satirlar = f.readlines()
            i = 0
            while i < len(satirlar):
                if "Ad Soyad:" in satirlar[i]:
                    ad = satirlar[i].replace("Ad Soyad:","").strip()
                    unvan = ""
                    if i+1 < len(satirlar) and "Unvan:" in satirlar[i+1]:
                        unvan = satirlar[i+1].replace("Unvan:","").strip(); i+=2
                    else: i+=1
                    key = (ad.lower(), unvan.lower())
                    if key not in goruldu:
                        goruldu.add(key)
                        liste.append({"ad":ad,"unvan":unvan})
                else: i+=1
        except: pass
    return liste

def yonetici_mi(unvan):
    for y in yonetici_listesi():
        if y["unvan"].strip().upper() == unvan.strip().upper(): return True
    return False

def sifre_oku():
    # Önce YONETICILER\şifre.txt, yoksa eski YÖNETİCİLER\şifre.txt dene
    for dosya in [SIFRE_DOSYA, os.path.join(ANA, "YÖNETİCİLER", "şifre.txt")]:
        if os.path.exists(dosya):
            try:
                with open(dosya,"r",encoding="utf-8") as f: return f.read().strip()
            except: pass
    return DEFAULT_SIFRE

def sifre_kontrol(s): return s == sifre_oku()

def sifre_degistir(eski, yeni):
    if not sifre_kontrol(eski): return False,"Eski sifre yanlis!"
    try:
        eski_liste = open(ESKI_DOSYA,"r",encoding="utf-8").read().splitlines()
    except: eski_liste=[]
    if yeni in eski_liste: return False,"Bu sifre daha once kullanildi!"
    with open(ESKI_DOSYA,"a",encoding="utf-8") as f: f.write(eski+"\n")
    with open(SIFRE_DOSYA,"w",encoding="utf-8") as f: f.write(yeni)
    return True,"Sifre degistirildi!"

def sifre_sifirla():
    try:
        with open(SIFRE_DOSYA,"w",encoding="utf-8") as f: f.write(DEFAULT_SIFRE)
        return True, f"Sifre sifirlandi: {DEFAULT_SIFRE}"
    except: return False,"Sifirlanamadi!"

def test_yazi():
    """test.txt dosyasından okur — her iki klasörü de dener"""
    for dosya in [TEST_DOSYA,
                  os.path.join(ANA, "YÖNETİCİLER", "test.txt")]:
        if os.path.exists(dosya):
            try:
                icerik = open(dosya,"r",encoding="utf-8").read().strip()
                if icerik: return icerik
            except: pass
    return "güvenlik testi"

#  DOSYA NUMARALAMA (tekrar giris -> _2, _3...) ============
def siradaki_dosya(klasor, isim, uzanti):
    hedef = os.path.join(klasor, f"{isim}{uzanti}")
    if not os.path.exists(hedef): return hedef
    n = 2
    while True:
        hedef = os.path.join(klasor, f"{isim}_{n}{uzanti}")
        if not os.path.exists(hedef): return hedef
        n += 1

#  KLAVYE İZLEME =======
class KlavyeIzleyici:
    
    def __init__(self, dosya_yolu):
        self._dosya   = dosya_yolu
        self._aktif   = True
        self._satir_n = 0   # mevcut satırdaki karakter sayısı
        self._hook    = None
        self._hfunc   = None
        self._u32     = ctypes.windll.user32
        self._lock    = threading.Lock()
        # Dosyayı oluştur
        try:
            os.makedirs(os.path.dirname(self._dosya), exist_ok=True)
            if not os.path.exists(self._dosya):
                open(self._dosya, "w", encoding="utf-8").close()
        except: pass
        threading.Thread(target=self._baslat, daemon=True).start()
        atexit.register(self._yeni_satir)

    def _yaz(self, kar):
        
        try:
            with self._lock:
                with open(self._dosya, "a", encoding="utf-8") as f:
                    if self._satir_n >= 50:
                        # 50 karakter doldu — yeni satır
                        f.write("\n")
                        self._satir_n = 0
                    if self._satir_n == 0:
                        # Satır başında virgül yok
                        f.write(kar)
                    else:
                        f.write("," + kar)
                    self._satir_n += len(kar) + 1  # karakter + virgül
        except: pass

    def _yeni_satir(self):
        
        try:
            with self._lock:
                with open(self._dosya, "a", encoding="utf-8") as f:
                    f.write("\n")
                self._satir_n = 0
        except: pass

    def _baslat(self):
        WH_KEYBOARD_LL = 13
        WM_KEYDOWN     = 0x0100

        VK_ISIM = {
            0x20: "BOSLUK",
            0x0D: "ENTER",
            0x08: "SIL",
            0x09: "TAB",
            0x1B: "ESC",
            0x2E: "DELETE",
            0x25: "SOL",    0x26: "YUKARI",
            0x27: "SAG",    0x28: "ASAGI",
            0x70: "F1",  0x71: "F2",  0x72: "F3",  0x73: "F4",
            0x74: "F5",  0x75: "F6",  0x76: "F7",  0x77: "F8",
            0x78: "F9",  0x79: "F10", 0x7A: "F11", 0x7B: "F12",
            0xBE: ".",   0xBC: ",",   0xBA: ";",
        }

        HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                       ctypes.POINTER(ctypes.c_void_p))

        def hook(nCode, wParam, lParam):
            if nCode >= 0 and wParam == WM_KEYDOWN:
                try:
                    vk    = ctypes.cast(lParam, ctypes.POINTER(ctypes.c_ulong))[0]
                    shift = bool(self._u32.GetAsyncKeyState(0x10) & 0x8000)
                    caps  = bool(self._u32.GetKeyState(0x14) & 0x0001)

                    if 0x41 <= vk <= 0x5A:
                        buyuk = shift ^ caps
                        kar = chr(vk) if buyuk else chr(vk).lower()
                    elif 0x30 <= vk <= 0x39:
                        kar = chr(vk)
                    elif vk in VK_ISIM:
                        kar = VK_ISIM[vk]
                        if kar == "ENTER":
                            self._yaz("ENTER")
                            self._yeni_satir()
                            return self._u32.CallNextHookEx(None, nCode, wParam, lParam)
                    else:
                        kar = None

                    if kar:
                        self._yaz(kar)
                except: pass
            return self._u32.CallNextHookEx(None, nCode, wParam, lParam)

        self._hfunc = HOOKPROC(hook)
        self._hook  = self._u32.SetWindowsHookExW(WH_KEYBOARD_LL, self._hfunc, None, 0)

        msg = ctypes.wintypes.MSG()
        while self._aktif:
            try:
                if self._u32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):
                    self._u32.TranslateMessage(ctypes.byref(msg))
                    self._u32.DispatchMessageW(ctypes.byref(msg))
            except: pass
            time.sleep(0.003)

    def durdur(self):
        self._aktif = False
        self._yeni_satir()
        try:
            if self._hook: self._u32.UnhookWindowsHookEx(self._hook)
        except: pass

#  KAYIT YÖNTİCİSİ=========
class KayitYoneticisi:
    def __init__(self, kullanici_adi):
        self.adi  = kullanici_adi
        klasor    = os.path.join(IZLENEN, kullanici_adi)
        os.makedirs(klasor,exist_ok=True)
        ekran_d   = siradaki_dosya(klasor,f"{kullanici_adi}_ekran_kayit",".mp4")
        kamera_d  = siradaki_dosya(klasor,f"{kullanici_adi}_kamera_kayit",".mp4")
        klavye_d  = siradaki_dosya(klasor,f"{kullanici_adi}_klavye",".txt")
        self._aktif       = True
        self._ekran_proc  = None
        self._kamera_proc = None
        self._kamera_cap  = None
        self._klavye      = None
        self._ekran_baslat(ekran_d)
        threading.Thread(target=self._kamera_baslat,args=(kamera_d,),daemon=True).start()
        self._klavye = KlavyeIzleyici(klavye_d)
        atexit.register(self.durdur)

    def _ekran_baslat(self, dosya):
        """
        Ekran kaydı — sesli, Windows Media Player / VLC ile açılabilen format.
        gdigrab (ekran) + dshow (mikrofon) → mp4 H264+AAC
        """
        try:
            
            mikrofon = self._mikrofon_bul()

            if mikrofon:
                cmd = [
                    FFMPEG, "-y",
                    
                    "-f", "gdigrab", "-framerate", "15",
                    "-draw_mouse", "1", "-i", "desktop",
                    
                    "-f", "dshow", "-i", f"audio={mikrofon}",
                    
                    "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "28",
                    "-pix_fmt", "yuv420p",   #olmadan bazı oynatıcılar açamaz
                    
                    "-c:a", "aac", "-b:a", "128k",
                    #(oynatılabilirlik)
                    "-movflags", "+faststart",
                    dosya
                ]
            else:
                cmd = [
                    FFMPEG, "-y",
                    "-f", "gdigrab", "-framerate", "15",
                    "-draw_mouse", "1", "-i", "desktop",
                    "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "28",
                    "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart",
                    dosya
                ]

            self._ekran_proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        except:
            pass

    def _mikrofon_bul(self):
        """DirectShow ile kullanılabilir mikrofon adını bul"""
        try:
            r = subprocess.run(
                [FFMPEG, "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
                capture_output=True, text=True,
                encoding="utf-8", errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5
            )
            cikti = r.stderr
            satirlar = cikti.split("\n")
            for i, s in enumerate(satirlar):
                if "audio" in s.lower() and i + 1 < len(satirlar):
                    
                    import re
                    m = re.search(r'"([^"]+)"', satirlar[i+1])
                    if m: return m.group(1)
            
            for s in satirlar:
                if "microphone" in s.lower() or "mikrofon" in s.lower():
                    import re
                    m = re.search(r'"([^"]+)"', s)
                    if m: return m.group(1)
        except:
            pass
        return None

    def _kamera_baslat(self,dosya):
        try:
            cap=cv2.VideoCapture(0,cv2.CAP_DSHOW)
            if not cap.isOpened(): cap=cv2.VideoCapture(1,cv2.CAP_DSHOW)
            if not cap.isOpened(): return
            self._kamera_cap=cap
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
            #hepsinde açılır
            cmd=[FFMPEG,"-y",
                 "-f","rawvideo","-vcodec","rawvideo",
                 "-s","640x480","-pix_fmt","bgr24","-r","10","-i","pipe:0",
                 "-c:v","libx264","-preset","veryfast",
                 "-crf","28",
                 "-pix_fmt","yuv420p",     
                 "-movflags","+faststart",
                 dosya]
            proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW)
            self._kamera_proc=proc
            while self._aktif:
                ret,frame=cap.read()
                if not ret: time.sleep(0.05); continue
                try: proc.stdin.write(frame.tobytes())
                except: break
                time.sleep(0.1)
        except: pass
        finally:
            try:
                if self._kamera_cap: self._kamera_cap.release()
                if self._kamera_proc and self._kamera_proc.stdin:
                    self._kamera_proc.stdin.close()
            except: pass

    def durdur(self):
        self._aktif=False
        if self._klavye:
            try: self._klavye.durdur()
            except: pass
        for p in [self._ekran_proc,self._kamera_proc]:
            if p:
                try: p.stdin.close(); p.wait(timeout=3)
                except:
                    try: p.kill()
                    except: pass


_aktif_kayit: KayitYoneticisi = None


#  KAMERA - LANDMARK ÇİZİMİ=======
def _casc(n):
    p=os.path.join(os.path.dirname(cv2.__file__),"data",n)
    c=cv2.CascadeClassifier(p if os.path.exists(p) else n)
    return c if not c.empty() else None

CASCADE = _casc("haarcascade_frontalface_default.xml")
EYE_C   = _casc("haarcascade_eye.xml")

def landmark_ciz(frame):
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    faces=[]
    if CASCADE:
        try:
            d=CASCADE.detectMultiScale(gray,1.1,4,minSize=(50,50))
            if isinstance(d,np.ndarray): faces=list(d)
        except: pass
    out=frame.copy()
    for (x,y,w,h) in faces:
        u=min(w,h)//5
        for (cx,cy,sx,sy) in [(x,y,1,1),(x+w,y,-1,1),(x,y+h,1,-1),(x+w,y+h,-1,-1)]:
            cv2.line(out,(cx,cy),(cx+sx*u,cy),(0,220,120),3)
            cv2.line(out,(cx,cy),(cx,cy+sy*u),(0,220,120),3)
            cv2.circle(out,(cx,cy),4,(0,220,120),-1)
        roi=gray[y:y+h,x:x+w]
        if EYE_C and w>=60:
            try:
                gz=EYE_C.detectMultiScale(roi,1.1,3,minSize=(w//7,h//8))
                for (ex,ey,ew,eh) in gz[:2]:
                    gcx,gcy=x+ex+ew//2,y+ey+eh//2
                    cv2.ellipse(out,(gcx,gcy),(ew//3,eh//3),0,0,360,(0,220,120),2)
                    cv2.circle(out,(gcx,gcy),3,(255,255,255),-1)
            except: pass
    return out, faces

#  EK DOĞRULAMA ========
class EkDogrulamaEkrani(ctk.CTkToplevel):
    """
    Tam ekran ek dogrulama - test.txt'den okur, yazmayi bekler.
    callback: basarili olunca cagrilan fonksiyon
    """
    def __init__(self, parent=None, callback=None):
        super().__init__(parent)
        self.callback = callback

        # Tam ekran
        self.overrideredirect(True)
        W = self.winfo_screenwidth()
        H = self.winfo_screenheight()
        self.geometry(f"{W}x{H}+0+0")
        self.configure(fg_color="#000000")
        self.attributes("-topmost",True)
        self.lift(); self.focus_force()
        self.W, self.H = W, H

        
        self.canvas = tk.Canvas(self,width=W,height=H,
                                bg="#000000",highlightthickness=0)
        self.canvas.pack()
        for i in range(0,W,60):
            self.canvas.create_line(i,0,i,H,fill="#0a0a0a")
        for i in range(0,H,60):
            self.canvas.create_line(0,i,W,i,fill="#0a0a0a")

        
        mx = W//2 - 300
        my = H//2 - 220
        self.cerceve = ctk.CTkFrame(self,width=600,height=440,
                                     fg_color="#0d0d14",corner_radius=15,
                                     border_width=2,border_color="#ffaa00")
        self.cerceve.place(x=mx,y=my)

        
        ctk.CTkLabel(self.cerceve,text="EK DOGRULAMA",
                     font=ctk.CTkFont("Consolas",26,"bold"),
                     text_color="#ffaa00").place(x=120,y=25)

        ctk.CTkLabel(self.cerceve,
                     text="Asagidaki yazi ile ayni sekilde yazin:",
                     font=ctk.CTkFont("Consolas",14),
                     text_color="#888899").place(x=80,y=90)

        # Test yazısı
        self._tz = test_yazi()
        self._tb = ctk.CTkTextbox(self.cerceve,width=440,height=80,
                                   font=ctk.CTkFont("Consolas",15,"bold"),
                                   fg_color="#1a1a2e",
                                   border_color="#ffaa00",border_width=2)
        self._tb.place(x=80,y=120)
        self._tb.insert("0.0",self._tz)
        self._tb.configure(state="disabled")

        ctk.CTkLabel(self.cerceve,text="Cevabin:",
                     font=ctk.CTkFont("Consolas",14),
                     text_color="#888899").place(x=80,y=220)

        self._entry = ctk.CTkEntry(self.cerceve,width=440,height=42,
                                    font=ctk.CTkFont("Consolas",15),
                                    fg_color="#1a1a2e",border_color="#2a2a3e")
        self._entry.place(x=80,y=250)
        self._entry.focus_set()

        self._dlbl = ctk.CTkLabel(self.cerceve,text="",
                                   font=ctk.CTkFont("Consolas",13))
        self._dlbl.place(x=80,y=302)

        # Butonlar
        ctk.CTkButton(self.cerceve,text="ONAYLA",width=160,height=42,
                      font=ctk.CTkFont("Consolas",14,"bold"),
                      fg_color="#ffaa00",hover_color="#ffcc00",
                      text_color="#000000",
                      command=self._onayla).place(x=120,y=360)

        ctk.CTkButton(self.cerceve,text="İPTAL",width=140,height=42,
                      font=ctk.CTkFont("Consolas",14,"bold"),
                      fg_color="#1a0a0a",hover_color="#ff4444",
                      command=self._iptal).place(x=310,y=360)

        self.bind("<Return>",lambda e: self._onayla())

        # Saat gostergesi
        self._saat_guncelle()

    def _saat_guncelle(self):
        if not self.winfo_exists(): return
        self.canvas.delete("saat")
        self.canvas.create_text(30,self.H-28,
            text=datetime.now().strftime('%d.%m.%Y  %H:%M:%S'),
            fill="#333366",font=("Consolas",10),anchor="w",tags="saat")
        self.after(1000,self._saat_guncelle)

    def _onayla(self):
        girilen = self._entry.get().strip()
        beklenen = self._tz.strip()
        if girilen == beklenen:
            self._dlbl.configure(text="Doğrulama başarılı!",text_color="#00ff88")
            self.update()
            time.sleep(0.4)
            if self.callback: self.callback()
            self.destroy()
        else:
            self._dlbl.configure(
                text=f"Yanlis! Beklenen: '{beklenen[:20]}...' Girilen: '{girilen[:20]}'",
                text_color="#ff5555")
            _mp3_cal(MP3_UYARI)

    def _iptal(self):
        self.destroy()


#  DOĞRULAMA EKRANI=====
class DogrulamaEkrani(ctk.CTkToplevel):
    def __init__(self, master=None, callback_kapat=None):
        super().__init__(master)
        self._u32           = ctypes.windll.user32
        self._callback_kapat= callback_kapat

        self.overrideredirect(True)
        W=self.winfo_screenwidth(); H=self.winfo_screenheight()
        self.geometry(f"{W}x{H}+0+0")
        self.configure(fg_color="#000000")
        self.attributes("-topmost",True)
        self.lift(); self.focus_force()

        self._aktif  = True
        self._hook   = None
        self._hfunc  = None
        self._durum  = "bekleniyor"
        self._t0     = time.time()
        self._onay_t = None
        self.W, self.H = W, H

        self._klavye_hook_kur()
        self._usb_kilitle()

        self.canvas=tk.Canvas(self,width=W,height=H,
                               bg="#000000",highlightthickness=0)
        self.canvas.pack()

        self._form_kur()
        self._ciz()
        self.protocol("WM_DELETE_WINDOW",lambda: None)

    #sadece Win/Alt+F4/ESC engelle ───────────
    def _klavye_hook_kur(self):
        WH_KEYBOARD_LL=13; WM_KEYDOWN=0x0100; WM_SYSKEYDOWN=0x0104
        ENGEL={0x5B,0x5C,0x5D}  # Win L, Win R, App

        HOOKPROC=ctypes.WINFUNCTYPE(ctypes.c_int,ctypes.c_int,ctypes.c_int,
                                     ctypes.POINTER(ctypes.c_void_p))
        def hook(nCode,wParam,lParam):
            if nCode>=0 and wParam in (WM_KEYDOWN,WM_SYSKEYDOWN):
                try:
                    vk=ctypes.cast(lParam,ctypes.POINTER(ctypes.c_ulong))[0]
                    if vk in ENGEL: return 1
                   
                    if vk==0x73 and self._u32.GetAsyncKeyState(0x12)&0x8000: return 1
                    
                    if vk==0x1B: return 1
                    
                    if vk==0x2E:
                        if (self._u32.GetAsyncKeyState(0x11)&0x8000 and
                            self._u32.GetAsyncKeyState(0x12)&0x8000): return 1
                except: pass
            return self._u32.CallNextHookEx(None,nCode,wParam,lParam)

        self._hfunc=HOOKPROC(hook)
        self._hook=self._u32.SetWindowsHookExW(WH_KEYBOARD_LL,self._hfunc,None,0)

        def _msg():
            msg=ctypes.wintypes.MSG()
            while self._aktif:
                try:
                    if self._u32.PeekMessageW(ctypes.byref(msg),None,0,0,1):
                        self._u32.TranslateMessage(ctypes.byref(msg))
                        self._u32.DispatchMessageW(ctypes.byref(msg))
                except: pass
                time.sleep(0.005)
        threading.Thread(target=_msg,daemon=True).start()

    def _usb_kilitle(self):
        try:
            subprocess.run(["reg","add",
                r"HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR",
                "/v","Start","/t","REG_DWORD","/d","4","/f"],
                capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        except: pass

    def _usb_ac(self):
        try:
            subprocess.run(["reg","add",
                r"HKLM\SYSTEM\CurrentControlSet\Services\USBSTOR",
                "/v","Start","/t","REG_DWORD","/d","3","/f"],
                capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
        except: pass

    
    def _form_kur(self):
        W,H=self.W,self.H
        gx=W//2-200; gy=H-360

        self.form_f=ctk.CTkFrame(self,width=400,height=310,
                                  fg_color="#0d0d14",corner_radius=14,
                                  border_width=2,border_color="#00d4ff")
        self.form_f.place(x=gx,y=gy)

        ctk.CTkLabel(self.form_f,text="KULLANICI GİRİŞİ",
                     font=ctk.CTkFont("Consolas",16,"bold"),
                     text_color="#00d4ff").place(x=20,y=12)

        ctk.CTkLabel(self.form_f,text="ÜNVAN:",
                     font=ctk.CTkFont("Consolas",11),
                     text_color="#888899").place(x=20,y=52)
        self._unvan=ctk.CTkEntry(self.form_f,width=360,height=34,
                                  font=ctk.CTkFont("Consolas",13),
                                  fg_color="#1a1a2e",border_color="#2a2a3e",
                                  placeholder_text="Ünvanınızı girin")
        self._unvan.place(x=20,y=74)

        ctk.CTkLabel(self.form_f,text="ŞİFRE:",
                     font=ctk.CTkFont("Consolas",11),
                     text_color="#888899").place(x=20,y=116)
        self._sifre=ctk.CTkEntry(self.form_f,width=360,height=34,
                                  font=ctk.CTkFont("Consolas",13),
                                  fg_color="#1a1a2e",border_color="#2a2a3e",
                                  show="*",placeholder_text="Şifrenizi girin")
        self._sifre.place(x=20,y=138)

        self._giris_btn=ctk.CTkButton(
            self.form_f,text="GİRİŞ YAP",width=360,height=38,
            font=ctk.CTkFont("Consolas",13,"bold"),
            fg_color="#003d5c",hover_color="#00d4ff",
            command=self._giris)
        self._giris_btn.place(x=20,y=184)

        self._durum_lbl=ctk.CTkLabel(self.form_f,text="",
                                      font=ctk.CTkFont("Consolas",11))
        self._durum_lbl.place(x=20,y=232)

        self._ek_f=ctk.CTkFrame(self.form_f,fg_color="#0d0d14",
                                 width=360,height=72)
        self._ek_f.place_forget()

        self.bind("<Return>",lambda e: self._giris())
        self._unvan.focus_set()

    # ── Giris kontrol───────────
    def _giris(self):
        unvan=self._unvan.get().strip()
        sifre=self._sifre.get().strip()
        if not unvan:
            self._durum_lbl.configure(text="Unvan girin!",text_color="#ff5555")
            return

        self._giris_btn.configure(state="disabled")
        self._durum_lbl.configure(text="Analiz ediliyor...",text_color="#ffaa00")

        
        _mp3_cal(MP3_AN)

        def _kontrol():
            time.sleep(4) 

            if yonetici_mi(unvan):
                
                _mp3_durdur()
                _mp3_cal(MP3_SISTEM)
                self.after(0,lambda: self._durum_lbl.configure(
                    text=f"Hos geldiniz, {unvan}!",text_color="#00ff88"))
                self._durum  = "onaylandi"
                self._onay_t = time.time()

            else:
                
                if not sifre:
                    _mp3_durdur()
                    self.after(0,lambda: self._durum_lbl.configure(
                        text="Sifre girin!",text_color="#ff5555"))
                    self.after(0,lambda: self._giris_btn.configure(state="normal"))
                    return

                if sifre_kontrol(sifre):
                    
                    _mp3_durdur()
                    self.after(0,lambda: self._ek_dogrulama_baslat(unvan))
                else:
                    
                    _mp3_durdur()
                    _mp3_cal(MP3_UYARI)
                    self.after(0,lambda: self._durum_lbl.configure(
                        text="Sifre yanlis! Tekrar deneyin.",text_color="#ff5555"))
                    self.after(0,lambda: self._giris_btn.configure(state="normal"))

        threading.Thread(target=_kontrol,daemon=True).start()

    def _ek_dogrulama_baslat(self, unvan):
        """Ek dogrulama ekranini ac"""
        self._ek_unvan = unvan
        
        def _ek_basarili():
            _mp3_durdur()
            _mp3_cal(MP3_SISTEM)
            self._durum_lbl.configure(
                text=f"{unvan} hos geldiniz! (IZLENIYOR)",
                text_color="#00ff88")
            
            threading.Thread(
                target=self._kayit_baslat,
                args=(unvan,),daemon=True).start()
            self._durum  = "onaylandi"
            self._onay_t = time.time()

        EkDogrulamaEkrani(self, callback=_ek_basarili)
        self._durum_lbl.configure(
            text="Ek dogrulama bekleniyor...",text_color="#ffaa00")

    def _kayit_baslat(self, unvan):
        global _aktif_kayit
        _aktif_kayit = KayitYoneticisi(unvan)

    # ── Animasyon─────
    def _ciz(self):
        if not self._aktif: return
        c=self.canvas; W,H=self.W,self.H
        t=time.time(); gec=t-self._t0
        c.delete("all")

        for i in range(0,W,60): c.create_line(i,0,i,H,fill="#0a0a0a")
        for i in range(0,H,60): c.create_line(0,i,W,i,fill="#0a0a0a")

        if self._durum=="bekleniyor":
            renk="#00ccff"; baslik="GÜVENLİ GİRİŞ SİSTEMİ"; alt="Lutfen bilgilerinizi girin"
            adimlar=[(True,False,"[ 1 ]  Kullanici Girisi"),
                     (False,False,"[ 2 ]  Kimlik Dogrulama"),
                     (False,False,"[ 3 ]  Yetki Kontrolu"),
                     (False,False,"[ 4 ]  Erisim Saglanıyor")]
            ilerleme=0
        elif self._durum=="onaylandi":
            renk="#00ff88"; baslik="GİRİŞ BAŞARILI"; alt="Yonlendiriliyorsunuz..."
            adimlar=[(True,True,"[ 1 ]  Kullanici Girisi"),
                     (True,True,"[ 2 ]  Kimlik Dogrulama"),
                     (True,True,"[ 3 ]  Yetki Kontrolu"),
                     (True,False,"[ 4 ]  Erisim Saglaniyor...")]
            ilerleme=85
            if t-self._onay_t>2.5: self._kapat(); return
        else:
            renk="#555"; baslik=""; alt=""; adimlar=[]; ilerleme=0

        c.create_rectangle(100,50,W-100,H-50,fill="#0a0a0a",outline=renk,width=3)
        c.create_text(W//2,120,text=baslik,fill=renk,font=("Consolas",32,"bold"))
        c.create_text(W//2,162,text=alt,fill="#444466",font=("Consolas",14))
        c.create_line(200,190,W-200,190,fill="#1a1a2e",width=2)

        ay=245; blink=int(t*2)%2==0
        for (aktif,tamam,metin) in adimlar:
            if tamam: rc,sym="#00dd66","✓"
            elif aktif: rc,sym=renk,("►" if blink else " ")
            else: rc,sym="#2a2a3a","○"
            c.create_text(250,ay,text=f"{sym}  {metin}",fill=rc,
                          font=("Consolas",16),anchor="w")
            ay+=44

        bx1,by1,bx2,by2=250,420,W-250,438
        c.create_rectangle(bx1,by1,bx2,by2,fill="#111122",outline="#222233",width=2)
        if ilerleme>0:
            d=bx1+int((bx2-bx1)*ilerleme/100)
            c.create_rectangle(bx1,by1,d,by2,fill=renk,outline="")
        c.create_text(bx2+28,by2-4,text=f"%{ilerleme}",fill=renk,font=("Consolas",12))
        c.create_text(30,H-28,text=datetime.now().strftime('%d.%m.%Y  %H:%M:%S'),
                      fill="#333366",font=("Consolas",10),anchor="w")
        self.after(30,self._ciz)

    def _kapat(self):
        self._aktif=False
        try:
            if self._hook: self._u32.UnhookWindowsHookEx(self._hook)
        except: pass
        self._usb_ac()
        if self._callback_kapat: self._callback_kapat()
        self.destroy()


#  KLASÖR GÖRÜNÜMÜ=======
class KlasorPaneli(ctk.CTkFrame):
    """
    Ana GUI icinde gosterilen klasor tarayici.
    Sag tik: Sifrele / Sifre Coz
    """
    def __init__(self, master, yol=ANA, **kw):
        super().__init__(master, fg_color="#0a0a0f", **kw)
        self.yol = yol
        self._resimler = {}

        # Ust bar
        ust=ctk.CTkFrame(self,fg_color="#0d0d14")
        ust.pack(fill="x",padx=4,pady=4)
        self._yol_lbl=ctk.CTkLabel(ust,text="",
                                    font=ctk.CTkFont("Consolas",10),
                                    text_color="#00d4ff")
        self._yol_lbl.pack(side="left",padx=8)
        ctk.CTkButton(ust,text="Yukari",width=70,height=26,
                      font=ctk.CTkFont("Consolas",9),
                      fg_color="#111118",hover_color="#1a1a2e",
                      command=self._yukari).pack(side="right",padx=4)
        ctk.CTkButton(ust,text="Yenile",width=70,height=26,
                      font=ctk.CTkFont("Consolas",9),
                      fg_color="#111118",hover_color="#1a1a2e",
                      command=self._yenile).pack(side="right",padx=4)

        self._sf=ctk.CTkScrollableFrame(self,fg_color="#0a0a0f")
        self._sf.pack(fill="both",expand=True,padx=4,pady=4)

        self._goster(yol)

    def _goster(self,yol):
        self.yol=yol
        self._yol_lbl.configure(text=yol)
        for w in self._sf.winfo_children(): w.destroy()
        try:
            icerik=sorted(os.listdir(yol),key=lambda x:(not os.path.isdir(os.path.join(yol,x)),x.lower()))
            for isim in icerik:
                tam=os.path.join(yol,isim)
                icon="📁" if os.path.isdir(tam) else "📄"
                renk="#00d4ff" if os.path.isdir(tam) else "#aaaacc"

                sat=ctk.CTkFrame(self._sf,fg_color="#0d0d14",corner_radius=4)
                sat.pack(fill="x",padx=2,pady=1)

                lbl=ctk.CTkLabel(sat,text=f"  {icon}  {isim}",
                                  font=ctk.CTkFont("Consolas",10),
                                  text_color=renk,anchor="w")
                lbl.pack(side="left",fill="x",expand=True,padx=4,pady=3)

                
                if os.path.isdir(tam):
                    lbl.bind("<Double-Button-1>",lambda e,p=tam: self._goster(p))
                    sat.bind("<Double-Button-1>",lambda e,p=tam: self._goster(p))

                
                m=Menu(self,tearoff=0,bg="#0d0d1e",fg="white",
                       activebackground="#003d5c",font=("Consolas",10))
                if os.path.isdir(tam):
                    m.add_command(label="🔒  Şifrele (Erişim Engelle)",
                                  command=lambda p=tam: self._sifrele(p))
                    m.add_command(label="🔓  Şifre ÇÖz (Erişim Aç)",
                                  command=lambda p=tam: self._sifre_coz(p))
                    m.add_separator()
                m.add_command(label="📂  Ac",
                              command=lambda p=tam: os.startfile(p) if os.path.exists(p) else None)

                sat.bind("<Button-3>",lambda e,mn=m: mn.tk_popup(e.x_root,e.y_root))
                lbl.bind("<Button-3>",lambda e,mn=m: mn.tk_popup(e.x_root,e.y_root))

        except PermissionError:
            ctk.CTkLabel(self._sf,text="Erisim engellendi.",
                         font=ctk.CTkFont("Consolas",10),
                         text_color="#ff5555").pack(pady=10)

    def _yukari(self):
        ust=os.path.dirname(self.yol)
        if ust and ust!=self.yol: self._goster(ust)

    def _yenile(self):
        self._goster(self.yol)

    def _sifrele(self, yol):
        """icacls ile herkese erisimi engelle"""
        try:
            usr=os.environ.get("USERNAME","Everyone")
            r1=subprocess.run(
                ["icacls",yol,"/inheritance:r","/deny",f"{usr}:(OI)(CI)F"],
                capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,
                text=True)
            r2=subprocess.run(
                ["icacls",yol,"/deny","Everyone:(OI)(CI)F"],
                capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,
                text=True)
            messagebox.showinfo("Sifrele",
                f"Klasor sifrelendi!\n{os.path.basename(yol)}\n\n"
                "Windows 'Erisim engellendi' hatasi verecek.")
            self._yenile()
        except Exception as e:
            messagebox.showerror("Hata",str(e))

    def _sifre_coz(self, yol):
        """Sifre kontrolu yap, sonra erisim kaldir"""
        gir=simpledialog.askstring("Sifre Coz","Sisteme sifrenizi girin:",show="*")
        if not gir: return
        if not sifre_kontrol(gir):
            messagebox.showerror("Hata","Yanlis sifre!")
            return
        try:
            usr=os.environ.get("USERNAME","Everyone")
            subprocess.run(["icacls",yol,"/remove:d",usr],
                           capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["icacls",yol,"/remove:d","Everyone"],
                           capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["icacls",yol,"/inheritance:e"],
                           capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
            messagebox.showinfo("Tamam",
                f"Erisim engeli kaldirildi!\n{os.path.basename(yol)}")
            self._yenile()
        except Exception as e:
            messagebox.showerror("Hata",str(e))


#  ANA UYGULAMA======
class AnaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GÜVENLİK SİSTEMİ v14.1")
        sw,sh=self.winfo_screenwidth(),self.winfo_screenheight()
        self.geometry(f"1280x740+{(sw-1280)//2}+{(sh-740)//2}")
        self.configure(fg_color="#0a0a0f")
        self.resizable(True,True)

        self._yon_resimler = []
        self._ekle_aktif  = False
        self._son_frame   = None
        self._ayarlar     = ayar_yukle()
        self._klasor_panel= None

        self._ui_kur()
        self._ana_sayfa()

    # ────────────────────────────────────────────────────────
    def _ui_kur(self):
        
        self.sol=ctk.CTkFrame(self,width=280,corner_radius=0,fg_color="#0d0d14")
        self.sol.pack(side="left",fill="y")
        self.sol.pack_propagate(False)

        
        logo_row=ctk.CTkFrame(self.sol,fg_color="#0d0d14")
        logo_row.pack(fill="x",padx=14,pady=(55,4))

        ctk.CTkLabel(logo_row,text="GUVENLIK\nSISTEMI",
                     font=ctk.CTkFont("Consolas",20,"bold"),
                     text_color="#00d4ff",justify="left").pack(side="left")

        self._amenu_btn=ctk.CTkButton(logo_row,text="Ayarlar",
                                       width=90,height=30,
                                       font=ctk.CTkFont("Consolas",10),
                                       fg_color="#1a1a2e",hover_color="#2a2a4e",
                                       command=self._amenu_goster)
        self._amenu_btn.pack(side="right",padx=(10,0))

        
        self._amenu=Menu(self,tearoff=0,bg="#0d0d1e",fg="white",
                         activebackground="#003d5c",font=("Consolas",10))
        tema_m=Menu(self._amenu,tearoff=0,bg="#0d0d1e",fg="white",
                    activebackground="#003d5c",font=("Consolas",10))
        for t in TEMA_RENK:
            tema_m.add_command(label=t,command=lambda x=t: self._tema_sec(x))
        self._amenu.add_cascade(label="Tema",menu=tema_m)
        self._amenu.add_separator()
        self._amenu.add_command(label="Ana Klasor",command=self._klasor_ac)

        ctk.CTkFrame(self.sol,fg_color="#1a1a2e",height=1).pack(fill="x",padx=14,pady=6)

        bkw=dict(width=250,height=44,corner_radius=8,
                 font=ctk.CTkFont("Consolas",12,"bold"),anchor="w")

        ctk.CTkButton(self.sol,text="  DOğRULAMA",
                      fg_color="#2a1a00",hover_color="#ffaa00",
                      command=self._dogrulama_ac,**bkw).pack(padx=14,pady=4)

        ctk.CTkButton(self.sol,text="  YÖNETİCİ EKLE",
                      fg_color="#003d5c",hover_color="#00d4ff",
                      command=self._yon_ekle_goster,**bkw).pack(padx=14,pady=4)

        ctk.CTkFrame(self.sol,fg_color="#1a1a2e",height=1).pack(fill="x",padx=14,pady=6)

        
        ctk.CTkLabel(self.sol,text="ŞİFRE İŞLEMLERİ",
                     font=ctk.CTkFont("Consolas",11,"bold"),
                     text_color="#ffaa00").pack(anchor="w",padx=14,pady=(4,2))

        sf=ctk.CTkFrame(self.sol,fg_color="#111118",corner_radius=8)
        sf.pack(fill="x",padx=10,pady=4)

        for lbl,attr in [("Eski Şifre","_se_eski"),
                          ("Yeni Şifre","_se_yeni"),
                          ("Tekrar","_se_yeni2")]:
            ctk.CTkLabel(sf,text=lbl+":",
                         font=ctk.CTkFont("Consolas",9),
                         text_color="#888899").pack(anchor="w",padx=10,pady=(4,0))
            e=ctk.CTkEntry(sf,width=230,height=28,show="*",
                            fg_color="#1a1a2e",border_color="#2a2a3e",
                            font=ctk.CTkFont("Consolas",10))
            e.pack(padx=10)
            setattr(self,attr,e)

        self._sifre_dlbl=ctk.CTkLabel(sf,text="",
                                       font=ctk.CTkFont("Consolas",9))
        self._sifre_dlbl.pack(pady=2)

        bf2=ctk.CTkFrame(sf,fg_color="#111118")
        bf2.pack(pady=6)
        ctk.CTkButton(bf2,text="DEĞİŞTİR",width=100,height=28,
                      font=ctk.CTkFont("Consolas",9),
                      fg_color="#003d5c",hover_color="#00d4ff",
                      command=self._sifre_degistir).pack(side="left",padx=3)
        ctk.CTkButton(bf2,text="SIFIRLA",width=100,height=28,
                      font=ctk.CTkFont("Consolas",9),
                      fg_color="#1a0a0a",hover_color="#ff4444",
                      command=self._sifre_sifirla).pack(side="left",padx=3)

        ctk.CTkFrame(self.sol,fg_color="#1a1a2e",height=1).pack(fill="x",padx=14,pady=6)

        
        ctk.CTkLabel(self.sol,text="YÖNETİCİLER",
                     font=ctk.CTkFont("Consolas",11,"bold"),
                     text_color="#ffaa00").pack(anchor="w",padx=14)
        self._yon_sf=ctk.CTkScrollableFrame(self.sol,fg_color="#0d0d14")
        self._yon_sf.pack(fill="both",expand=True,padx=8,pady=4)
        self._yon_listele()

        
        self.sag=ctk.CTkFrame(self,fg_color="#0a0a0f")
        self.sag.pack(side="left",fill="both",expand=True,padx=4)

    
    def _amenu_goster(self):
        x=self._amenu_btn.winfo_rootx()
        y=self._amenu_btn.winfo_rooty()+self._amenu_btn.winfo_height()
        self._amenu.tk_popup(x,y)

    def _tema_sec(self, tema):
        global _aktif_tema
        _aktif_tema = tema
        self._ayarlar["tema"]=tema
        ayar_kaydet(self._ayarlar)
        bg,mg,ac=TEMA_RENK[tema]
        
        if "Acik" in tema:
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("dark")
        self.configure(fg_color=bg)
        self.sol.configure(fg_color=mg)

    def _klasor_ac(self):
        self._anim_aktif = False
        """Ana klasoru GUI icinde goster"""
        for w in self.sag.winfo_children(): w.destroy()
        self._klasor_panel=KlasorPaneli(self.sag,yol=ANA)
        self._klasor_panel.pack(fill="both",expand=True)

    
    def _sifre_degistir(self):
        e=self._se_eski.get(); y=self._se_yeni.get(); y2=self._se_yeni2.get()
        if y!=y2:
            self._sifre_dlbl.configure(text="Şifreler eşleşmiyor!",text_color="#ff5555"); return
        ok,m=sifre_degistir(e,y)
        renk="#00ff88" if ok else "#ff5555"
        self._sifre_dlbl.configure(text=("OK: " if ok else "HATA: ")+m,text_color=renk)
        if ok:
            for w in [self._se_eski,self._se_yeni,self._se_yeni2]: w.delete(0,"end")

    def _sifre_sifirla(self):
        
        dlg = ctk.CTkToplevel(self)
        dlg.title("Şifre Sıfırla")
        dlg.geometry("340x180")
        dlg.resizable(False, False)
        dlg.configure(fg_color="#0a0a14")
        dlg.grab_set()
        dlg.lift()

        ctk.CTkLabel(dlg, text="Mevcut şifreyi girin:",
                     font=ctk.CTkFont("Consolas", 12),
                     text_color="#ffaa00").pack(pady=(18, 6))

        e = ctk.CTkEntry(dlg, show="*", width=220, height=34,
                         fg_color="#111120", border_color="#333355",
                         font=ctk.CTkFont("Consolas", 13))
        e.pack(pady=4)
        e.focus()

        msg_lbl = ctk.CTkLabel(dlg, text="", font=ctk.CTkFont("Consolas", 10))
        msg_lbl.pack(pady=2)

        def onayla():
            girilen = e.get().strip()
            mevcut  = sifre_oku()
            if girilen != mevcut:
                msg_lbl.configure(text="Mevcut şifre yanlış!", text_color="#ff5555")
                return
            dlg.destroy()
            if messagebox.askyesno("Sıfırla", f"Şifre '{DEFAULT_SIFRE}' olarak sıfırlansın mı?"):
                ok, m = sifre_sifirla()
                self._sifre_dlbl.configure(
                    text=m, text_color="#00ff88" if ok else "#ff5555")

        ctk.CTkButton(dlg, text="Devam", command=onayla,
                      fg_color="#1a2a0a", hover_color="#ffaa00",
                      font=ctk.CTkFont("Consolas", 12), height=32).pack(pady=8)
        e.bind("<Return>", lambda e: onayla())

    
    def _yon_listele(self):
        for w in self._yon_sf.winfo_children(): w.destroy()
        self._yon_resimler=[]
        liste=yonetici_listesi()
        if not liste:
            ctk.CTkLabel(self._yon_sf,text="Yönetici yok.",
                         text_color="#333344",
                         font=ctk.CTkFont("Consolas",10)).pack(pady=10)
            return
        for y in liste: self._yon_kart(y)

    def _yon_kart(self,y):
        kart=ctk.CTkFrame(self._yon_sf,fg_color="#111118",
                          corner_radius=6,height=58)
        kart.pack(fill="x",padx=2,pady=2)
        kart.pack_propagate(False)

        resim_ok=False
        _tum_resimler = [(YON_RESIM,f) for f in os.listdir(YON_RESIM) if os.path.exists(YON_RESIM)] + [(os.path.join(ANA,'YÖNETİCİLER','resimler'),f) for _rp in [os.path.join(ANA,'YÖNETİCİLER','resimler')] if os.path.exists(_rp) for f in os.listdir(_rp)]
        for _rklasör, f in _tum_resimler:
            if y["ad"] in f and y["unvan"] in f and f.endswith(".jpg"):
                try:
                    img=Image.open(os.path.join(_rklasör,f)).resize((48,48))
                    imgtk=ImageTk.PhotoImage(img)
                    self._yon_resimler.append(imgtk)
                    lb=ctk.CTkLabel(kart,image=imgtk,text="",width=48,height=48)
                    lb.imgtk=imgtk; lb.place(x=5,y=5)
                    resim_ok=True
                except: pass
                break
        if not resim_ok:
            ctk.CTkLabel(kart,text="👤",font=ctk.CTkFont("Consolas",24)).place(x=10,y=12)

        ctk.CTkLabel(kart,text=y["ad"],
                     font=ctk.CTkFont("Consolas",11,"bold"),
                     text_color="#e0e0f0",fg_color="#111118").place(x=62,y=8)
        ctk.CTkLabel(kart,text=y["unvan"],
                     font=ctk.CTkFont("Consolas",9),
                     text_color="#888899",fg_color="#111118").place(x=62,y=30)

        m=Menu(self,tearoff=0,bg="#0d0d1e",fg="white",
               activebackground="#333366",font=("Consolas",10))
        m.add_command(label="Kaldir",command=lambda: self._yon_kaldir(y))
        kart.bind("<Button-3>",lambda e,mn=m: mn.tk_popup(e.x_root,e.y_root))

    def _yon_kaldir(self,y):
        s=simpledialog.askstring("Onay","Sisteme sifrenizi girin:",show="*")
        if s and sifre_kontrol(s):
            messagebox.showinfo("Bilgi","Yonetici.txt dosyasindan manuel siliniz.")
        elif s:
            messagebox.showerror("Hata","Yanlis sifre!")

    
    def _ana_sayfa(self):
        for w in self.sag.winfo_children(): w.destroy()
        self._anim_aktif = True

        import random, math

        try:
            import psutil
            _psutil_ok = True
        except:
            _psutil_ok = False

        cv = tk.Canvas(self.sag, bg="#07070e", highlightthickness=0)
        cv.pack(fill="both", expand=True)

        
        NOKTA = 30
        pts = [{"x": random.random(), "y": random.random(),
                "vx": random.uniform(-0.0003, 0.0003),
                "vy": random.uniform(-0.0003, 0.0003),
                "r":  random.uniform(2, 4)} for _ in range(NOKTA)]

        
        SUTUN = 20
        rain = [{"xr": (i+0.5)/SUTUN, "y": random.random(),
                 "sp": random.uniform(0.003, 0.008),
                 "ch": [random.choice("01") for _ in range(14)]}
                for i in range(SUTUN)]

        rad_a = [0]

        GECMIS = 40
        cpu_hist = [0.0] * GECMIS
        ram_hist = [0.0] * GECMIS
        gpu_hist = [0.0] * GECMIS
        hw_sayac = [0]

        def _hw_guncelle():
            if _psutil_ok:
                try:
                    cpu_hist.append(psutil.cpu_percent(interval=None))
                    ram_hist.append(psutil.virtual_memory().percent)
                except:
                    cpu_hist.append(random.uniform(20,60))
                    ram_hist.append(random.uniform(40,75))
            else:
                cpu_hist.append(random.uniform(20,60))
                ram_hist.append(random.uniform(40,75))
            try:
                import subprocess as _sp
                r = _sp.run(["nvidia-smi","--query-gpu=utilization.gpu",
                             "--format=csv,noheader,nounits"],
                            capture_output=True, text=True,
                            encoding="utf-8", errors="ignore",
                            creationflags=0x08000000, timeout=1)
                gpu_hist.append(float(r.stdout.strip().split("\n")[0]))
            except:
                gpu_hist.append(random.uniform(5,40))
            while len(cpu_hist) > GECMIS: cpu_hist.pop(0)
            while len(ram_hist) > GECMIS: ram_hist.pop(0)
            while len(gpu_hist) > GECMIS: gpu_hist.pop(0)

        for _ in range(GECMIS):
            _hw_guncelle()

        KOD = [
            "import ctypes, os, sys, threading",
            "class GuvenlikSistemi:",
            "    def __init__(self):",
            "        self._aktif = True",
            "        self._hook  = None",
            "    def klavye_izle(self):",
            "        WH_KEYBOARD_LL = 13",
            "        HOOKPROC = ctypes.WINFUNCTYPE(...)",
            "        self._hook = SetWindowsHookExW(...)",
            "    def ekran_kaydet(self, dosya):",
            "        cap = ImageGrab.grab(bbox=...)",
            "        frame = cv2.cvtColor(...)",
            "        self._proc.stdin.write(...)",
            "    def yuz_tani(self, frame):",
            "        gray = cv2.cvtColor(frame, GRAY)",
            "        faces = CASCADE.detectMultiScale(...)",
            "        return faces",
            "    def ses_kaydet(self):",
            "        stream = pyaudio.open(...)",
            "        data = stream.read(CHUNK)",
            "import numpy as np",
            "ffmpeg = subprocess.Popen(cmd, stdin=PIPE)",
            "threading.Thread(target=self._baslat).start()",
            "atexit.register(self.durdur)",
            "if __name__ == '__main__':",
            "    app = GuvenlikSistemi()",
            "    app.mainloop()",
            "# GUVENLIK SISTEMI v14 - AKTIF",
            "# KLAVYE: IZLENIYOR",
            "# EKRAN: KAYDEDILIYOR",
        ]
        KOD_H   = 16
        kod_ofs = [0.0]

        glitch_t     = [0.0]
        glitch_aktif = [False]
        glitch_sure  = [0.0]
        glitch_tip   = [0]    # 0-5 arası tip

        t0 = [time.time()]

        def _mini_g(x0, y0, gw, gh, hist, renk, etiket):
            cv.create_rectangle(x0, y0, x0+gw, y0+gh,
                                fill="#0a0f0a", outline="#1a2a1a")
            for pct in (25, 50, 75):
                gy = y0 + gh - int(gh * pct / 100)
                cv.create_line(x0, gy, x0+gw, gy, fill="#0d1f0d")
            n = len(hist)
            if n >= 2:
                pts_g = [(x0 + int(i*gw/(n-1)),
                          y0 + gh - int(gh * min(100,max(0,v)) / 100))
                         for i,v in enumerate(hist)]
                poly = [(x0,y0+gh)] + pts_g + [(x0+gw,y0+gh)]
                r_=max(0,int(int(renk[1:3],16)*0.25))
                g_=max(0,int(int(renk[3:5],16)*0.25))
                b_=max(0,int(int(renk[5:7],16)*0.25))
                cv.create_polygon(poly, fill=f"#{r_:02x}{g_:02x}{b_:02x}", outline="")
                for i in range(len(pts_g)-1):
                    cv.create_line(pts_g[i][0],pts_g[i][1],
                                   pts_g[i+1][0],pts_g[i+1][1],
                                   fill=renk, width=2)
            cv.create_text(x0+4, y0+4, text=etiket, fill=renk,
                           font=("Consolas",8,"bold"), anchor="nw")
            cv.create_text(x0+gw-4, y0+4, text=f"{hist[-1]:.0f}%",
                           fill=renk, font=("Consolas",9,"bold"), anchor="ne")

        def _ciz():
            if not self._anim_aktif: return
            try:
                if not cv.winfo_exists(): return
            except: return

            W = cv.winfo_width()
            H = cv.winfo_height()
            if W < 20 or H < 20:
                self.sag.after(50, _ciz); return

            cv.delete("all")
            now = time.time()
            t   = now

            for gx in range(0, W, 55):
                cv.create_line(gx, 0, gx, H, fill="#0c0c18")
            for gy in range(0, H, 55):
                cv.create_line(0, gy, W, gy, fill="#0c0c18")

            kod_ofs[0] += 0.55
            toplam_h = len(KOD) * KOD_H
            if kod_ofs[0] > toplam_h: kod_ofs[0] = 0.0
            for i, satir in enumerate(KOD * 3):
                sy = int(i * KOD_H - kod_ofs[0])
                if sy < -KOD_H or sy > H + KOD_H: continue
                fade = min(1.0, min(sy+20, H-sy) / 70)
                g_v  = max(0, int(75 * fade))
                if satir.startswith("    "):
                    col = f"#00{min(255,int(g_v*1.3)):02x}55"
                elif satir.startswith("class") or satir.startswith("import"):
                    col = f"#33{min(255,int(g_v*1.2)):02x}88"
                elif satir.startswith("#"):
                    col = f"#55{min(255,int(g_v*0.8)):02x}22"
                else:
                    col = f"#00{g_v:02x}33"
                cv.create_text(10, sy, text=satir, fill=col,
                               font=("Consolas",9), anchor="nw")

            for s in rain:
                sx = int(s["xr"] * W)
                if sx < W * 0.42: continue
                s["y"] += s["sp"]
                if s["y"] > 1.1:
                    s["y"] = -0.05
                    s["ch"] = [random.choice("01") for _ in range(14)]
                for j, k in enumerate(s["ch"]):
                    fy = s["y"] - j * 0.04
                    if fy < 0 or fy > 1: continue
                    py = int(fy * H)
                    fd = max(0.0, 1.0 - j * 0.09)
                    col = ("#00ffaa" if j==0 else
                           f"#00{int(140*fd):02x}44" if j<3 else
                           f"#00{int(55*fd):02x}22")
                    cv.create_text(sx, py, text=k, fill=col,
                                   font=("Consolas",10))

            for n in pts:
                n["x"] = max(0.0,min(1.0,n["x"]+n["vx"]))
                n["y"] = max(0.0,min(1.0,n["y"]+n["vy"]))
                if n["x"] in (0.0,1.0): n["vx"]*=-1
                if n["y"] in (0.0,1.0): n["vy"]*=-1
            for i in range(len(pts)):
                for j in range(i+1, len(pts)):
                    dx=pts[i]["x"]-pts[j]["x"]; dy=pts[i]["y"]-pts[j]["y"]
                    d=math.hypot(dx,dy)
                    if d < 0.18:
                        a=int(90*(1-d/0.18))
                        cv.create_line(int(pts[i]["x"]*W),int(pts[i]["y"]*H),
                                       int(pts[j]["x"]*W),int(pts[j]["y"]*H),
                                       fill=f"#00{min(255,a*2):02x}{min(255,a*3):02x}",width=1)
            for n in pts:
                px,py=int(n["x"]*W),int(n["y"]*H)
                rc=int(n["r"]+(0.5+0.5*math.sin(t*2+n["x"]*9))*2)
                cv.create_oval(px-rc,py-rc,px+rc,py+rc,
                               fill="#00c8ff",outline="#00ffcc",width=1)

            rr=min(72,W//12)
            rx,ry=W-rr-18,rr+18
            for ring in (1.0,0.66,0.33):
                ri=int(rr*ring)
                cv.create_oval(rx-ri,ry-ri,rx+ri,ry+ri,outline="#002b1a",width=1)
            cv.create_line(rx-rr,ry,rx+rr,ry,fill="#002b1a")
            cv.create_line(rx,ry-rr,rx,ry+rr,fill="#002b1a")
            rad_a[0]=(rad_a[0]+3)%360
            ar=math.radians(rad_a[0])
            cv.create_line(rx,ry,rx+int(rr*math.cos(ar)),
                           ry+int(rr*math.sin(ar)),fill="#00ff88",width=2)
            for iz in range(1,18):
                a2=math.radians((rad_a[0]-iz*4)%360)
                g2=max(0,int(200*(1-iz/18)))
                cv.create_line(rx,ry,rx+int(rr*math.cos(a2)),
                               ry+int(rr*math.sin(a2)),
                               fill=f"#00{g2:02x}33",width=1)
            cv.create_oval(rx-3,ry-3,rx+3,ry+3,fill="#00ff88",outline="#00ffaa")
            cv.create_text(rx,ry+rr+12,text="RADAR",
                           fill="#00aa55",font=("Consolas",8,"bold"))

            hw_sayac[0]+=1
            if hw_sayac[0]%25==0: _hw_guncelle()
            GW=rr*2+4; GH=34; GAP=7
            gx0=rx-rr-2; gy0=ry+rr+26
            _mini_g(gx0,gy0,         GW,GH,cpu_hist,"#00d4ff","CPU")
            _mini_g(gx0,gy0+GH+GAP,  GW,GH,ram_hist,"#ffaa00","RAM")
            _mini_g(gx0,gy0+(GH+GAP)*2,GW,GH,gpu_hist,"#ff4488","GPU")

            
            cx  = W // 2
            LOGO = [
                r" ___  _   _  ___  _  _  _    ___ _  __",
                r"/ __|| | | || __|| \| || |  |_ _|| |/ /",
                r"\__ \| |_| || _| | .` || |__ | | | ' < ",
                r"|___/ \___/ |___||_|\_||____|___||_|\_\ ",
            ]
            ALT = "S E C U R I T Y   S Y S T E M   v14"
            LF  = ("Consolas", 16, "bold")
            LH  = 24
            top = H//2 - (len(LOGO)*LH + 40)//2 - 20

            # Glitch tetik
            glitch_t[0] += 0.04
            if not glitch_aktif[0] and glitch_t[0] > random.uniform(2.5,5.0):
                glitch_aktif[0] = True
                glitch_sure[0]  = random.uniform(0.10, 0.40)
                glitch_tip[0]   = random.randint(0, 5)
                glitch_t[0]     = 0.0
            if glitch_aktif[0]:
                glitch_sure[0] -= 0.04
                if glitch_sure[0] <= 0:
                    glitch_aktif[0] = False

            tip = glitch_tip[0]

            for li, satir in enumerate(LOGO):
                y_pos = top + li * LH

                if glitch_aktif[0]:
                    if tip == 0:
                        
                        ofs = random.randint(6,16)
                        cv.create_text(cx+ofs, y_pos, text=satir,
                                       fill="#ff0033", font=LF)
                        cv.create_text(cx-ofs, y_pos, text=satir,
                                       fill="#0044ff", font=LF)

                    elif tip == 1:
                        
                        if li % 2 == 0:
                            cv.create_rectangle(cx-260,y_pos-4,cx+260,y_pos+4,
                                               fill="#001100",outline="")

                    elif tip == 2:
                        
                        if random.random() < 0.6:
                            boz = list(satir)
                            for bi in random.sample(range(len(boz)),
                                                    min(8,len(boz))):
                                if boz[bi] not in (' ',):
                                    boz[bi] = random.choice("!#$%@*01<>|^~")
                            satir = "".join(boz)

                    elif tip == 3:
                        
                        cv.create_rectangle(cx-260,y_pos-LH//2,
                                           cx+260,y_pos+LH//2,
                                           fill="#00ffaa",outline="")
                        cv.create_text(cx, y_pos, text=satir,
                                       fill="#000000", font=LF)
                        continue

                    elif tip == 4:
                        
                        ofs = int(math.sin(li*2.1 + t*8) * 14)
                        cv.create_text(cx+ofs, y_pos, text=satir,
                                       fill="#00ffcc", font=LF)
                        continue

                    elif tip == 5:
                        
                        ofs2 = random.randint(2,8)
                        cv.create_text(cx, y_pos+ofs2, text=satir,
                                       fill="#003333", font=LF)

                
                cv.create_text(cx, y_pos, text=satir,
                               fill="#d0eeff", font=LF)

            
            ly = top + len(LOGO)*LH + 8
            cv.create_line(cx-250,ly,cx+250,ly,fill="#00d4ff",width=1)

            
            pulse=0.5+0.5*math.sin(t*1.3)
            bc=int(150+105*pulse)
            cv.create_text(cx, ly+18, text=ALT,
                           fill=f"#00{bc:02x}ff",
                           font=("Consolas",13,"bold"))

            
            blink=int(t*2)%2==0
            cv.create_oval(cx-115,ly+38,cx-103,ly+50,
                           fill="#00ff88" if blink else "#004422",outline="")
            cv.create_text(cx-95, ly+44, text="SISTEM HAZIR",
                           fill="#00ff88",font=("Consolas",10,"bold"),anchor="w")

            
            gecen=int(now-t0[0])
            bilgiler=[
                (f"[ SISTEM: AKTIF ]",                            "#00ff88"),
                (f"[ SURE: {gecen//3600:02d}:{(gecen%3600)//60:02d}:{gecen%60:02d} ]","#ffaa00"),
                (f"[ GUVENLIK: AKTIF ]",                          "#00d4ff"),
                (f"[ IZLEME: CALISIYOR ]",                        "#aaaacc"),
                (datetime.now().strftime("[ %d.%m.%Y  %H:%M:%S ]"),"#445566"),
            ]
            for i,(metin,renk) in enumerate(bilgiler):
                cv.create_text(14,H-118+i*22,text=metin,fill=renk,
                               font=("Consolas",9,"bold"),anchor="w")

            self.sag.after(40, _ciz)

        cv.after(120, _ciz)

    def _yon_ekle_goster(self):
        self._anim_aktif = False   
        for w in self.sag.winfo_children(): w.destroy()
        self._ekle_aktif=True; self._son_frame=None

        ana=ctk.CTkFrame(self.sag,fg_color="#0a0a0f")
        ana.pack(fill="both",expand=True,padx=20,pady=20)

        ctk.CTkLabel(ana,text="YÖNETİCİ EKLE",
                     font=ctk.CTkFont("Consolas",24,"bold"),
                     text_color="#00d4ff").pack(pady=(10,14))

        frm=ctk.CTkFrame(ana,fg_color="#0d0d14",corner_radius=10)
        frm.pack(fill="x",padx=16,pady=6)

        for lbl,attr in [("Ad Soyad","_ye_ad"),("Unvan","_ye_unvan")]:
            row=ctk.CTkFrame(frm,fg_color="#0d0d14")
            row.pack(fill="x",padx=16,pady=4)
            ctk.CTkLabel(row,text=lbl+":",
                         font=ctk.CTkFont("Consolas",12),
                         text_color="#888899",width=90).pack(side="left")
            e=ctk.CTkEntry(row,width=300,height=32,
                            fg_color="#1a1a2e",border_color="#2a2a3e",
                            font=ctk.CTkFont("Consolas",12))
            e.pack(side="left",padx=8)
            setattr(self,attr,e)

        cam_f=ctk.CTkFrame(ana,fg_color="#0d0d14",corner_radius=10)
        cam_f.pack(fill="both",expand=True,padx=16,pady=6)

        ctk.CTkLabel(cam_f,text="KAMERA",
                     font=ctk.CTkFont("Consolas",14,"bold"),
                     text_color="#00d4ff").pack(pady=(8,4))

        self._ye_durum=ctk.CTkLabel(cam_f,text="Kamera baslatiliyor...",
                                     font=ctk.CTkFont("Consolas",10),
                                     text_color="#ffaa00")
        self._ye_durum.pack()

        self._ye_cam=ctk.CTkLabel(cam_f,text="",width=520,height=320)
        self._ye_cam.pack(pady=4)

        bf=ctk.CTkFrame(cam_f,fg_color="#0d0d14")
        bf.pack(pady=8)
        ctk.CTkButton(bf,text="KAYDET",width=130,height=40,
                      font=ctk.CTkFont("Consolas",13,"bold"),
                      fg_color="#003322",hover_color="#00ff88",
                      command=self._yon_kaydet).pack(side="left",padx=8)
        ctk.CTkButton(bf,text="İPTAL",width=110,height=40,
                      font=ctk.CTkFont("Consolas",12),
                      fg_color="#1a0a0a",hover_color="#ff4444",
                      command=self._yon_ekle_kapat).pack(side="left",padx=8)

        threading.Thread(target=self._yon_kamera,daemon=True).start()

    def _yon_kamera(self):
        cap=cv2.VideoCapture(0,cv2.CAP_DSHOW)
        if not cap.isOpened(): cap=cv2.VideoCapture(1,cv2.CAP_DSHOW)
        if not cap.isOpened():
            self.after(0,lambda: self._ye_durum.configure(
                text="Kamera bulunamadi!",text_color="#ff5555")); return
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT,480)
        self._ekle_cap=cap
        self.after(0,lambda: self._ye_durum.configure(
            text="Kamera hazir",text_color="#00ff88"))

        while self._ekle_aktif:
            ret,frame=cap.read()
            if not ret: time.sleep(0.03); continue
            self._son_frame=frame.copy()
            gorunen,_=landmark_ciz(frame)
            rgb=cv2.cvtColor(gorunen,cv2.COLOR_BGR2RGB)
            pil=Image.fromarray(rgb).resize((520,320))
            cimg=ctk.CTkImage(light_image=pil,size=(520,320))
            def _update_cam(img=cimg):
                try:
                    if self._ekle_aktif and hasattr(self,'_ye_cam') and self._ye_cam.winfo_exists():
                        self._ye_cam.configure(image=img)
                        self._ye_cam.image = img
                except: pass
            self.after(0, _update_cam)
            time.sleep(0.03)
        cap.release()

    def _yon_kaydet(self):
        ad=self._ye_ad.get().strip(); unvan=self._ye_unvan.get().strip()
        if not ad or not unvan:
            messagebox.showwarning("Uyari","Ad Soyad ve Unvan girin!"); return
        if self._son_frame is None:
            messagebox.showwarning("Uyari","Kamera goruntüsü yok!"); return

        ts=datetime.now().strftime("%Y%m%d%H%M%S")
        dosya=os.path.join(YON_RESIM,f"{ad}_{unvan}_{ts}.jpg")
        rgb=cv2.cvtColor(self._son_frame,cv2.COLOR_BGR2RGB)
        Image.fromarray(rgb).save(dosya)

        with open(YON_DOSYA,"a",encoding="utf-8") as f:
            f.write(f"Ad Soyad: {ad}\n")
            f.write(f"Unvan: {unvan}\n")
            f.write(f"Kayit Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
            f.write("-"*30+"\n")

        messagebox.showinfo("Basarili",f"'{ad}' eklendi!")
        self._yon_ekle_kapat()
        self._yon_listele()

    def _yon_ekle_kapat(self):
        self._ekle_aktif=False
        self._ana_sayfa()

    
    def _dogrulama_ac(self):
        DogrulamaEkrani(self)

#  ARKA PLAN===
class ArkaplanMod:
    
    def __init__(self):
        self.root=ctk.CTk()
        self.root.withdraw()
        self.root.title("_guvenlik_bg")
        self._gorev_cubu_gizle()

        _mp3_init()
        self._dogrulama_ac()
        threading.Thread(target=_df_yukle_bg_safe,daemon=True).start()
        self.root.mainloop()

    def _gorev_cubu_gizle(self):
        
        try:
            import ctypes
            hwnd=ctypes.windll.user32.FindWindowW(None,self.root.title())
            GWL_EXSTYLE=    -20
            WS_EX_APPWINDOW=0x00040000
            WS_EX_TOOLWINDOW=0x00000080
            stil=ctypes.windll.user32.GetWindowLongW(hwnd,GWL_EXSTYLE)
            stil=(stil & ~WS_EX_APPWINDOW) | WS_EX_TOOLWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd,GWL_EXSTYLE,stil)
        except: pass

    def _dogrulama_ac(self):
        yuzler=[f for f in os.listdir(YON_KL)
                if f.endswith((".jpg",".png"))] if os.path.exists(YON_KL) else []
        if not yonetici_listesi():
            self.root.after(2000,self._dogrulama_ac); return

        def _kapandi():
            self.root.after(500, self._dogrulama_ac)

        DogrulamaEkrani(self.root, callback_kapat=_kapandi)


def _df_yukle_bg_safe():
    """DeepFace modeli varsa yukle (opsiyonel)"""
    try:
        from deepface import DeepFace
        DeepFace.build_model("VGG-Face")
    except: pass

#  AÇILIŞ EKRANI====
class AcilisEkrani:
    """
    ffplay ile video oynatır.
    Üstüne Tk overlay: "ATLAMAK İÇİN BİR TUŞA BASIN" yanıp söner.
    Herhangi tuş/tık → ffplay öldür → devam.
    """
    VIDEO_SURE = 18

    def __init__(self):
        video_yol = os.path.join(ANA, "a.mp4")
        if not os.path.exists(video_yol):
            return

        ffplay = os.path.join(ANA,
            "ffmpeg-2026-03-15-git-6ba0b59d8b-full_build",
            "bin", "ffplay.exe")
        if not os.path.exists(ffplay):
            ffplay = "ffplay"

        try:
            user32 = ctypes.windll.user32
            W = user32.GetSystemMetrics(0)
            H = user32.GetSystemMetrics(1)
        except:
            W, H = 1920, 1080

        
        proc = None
        try:
            proc = subprocess.Popen(
                [ffplay, "-fs", "-autoexit",
                 "-t", str(self.VIDEO_SURE),
                 "-x", str(W), "-y", str(H),
                 video_yol],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            return


        import tkinter as _tk
        root = _tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-transparentcolor", "black")
        root.configure(bg="black")
        root.geometry(f"{W}x{H}+0+0")

    
        lbl = _tk.Label(
            root,
            text="ATLAMAK İÇİN BİR TUŞA BASIN",
            bg="black",
            fg="white",
            font=("Consolas", int(H * 0.022), "bold"),
        )
        lbl.place(relx=0.5, rely=0.92, anchor="center")

        atla = [False]

        def _atla(*_):
            atla[0] = True
            root.destroy()

        root.bind("<Key>",    _atla)
        root.bind("<Button>", _atla)
        root.focus_force()

        
        blink_state = [True]
        RENKLER = ["white", "#888888"]

        def _blink():
            if not atla[0] and root.winfo_exists():
                blink_state[0] = not blink_state[0]
                lbl.configure(fg=RENKLER[0] if blink_state[0] else RENKLER[1])
                root.after(500, _blink)

        
        def _goster():
            if not atla[0] and root.winfo_exists():
                lbl.lift()
                _blink()

        root.after(2000, _goster)

        
        def _kontrol():
            if atla[0]: return
            if proc.poll() is not None:
                root.destroy()
                return
            root.after(300, _kontrol)

        root.after(300, _kontrol)
        root.mainloop()

        
        try:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=2)
        except Exception:
            pass

#  UYGULAMA GİRİŞ ŞIFRE EKRAN====
class UygulamaGirisEkrani:
    def __init__(self):
        self.sonuc    = False
        self._aktif   = True
        self._deneme  = 0
        self._root = ctk.CTk()
        self._root.title("Güvenlik Sistemi — Giriş")
        self._root.resizable(True, True)
        self._root.configure(fg_color="#07070e")
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        self._root.geometry("500x500")
        self._root.state("zoomed")

        self._kur()
        self._root.mainloop()


    def _kur(self):
        import random, math

        try:
            import psutil as _ps; _psu = True
        except: _psu = False

        self._cv = tk.Canvas(self._root, bg="#07070e", highlightthickness=0)
        self._cv.place(x=0, y=0, relwidth=1, relheight=1)

        NOKTA = 30
        pts = [{"x": random.random(), "y": random.random(),
                "vx": random.uniform(-0.0003, 0.0003),
                "vy": random.uniform(-0.0003, 0.0003),
                "r":  random.uniform(2, 4)} for _ in range(NOKTA)]


        SUTUN = 20
        rain = [{"xr": (i+0.5)/SUTUN, "y": random.random(),
                 "sp": random.uniform(0.003, 0.008),
                 "ch": [random.choice("01") for _ in range(14)]}
                for i in range(SUTUN)]

    
        rad_a = [0]

        
        GECMIS = 40
        cpu_h = [0.0]*GECMIS; ram_h=[0.0]*GECMIS; gpu_h=[0.0]*GECMIS
        hw_n  = [0]

        def _hw():
            if _psu:
                try:
                    cpu_h.append(_ps.cpu_percent(interval=None))
                    ram_h.append(_ps.virtual_memory().percent)
                except:
                    cpu_h.append(random.uniform(20,60))
                    ram_h.append(random.uniform(40,75))
            else:
                cpu_h.append(random.uniform(20,60))
                ram_h.append(random.uniform(40,75))
            try:
                import subprocess as _sp2
                r2 = _sp2.run(["nvidia-smi","--query-gpu=utilization.gpu",
                               "--format=csv,noheader,nounits"],
                              capture_output=True, text=True,
                              encoding="utf-8", errors="ignore",
                              creationflags=0x08000000, timeout=1)
                gpu_h.append(float(r2.stdout.strip().split("\n")[0]))
            except: gpu_h.append(random.uniform(5,40))
            while len(cpu_h)>GECMIS: cpu_h.pop(0)
            while len(ram_h)>GECMIS: ram_h.pop(0)
            while len(gpu_h)>GECMIS: gpu_h.pop(0)

        for _ in range(GECMIS): _hw()

        # ── Akan kod───
        KOD = [
            "import ctypes, os, sys, threading",
            "class GuvenlikSistemi:",
            "    def __init__(self):",
            "        self._aktif = True",
            "        self._hook  = None",
            "    def klavye_izle(self):",
            "        WH_KEYBOARD_LL = 13",
            "        HOOKPROC = ctypes.WINFUNCTYPE(...)",
            "        self._hook = SetWindowsHookExW(...)",
            "    def ekran_kaydet(self, dosya):",
            "        cap = ImageGrab.grab(bbox=...)",
            "        frame = cv2.cvtColor(...)",
            "        self._proc.stdin.write(...)",
            "    def yuz_tani(self, frame):",
            "        gray = cv2.cvtColor(frame, GRAY)",
            "        faces = CASCADE.detectMultiScale(...)",
            "        return faces",
            "    def ses_kaydet(self):",
            "        stream = pyaudio.open(...)",
            "        data = stream.read(CHUNK)",
            "import numpy as np",
            "ffmpeg = subprocess.Popen(cmd, stdin=PIPE)",
            "threading.Thread(target=self._baslat).start()",
            "atexit.register(self.durdur)",
            "if __name__ == '__main__':",
            "    app = GuvenlikSistemi()",
            "    app.mainloop()",
            "# GUVENLIK SISTEMI v14 - AKTIF",
            "# KLAVYE: IZLENIYOR",
            "# EKRAN: KAYDEDILIYOR",
        ]
        KOD_H = 16; kod_ofs = [0.0]

        # ── Glitch───
        gl_t=[0.0]; gl_ak=[False]; gl_su=[0.0]; gl_tp=[0]
        t0_g = [time.time()]

        # ── Mini grafik────
        cv = self._cv
        def _mg(x0,y0,gw,gh,hist,renk,etk):
            cv.create_rectangle(x0,y0,x0+gw,y0+gh,fill="#0a0f0a",outline="#1a2a1a")
            for pct in (25,50,75):
                gy2=y0+gh-int(gh*pct/100)
                cv.create_line(x0,gy2,x0+gw,gy2,fill="#0d1f0d")
            n=len(hist)
            if n>=2:
                pg=[(x0+int(i*gw/(n-1)),y0+gh-int(gh*min(100,max(0,v))/100))
                    for i,v in enumerate(hist)]
                poly=[(x0,y0+gh)]+pg+[(x0+gw,y0+gh)]
                r_=max(0,int(int(renk[1:3],16)*0.25))
                g_=max(0,int(int(renk[3:5],16)*0.25))
                b_=max(0,int(int(renk[5:7],16)*0.25))
                cv.create_polygon(poly,fill=f"#{r_:02x}{g_:02x}{b_:02x}",outline="")
                for i in range(len(pg)-1):
                    cv.create_line(pg[i][0],pg[i][1],pg[i+1][0],pg[i+1][1],fill=renk,width=2)
            cv.create_text(x0+4,y0+4,text=etk,fill=renk,font=("Consolas",8,"bold"),anchor="nw")
            cv.create_text(x0+gw-4,y0+4,text=f"{hist[-1]:.0f}%",fill=renk,font=("Consolas",9,"bold"),anchor="ne")

        
        def _ciz():
            if not self._aktif: return
            try:
                if not cv.winfo_exists(): return
            except: return

            W=cv.winfo_width(); H=cv.winfo_height()
            if W<20 or H<20:
                self._root.after(50,_ciz); return

            cv.delete("all")
            t=time.time()

            
            for gx2 in range(0,W,55): cv.create_line(gx2,0,gx2,H,fill="#0c0c18")
            for gy2 in range(0,H,55): cv.create_line(0,gy2,W,gy2,fill="#0c0c18")

            
            kod_ofs[0]+=0.55
            th=len(KOD)*KOD_H
            if kod_ofs[0]>th: kod_ofs[0]=0.0
            for i,satir in enumerate(KOD*3):
                sy=int(i*KOD_H-kod_ofs[0])
                if sy<-KOD_H or sy>H+KOD_H: continue
                fade=min(1.0,min(sy+20,H-sy)/70)
                g_v=max(0,int(75*fade))
                if satir.startswith("    "):   col=f"#00{min(255,int(g_v*1.3)):02x}55"
                elif satir.startswith("class") or satir.startswith("import"): col=f"#33{min(255,int(g_v*1.2)):02x}88"
                elif satir.startswith("#"):    col=f"#55{min(255,int(g_v*0.8)):02x}22"
                else:                          col=f"#00{g_v:02x}33"
                cv.create_text(10,sy,text=satir,fill=col,font=("Consolas",9),anchor="nw")

            
            for s in rain:
                sx=int(s["xr"]*W)
                if sx<W*0.42: continue
                s["y"]+=s["sp"]
                if s["y"]>1.1:
                    s["y"]=-0.05
                    s["ch"]=[random.choice("01") for _ in range(14)]
                for j,k in enumerate(s["ch"]):
                    fy=s["y"]-j*0.04
                    if fy<0 or fy>1: continue
                    py2=int(fy*H)
                    fd=max(0.0,1.0-j*0.09)
                    col=("#00ffaa" if j==0 else f"#00{int(140*fd):02x}44" if j<3 else f"#00{int(55*fd):02x}22")
                    cv.create_text(sx,py2,text=k,fill=col,font=("Consolas",10))

            
            for n in pts:
                n["x"]=max(0.0,min(1.0,n["x"]+n["vx"]))
                n["y"]=max(0.0,min(1.0,n["y"]+n["vy"]))
                if n["x"] in(0.0,1.0): n["vx"]*=-1
                if n["y"] in(0.0,1.0): n["vy"]*=-1
            for i in range(len(pts)):
                for j in range(i+1,len(pts)):
                    dx=pts[i]["x"]-pts[j]["x"]; dy=pts[i]["y"]-pts[j]["y"]
                    d=math.hypot(dx,dy)
                    if d<0.18:
                        a=int(90*(1-d/0.18))
                        cv.create_line(int(pts[i]["x"]*W),int(pts[i]["y"]*H),
                                       int(pts[j]["x"]*W),int(pts[j]["y"]*H),
                                       fill=f"#00{min(255,a*2):02x}{min(255,a*3):02x}",width=1)
            for n in pts:
                px2,py2=int(n["x"]*W),int(n["y"]*H)
                rc=int(n["r"]+(0.5+0.5*math.sin(t*2+n["x"]*9))*2)
                cv.create_oval(px2-rc,py2-rc,px2+rc,py2+rc,fill="#00c8ff",outline="#00ffcc",width=1)

            
            rr=min(72,W//12); rx2=W-rr-18; ry2=rr+18
            for ring in(1.0,0.66,0.33):
                ri=int(rr*ring)
                cv.create_oval(rx2-ri,ry2-ri,rx2+ri,ry2+ri,outline="#002b1a",width=1)
            cv.create_line(rx2-rr,ry2,rx2+rr,ry2,fill="#002b1a")
            cv.create_line(rx2,ry2-rr,rx2,ry2+rr,fill="#002b1a")
            rad_a[0]=(rad_a[0]+3)%360
            ar=math.radians(rad_a[0])
            cv.create_line(rx2,ry2,rx2+int(rr*math.cos(ar)),ry2+int(rr*math.sin(ar)),fill="#00ff88",width=2)
            for iz in range(1,18):
                a2=math.radians((rad_a[0]-iz*4)%360)
                g2=max(0,int(200*(1-iz/18)))
                cv.create_line(rx2,ry2,rx2+int(rr*math.cos(a2)),ry2+int(rr*math.sin(a2)),fill=f"#00{g2:02x}33",width=1)
            cv.create_oval(rx2-3,ry2-3,rx2+3,ry2+3,fill="#00ff88",outline="#00ffaa")
            cv.create_text(rx2,ry2+rr+12,text="RADAR",fill="#00aa55",font=("Consolas",8,"bold"))

            # CPU/RAM/GPU
            hw_n[0]+=1
            if hw_n[0]%25==0: _hw()
            GW=rr*2+4; GH=34; GAP=7
            gx0=rx2-rr-2; gy0=ry2+rr+26
            _mg(gx0,gy0,GW,GH,cpu_h,"#00d4ff","CPU")
            _mg(gx0,gy0+GH+GAP,GW,GH,ram_h,"#ffaa00","RAM")
            _mg(gx0,gy0+(GH+GAP)*2,GW,GH,gpu_h,"#ff4488","GPU")

            # LOGO + GLITCH
            cxl=W//2
            LOGO=[
                r" ___  _   _  ___  _  _  _    ___ _  __",
                r"/ __|| | | || __|| \| || |  |_ _|| |/ /",
                r"\__ \| |_| || _| | .` || |__ | | | ' < ",
                r"|___/ \___/ |___||_|\_||____|___||_|\_\ ",
            ]
            ALT="S E C U R I T Y   S Y S T E M   v14"
            LF=("Consolas",16,"bold"); LH=24
            top=H//2-(len(LOGO)*LH+40)//2-80

            gl_t[0]+=0.04
            if not gl_ak[0] and gl_t[0]>random.uniform(2.5,5.0):
                gl_ak[0]=True; gl_su[0]=random.uniform(0.10,0.40)
                gl_tp[0]=random.randint(0,5); gl_t[0]=0.0
            if gl_ak[0]:
                gl_su[0]-=0.04
                if gl_su[0]<=0: gl_ak[0]=False

            tip=gl_tp[0]
            for li,satir in enumerate(LOGO):
                y_pos=top+li*LH
                if gl_ak[0]:
                    if tip==0:
                        ofs=random.randint(6,16)
                        cv.create_text(cxl+ofs,y_pos,text=satir,fill="#ff0033",font=LF)
                        cv.create_text(cxl-ofs,y_pos,text=satir,fill="#0044ff",font=LF)
                    elif tip==1:
                        if li%2==0: cv.create_rectangle(cxl-260,y_pos-4,cxl+260,y_pos+4,fill="#001100",outline="")
                    elif tip==2:
                        if random.random()<0.6:
                            boz=list(satir)
                            for bi in random.sample(range(len(boz)),min(8,len(boz))):
                                if boz[bi]!=' ': boz[bi]=random.choice("!#$%@*01<>|^~")
                            satir="".join(boz)
                    elif tip==3:
                        cv.create_rectangle(cxl-260,y_pos-LH//2,cxl+260,y_pos+LH//2,fill="#00ffaa",outline="")
                        cv.create_text(cxl,y_pos,text=satir,fill="#000000",font=LF); continue
                    elif tip==4:
                        ofs=int(math.sin(li*2.1+t*8)*14)
                        cv.create_text(cxl+ofs,y_pos,text=satir,fill="#00ffcc",font=LF); continue
                    elif tip==5:
                        ofs2=random.randint(2,8)
                        cv.create_text(cxl,y_pos+ofs2,text=satir,fill="#003333",font=LF)
                cv.create_text(cxl,y_pos,text=satir,fill="#d0eeff",font=LF)

            ly2=top+len(LOGO)*LH+8
            cv.create_line(cxl-250,ly2,cxl+250,ly2,fill="#00d4ff",width=1)
            pulse=0.5+0.5*math.sin(t*1.3)
            bc=int(150+105*pulse)
            cv.create_text(cxl,ly2+18,text=ALT,fill=f"#00{bc:02x}ff",font=("Consolas",13,"bold"))

            
            gecen=int(t-t0_g[0])
            bilgiler=[
                ("[ SİSTEM: AKTİF ]","#00ff88"),
                (f"[ SÜRE: {gecen//3600:02d}:{(gecen%3600)//60:02d}:{gecen%60:02d} ]","#ffaa00"),
                ("[ GÜVENLİK: AKTİF ]","#00d4ff"),
                ("[ ERİŞİM BEKLENİYORR ]","#aaaacc"),
                (datetime.now().strftime("[ %d.%m.%Y  %H:%M:%S ]"),"#445566"),
            ]
            for i2,(metin,renk) in enumerate(bilgiler):
                cv.create_text(14,H-118+i2*22,text=metin,fill=renk,font=("Consolas",9,"bold"),anchor="w")

            self._root.after(40,_ciz)

        self._cv.after(120,_ciz)

        form=ctk.CTkFrame(self._root,
                          width=420,height=280,
                          fg_color="#07070e",
                          bg_color="#07070e",
                          corner_radius=16,
                          border_width=2,
                          border_color="#00d4ff")
    
        form.place(relx=0.5, rely=0.72, anchor="center")
        form.pack_propagate(False)

        ctk.CTkLabel(form,
                     text="GÜVENLİK SİSTEMİ",
                     font=ctk.CTkFont("Consolas",18,"bold"),
                     text_color="#00d4ff").pack(pady=(22,2))

        ctk.CTkLabel(form,
                     text="Uygulama şifresini girin",
                     font=ctk.CTkFont("Consolas",10),
                     text_color="#445566").pack(pady=(0,12))

        self._e = ctk.CTkEntry(
            form,
            show="●",
            width=280, height=40,
            fg_color="transparent",
            border_color="#00d4ff",
            border_width=1,
            text_color="#c8eeff",
            font=ctk.CTkFont("Consolas",14),
            placeholder_text="Şifre...",
            placeholder_text_color="#334455",
        )
        self._e.pack(pady=4)

        self._msg = ctk.CTkLabel(form, text="",
                                  font=ctk.CTkFont("Consolas",10),
                                  text_color="#ff5555")
        self._msg.pack(pady=2)

        ctk.CTkButton(
            form,
            text="GİRİŞ",
            command=self._kontrol,
            width=180, height=38,
            fg_color="#003d5c",
            hover_color="#00d4ff",
            text_color="#c8eeff",
            font=ctk.CTkFont("Consolas",13,"bold"),
            corner_radius=8
        ).pack(pady=8)

        self._e.bind("<Return>", lambda _: self._kontrol())
        self._root.protocol("WM_DELETE_WINDOW", self._kapat)
        self._root.after(200, lambda: self._e.focus())

    def _kontrol(self):
        girilen = self._e.get().strip()
        dogru   = sifre_oku()
        if girilen == dogru:
            self._aktif  = False
            self.sonuc   = True
            self._root.destroy()
        else:
            self._deneme += 1
            self._e.delete(0, "end")
            if self._deneme >= 3:
                self._msg.configure(text="3 hatalı deneme — çıkılıyor.",
                                     text_color="#ff3333")
                self._root.after(1500, self._kapat)
            else:
                self._msg.configure(
                    text=f"Hatalı şifre! ({self._deneme}/3)",
                    text_color="#ff5555")

    def _kapat(self):
        self._aktif = False
        self.sonuc  = False
        self._root.destroy()





if __name__ == "__main__":
    _mp3_init()

    if "--dogrula" in sys.argv:
        ArkaplanMod()
    else:
        # 1. Açılış videosu (varsa)
        video_yol = os.path.join(ANA, "a.mp4")
        if os.path.exists(video_yol):
            AcilisEkrani()

        # 2. Uygulama giriş şifre ekranı
        giris = UygulamaGirisEkrani()
        if not giris.sonuc:
            sys.exit(0)

        # 3. Ana GUI
        app = AnaApp()
        app.mainloop()