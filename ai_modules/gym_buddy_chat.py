import os
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

try:
    from ai_modules import storage
except ImportError:  # pragma: no cover
    import storage

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", google_api_key=api_key)

# Lightweight lexicon-based sentiment detector (no extra dependency).
_POSITIVE_WORDS = {
    "good", "great", "happy", "motivated", "strong", "energized", "energised", "excited", "proud",
    "awesome", "amazing", "better", "confident", "fantastic", "pumped", "ready", "love", "fit",
}
_NEGATIVE_WORDS = {
    "tired", "sad", "lazy", "unmotivated", "stressed", "exhausted", "sore", "frustrated", "bad",
    "anxious", "worried", "weak", "down", "depressed", "overwhelmed", "hopeless", "hate", "pain",
}
# A negator directly before a sentiment word flips it ("not good" -> negative).
_NEGATORS = {"not", "no", "never", "hardly", "cant", "cannot", "wont", "dont", "isnt", "arent",
             "wasnt", "didnt", "doesnt", "barely"}

# Words allowed between a negator and the sentiment word ("don't FEEL tired", "not VERY good").
_FILLERS = {"feel", "feeling", "felt", "very", "so", "really", "too", "that", "quite", "been", "being",
            "all", "at", "particularly", "especially", "even"}

_HISTORY_TURNS = 5  # how many previous messages the buddy remembers


def detect_sentiment(message: str) -> str:
    """Keyword sentiment detection with simple negation handling."""
    # strip apostrophes so "don't" -> "dont", then split into plain words
    words = re.findall(r"[a-z]+", message.lower().replace("'", "").replace("’", ""))
    pos = neg = 0
    for i, word in enumerate(words):
        if word not in _POSITIVE_WORDS and word not in _NEGATIVE_WORDS:
            continue
        negated = (i > 0 and words[i - 1] in _NEGATORS) or \
                  (i > 1 and words[i - 1] in _FILLERS and words[i - 2] in _NEGATORS)
        is_positive = word in _POSITIVE_WORDS
        if is_positive != negated:   # positive and not negated, or negative word that was negated
            pos += 1
        else:
            neg += 1
    if neg > pos:
        return "negative"
    if pos > neg:
        return "positive"
    return "neutral"


buddy_prompt = PromptTemplate(
    input_variables=["history", "message", "sentiment"],
    template="""You are a friendly, motivating AI Gym Buddy — supportive like a workout partner,
not clinical. The user's detected mood is: {sentiment}.

If mood is negative: be encouraging and empathetic, suggest a small achievable step.
If mood is positive: match their energy and reinforce the momentum.
If mood is neutral: be warm and ask an engaging follow-up about their fitness goals.

Recent conversation (oldest first, may be empty):
{history}

User's new message: {message}

Respond in 2-4 sentences, casual and encouraging tone. Use the recent conversation for
context so you don't repeat yourself or forget what the user already told you."""
)


def _format_history(user_id: str) -> str:
    rows = storage.get_chats(user_id=user_id, limit=_HISTORY_TURNS * 2)[-_HISTORY_TURNS * 2:]
    if not rows:
        return "(no earlier messages)"
    return "\n".join(f"{'User' if r['role'] == 'user' else 'Buddy'}: {r['message']}" for r in rows)


def chat_with_buddy(message: str, user_id: str = "default") -> dict:
    """Generates a motivational, mood-aware response that remembers recent turns."""
    sentiment = detect_sentiment(message)
    history = _format_history(user_id)          # read BEFORE saving the new message
    prompt = buddy_prompt.format(history=history, message=message, sentiment=sentiment)
    response = llm.invoke(prompt)

    if isinstance(response.content, list):
        reply = "".join(block.get("text", "") for block in response.content if isinstance(block, dict))
    else:
        reply = response.content

    storage.log_chat("user", message, sentiment, user_id=user_id)
    storage.log_chat("buddy", reply, None, user_id=user_id)
    return {"sentiment": sentiment, "reply": reply}


_SCORE = {"positive": 1, "neutral": 0, "negative": -1}


def get_mood_trend(user_id: str = "default", limit: int = 50) -> dict:
    """Emotional-state history: one point per user message, plus an overall summary."""
    rows = [r for r in storage.get_chats(user_id=user_id) if r["role"] == "user"][-limit:]
    points = [{"time": r["created_at"], "sentiment": r["sentiment"],
               "score": _SCORE.get(r["sentiment"], 0)} for r in rows]
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    for p in points:
        counts[p["sentiment"]] = counts.get(p["sentiment"], 0) + 1
    recent = points[-5:]
    avg_recent = round(sum(p["score"] for p in recent) / len(recent), 2) if recent else 0
    overall = "Positive" if avg_recent > 0.2 else "Low" if avg_recent < -0.2 else "Balanced"
    return {"user_id": user_id, "messages": len(points), "counts": counts,
            "recent_mood": overall if points else "No data", "points": points}
