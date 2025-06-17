import requests
from bs4 import BeautifulSoup
import random
import os
from openai import OpenAI
from PIL import Image
from io import BytesIO
import pytesseract
import re

# ========== CONFIGURAZIONE ==========
URL = "https://www.awakenedsoul.ch/shop"
headers = {'User-Agent': 'Mozilla/5.0'}
openai_api_key = os.getenv("OPENAI_API_KEY")
webhook_url = "https://hooks.zapier.com/hooks/catch/23181653/2vr280p/"
sito_web = "www.awakenedsoul.ch"

# Controllo presenza chiave API
if not openai_api_key:
    raise ValueError("❌ OPENAI_API_KEY non è impostata. Assicurati che sia presente nelle variabili d'ambiente.")

client = OpenAI(api_key=openai_api_key)

# ========== SCARICA IMMAGINI DA PIÙ PAGINE ==========
all_images = []

for page_num in range(1, 9):  # Pagine da 1 a 8
    paged_url = f"{URL}?page={page_num}"
    try:
        response = requests.get(paged_url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"⚠️ Errore nel caricamento della pagina {page_num}: {e}")
        continue

    soup = BeautifulSoup(response.text, 'html.parser')
    images = soup.find_all('img')
    for img in images:
        src = img.get('src', '')
        if 'wixstatic' in src and src.startswith('http'):
            all_images.append(src)

# ========== FILTRA IMMAGINI PER FORMATO INSTAGRAM ==========
filtered_images = []
os.makedirs("immagini_prodotto", exist_ok=True)

for img_url in all_images:
    try:
        res = requests.get(img_url)
        res.raise_for_status()
        img = Image.open(BytesIO(res.content))
        width, height = img.size
        aspect_ratio = width / height

        # Instagram ideale: verticale o quadrata
        if 0.8 <= aspect_ratio <= 1.2 and height >= 600:
            filtered_images.append((img_url, img))
    except Exception as e:
        print(f"⚠️ Errore nel processamento immagine: {e}")
        continue

if not filtered_images:
    print("⚠️ Nessuna immagine adatta trovata.")
    exit()

# ========== SELEZIONA IMMAGINE CASUALE ==========
img_url, selected_img = random.choice(filtered_images)
print("📷 Immagine originale:", img_url)

filename = img_url.split("/")[-1]
filepath = f"immagini_prodotto/{filename}"
selected_img.save(filepath)
print(f"✅ Immagine salvata come '{filepath}'")

# ========== ESTRATTO TESTO DALL'IMMAGINE ==========
try:
    raw_text = pytesseract.image_to_string(selected_img, lang='ita')
    testo_estratto = re.sub(r'[^a-zA-Z0-9àèéìòùÀÈÉÌÒÙ\s.,!?\'"]+', ' ', raw_text)
    testo_estratto = re.sub(r'\s+', ' ', testo_estratto).strip()
    if not testo_estratto:
        testo_estratto = "No readable text found on image"
    print("🔍 Testo estratto dall'immagine:", testo_estratto)
except Exception as e:
    print(f"⚠️ Errore OCR: {e}")
    testo_estratto = "No readable text found on image"

# ========== GENERA CAPTION CON GPT ==========
prompt = (
    f"You are a social media copywriter for a conscious fashion brand. "
    f"Generate a creative Instagram caption in English (max 250 characters) using this text found on a product image: \"{testo_estratto}\". "
    f"The brand promotes spiritual and mindset messages such as vulnerability, self-worth, integrity, presence, and boundaries. "
    f"Include emojis, a warm inspiring tone, and a call to action inviting followers to visit {sito_web}."
)

try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You write inspiring Instagram captions for a spiritual clothing brand."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.9,
        max_tokens=150
    )
    caption = response.choices[0].message.content.strip()
    if len(caption) > 250:
        caption = caption[:247] + "..."
except Exception as e:
    caption = (
        "🌿 Embrace growth and self-awareness through conscious fashion. Every design carries a message to uplift your spirit. "
        f"Discover more at {sito_web}. ✨ #MindfulStyle #SpiritualFashion"
    )
    print(f"⚠️ Errore GPT: {e}")

# ========== INVIA A ZAPIER ==========
print("\n📌 Caption per Instagram:")
print("=" * 50)
print(caption)

data = {
    "caption": caption,
    "image_url": img_url,
    "prompt": prompt
}

try:
    zap_response = requests.post(webhook_url, json=data)
    zap_response.raise_for_status()
    print("✅ Dati inviati con successo a Zapier!")
except Exception as e:
    print(f"❌ Errore nell'invio dei dati a Zapier: {e}")
