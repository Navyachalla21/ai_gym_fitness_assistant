import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", google_api_key=api_key)

# Simple lexicon-based sentiment detector (lightweight, no extra dependency)
_POSITIVE_WORDS = {"good", "great", "happy", "motivated", "strong", "energized", "excited", "proud"}
_NEGATIVE_WORDS = {"tired", "sad", "lazy", "unmotivated", "stressed", "exhausted", "sore", "frustrated", "bad"}


def detect_sentiment(message: str) -> str:
    """Basic keyword-based sentiment detection from user's message."""
    words = set(message.lower().split())
    pos = len(words & _POSITIVE_WORDS)
    neg = len(words & _NEGATIVE_WORDS)
    if neg > pos:
        return "negative"
    elif pos > neg:
        return "positive"
    return "neutral"


buddy_prompt = PromptTemplate(
    input_variables=["message", "sentiment"],
    template="""You are a friendly, motivating AI Gym Buddy — supportive like a workout partner,
not clinical. The user's detected mood is: {sentiment}.

If mood is negative: be encouraging and empathetic, suggest a small achievable step.
If mood is positive: match their energy and reinforce the momentum.
If mood is neutral: be warm and ask an engaging follow-up about their fitness goals.

User's message: {message}

Respond in 2-4 sentences, casual and encouraging tone."""
)


def chat_with_buddy(message: str) -> dict:
    """Generates a motivational, mood-aware response to the user's message."""
    sentiment = detect_sentiment(message)
    prompt = buddy_prompt.format(message=message, sentiment=sentiment)
    response = llm.invoke(prompt)

    if isinstance(response.content, list):
        reply = "".join(block.get("text", "") for block in response.content if isinstance(block, dict))
    else:
        reply = response.content

    return {"sentiment": sentiment, "reply": reply}