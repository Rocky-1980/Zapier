import openai
import os

# Prende la chiave API da una variabile d'ambiente
openai.api_key = os.getenv("OPENAI_API_KEY")

# Prompt di esempio: puoi personalizzarlo
def genera_prompt(categoria="ispirazione", stile="minimal", emozione="positiva"):
    prompt = f"Genera un prompt per un'immagine AI in stile {stile}, con tema {categoria}, che trasmetta un'emozione {emozione}."
    
    try:
        risposta = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Sei un creativo che scrive prompt per generare immagini AI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=100
        )
        output = risposta['choices'][0]['message']['content'].strip()
        return output
    
    except Exception as e:
        print("Errore nella generazione del prompt:", e)
        return None

# Esecuzione di esempio
if __name__ == "__main__":
    prompt = genera_prompt()
    if prompt:
        print("Prompt generato:")
        print(prompt)
    else:
        print("Nessun prompt generato.")
