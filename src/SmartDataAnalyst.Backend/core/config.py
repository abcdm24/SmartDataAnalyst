from dataclasses import dataclass

@dataclass
class ModelConfig:
    """
    Configurable parameteres for LLM memory and token budgets.
    """
    model_name: str = "gpt-3.5-turbo"
    max_tokens: int = 120000
    safety_margin: int = 5000
    chars_per_token: int = 4
    summarize_every: int = 3

    @property
    def max_chars(self) -> int:
        """Character limit equivalent of token budget."""
        return (self.max_tokens - self.safety_margin) * self.chars_per_token
    

MODEL_BUDGETS = {
    "gpt-4-turbo": ModelConfig(model_name="gpt-4-turbo", max_tokens=120000),
    "gpt-3.5-turbo": ModelConfig(model_name="gpt-3.5-turbo", max_tokens=16000),
    "gpt-4o-mini": ModelConfig(model_name="gpt-4o-mini",max_tokens=32000),
}