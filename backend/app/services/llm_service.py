from transformers import AutoTokenizer, AutoModelForCausalLM
import torch


class LLMService:
    """
    Local instruction LLM service.

    Development model:
    Qwen/Qwen2.5-0.5B-Instruct

    This model is being used for CPU-based development.
    Later, the LLM layer can be replaced with a larger
    self-hosted model served through vLLM.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
    ):
        print(
            f"Loading local LLM: {model_name}"
        )

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name
        )

        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            dtype=torch.float32,
        )

        # CPU for current development environment
        self.device = torch.device("cpu")

        self.model.to(self.device)

        # Evaluation mode
        self.model.eval()

        print(
            "Local LLM loaded successfully."
        )

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 200,
    ) -> str:
        """
        Generate an answer using the Qwen
        instruction/chat format.
        """

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful enterprise "
                    "document assistant."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        # Use Qwen's chat template
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=2048,
        )

        # Move tensors to CPU
        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        # Generate
        with torch.no_grad():

            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                pad_token_id=(
                    self.tokenizer.eos_token_id
                ),
            )

        # Remove the original prompt tokens
        generated_tokens = outputs[
            0
        ][
            inputs["input_ids"].shape[1]:
        ]

        # Decode generated text
        answer = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        )

        return answer.strip()