import random
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class InputData(BaseModel):
    client_id: str
    website_url: str

def random_score(min_val, max_val):
    return random.randint(min_val, max_val)

@app.post("/api/run_qa_test")
async def run_qa_test(data: InputData):
    url = data.website_url

    # Simulate real test delay
    import time
    time.sleep(random.randint(2, 4))

    perf = random_score(40, 95)
    seo = random_score(60, 100)
    sec = random_score(70, 98)
    mob = random_score(50, 99)
    link = random_score(80, 100)
    health = int((perf * 0.25 + seo * 0.2 + sec * 0.2 + mob * 0.15 + link * 0.2))

    issues = []
    if perf < 70: issues.extend(["Slow loading", "Large images"])
    if seo < 85: issues.append("Missing meta tags")

    return {
        "id": f"report_{int(time.time())}",
        "websiteUrl": url,
        "healthScore": health,
        "summary": {"performance": perf, "seo": seo, "security": sec, "mobile": mob, "links": link},
        "issuesFound": issues,
        "details": {"performance": {"score": perf}, "seo": {"score": seo}},
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health(): return {"status": "ok"}
