# app/web_main.py

from flask import Flask, render_template, request, jsonify
# Import fungsi-fungsi dari main.py kita
# Kita perlu sedikit modifikasi main.py biar fungsinya bisa di-import
import sys
import os

# Tambahin path ke folder utama biar bisa import main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import importlib.util

main_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
spec = importlib.util.spec_from_file_location("main", main_path)
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)

app = Flask(__name__)

# Load database sekali pas app start
TRUSTED_SOURCES = main.load_trusted_sources()
TRUSTED_ARTICLES_DB = main.load_trusted_articles()

@app.route('/')
def index():
    """Halaman utama web app."""
    return render_template('index.html')

@app.route('/check_url', methods=['POST'])
def check_url():
    """Endpoint API buat ngecek URL."""
    data = request.get_json()
    url_input = data.get('url', '').strip()

    if not url_input:
        return jsonify({'error': 'URL tidak boleh kosong'}), 400

    # --- Logika cek URL (dipanggil dari main.py) ---
    # Kita perlu sedikit modifikasi fungsi di main.py biar bisa return hasil, bukan print.
    # Untuk sekarang, kita simulasi dulu.
    
    # Cek apakah URL trusted
    is_trusted = main.is_trusted_url(url_input, TRUSTED_SOURCES)
    
    if is_trusted:
        article_text = main.extract_text_from_url(url_input)
        if article_text:
            # Kita perlu modifikasi analyze_text buat return dict, bukan print
            # Untuk sementara, kita return hasil sederhana
            return jsonify({
                'status': 'trusted',
                'message': 'BERITA INI DARI SUMBER TERPERCAYA!',
                'preview': article_text[:300] + ("..." if len(article_text) > 300 else "")
            })
        else:
            return jsonify({'error': 'Gagal ngambil teks dari URL ini.'}), 500
    else:
        suspicious_text = main.extract_text_from_url(url_input)
        if suspicious_text:
            # Analisis teks
            similarity_score, similar_url, _ = main.find_similar_trusted_articles(suspicious_text, TRUSTED_ARTICLES_DB)
            similarity_percentage = round(similarity_score * 100, 2)
            
            # Tentukan indikator
            if similarity_percentage > 70:
                indicator = "PARTIALLY TRUE"
                message = "POTENSIAL BERITA ASLI!"
            elif similarity_percentage > 30:
                indicator = "POTENTIALLY HOAX"
                message = "BERITA MENCURIGAKAN!"
            else:
                indicator = "HIGHLY SUSPICIOUS"
                message = "BERITA SANGAT MENCURIGAKAN!"
                
            return jsonify({
                'status': 'checked',
                'message': message,
                'indicator': indicator,
                'similarity': f"{similarity_percentage}%",
                'similar_url': similar_url,
                'preview': suspicious_text[:300] + ("..." if len(suspicious_text) > 300 else "")
            })
        else:
             return jsonify({'error': 'Gagal ngambil teks dari URL ini.'}), 500

@app.route('/check_text', methods=['POST'])
def check_text():
    """Endpoint API buat ngecek teks langsung."""
    data = request.get_json()
    user_text = data.get('text', '').strip()

    if not user_text:
        return jsonify({'error': 'Teks tidak boleh kosong'}), 400

    # Analisis teks
    similarity_score, similar_url, _ = main.find_similar_trusted_articles(user_text, TRUSTED_ARTICLES_DB)
    similarity_percentage = round(similarity_score * 100, 2)
    
    # Tentukan indikator
    if similarity_percentage > 70:
        indicator = "PARTIALLY TRUE"
        message = "POTENSIAL BERITA ASLI!"
    elif similarity_percentage > 30:
        indicator = "POTENTIALLY HOAX"
        message = "BERITA MENCURIGAKAN!"
    else:
        indicator = "HIGHLY SUSPICIOUS"
        message = "BERITA SANGAT MENCURIGAKAN!"
        
    return jsonify({
        'status': 'checked',
        'message': message,
        'indicator': indicator,
        'similarity': f"{similarity_percentage}%",
        'similar_url': similar_url,
        'preview': user_text[:300] + ("..." if len(user_text) > 300 else "")
    })

if __name__ == '__main__':
    app.run(debug=True) # debug=True biar gampang develop, matiin pas production
