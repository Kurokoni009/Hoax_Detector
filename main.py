# main.py

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
        with open(filename, 'r') as f:
            data = json.load(f)
        return data['trusted_sources']
    except FileNotFoundError:
        print(f"❌ File {filename} nggak ketemu. Pastikan filenya ada.")
        return []
    except KeyError:
        print("❌ Format JSON-nya salah. Harus ada key 'trusted_sources'.")
        return []
    except Exception as e:
        print(f"❌ Error pas load trusted sources: {e}")
        return []

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
            print("⚠️  Warning: Gak nemu teks di halaman ini.")
            return ""
            
        return text.strip()
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error pas ambil data dari URL: {e}")
        return ""
    except Exception as e:
        print(f"❌ Error pas ekstrak teks: {e}")
        return ""

# --- Fungsi Baru Buat Analisis Teks ---

def calculate_similarity(text1, text2):
    """Hitung kemiripan antara dua teks menggunakan cosine similarity."""
    if not text1 or not text2:
        return 0.0
    
    # Vectorizer bakal ubah teks jadi angka yang bisa dibandingin
    vectorizer = TfidfVectorizer().fit([text1, text2])
    tfidf1 = vectorizer.transform([text1])
    tfidf2 = vectorizer.transform([text2])
    
    # Cosine similarity ngasih nilai antara 0 (nggak mirip) sampe 1 (sama persis)
    similarity_score = cosine_similarity(tfidf1, tfidf2)[0][0]
    return similarity_score

def find_similar_trusted_articles(suspicious_text, trusted_texts_db):
    """
    Cek kemiripan teks mencurigakan dengan semua teks trusted.
    Balikin skor kemiripan tertinggi dan teks trusted yang mirip.
    """
    if not suspicious_text or not trusted_texts_db:
        return 0.0, ""

    # Siapin semua teks buat dibandingin
    all_texts = list(trusted_texts_db.values()) # Isi teks trusted
    labels = list(trusted_texts_db.keys())      # Label/URL dari teks trusted
    
    # Tambahin teks mencurigakan ke list terakhir
    all_texts.append(suspicious_text)
    
    # Hitung TF-IDF
    vectorizer = TfidfVectorizer().fit(all_texts)
    tfidf_matrix = vectorizer.transform(all_texts)
    
    # Bandingin teks terakhir (suspicious) dengan semua teks sebelumnya
    similarities = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1])
    
    # Cari yang paling mirip
    max_index = similarities.argmax()
    max_similarity = similarities[0][max_index]
    
    most_similar_label = labels[max_index]
    most_similar_text = all_texts[max_index]
    
    return max_similarity, most_similar_label, most_similar_text

# --- Simulasi Database Teks Trusted (Untuk Testing) ---
# Di dunia nyata, ini bakal diambil dari database atau file lain.
TRUSTED_TEXTS_DB = {
    "https://www.bbc.com/news/world-111111": "Scientists have discovered a new species of dinosaur in Patagonia. The fossil, believed to be 90 million years old, suggests a unique evolutionary path.",
    "https://www.reuters.com/article/health-coronavirus-vaccine-id-222222": "A new study shows that the latest vaccine is 95% effective against the current strain of the virus. Experts call it a major breakthrough.",
    "https://www.kompas.com/teknologi/read/333333/ai-in-indonesia": "Indonesia is investing heavily in artificial intelligence research to boost its digital economy. The government plans to build several AI research centers."
}

# --- Fungsi Utama (Main Program) ---

def main():
    print("\n🚀 Selamat datang di Hoax Detector (Versi 3.0)!")
    print("   Sekarang kita bisa ngecek URL, ngambil teks, dan ngebandingin isinya!\n")
    
    # Load daftar sumber terpercaya
    trusted_sources = load_trusted_sources()
    if not trusted_sources:
        print("❌ Gagal load trusted sources. Program berhenti.")
        return

    print(f"✅ Loaded {len(trusted_sources)} trusted sources.\n")
    
    # Input URL dari user
    url_input = input("🔗 Masukin URL berita yang mau di cek: ").strip()
    
    if not url_input:
        print("❌ URL kosong. Coba lagi.")
        return

    print("\n🔍 Lagi ngecek URL...")
    
    # Cek apakah URL trusted
    if is_trusted_url(url_input, trusted_sources):
        print("✅ BERITA INI DARI SUMBER TERPERCAYA!")
        
        # Ambil teks dari URL trusted
        print("📄 Lagi ngambil teks dari berita...")
        article_text = extract_text_from_url(url_input)
        
        if article_text:
            print("👀 Preview teks berita (500 karakter pertama):")
            print("-" * 50)
            print(article_text[:500] + ("..." if len(article_text) > 500 else ""))
            print("-" * 50)
        else:
            print("⚠️  Gagal ngambil teks dari berita ini.")
            
    else:
        print("❌ WASPADA! BERITA INI BUKAN DARI SUMBER TERPERCAYA.")
        print("   Tapi jangan panik! Kita bakal cek isinya...")
        
        # Ambil teks dari URL yang mencurigakan
        print("📄 Lagi ngambil teks dari berita...")
        suspicious_text = extract_text_from_url(url_input)
        
        if suspicious_text:
            print("👀 Preview teks berita mencurigakan (500 karakter pertama):")
            print("-" * 50)
            print(suspicious_text[:500] + ("..." if len(suspicious_text) > 500 else ""))
            print("-" * 50)
            
            # --- Bagian Baru: Cek Kemiripan ---
            print("\n🧠 Lagi ngecek kemiripan dengan berita terpercaya...")
            similarity_score, similar_url, similar_text = find_similar_trusted_articles(suspicious_text, TRUSTED_TEXTS_DB)
            
            # Konversi ke persentase
            similarity_percentage = round(similarity_score * 100, 2)
            
            if similarity_percentage > 70: # Threshold bisa diubah
                print(f"\n✅ POTENSIAL BERITA ASLI!")
                print(f"   Kemiripan dengan berita terpercaya: {similarity_percentage}%")
                print(f"   Berita mirip ditemukan di: {similar_url}")
                print("   Indikator: PARTIALLY TRUE / BERITA INI MIRIP DENGAN YANG ASLI")
            elif similarity_percentage > 30:
                print(f"\n⚠️  BERITA MENCURIGAKAN!")
                print(f"   Kemiripan dengan berita terpercaya: {similarity_percentage}%")
                print(f"   Berita mirip ditemukan di: {similar_url}")
                print("   Indikator: POTENTIALLY HOAX / BERITA INI MUNGKIN HOAX")
            else:
                print(f"\n🚨 BERITA SANGAT MENCURIGAKAN!")
                print(f"   Kemiripan dengan berita terpercaya: {similarity_percentage}%")
                print("   Indikator: HIGHLY SUSPICIOUS / KEMUNGKINAN BESAR HOAX")
                
        else:
            print("⚠️  Gagal ngambil teks dari berita ini.")

# Jalanin fungsi utama kalo file ini di-run langsung
if __name__ == "__main__":
    main()
