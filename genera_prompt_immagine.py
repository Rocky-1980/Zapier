import requests
from bs4 import BeautifulSoup
import random
import os
import openai
from PIL import Image
from io import BytesIO

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
            filtered_images.append(img_url)
    except Exception:
        continue

print(f"✅ Immagini filtrate per Instagram: {len(filtered_images)}")

# ========== SELEZIONE IMMAGINE ==========
if filtered_images:
    img_url = random.choice(filtered_images)
    print("📷 Immagine selezionata:", img_url)
else:
    print("⚠️ Nessuna immagine valida trovata. Non invio nulla a Zapier.")
    exit(0)

# ========== PROMPT E CAPTION GPT-4o ==========
prompt = (
    "You are an exceptionally creative and original Instagram caption copywriter for a spiritual clothing brand. "
    "For each post, write a *unique* and *fresh* caption (max 250 characters) inspired by values like vulnerability, self-worth, integrity, brotherhood, presence, and boundaries. "
    "Every caption must start with a DIFFERENT phrase or style, avoiding formulas like 'Embrace your...'. "
    "Surprise the reader: use poetic, metaphoric, evocative, or even provocative openings, rhetorical questions, quotes, calls to action, or direct messages. "
    f"Always include relevant emojis and invite followers to visit {SITO_WEB}. Do NOT repeat the same structure in multiple captions."
)

try:
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an Instagram caption copywriter for a spiritual clothing brand. Every caption should be fresh and not repetitive."},
            {"role": "user", "content": prompt}
        ],
        temperature=1.0,    # Più alta = caption più varie e creative
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
