from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import os
import json
import re

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

class AnalyzeRequest(BaseModel):
    url: str
    groq_key: str = ""

@app.get("/")
def root():
    return {"status": "ClipBook Server Running"}

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    api_key = req.groq_key or GROQ_API_KEY
    if not api_key:
        raise HTTPException(status_code=400, detail="Missing Groq API key")

    url = req.url
    platform = "Instagram" if "instagram" in url else "TikTok" if "tiktok" in url else "YouTube" if "youtube" in url or "youtu.be" in url else "Social Media"

    prompt = f"""נתחי את הכתובת הזו של סרטון מ-{platform}: {url}
החזירי JSON בעברית בלבד:
מתכון: {{"aiType":"recipe","title":"...","category":"ארוחות ערב","emoji":"🍳","creator":"@x","ingredients":[{{"n":"מצרך","a":"כמות","h":true}}],"equipment":["כלי"],"steps":[{{"t":"0:30","s":"שלב"}}],"tips":["טיפ"],"subs":[]}}
אימון: {{"aiType":"workout","title":"...","category":"כושר","emoji":"💪","creator":"@x","equipment":["מזרן"],"exercises":[{{"n":"תרגיל","sets":"3","reps":"15","t":"0:30","m":"שריר"}}],"tips":["טיפ"]}}
טיול: {{"aiType":"travel","title":"...","emoji":"✈️","creator":"@x","location":"עיר, מדינה","status":"רוצה לבקר","notes":"תיאור"}}
סרט: {{"aiType":"movie","title":"...","emoji":"🎬","creator":null,"genre":"דרמה","status":"רוצה לצפות","notes":"תיאור"}}
ספר: {{"aiType":"book","title":"...","emoji":"📚","creator":"מחבר","genre":"עצמי","status":"רוצה לקרוא","notes":"תיאור"}}"""

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.2, "max_tokens": 1000}
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Groq API error")

    data = resp.json()
    text = data["choices"][0]["message"]["content"].strip()
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        raise HTTPException(status_code=500, detail="No JSON")
    return json.loads(match.group(0))
