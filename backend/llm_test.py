from app.services.llm_service import LLMService


def main():

    llm = LLMService()

    prompt = """
Answer the following question.

Question:
How many days of annual leave do employees receive?

Answer:
"""

    answer = llm.generate(
        prompt=prompt,
        max_new_tokens=100,
    )

    print("\nLLM Response:")
    print(answer)


if __name__ == "__main__":
    main()