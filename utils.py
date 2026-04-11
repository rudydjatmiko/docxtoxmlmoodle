import re

def wrap_arabic(text):
    """
    Blok Utilitas: Memformat teks Arab agar tampil Right-to-Left (RTL) 
    dan memiliki ukuran font yang nyaman dibaca di Moodle.
    """
    if not text: return ""
    # Mencari karakter Arab menggunakan range Unicode
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 22px; line-height: 1.6;">\1</span>', text)

def clean_line(text):
    """
    Blok Utilitas: Membersihkan karakter sampah dari MS Word yang sering
    menggagalkan deteksi kunci jawaban atau teks soal.
    """
    if not text: return ""
    # Membersihkan non-breaking space (\xa0) dan zero-width space (\u200b)
    return text.replace('\xa0', ' ').replace('\u200b', '').strip()
