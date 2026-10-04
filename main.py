import ast
import base64
import operator as op
from pathlib import Path

import streamlit as st

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Hello Kitty Calculator", page_icon="🎀", layout="centered")

# ---------------- SAFE CALCULATOR ----------------
OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Mod: op.mod,
    ast.USub: op.neg,
}


def calculate(expression):
    """Safely evaluate a basic arithmetic expression."""

    def solve(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](solve(node.left), solve(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](solve(node.operand))
        raise ValueError("Invalid expression")

    return solve(ast.parse(expression, mode="eval").body)


def fmt(number):
    number = round(number, 10)
    return str(int(number)) if float(number).is_integer() else str(number)


# ---------------- SESSION STATE ----------------
st.session_state.setdefault("display", "0")
st.session_state.setdefault("expression", "")
st.session_state.setdefault("new_number", True)

# ---------------- CSS ----------------
# NOTE: HTML passed to st.markdown must NOT be indented by 4+ spaces,
# otherwise Markdown treats it as a code block (the dark boxes in your screenshot).
CSS = """
<style>
.stApp { background: linear-gradient(135deg, #fff5f8, #ffdce8); }
#MainMenu, footer, header { visibility: hidden; }
.block-container { max-width: 440px !important; padding-top: 1.5rem !important; }

/* The calculator body (st.container(key="calc") -> class st-key-calc) */
.st-key-calc {
    padding: 22px;
    background: linear-gradient(145deg, #fffafa, #ffe6ef);
    border: 3px solid #f7a5c2;
    border-radius: 30px;
    box-shadow: 0 15px 35px rgba(220,90,130,0.25), inset 0 0 20px rgba(255,255,255,0.8);
    gap: 0.6rem;
}

.kitty-header { display:flex; align-items:center; justify-content:space-between; }
.kitty-title { color:#ed6f9b; font-size:27px; font-weight:700; font-family:cursive; }
.heart { color:#f28aad; font-size:25px; }

.display {
    background: rgba(255,255,255,0.55);
    border: 2px solid #f6a8c4;
    border-radius: 23px;
    padding: 12px 20px;
    text-align: right;
    box-shadow: inset 0 2px 10px rgba(240,120,160,0.08);
}
.expression { color:#9b7180; font-size:20px; min-height:28px; overflow:hidden; }
.result { color:#713f4e; font-size:42px; font-weight:600; line-height:48px; overflow:hidden; }

/* Buttons */
.st-key-calc div.stButton > button {
    width: 100%;
    height: 62px;
    border-radius: 22px;
    border: none;
    background: #fffafa;
    box-shadow: 0 5px 10px rgba(200,100,130,0.15), inset 0 1px 3px white;
    transition: all 0.12s ease;
}
.st-key-calc div.stButton > button p {
    color: #ed719b;
    font-size: 24px;
    font-weight: 600;
    margin: 0;
}
.st-key-calc div.stButton > button:hover { transform: translateY(-2px); background:#fff; }
.st-key-calc div.stButton > button:active { transform: scale(0.95); }

/* Pink operator buttons (keys starting with "op_") */
[class*="st-key-op_"] div.stButton > button {
    background: linear-gradient(145deg, #f98eb4, #ef6e9e) !important;
    box-shadow: 0 5px 12px rgba(230,90,130,0.25) !important;
}
[class*="st-key-op_"] div.stButton > button p { color: white !important; }

.kitty-footer { text-align:center; color:#f28aad; font-size:20px; letter-spacing:8px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------- LOGIC ----------------
OPS = ["+", "-", "×", "÷"]


def press_button(button):
    s = st.session_state
    current = s.display

    if current in ("Error", "Can't divide by 0") and button != "AC":
        current = "0"
        s.display = "0"
        s.new_number = True

    if button == "AC":
        s.display, s.expression, s.new_number = "0", "", True

    elif button == "⌫":
        if s.new_number:
            return
        s.display = current[:-1] if len(current) > 1 and current != "-0" else "0"
        if s.display in ("", "-"):
            s.display = "0"

    elif button == "+/-":
        if current != "0":
            s.display = current[1:] if current.startswith("-") else "-" + current

    elif button == "%":
        try:
            s.display = fmt(float(current) / 100)
            s.new_number = True
        except ValueError:
            s.display, s.new_number = "Error", True

    elif button in OPS:
        if s.expression and s.new_number:
            # Replace the previous operator
            s.expression = s.expression[:-1] + button
        else:
            s.expression += current + button
        s.new_number = True

    elif button == "=":
        if not s.expression:
            return
        try:
            full = (s.expression + current).replace("×", "*").replace("÷", "/")
            s.display = fmt(calculate(full))
        except ZeroDivisionError:
            s.display = "Can't divide by 0"
        except Exception:
            s.display = "Error"
        s.expression = ""
        s.new_number = True

    elif button == ".":
        if s.new_number:
            s.display, s.new_number = "0.", False
        elif "." not in current:
            s.display += "."

    else:  # digits
        if s.new_number or current == "0":
            s.display, s.new_number = button, False
        else:
            s.display += button


# ---------------- HEADER IMAGE ----------------
def kitty_image_html():
    path = Path(__file__).parent / "hello_kitty.png"
    if path.exists():
        b64 = base64.b64encode(path.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}" style="width:70px;border-radius:14px;">'
    return '<span style="font-size:48px;">🎀</span>'


# ---------------- UI ----------------
buttons = [
    ["AC", "+/-", "%", "⌫"],
    ["7", "8", "9", "÷"],
    ["4", "5", "6", "×"],
    ["1", "2", "3", "-"],
    ["0", ".", "+", "="],
]
PINK = {"AC", "⌫", "÷", "×", "-", "+", "="}

with st.container(key="calc"):
    st.markdown(
        f"""<div class="kitty-header">
<div>{kitty_image_html()}</div>
<div class="kitty-title">Hello Kitty</div>
<div class="heart">♥</div>
</div>""",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""<div class="display">
<div class="expression">{st.session_state.expression or "&nbsp;"}</div>
<div class="result">{st.session_state.display}</div>
</div>""",
        unsafe_allow_html=True,
    )

    for r, row in enumerate(buttons):
        cols = st.columns(4, gap="small")
        for c, label in enumerate(row):
            prefix = "op" if label in PINK else "num"
            cols[c].button(
                label,
                key=f"{prefix}_{r}_{c}",
                use_container_width=True,
                on_click=press_button,
                args=(label,),
            )

    st.markdown('<div class="kitty-footer">🎀 ─── ♥ ─── 🎀</div>', unsafe_allow_html=True)