# main.py
"""
Hoax Detector v6.0
Main logic for both CLI and Web App.
"""

import json
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --- Fungsi-Fungsi Utama ---

def load_trusted_sources(filename="trusted_sources.json"):
    """Baca file JSON dan balikin list trusted sources."""
    try:
        import os
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'r') as f:
            data = json.load(f)
        return data.get('trusted_sources', [])
    except FileNotFoundError:
        print(f"❌ File {filename} nggak ketemu. Pastikan filenya ada.")
        return []
    except KeyError:
        print("❌ Format JSON-nya salah. Harus ada key 'trusted_sources'.")
        return []
    except Exception as e:
        print(f"❌ Error pas load trusted sources: {e}")
        return []

def load_trusted_articles(filename="trusted_articles.json"):
    """Baca file JSON dan balikin dictionary trusted articles."""
    try:
        import os
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('articles', {})
    except FileNotFoundError:
        print(f"❌ File {filename} nggak ketemu. Bakal dibuat baru kalo nambah artikel.")
        return {}
    except json.JSONDecodeError:
        print(f"❌ Format JSON di {filename} salah.")
        return {}
    except Exception as e:
        print(f"❌ Error pas load trusted articles: {e}")
        return {}

def is_trusted_url(url, trusted_sources):
    """Cek apakah domain dari URL ada di daftar trusted."""
    try:
        domain = urlparse(url).netloc.lower()
        trusted_domains = [source.lower() for source in trusted_sources]
        return domain in trusted_domains
    except Exception as e:
        print(f"❌ Error pas ngecek URL: {e}")
        return False

def extract_text_from_url(url):
    """Ambil teks utama dari sebuah URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # --- Cara sederhana buat ngambil paragraf ---
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text() for p in paragraphs])
        
        if not text.strip():
            # print("⚠️  Warning: Gak nemu teks di halaman ini.")
            return ""
            
        return text.strip()
        
    except requests.exceptions.RequestException as e:
        # print(f"❌ Error pas ambil data dari URL: {e}")
        return ""
    except Exception as e:
        # print(f"❌ Error pas ekstrak teks: {e}")
        return ""

# --- Fungsi Baru Buat Analisis Teks ---

def calculate_similarity(text1, text2):
    """Hitung kemiripan antara dua teks menggunakan cosine similarity."""
    if not text1 or not text2:
        return 0.0
    
    vectorizer = TfidfVectorizer().fit([text1, text2])
    tfidf1 = vectorizer.transform([text1])
    tfidf2 = vectorizer.transform([text2])
    
    similarity_score = cosine_similarity(tfidf1, tfidf2)[0][0]
    return similarity_score

def find_similar_trusted_articles(suspicious_text, trusted_articles_db):
    """
    Cek kemiripan teks mencurigakan dengan semua teks trusted.
    Balikin skor kemiripan tertinggi dan URL dari berita trusted yang mirip.
    """
    if not suspicious_text or not trusted_articles_db:
        return 0.0, "", ""

    # Siapin semua teks buat dibandingin
    all_texts = [article_data['text'] for article_data in trusted_articles_db.values()]
    labels = list(trusted_articles_db.keys()) # URL dari teks trusted
    
    # Tambahin teks mencurigakan ke list terakhir
    all_texts.append(suspicious_text)
    
    # Hitung TF-IDF
    vectorizer = TfidfVectorizer().fit(all_texts)
    tfidf_matrix = vectorizer.transform(all_texts)
    
    # Bandingin teks terakhir (suspicious) dengan semua teks sebelumnya
    similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    
    # Cari yang paling mirip
    if similarities.size > 0:
        max_index = similarities.argmax()
        max_similarity = similarities[0][max_index]
        
        most_similar_url = labels[max_index]
        # most_similar_text = all_texts[max_index] # Bisa dipake kalo perlu
        
        return max_similarity, most_similar_url, "" # Kita kosongin text return biar ringan
    else:
        return 0.0, "", ""

# --- Fungsi Utama untuk Analisis (Bisa dipake CLI/Web) ---

def analyze_text(text_to_analyze, trusted_articles_db, is_trusted=False, source_url=""):
    """
    Fungsi terpisah buat ngeanalisis teks, baik dari URL maupun input langsung.
    Sekarang return dictionary hasil, bukan langsung print.
    """
    result = {
        'status': 'unknown',
        'message': '',
        'indicator': '',
        'similarity': '',
        'similar_url': '',
        'preview': ''
    }

    preview_text = text_to_analyze[:500] + ("..." if len(text_to_analyze) > 500 else "")
    result['preview'] = preview_text

    if is_trusted:
        result['status'] = 'trusted'
        result['message'] = 'BERITA INI DARI SUMBER TERPERCAYA!'
    else:
        # --- Cek Kemiripan ---
        similarity_score, similar_url, _ = find_similar_trusted_articles(text_to_analyze, trusted_articles_db)
        
        # Konversi ke persentase
        similarity_percentage = round(similarity_score * 100, 2)
        result['similarity'] = f"{similarity_percentage}%"
        result['similar_url'] = similar_url
        
        if similarity_percentage > 70:
            result['status'] = 'checked'
            result['indicator'] = 'PARTIALLY TRUE'
            result['message'] = 'POTENSIAL BERITA ASLI!'
        elif similarity_percentage > 30:
            result['status'] = 'checked'
            result['indicator'] = 'POTENTIALLY HOAX'
            result['message'] = 'BERITA MENCURIGAKAN!'
        else:
            result['status'] = 'checked'
            result['indicator'] = 'HIGHLY SUSPICIOUS'
            result['message'] = 'BERITA SANGAT MENCURIGAKAN!'
            
    return result

# --- Fungsi-Fungsi Khusus CLI ---

def add_trusted_article(trusted_articles_db, filename="trusted_articles.json"):
    """
    Fungsi buat nambah artikel trusted ke database.
    """
    print("\n➕ Fitur Tambah Artikel Terpercaya")
    print("   Masukin URL artikel dari sumber terpercaya yang mau ditambahin.")
    
    url_to_add = input("🔗 URL Artikel: ").strip()
    
    if not url_to_add:
        print("❌ URL kosong. Batal nambah artikel.")
        return trusted_articles_db # Balikin db yang lama
    
    if url_to_add in trusted_articles_db:
        print("⚠️  Artikel dengan URL ini udah ada di database.")
        return trusted_articles_db

    print("📄 Lagi ngambil teks dari URL...")
    article_text = extract_text_from_url(url_to_add)
    
    if not article_text:
        print("❌ Gagal ngambil teks. Batal nambah artikel.")
        return trusted_articles_db

    # --- Simulasi ngambil judul ---
    title_words = article_text.split()[:10]
    article_title = " ".join(title_words) + "..."
    
    # Siapin data artikel baru
    new_article = {
        "url": url_to_add,
        "title": article_title,
        "text": article_text
    }
    
    # Tambahin ke database (dictionary di memory dulu)
    trusted_articles_db[url_to_add] = new_article
    
    # Simpan ke file
    try:
        # Baca dulu data lama (kalo ada) buat ngegabung
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            existing_data = {"articles": {}}
        
        # Update data articles
        existing_data.setdefault("articles", {}).update({url_to_add: new_article})
        
        # Tulis ulang file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Artikel berhasil ditambahin ke {filename}!")
        print(f"   Judul (preview): {article_title}")
        
    except Exception as e:
        print(f"❌ Error pas nyimpen ke file: {e}")
        # Kalo gagal simpan, hapus dari memory juga
        trusted_articles_db.pop(url_to_add, None)
        
    return trusted_articles_db # Balikin db yang udah diupdate

def print_result_to_console(result):
    """Print hasil analisis ke console dengan format yang rapi."""
    print("\n" + "="*50)
    if result['status'] == 'trusted':
        print(f"✅ {result['message']}")
        print("-" * 50)
        print("👀 Preview teks berita:")
        print(result['preview'])
    elif result['status'] == 'checked':
        print(f"🔍 {result['message']}")
        print(f"📊 Indikator: {result['indicator']}")
        print(f"📈 Kemiripan: {result['similarity']}")
        if result['similar_url']:
            print(f"🔗 Berita mirip: {result['similar_url']}")
        print("-" * 50)
        print("👀 Preview teks:")
        print(result['preview'])
    print("="*50)

def handle_url_input(trusted_sources, trusted_articles_db):
    """Handle logika input URL."""
    url_input = input("\n🔗 Masukin URL berita yang mau di cek: ").strip()
    
    if not url_input:
        print("❌ URL kosong. Coba lagi.")
        return

    print("\n🔍 Lagi ngecek URL...")
    
    if is_trusted_url(url_input, trusted_sources):
        print("✅ BERITA INI DARI SUMBER TERPERCAYA!")
        print("📄 Lagi ngambil teks dari berita...")
        article_text = extract_text_from_url(url_input)
        if article_text:
            result = analyze_text(article_text, trusted_articles_db, is_trusted=True, source_url=url_input)
            print_result_to_console(result)
        else:
            print("⚠️  Gagal ngambil teks dari berita ini.")
    else:
        print("❌ WASPADA! BERITA INI BUKAN DARI SUMBER TERPERCAYA.")
        print("   Tapi jangan panik! Kita bakal cek isinya...")
        print("📄 Lagi ngambil teks dari berita...")
        suspicious_text = extract_text_from_url(url_input)
        if suspicious_text:
            result = analyze_text(suspicious_text, trusted_articles_db, is_trusted=False, source_url=url_input)
            print_result_to_console(result)
        else:
            print("⚠️  Gagal ngambil teks dari berita ini.")

def handle_text_input(trusted_articles_db):
    """Handle logika input teks langsung."""
    print("\n📝 Masukin teks berita yang mau di cek:")
    print("(Tips: Paste teks panjang dan tekan Enter dua kali di akhir)")
    print("-" * 50)
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    user_text = "\n".join(lines)
    print("-" * 50)
    
    if not user_text.strip():
        print("❌ Teks kosong. Coba lagi.")
        return
        
    print("\n🧠 Lagi ngecek teks...")
    result = analyze_text(user_text, trusted_articles_db, is_trusted=False, source_url="Input Teks Langsung")
    print_result_to_console(result)

def run_cli():
    """Jalankan versi Command-Line Interface dari program."""
    print("\n🚀 Selamat datang di Hoax Detector (Versi 6.0)!")
    print("   Sekarang kita bisa tambah artikel terpercaya langsung dari sini!\n")
    
    # Load daftar sumber terpercaya
    trusted_sources = load_trusted_sources()
    if not trusted_sources:
        print("❌ Gagal load trusted sources. Program berhenti.")
        return

    # Load database teks terpercaya dari file
    trusted_articles_db = load_trusted_articles()
    if not trusted_articles_db:
        print("⚠️  Database teks trusted masih kosong. Program tetap jalan, tapi fitur analisis terbatas.")
    else:
        print(f"✅ Loaded {len(trusted_articles_db)} trusted articles from database.\n")
    
    # --- Menu Utama yang Diperluas ---
    while True: # Loop biar program nggak langsung keluar
        print("\n<Menu Utama>")
        print("1. Cek Keaslian Berita (URL)")
        print("2. Cek Keaslian Berita (Teks Langsung)")
        print("3. Tambah Artikel Terpercaya")
        print("4. Keluar")
        choice = input("Pilihan Anda (1/2/3/4): ").strip()

        if choice == "1":
            # --- Alur Input URL ---
            handle_url_input(trusted_sources, trusted_articles_db)
            
        elif choice == "2":
            # --- Alur Input Teks Langsung ---
            handle_text_input(trusted_articles_db)
            
        elif choice == "3":
            # --- Alur Tambah Artikel Trusted ---
            trusted_articles_db = add_trusted_article(trusted_articles_db)
            
        elif choice == "4":
            print("\n👋 Terima kasih sudah menggunakan Hoax Detector!")
            break # Keluar dari loop
            
        else:
            print("❌ Pilihan nggak valid. Coba lagi.")

# --- Bagian yang Ngejalanin Program CLI ---
if __name__ == "__main__":
    run_cli()
