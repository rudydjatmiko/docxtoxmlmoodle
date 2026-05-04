
import mammoth

def to_html(file):
    """Mengonversi Docx ke HTML untuk tampilan pratinjau di Streamlit."""
    try:
        # Reset pointer file ke awal
        file.seek(0)
        
        # Konversi ke HTML
        result = mammoth.convert_to_html(file)
        html = result.value
        
        # CSS sederhana untuk tampilan monitor
        custom_css = """
        <style>
            body { font-family: sans-serif; line-height: 1.6; padding: 20px; }
            table { border-collapse: collapse; width: 100%; }
            table, th, td { border: 1px solid #ddd; padding: 8px; }
            img { max-width: 100%; height: auto; }
        </style>
        """
        return f"{custom_css}<div>{html}</div>"
    except Exception as e:
        return f"<p>Error Pratinjau: {e}</p>"
