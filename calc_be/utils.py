import google.generativeai as genai
import json
import re
import ast
from PIL import Image
from math_noteess import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

def extract_list_from_gemini_response(text: str):
    cleaned = re.sub(r"```(?:json|python)?", "", text).strip()
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if match:
        raw_content = match.group(0)
        symbolic_keywords = [
            "ln", "log", "sin", "cos", "tan", "sec", "cot", "cosec",
            "√", "|", "π", "∞", "C", "∫", "∑", "Δ", "α", "β", "γ", "θ",
            "e", "^", "/", "-", "+", "*"
        ]
        def needs_quoting(value: str) -> bool:
            return (
                not value.replace('.', '', 1).isdigit() or
                any(sym in value for sym in symbolic_keywords)
            )
        def fix_result_field(match):
            result_val = match.group(1).strip()
            if result_val.startswith("'") or result_val.startswith('"'):
                return match.group(0)
            if needs_quoting(result_val):
                return f"'result': '{result_val}'"
            return match.group(0)
        fixed_content = re.sub(
            r"'result': ([^'{\[\]},\n]+)",
            fix_result_field,
            raw_content
        )
        try:
            parsed = json.loads(fixed_content.replace("'", '"'))
            print("✅ Parsed answers:", parsed)
            return parsed
        except Exception as e:
            print(f"❌ JSON parse failed: {e}")
            print("📄 Trying fallback using ast.literal_eval...")
            try:
                parsed = ast.literal_eval(raw_content)
                print("✅ Parsed with fallback:", parsed)
                return parsed
            except Exception as fallback_error:
                print(f"❌ Fallback parse failed: {fallback_error}")
                print("📄 Raw Gemini content (final):", raw_content)
    else:
        print("⚠️ No list found in Gemini response.")
    return []

def analyze_image(img: Image.Image, dict_of_vars: dict):
    model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    dict_of_vars_str = json.dumps(dict_of_vars, ensure_ascii=False)

    prompt = (
        f"You are given an image that contains a mathematical, physics, or civil engineering expression, problem, or drawing. "
        f"Your task is to analyze and SOLVE the problem with accurate reasoning. This can be a simple expression OR a multi-step complex problem.\n\n"
        f"⚠️ YOU MAY ENCOUNTER ANY OF THE FOLLOWING:\n"
        f"1. Simple expressions (e.g., 2 + 2, 3 * 4)\n"
        f"2. Complex math equations (nested operations, exponents, fractions, etc.)\n"
        f"3. Systems of equations (e.g., x^2 + 2x + 1 = 0, 2x + y = 10)\n"
        f"4. Variable assignments (e.g., x = 5, y = 10)\n"
        f"5. Physics-based word or graphical problems (motion, force, acceleration, energy, collisions, etc.)\n"
        f"6. Civil engineering problems (area, volume, stress, bending moment, etc.)\n"
        f"7. Graphical/visual representation problems involving interpretation\n"
        f"8. Conceptual problems (emotion, abstract interpretation, historical references)\n\n"
        f"👨‍🏫 YOU MUST:\n"
        f"- Solve using PEMDAS or scientific method as needed.\n"
        f"- Use **step-by-step reasoning** internally before producing final result.\n"
        f"- Use values from variable dictionary if any are present: {dict_of_vars_str}\n"
        f"- Include units like 'seconds', 'hours', 'm²', 'N·m', 'kg', etc. when applicable.\n"
        f"- Ensure multi-variable or multi-part problems return a list of results.\n"
        f"- Do not explain, only return a valid Python list of dicts as final answer.\n\n"
        f"📌 FORMAT RULES:\n"
        f"- Return ONLY a list of dictionaries.\n"
        f"- Each dictionary must contain:\n"
        f"  - 'expr': the original expression or statement from the image.\n"
        f"  - 'result': the final numerical or symbolic result.\n"
        f"  - Optional: 'unit' (e.g., 'hours', 'm/s²', 'm³')\n"
        f"  - Optional: 'assign': true if a variable is being assigned\n"
        f"  - Optional: 'var': the name of the variable being assigned\n\n"
        f"🧠 EXAMPLES:\n"
        f"• [{{'expr': '2 + 3 * 4', 'result': 14}}]\n"
        f"• [{{'expr': 'x^2 + 2x + 1 = 0', 'result': -1, 'assign': true, 'var': 'x'}}]\n"
        f"• [{{'expr': 'speed = 15 km/h, distance = 13 km => time = distance/speed', 'result': 0.8666666667, 'unit': 'hours'}}]\n"
        f"• [{{'expr': 'area = 0.5 * base * height = 0.5 * 10 * 4', 'result': 20.0, 'unit': 'm²'}}]\n"
        f"• [{{'expr': 'image shows patriotic unity through historical symbols', 'result': 'patriotism'}}]\n\n"
        f"🚫 DO NOT:\n"
        f"- Use markdown, backticks, or code formatting.\n"
        f"- Return anything other than a valid Python list of dictionaries.\n"
        f"- Leave unquoted keys or values (must be double quoted).\n"
        f"- Include explanation or commentary.\n\n"
        f"🎯 OUTPUT MUST BE COMPATIBLE with Python's `ast.literal_eval`.\n"
    )

    try:
        response = model.generate_content([prompt, img])
        text = response.text
        print("📤 Raw Gemini response:\n", text)
        answers = extract_list_from_gemini_response(text)
        for answer in answers:
            answer['assign'] = answer.get('assign', False)
        return answers
    except Exception as e:
        print(f"❌ Error in generating response from Gemini API: {e}")
        return []