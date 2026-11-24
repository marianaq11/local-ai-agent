from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
FILES = ("sample_auth.log", "injection_test.log")
MODELS = ("llama3.2:1b", "gemma3:1b")
DEFAULT_LIMIT = 5
MAX_LIMIT = 10
DEMO = (
    "Analyze sample_auth.log. Use evidence from the file. Summarize repeated "
    "failures and suspicious login sequences. Separate observed facts from "
    "possible threats, then recommend defensive measures."
)
