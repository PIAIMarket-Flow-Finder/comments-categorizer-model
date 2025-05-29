import asyncio
import httpx
import json
from asyncio import Semaphore

# Limite de requêtes en parallèle
sem = Semaphore(20)

#Génération du prompt
def build_prompt(comment):
    return (
        "System: You label app-store comments by improvement theme. "
        "Return ONLY the category number (1-6), nothing else.\n\n"
        "User comment:\n"
        f"{comment['content']}\n\n"
        "Categories:\n"
        "1 Bugs / technical issues\n"
        "2 Requested features\n"
        "3 Design & UX\n"
        "4 Performance & speed\n"
        "5 Login / account\n"
        "6 Other\n\n"
        "Answer with one digit (1-6)."
    )


# Appel Ollama
async def annotate_comment(comment):
    prompt = build_prompt(comment)
    async with sem:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(
                    "https://ollama.kube.isc.heia-fr.ch/api/generate",
                    json={"model": "qwen2.5:32b-instruct", "prompt": prompt, "stream": False},
                    timeout=60.0,
                )
                print(f"📥 Requête envoyée, code retour : {resp.status_code}")
                response = resp.json()["response"].strip()
                comment["category"] = response  # Ajoute la réponse directement
            except Exception as e:
                print(f"❌ Exception Python : {e}")
                if resp is not None:
                    print(f"📨 Statut HTTP : {resp.status_code}")
                    print(f"📦 Contenu : {resp.text}")
                comment["relevance_score"] = "error"
    return comment



async def main():
    with open("data/useful_comments.json", encoding="utf-8") as f:
        comments = json.load(f)
        #comments = comments[:100]

    tasks = [annotate_comment(c) for c in comments]  # limite optionnelle
    results = await asyncio.gather(*tasks)

    with open("data/categorized_comments.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(results)} commentaires annotés enregistrés dans categorized_comments.json")

asyncio.run(main())