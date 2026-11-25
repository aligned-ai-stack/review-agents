"""
company_agent.py: the company agent.

What the agent sees is set by the three blocks at the top:
  - Path("...")   -> the file's contents are inserted
  - "plain text"  -> the text is inserted as written
Comment out a CONTEXT line to remove that piece; add a line to add one.
Paths are relative to this file's folder.
"""

import os
from pathlib import Path

from pydantic import BaseModel

from llm_client import chat

# --------------------------------------------------------------------------- #
# Edit these
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT = Path("res/prompts/company.md")

# (title, source). Appended to the system prompt in this order.
CONTEXT = [
    ("DSA Article 34", Path("res/markdown/DSA 2022.md")),
    ("Google Risk Assessment 24", Path("res/markdown/Google Risk Assessment 24.md"))
]

USER_PROMPT = "Write your risk assessment for Article 34."


class CompanyOutput(BaseModel):
    response: str


# --------------------------------------------------------------------------- #
HERE = Path(__file__).parent.parent.parent


def _read(source: Path | str) -> str:
    if isinstance(source, Path):
        return (HERE / source).read_text(encoding="utf-8")
    return source


def build_system_prompt() -> str:
    parts = [_read(SYSTEM_PROMPT)]
    for title, source in CONTEXT:
        parts.append(f"## {title}\n\n{_read(source)}")
    return "\n\n".join(parts)


def run(user_prompt: str) -> CompanyOutput:
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": user_prompt},
    ]
    raw = chat(
        os.environ["LLM_MODEL"],
        messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "CompanyOutput",
                "schema": CompanyOutput.model_json_schema(),
            },
        },
    )
    return CompanyOutput.model_validate_json(raw)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    print(run(_read(USER_PROMPT)))