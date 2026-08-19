import re


SECTION_PATTERN = re.compile(
    r"(?=\b\d{1,2}\.\s+[A-Z][A-Za-z\s&/-]{2,60})"
)


def split_into_sections(text: str) -> list[str]:
    """
    Split policy/document text at numbered sections.

    Example:

    1. Working Hours
    ...
    2. Annual Leave Policy
    ...

    becomes separate sections.
    """

    sections = re.split(
        SECTION_PATTERN,
        text,
    )

    return [
        section.strip()
        for section in sections
        if section.strip()
    ]


def split_large_text(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """
    Split large text by words without cutting words.
    """

    words = text.split()

    chunks = []
    start = 0

    while start < len(words):

        current_words = []
        current_length = 0

        index = start

        while index < len(words):

            word = words[index]

            extra_length = len(word)

            if current_words:
                extra_length += 1

            if (
                current_length + extra_length
                > chunk_size
            ):
                break

            current_words.append(word)

            current_length += extra_length

            index += 1

        if not current_words:
            break

        chunk = " ".join(current_words)

        chunks.append(chunk)

        # Calculate overlap by characters.
        overlap_length = 0
        overlap_words = []

        for word in reversed(current_words):

            word_length = len(word)

            if overlap_words:
                word_length += 1

            if (
                overlap_length + word_length
                > chunk_overlap
            ):
                break

            overlap_words.insert(0, word)

            overlap_length += word_length

        # Move forward.
        next_start = index - len(overlap_words)

        # Safety protection against infinite loops.
        if next_start <= start:
            next_start = index

        start = next_start

    return chunks


def create_chunks(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[str]:
    """
    Create structure-aware document chunks.
    """

    if not text:
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )

    sections = split_into_sections(text)

    chunks = []

    for section in sections:

        # Keep smaller sections intact.
        if len(section) <= chunk_size:

            chunks.append(section.strip())

        else:

            # Split large sections while preserving
            # word boundaries.
            section_chunks = split_large_text(
                section,
                chunk_size,
                chunk_overlap,
            )

            chunks.extend(section_chunks)

    return chunks