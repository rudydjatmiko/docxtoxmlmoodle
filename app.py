import streamlit as st
from docx import Document
import re
import io

# --- 1. FUNGSI BACKEND ---

def wrap_arabic(text):
    if not text: return ""
    arabic_pattern = re.compile(r'([\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+)')
    return arabic_pattern.sub(r'<span dir="rtl" style="font-family: \'Traditional Arabic\', serif; font-size: 24px; line-height: 1.6;">\1</span>', text)

def convert_docx_to_moodle_xml(docx_file):
    doc = Document(docx_file)
    raw_lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'
    
    # State tracking
    current_mode = "MULTIPLE CHOICE" # Default awal
    q_num = 1
    i = 0
    
    # Statistik untuk ditampilkan di UI
    stats = {"PG (Single)": 0, "PG Kompleks (Set)": 0, "Essay": 0}
    
    while i < len(raw_lines):
        line = raw_lines[i]
        line_upper = line.upper()

        # A. DETEKSI PENANDA TIPE SOAL (Header penentu mode)
        if "MULTIPLE CHOICE SET" in line_upper:
            current_mode = "MULTIPLE CHOICE SET"
            i += 1
            continue
        elif "MULTIPLE CHOICE" in line_upper:
            current_mode = "MULTIPLE CHOICE"
            i += 1
            continue
        elif "ESSAY" in line_upper:
            current_mode = "ESSAY"
            i += 1
            continue
        
        # Abaikan header umum dokumen agar tidak masuk ke teks soal
        if any(h in line_upper for h in ["SAT PAI", "AKIDAH", "TAHUN PELAJARAN"]):
            i += 1
            continue

        # B. EKSEKUSI BERDASARKAN MODE
        if current_mode == "ESSAY":
            # Mode Essay: Ambil semua teks yang tersisa sebagai satu kesatuan soal essay
            # atau bisa dimodifikasi per butir jika essay Anda memiliki format "Ans:"
            essay_content = "<br/>".join(raw_lines[i:])
            xml_output += f"""
  <question type="essay">
    <name><text>Soal {q_num:02d} (Essay)</text></name>
    <questiontext format="html"><text><![CDATA[<p>{wrap_arabic(essay_content)}</p>]]></text></questiontext>
    <defaultgrade>1.0</defaultgrade>
    <responseformat>editor</responseformat>
    <responserequired>1</responserequired>
    <responsefieldlines>15</responsefieldlines>
  </question>\n"""
            stats["Essay"] += 1
            break 

        else:
            # Mode MULTIPLE CHOICE atau MULTIPLE CHOICE SET
            block = []
            while i < len(raw_lines):
                curr = raw_lines[i]
                curr_up = curr.upper()
                # Berhenti jika ketemu kunci jawaban ATAU ada penanda tipe soal baru
                if curr_up.startswith("ANS:") or any(m in curr_up for m in ["MULTIPLE CHOICE", "ESSAY"]):
                    break
                block.append(curr)
                i += 1
            
            # Jika blok berhenti karena menemukan kunci "Ans:"
            if i < len(raw_lines) and raw_lines[i].upper().startswith("ANS:"):
                ans_key = raw_lines[i].upper().replace("ANS:", "").strip()
                i += 1
                
                # Sesuai pola dokumen Anda: 4 baris terbawah dalam blok adalah pilihan A, B, C, D
                if len(block) >= 5:
                    choices = block[-4:] 
                    question_body = block[:-4] 
                    
                    q_html = "".join([f"<p>{wrap_arabic(p)}</p>" for p in question_body])
                    
                    # Tentukan status 'single' berdasarkan mode saat ini
                    is_single = "SET" not in current_mode
                    
                    xml_output += f'  <question type="multichoice">\n'
                    xml_output += f'    <name><text>Soal {q_num:02d}</text></name>\n'
                    xml_output += f'    <questiontext format="html"><text><![CDATA[{q_html}]]></text></questiontext>\n'
                    xml_output += f'    <single>{"true" if is_single else "false"}</single>\n'
                    xml_output += f'    <shuffleanswers>true</shuffleanswers>\n'
                    xml_output += f'    <answernumbering>abc</answernumbering>\n'

                    labels = ["A", "B", "C", "D"]
                    for idx, c_text in enumerate(choices):
                        label = labels[idx]
                        
                        if not is_single: # Jika mode MULTIPLE CHOICE SET
                            correct_list = [x.strip() for x in ans_key.split(',')]
                            # Skor dibagi rata (100% / jumlah jawaban benar)
                            fraction = str(round(100/len(correct_list), 5)) if label in correct_list else "0"
                        else: # Jika mode MULTIPLE CHOICE biasa
                            fraction = "100" if label == ans_key else "0"
                        
                        xml_output += f'    <answer fraction="{fraction}" format="html">\n'
                        xml_output += f'      <text><![CDATA[{wrap_arabic(c_text)}]]></text>\n'
                        xml_output += f'    </answer>\n'
                    
                    xml_output += '  </question>\n'
                    
                    # Update statistik
                    if is_single: stats["PG (Single)"] += 1
                    else: stats["PG Kompleks (Set)"] += 1
                    q_num += 1
            else:
                i += 1

    xml_output += '</quiz>'
    return xml_output, stats

# --- 2. ANTARMUKA (UI) STREAMLIT ---

st.set_page_config(page_title="Konverter Moodle Akidah", page_icon="🕌")

st.title("🕌 Konverter Moodle XML (Auto-Detection)")
st.markdown("""
Skrip ini akan mendeteksi tipe soal berdasarkan **Header** di dalam file Word Anda:
1. Menemukan **MULTIPLE CHOICE** → Soal PG biasa (1 jawaban).
2. Menemukan **MULTIPLE CHOICE SET** → Soal PG Kompleks (bisa banyak jawaban).
3. Menemukan **ESSAY** → Soal uraian.
""")

uploaded_file = st.file_uploader("Upload file .docx Anda", type=["docx"])

if uploaded_file:
    try:
        hasil_xml, statistik = convert_docx_to_moodle_xml(uploaded_file)
        
        # --- MENAMPILKAN JUMLAH & TIPE SOAL ---
        st.subheader("📊 Hasil Konversi")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("PG Biasa", statistik["PG (Single)"])
        with col2:
            st.metric("PG Kompleks (Set)", statistik["PG Kompleks (Set)"])
        with col3:
            st.metric("Essay", statistik["Essay"])
            
        total_soal = sum(statistik.values())
        st.write(f"**Total soal yang terbaca: {total_soal} soal.**")

        # Tombol Download
        file_xml = uploaded_file.name.replace(".docx", ".xml")
        st.download_button(
            label="📥 Download File XML untuk Moodle",
            data=hasil_xml,
            file_name=file_xml,
            mime="text/xml",
            use_container_width=True
        )
        
        st.success("File siap diimport ke Moodle via Question Bank!")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file: {e}")
