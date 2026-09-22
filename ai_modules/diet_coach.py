import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", google_api_key=api_key)


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculates BMI: weight(kg) / height(m)^2"""
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def get_bmi_category(bmi: float) -> str:
    """Classifies BMI into standard WHO categories."""
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal weight"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


diet_prompt = PromptTemplate(
    input_variables=["bmi", "category", "goal", "preferences"],
    template="""You are an AI Dietician and Calorie Coach. Based on the user's details below,
provide:
1. A brief, encouraging assessment of their current status
2. A simple one-day sample meal plan (breakfast, lunch, dinner, 1 snack) matching their goal and preferences
3. A short grocery list for that meal plan
4. An estimated daily calorie target

User details:
- BMI: {bmi} ({category})
- Goal: {goal}
- Dietary preferences: {preferences}

Keep the response practical and concise. Do not give medical diagnoses — recommend consulting
a doctor or nutritionist for personalized medical advice."""
)


def generate_diet_plan(weight_kg: float, height_cm: float, goal: str, preferences: str) -> dict:
    """
    Calculates BMI and generates a personalized diet plan using the LLM.
    Returns both the raw BMI data and the AI-generated plan text.
    """
    bmi = calculate_bmi(weight_kg, height_cm)
    category = get_bmi_category(bmi)

    prompt = diet_prompt.format(bmi=bmi, category=category, goal=goal, preferences=preferences)
    response = llm.invoke(prompt)

    # Handle both plain string and list-of-blocks response formats (as we saw before)
    if isinstance(response.content, list):
        plan_text = "".join(block.get("text", "") for block in response.content if isinstance(block, dict))
    else:
        plan_text = response.content

    return {
        "bmi": bmi,
        "category": category,
        "plan": plan_text
    }

