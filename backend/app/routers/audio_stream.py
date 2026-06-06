from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
from groq import Groq
import os
from dotenv import load_dotenv
import json

load_dotenv()

router = APIRouter()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


async def ai_stream_generator():
    try:
        # 🔥 Load resume
        try:
            with open("latest_resume.txt", "r", encoding="utf-8") as f:
                resume_text = f.read()
        except:
            yield "No resume uploaded yet.\n"
            return

        # 🔥 Load score (single source of truth)
        try:
            with open("latest_score.json", "r") as f:
                score_data = json.load(f)
                score = score_data.get("score", "N/A")
                score_reason = score_data.get("score_reason", "")
        except:
            score = "N/A"
            score_reason = ""

        # 🔥 FINAL PROMPT (NO RE-SCORING)
        prompt = f"""
You are an ATS resume reviewer.

IMPORTANT:
The ATS score is already calculated.

Score: {score}/100  
Reason: {score_reason}

Explain this score and provide detailed analysis.

Format:

📊 Resume Analysis

🔹 ATS Score: {score}/100
🔹 Reason: {score_reason}

🔹 Structure Issues:
- ...

🔹 Formatting Problems:
- ...

🔹 Content Gaps:
- ...

🔹 Improvements:
- ...

🔹 Improved Summary:
...

Resume:
{resume_text[:2000]}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )

        full_text = response.choices[0].message.content

        # 🔥 STREAM CLEANLY
        for line in full_text.split("\n"):
            yield line + "\n"
            await asyncio.sleep(0.05)

    except Exception as e:
        yield f"[Error: {str(e)}]\n"


@router.get("/stream-ai")
async def stream_ai():
    return StreamingResponse(
        ai_stream_generator(),
        media_type="text/plain"
    )