"""Turns the generator's plain-text replies into items. Code never travels in JSON:
the chat model strips its line breaks there."""

import re

_QUESTION = re.compile(r"=== QUESTION ===(.*?)=== END ===", re.DOTALL)
_OPTION = re.compile(r"^\s*([A-E])\)\s*(.*?)\s*\|\|\s*(\S+)\s*$", re.MULTILINE)
_FENCE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)


def _section(block: str, name: str, following: tuple[str, ...]) -> str:
    stops = "|".join(re.escape(f) for f in following)
    pattern = rf"^{name}:\s*(.*?)(?=^(?:{stops}):|\Z)" if stops else rf"^{name}:\s*(.*)"
    match = re.search(pattern, block, re.DOTALL | re.MULTILINE)
    return match.group(1).strip() if match else ""


def parse_mcqs(text: str) -> list[dict]:
    items = []
    for block in _QUESTION.findall(text or ""):
        difficulty = _section(block, "DIFFICULTY", ("STEM",)).split()[0:1]
        stem = _section(block, "STEM", ("OPTIONS",))
        options_text = _section(block, "OPTIONS", ("VERIFY",))
        verify_block = _section(block, "VERIFY", ("EXPLANATION",))
        explanation = _section(block, "EXPLANATION", ())

        options, answer = [], None
        for index, (_, option, tag) in enumerate(_OPTION.findall(options_text)):
            tag = tag.strip().lower()
            if tag == "correct":
                answer = index if answer is None else -1
                tag = None
            elif tag == "none":
                tag = None
            options.append({"text": option.strip().strip("`"), "misconception": tag})

        fenced = _FENCE.search(verify_block)
        items.append({
            "language": _section(block, "LANGUAGE", ("DIFFICULTY",)).lower() or "python",
            "difficulty": difficulty[0].lower() if difficulty else "",
            "stem": stem,
            "options": options,
            "answer_index": answer if answer is not None and answer >= 0 else -1,
            "verify_code": (fenced.group(1) if fenced else verify_block).strip("\n"),
            "explanation": explanation,
        })
    return items


_DEBUG = re.compile(r"=== DEBUG ===(.*?)=== END ===", re.DOTALL)
_PROBLEM = re.compile(r"=== PROBLEM ===(.*?)=== END ===", re.DOTALL)
_TEST_MARKER = re.compile(r"^###\s*(input|output)\s*$")


def _tests(text: str) -> list[dict]:
    cases, field = [], None
    for line in text.split("\n"):
        marker = _TEST_MARKER.match(line.strip())
        if marker and marker.group(1) == "input":
            cases.append({"stdin": [], "expected_stdout": []})
            field = "stdin"
        elif marker and cases:
            field = "expected_stdout"
        elif cases and field:
            cases[-1][field].append(line)
    return [{"kind": "sample" if n == 0 else "normal",
             "stdin": "\n".join(case["stdin"]).strip("\n") + "\n",
             "expected_stdout": "\n".join(case["expected_stdout"]).strip("\n")}
            for n, case in enumerate(cases)]


def _problems(text: str, topic: str) -> list[dict]:
    problems = []
    for block in _PROBLEM.findall(text or ""):
        reference = _FENCE.search(_section(block, "REFERENCE", ("TESTS",)))
        problems.append({
            "external_id": _section(block, "ID", ("DIFFICULTY",)),
            "topic": topic,
            "difficulty": _section(block, "DIFFICULTY", ("STATEMENT",)).lower(),
            "statement": " ".join(_section(block, "STATEMENT", ("CONSTRAINTS",)).split()),
            "constraints": " ".join(_section(block, "CONSTRAINTS", ("REFERENCE",)).split()),
            "reference": reference.group(1) if reference else "",
            "tests": _tests(_section(block, "TESTS", ())),
        })
    return problems


def parse_authored(text: str, topic: str) -> dict:
    """A hand-written practice file for one topic: QUESTION blocks as above, each with a
    LANGUAGE line (c, cpp, python, or any for a concept question); PROBLEM blocks with a
    statement, a Python reference and tests; and DEBUG blocks that name a problem, a
    language and a bug type. MCQ external ids follow the order of the blocks."""
    mcqs, numbers = [], {}
    for item in parse_mcqs(text):
        language = item["language"]
        numbers[language] = numbers.get(language, 0) + 1
        prefix = f"concept-{topic}" if language == "any" else f"mcq-{language}-{topic}"
        mcqs.append({**item, "topic": topic, "external_id": f"{prefix}-{numbers[language]}",
                     "explanations": [item["explanation"]] if item["explanation"] else []})
    debug = []
    for block in _DEBUG.findall(text or ""):
        problem = _section(block, "PROBLEM", ("LANGUAGE",))
        language = _section(block, "LANGUAGE", ("BUG",)).lower()
        programs = parse_debug(block)
        debug.append({
            "external_id": f"debug-{language}-{problem}",
            "problem_external_id": problem,
            "language": language,
            "bug_type": _section(block, "BUG", ("CORRECT",)),
            "fixed_code": programs[0] if programs else "",
            "buggy_code": programs[1] if programs else "",
        })
    return {"problems": _problems(text, topic), "mcqs": mcqs, "debug": debug}


_THEORY = re.compile(r"=== THEORY ===(.*?)=== END ===", re.DOTALL)


def parse_theory(text: str, topic: str) -> list[dict]:
    """THEORY blocks: LANGUAGE, DIFFICULTY, QUESTION, MODEL ANSWER, and KEY POINTS as a
    `- ` list. External ids follow the order of the blocks within each language."""
    items, numbers = [], {}
    for block in _THEORY.findall(text or ""):
        language = _section(block, "LANGUAGE", ("DIFFICULTY",)).lower()
        numbers[language] = numbers.get(language, 0) + 1
        points = _section(block, "KEY POINTS", ())
        items.append({
            "external_id": f"theory-{language}-{topic}-{numbers[language]}",
            "topic": topic,
            "language": language,
            "difficulty": _section(block, "DIFFICULTY", ("QUESTION",)).lower(),
            "question": _section(block, "QUESTION", ("MODEL ANSWER",)),
            "model_answer": _section(block, "MODEL ANSWER", ("KEY POINTS",)),
            "key_points": [line.strip()[2:].strip() for line in points.split("\n")
                           if line.strip().startswith("- ")],
        })
    return items


def parse_debug(text: str) -> tuple[str, str] | None:
    """(correct, buggy) programs, or None when the reply is not in the expected shape."""
    correct = re.search(r"CORRECT:\s*```[^\n]*\n(.*?)```", text or "", re.DOTALL)
    buggy = re.search(r"BUGGY:\s*```[^\n]*\n(.*?)```", text or "", re.DOTALL)
    if not correct or not buggy:
        return None
    return correct.group(1), buggy.group(1)
