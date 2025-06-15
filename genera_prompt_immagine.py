import requests
from bs4 import BeautifulSoup
import random
import os
from openai import OpenAI

# ========== CONFIGURAZIONE ==========
URL = "https://www.awakenedsoul.ch/shop"
headers = {'User-Agent': 'Mozilla/5.0'}

# Prendi la API Key OpenAI da variabile d'ambiente
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("La variabile d'ambiente OPENAI_API_KEY non è impostata.")

webhook_url = "https://hooks.zapier.com/hooks/catch/23181653/2vr280p/"
sito_web = "www.awakenedsoul.ch"

# Crea client OpenAI
client = OpenAI(api_key=openai_api_key)

# ========== SCARICA IMMAGINE ==========
response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, 'html.parser')
images = soup.find_all('img')
product_images = [img['src'] for img in images if 'wixstatic' in img.get('src', '')]

if product_images:
    img_url = random.choice(product_images)
    if "/v1/" in img_url:
        img_url = img_url.split("/v1/")[0]

    print("📷 Immagine originale:", img_url)

    os.makedirs("immagini_prodotto", exist_ok=True)
    filename = img_url.split("/")[-1]
    filepath = f"immagini_prodotto/{filename}"
    with open(filepath, 'wb') as f:
        f.write(requests.get(img_url).content)
    print(f"✅ Immagine salvata come '{filepath}'")

    # ========== GENERA TESTO GPT ==========
    keywords = filename.replace("_", " ").replace("-", " ").lower()

    prompt = (
        f"You are a social media copywriter for a conscious fashion brand. "
        f"Generate a creative and engaging Instagram caption in English (max 250 characters) for a product with these keywords: '{keywords}'. "
        f"The brand sells clothing with spiritual and mindset messages. Include relevant emojis, use a warm and inspiring tone, "
        f"and add a clear call-to-action inviting followers to visit {sito_web} to shop. "
        f"Consider keywords like vulnerability, self-esteem, setting boundaries, brotherhood, integrity, and presence."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You write inspiring captions for spiritual clothing brands."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=150
        )
        caption = response.choices[0].message.content.strip()
    except Exception as e:
        caption = (
            "🌿 Growth is a continuous journey. Every day, we have the opportunity to challenge ourselves, "
            "evolve, and become the best version of who we are. With each step we take, we spread awareness, "
            "and wearing our pieces with mindful messages is our way of reminding ourselves of this mission. "
            "Be the change you want to see in the world, with integrity, vulnerability, and presence. 💫"
            f" Explore our collection and let your style speak for you at {sito_web}. ✨\n\n"
            "#GrowthMindset #ConsciousFashion #BeTheChange #SelfAwareness #MindfulStyle #Integrity #Vulnerability #SpreadAwareness #FashionWithPurpose"
        )
        print(f"⚠️ Errore nella generazione GPT: {e}")

    print("\n📌 Caption per Instagram:")
    print("="*50)
    print(caption)

    # ========== INVIA A ZAPIER ==========
    data = {
        "caption": caption,
        "media": img_url,  # qui la chiave corretta per Zapier/Instagram
        "prompt": prompt
    }

    zap_response = requests.post(webhook_url, json=data)
    if zap_response.status_code == 200:
        print("✅ Dati inviati con successo a Zapier!")
    else:
        print(f"❌ Errore nell'invio dei dati a Zapier: {zap_response.status_code}")

else:
    print("⚠️ Nessuna immagine trovata.")
