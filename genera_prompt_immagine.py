import requests
from bs4 import BeautifulSoup
import random
import os
import pytesseract
from PIL import Image
from io import BytesIO
import openai

# ========== CONFIGURAZIONE ==========
print("🚀 Avvio script Instagram Post Generator")

BASE_URL = "https://www.awakenedsoul.ch/shop"
TOTAL_PAGES = 8
HEADERS = {'User-Agent': 'Mozilla/5.0'}
WEBHOOK_URL = "https://hooks.zapier.com/hooks/catch/23181653/2vr280p/"
SITO_WEB = "www.awakenedsoul.ch"

# Imposta la chiave API da variabile d'ambiente
openai.api_key = os.getenv("OPENAI_API_KEY")

# ========== RACCOLTA IMMAGINI ==========
print("🔍 Scansione immagini da sito...")
product_images = []

for page in range(1, TOTAL_PAGES + 1):
    url = f"{BASE_URL}?page={page}"
    print(f"➡️ Scansione: {url}")
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, 'html.parser')
    for img in soup.find_all('img'):
        src = img.get('src')
        if src and 'wixstatic' in src:
            clean_src = src.split("/v1/")[0] if "/v1/" in src else src
            if clean_src not in product_images:
                product_images.append(clean_src)

print(f"\n📦 Trovate {len(product_images)} immagini totali.")

# ========== FILTRAGGIO IMMAGINI PER INSTAGRAM ==========
filtered_images = []

for img_url in product_images:
    try:
        img_data = requests.get(img_url).content
        img = Image.open(BytesIO(img_data))
        width, height = img.size
        aspect_ratio = width / height
        if aspect_ratio <= 1.3 and height >= 600:
            filtered_images.append((img_url, img_data))
    except Exception:
        continue

print(f"✅ Immagini filtrate per Instagram: {len(filtered_images)}")

# ========== SELEZIONE IMMAGINE ==========
if filtered_images:
    img_url, selected_data = random.choice(filtered_images)
    print("📷 Immagine selezionata:", img_url)
    try:
        img = Image.open(BytesIO(selected_data))
        extracted_text = pytesseract.image_to_string(img)
        print("📄 Testo OCR:", extracted_text.strip())
    except Exception as e:
        print(f"⚠️ Errore OCR migliorato: {e}")
        extracted_text = ""
else:
    img_url = "https://static.wixstatic.com/media/d88eeb_d5cec62a575b45a7880d8156a00fbfda~mv2.jpg"
    print("⚠️ Nessuna immagine valida trovata. Uso fallback:", img_url)
    extracted_text = ""

# ========== PROMPT E CAPTION ==========
prompt = (
    f"You are a creative social media copywriter for a conscious fashion brand. "
    f"Generate a creative Instagram caption in English (max 250 characters) using this text found on a product image: \"{testo_estratto}\". "
    f"The brand promotes spiritual and mindset messages such as self-esteem, brotherhood and sisterhood, integrity, mindfulness, acceptance, presence, and boundaries. "
    f"Include emojis, a warm and inspiring tone that invites people to work on their mindset to become better human beings, and a call to action inviting followers to visit {sito_web}."
	)


try:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an Instagram caption copywriter for a spiritual clothing brand."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=150
    )
    caption = response.choices[0].message.content.strip()
except Exception as e:
    print(f"⚠️ Errore GPT: {e}")
    caption = (
        f"🌿 Embrace growth and self-awareness through conscious fashion. "
        f"Discover more at {SITO_WEB}. ✨ #MindfulStyle #SpiritualFashion"
    )

# ========== INVIO A ZAPIER ==========
print("\n📌 Caption per Instagram:")
print("=" * 50)
print(caption)

data = {
    "caption": caption,
    "image_url": img_url,
    "prompt": prompt
}

zap_resp = requests.post(WEBHOOK_URL, json=data)
if zap_resp.status_code == 200:
    print("✅ Dati inviati con successo a Zapier!")
else:
    print(f"❌ Errore nell'invio a Zapier: {zap_resp.status_code}")
