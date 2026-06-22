import os
import re
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage
from schemas import State, GlobalImagePlan
from llm import llm


# Helpers 

def safe_slug(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"


#  Node 1: Merge all sections into one markdown

def merge_content(state: State) -> dict:
    plan = state["plan"]
    if plan is None:
        raise ValueError("merge_content called without a plan.")

    ordered = [md for _, md in sorted(state["sections"], key=lambda x: x[0])]
    body = "\n\n".join(ordered).strip()

    # Add sources section at the bottom if evidence exists
    evidence = state.get("evidence", [])
    sources_section = ""
    if evidence:
        sources_lines = "\n".join(
            f"- [{e.title}]({e.url}){' — ' + e.published_at if e.published_at else ''}"
            for e in evidence
            if e.url
        )
        sources_section = f"\n\n---\n\n## 📚 Sources\n\n{sources_lines}"

    merged_md = f"# {plan.blog_title}\n\n{body}{sources_section}\n"
    return {"merged_md": merged_md}


# Node 2: Decide where images go 

DECIDE_IMAGES_SYSTEM = """You are an expert technical editor.
Decide if images are needed for this blog.

Rules:
- Max 3 images total.
- Each image must visually enhance the blog content.
- Insert placeholders exactly: [[IMAGE_1]], [[IMAGE_2]], [[IMAGE_3]].
- Place each placeholder on its own line, right after the paragraph it illustrates.
- If no images needed: md_with_placeholders must equal input markdown and images=[].
- Write detailed, photorealistic image generation prompts (50+ words each).
- Prompts must request: photorealistic, high quality, 4K, professional photography style.
- NO diagrams, NO illustrations, NO infographics, NO cartoon style.
- filename field must contain ONLY the filename like "fort.jpg", never "images/fort.jpg".
Return strictly GlobalImagePlan schema.
"""

def decide_images(state: State) -> dict:
    planner = llm.with_structured_output(GlobalImagePlan)
    merged_md = state["merged_md"]
    plan = state["plan"]

    image_plan = planner.invoke([
        SystemMessage(content=DECIDE_IMAGES_SYSTEM),
        HumanMessage(content=(
            f"Blog kind: {plan.blog_kind}\n"
            f"Topic: {state['topic']}\n\n"
            "Insert placeholders where images would help understanding.\n\n"
            f"{merged_md}"
        )),
    ])

    return {
        "md_with_placeholders": image_plan.md_with_placeholders,
        "image_specs": [img.model_dump() for img in image_plan.images],
    }


# Node 3: Generate images via OpenAI and place into markdown

def _openai_generate_image_bytes(prompt: str) -> bytes:
    """
    Generates an image using OpenAI gpt-image-1 and returns raw bytes.
    Env var: OPENAI_API_KEY
    """
    import base64
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    result = client.images.generate(
        model="gpt-image-1",
        prompt=prompt,
        size="1024x1024",
    )
    image_base64 = result.data[0].b64_json
    return base64.b64decode(image_base64)


def generate_and_place_images(state: State) -> dict:
    plan = state["plan"]
    md = state.get("md_with_placeholders") or state["merged_md"]
    image_specs = state.get("image_specs", []) or []

    # No images requested — just save markdown
    if not image_specs:
        filename = f"{safe_slug(plan.blog_title)}.md"
        Path(filename).write_text(md, encoding="utf-8")
        return {"final": md}

    images_dir = Path("images")
    images_dir.mkdir(exist_ok=True)

    for spec in image_specs:
        placeholder = spec["placeholder"]
        # Strip any leading "images/" or "images\" prefix LLM might add
        filename = Path(spec["filename"]).name
        out_path = images_dir / filename

        if not out_path.exists():
            try:
                img_bytes = _openai_generate_image_bytes(spec["prompt"])
                out_path.write_bytes(img_bytes)
            except Exception as e:
                fallback = (
                    f"\n> **[Image: {spec.get('caption', '')}]**\n"
                    f"> *{spec.get('alt', '')}*\n"
                    f"> *(Image generation failed: {e})*\n"
                )
                md = md.replace(placeholder, fallback)
                continue

        # Replace placeholder with actual image markdown
        img_md = (
            f"\n![{spec['alt']}](images/{filename})\n"
            f"*{spec['caption']}*\n"
        )
        md = md.replace(placeholder, img_md)

    blog_filename = f"{safe_slug(plan.blog_title)}.md"
    Path(blog_filename).write_text(md, encoding="utf-8")
    return {"final": md}