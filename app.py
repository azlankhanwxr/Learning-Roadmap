"""AI Learning Roadmap Generator

Enter a field, your skill level and how long you have to learn, and the app
asks a Gemini Flash model to build a phase-by-phase learning roadmap.
"""

import json
import os
import re

import streamlit as st
from google import genai
from google.genai import types

DEFAULT_MODEL = "gemini-2.5-flash"
LEVELS = ["Beginner", "Intermediate", "Advanced"]
DURATION_UNITS = ["Weeks", "Months"]
MAX_FIELD_LENGTH = 100


# --------------------------------------------------------------------------
# Config helpers
# --------------------------------------------------------------------------
def get_secret(name: str, default: str = "") -> str:
    """Read a value from Streamlit secrets, then environment variables."""
    try:
        value = st.secrets.get(name)  # raises if no secrets.toml exists
        if value:
            return str(value)
    except Exception:
        pass
    return os.environ.get(name, default)


# --------------------------------------------------------------------------
# Prompt + model call
# --------------------------------------------------------------------------
def build_prompt(field: str, level: str, duration: int, unit: str, hours_per_week: int) -> str:
    return f"""You are an expert career and learning coach.
Create a practical, realistic learning roadmap.

Field / domain: {field}
Current skill level: {level}
Total time available: {duration} {unit.lower()}
Study time per week: {hours_per_week} hours

Rules:
- Fit the whole roadmap inside the total time. Phase durations must add up to roughly that time.
- Start from the {level.lower()} level; do not repeat basics for higher levels.
- Use 3 to 6 phases, in logical order.
- Each phase needs 3 to 6 specific topics (concrete skills or concepts, not vague words).
- Suggest 2 to 4 learning resources per phase. Give the resource NAME and TYPE only
  (e.g. "Official documentation", "freeCodeCamp course"). Do NOT invent URLs.
- Each phase ends with one hands-on project and one measurable milestone.
- Add 3 to 5 short general tips at the end.

Respond with ONLY valid JSON in exactly this shape:
{{
  "title": "string",
  "summary": "2-3 sentence overview",
  "phases": [
    {{
      "name": "string",
      "duration": "e.g. 2 weeks",
      "goal": "string",
      "topics": ["string"],
      "resources": [{{"title": "string", "type": "string"}}],
      "project": "string",
      "milestone": "string"
    }}
  ],
  "tips": ["string"]
}}"""


def parse_roadmap(text: str) -> dict:
    """Parse and validate the model's JSON. Raises ValueError if unusable."""
    cleaned = (text or "").strip()
    # Strip markdown code fences if the model added them.
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Model response was not a JSON object.")
    phases = data.get("phases")
    if not isinstance(phases, list) or not phases:
        raise ValueError("Model response had no phases.")

    # Normalise so rendering never breaks on missing keys.
    roadmap = {
        "title": str(data.get("title") or "Your Learning Roadmap"),
        "summary": str(data.get("summary") or ""),
        "phases": [],
        "tips": [str(t) for t in data.get("tips", []) if t],
    }
    for p in phases:
        if not isinstance(p, dict):
            continue
        resources = []
        for r in p.get("resources", []) or []:
            if isinstance(r, dict):
                resources.append(
                    {"title": str(r.get("title", "")), "type": str(r.get("type", ""))}
                )
            elif r:
                resources.append({"title": str(r), "type": ""})
        roadmap["phases"].append(
            {
                "name": str(p.get("name") or "Phase"),
                "duration": str(p.get("duration") or ""),
                "goal": str(p.get("goal") or ""),
                "topics": [str(t) for t in p.get("topics", []) or [] if t],
                "resources": resources,
                "project": str(p.get("project") or ""),
                "milestone": str(p.get("milestone") or ""),
            }
        )
    if not roadmap["phases"]:
        raise ValueError("Model response had no usable phases.")
    return roadmap


def generate_roadmap(api_key: str, model: str, prompt: str, retries: int = 1) -> dict:
    """Call Gemini and return a validated roadmap dict."""
    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        temperature=0.4,
    )
    last_error = None
    for _ in range(retries + 1):
        response = client.models.generate_content(
            model=model, contents=prompt, config=config
        )
        try:
            return parse_roadmap(response.text)
        except ValueError as exc:  # bad JSON -> try once more
            last_error = exc
    raise last_error


def roadmap_to_markdown(roadmap: dict) -> str:
    lines = [f"# {roadmap['title']}", "", roadmap["summary"], ""]
    for i, p in enumerate(roadmap["phases"], 1):
        header = f"## Phase {i}: {p['name']}"
        if p["duration"]:
            header += f" ({p['duration']})"
        lines += [header, ""]
        if p["goal"]:
            lines += [f"**Goal:** {p['goal']}", ""]
        if p["topics"]:
            lines += ["**Topics**"] + [f"- {t}" for t in p["topics"]] + [""]
        if p["resources"]:
            lines += ["**Resources**"]
            for r in p["resources"]:
                lines.append(f"- {r['title']}" + (f" ({r['type']})" if r["type"] else ""))
            lines.append("")
        if p["project"]:
            lines += [f"**Project:** {p['project']}", ""]
        if p["milestone"]:
            lines += [f"**Milestone:** {p['milestone']}", ""]
    if roadmap["tips"]:
        lines += ["## Tips", ""] + [f"- {t}" for t in roadmap["tips"]]
    return "\n".join(lines).strip() + "\n"


# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------
def render_roadmap(roadmap: dict) -> None:
    st.header(roadmap["title"])
    if roadmap["summary"]:
        st.write(roadmap["summary"])

    for i, p in enumerate(roadmap["phases"], 1):
        label = f"Phase {i}: {p['name']}" + (f"  ·  {p['duration']}" if p["duration"] else "")
        with st.expander(label, expanded=(i == 1)):
            if p["goal"]:
                st.markdown(f"**Goal:** {p['goal']}")
            if p["topics"]:
                st.markdown("**Topics**")
                st.markdown("\n".join(f"- {t}" for t in p["topics"]))
            if p["resources"]:
                st.markdown("**Resources**")
                st.markdown(
                    "\n".join(
                        f"- {r['title']}" + (f" *({r['type']})*" if r["type"] else "")
                        for r in p["resources"]
                    )
                )
            if p["project"]:
                st.markdown(f"**Project:** {p['project']}")
            if p["milestone"]:
                st.markdown(f"**Milestone:** {p['milestone']}")

    if roadmap["tips"]:
        st.subheader("Tips")
        st.markdown("\n".join(f"- {t}" for t in roadmap["tips"]))


def main() -> None:
    st.set_page_config(page_title="AI Learning Roadmap Generator", page_icon="🗺️")
    st.title("🗺️ AI Learning Roadmap Generator")
    st.caption("Tell me what you want to learn and I'll build a step-by-step plan.")

    api_key = get_secret("GEMINI_API_KEY")
    model = get_secret("GEMINI_MODEL", DEFAULT_MODEL)

    with st.sidebar:
        st.subheader("Settings")
        if not api_key:
            api_key = st.text_input(
                "Gemini API key", type="password",
                help="Get a free key at https://aistudio.google.com/apikey",
            ).strip()
        else:
            st.success("API key loaded")
        model = st.text_input("Model", value=model)

    with st.form("roadmap_form"):
        field = st.text_input(
            "Field / domain",
            placeholder="e.g. Data Science, Web Development, Cybersecurity",
            max_chars=MAX_FIELD_LENGTH,
        )
        level = st.selectbox("Your skill level", LEVELS)
        col1, col2 = st.columns(2)
        duration = col1.number_input("Time to learn", min_value=1, max_value=60, value=3, step=1)
        unit = col2.selectbox("Unit", DURATION_UNITS, index=1)
        hours = st.slider("Hours you can study per week", 1, 40, 8)
        submitted = st.form_submit_button("Generate roadmap", type="primary")

    if submitted:
        if not field.strip():
            st.warning("Please enter a field or domain.")
        elif not api_key:
            st.warning("Please add your Gemini API key in the sidebar.")
        else:
            prompt = build_prompt(field.strip(), level, int(duration), unit, int(hours))
            try:
                with st.spinner("Building your roadmap..."):
                    st.session_state["roadmap"] = generate_roadmap(api_key, model.strip(), prompt)
            except Exception as exc:
                st.session_state.pop("roadmap", None)
                st.error(f"Could not generate the roadmap: {exc}")

    # Stored in session_state so the roadmap survives reruns (e.g. download click).
    roadmap = st.session_state.get("roadmap")
    if roadmap:
        render_roadmap(roadmap)
        st.download_button(
            "Download as Markdown",
            data=roadmap_to_markdown(roadmap),
            file_name="learning_roadmap.md",
            mime="text/markdown",
        )


if __name__ == "__main__":
    main()
