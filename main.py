# --- Bagian Akhir main.py ---

# Fungsi analyze_text yang di-update buat return hasil
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
        similarity_score, similar_url, similar_text = find_similar_trusted_articles(text_to_analyze, trusted_articles_db)
        
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

# Fungsi main() yang lama kita rename jadi run_cli() biar nggak bentrok
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

# Fungsi handler yang di-update buat pake analyze_text yang baru
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

# --- Bagian yang Ngejalanin Program CLI ---
# Ini yang bakal jalan kalo main.py di-run langsung
if __name__ == "__main__":
    run_cli()
