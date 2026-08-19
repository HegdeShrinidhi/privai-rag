import re


def clean_text(text: str) -> str:
    """
    Clean PDF-extracted text while preserving useful structure.

    The cleaner:
    - normalizes line endings
    - fixes common PDF spacing issues
    - preserves paragraph boundaries
    - removes excessive whitespace
    - avoids destroying meaningful text
    """

    if not text:
        return ""

    # ---------------------------------------------------------
    # 1. Normalize line endings
    # ---------------------------------------------------------

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # ---------------------------------------------------------
    # 2. Fix words that were split across a line
    #
    # Example:
    # annual
    # leave
    #
    # becomes:
    # annual leave
    # ---------------------------------------------------------

    text = re.sub(
        r"(?<=[a-z])\n(?=[a-z])",
        " ",
        text,
    )

    # ---------------------------------------------------------
    # 3. Replace remaining single line breaks with spaces
    #
    # PDF extraction often puts every visual line on a
    # separate line even though it is one paragraph.
    # ---------------------------------------------------------

    text = re.sub(
        r"(?<!\n)\n(?!\n)",
        " ",
        text,
    )

    # ---------------------------------------------------------
    # 4. Normalize spaces
    # ---------------------------------------------------------

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    # ---------------------------------------------------------
    # 5. Fix common missing spaces around words
    # ---------------------------------------------------------

    text = re.sub(
        r"([a-z])([A-Z])",
        r"\1 \2",
        text,
    )

    # ---------------------------------------------------------
    # 6. Fix common PDF extraction cases where punctuation
    # is directly followed by a word.
    # ---------------------------------------------------------

    text = re.sub(
        r"([.,;:])([A-Za-z])",
        r"\1 \2",
        text,
    )

    # ---------------------------------------------------------
    # 7. Normalize multiple blank lines
    # ---------------------------------------------------------

    text = re.sub(
        r"\n\s*\n+",
        "\n\n",
        text,
    )

    # ---------------------------------------------------------
    # 8. Remove whitespace around lines
    # ---------------------------------------------------------

    text = "\n".join(
        line.strip()
        for line in text.split("\n")
    )

    # ---------------------------------------------------------
    # 9. Final cleanup
    # ---------------------------------------------------------

    text = text.strip()

    return text