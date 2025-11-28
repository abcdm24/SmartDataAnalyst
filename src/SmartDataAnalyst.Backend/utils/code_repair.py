
def prepare_code(code:str) -> str:
    """
    Ensures required imports exist in the generated code.
    Automatically injects missing imports sunch as pandas.    
    """

    lines = code.strip().split("\n")

    # If code uses 'pd.' but no import pandas exists
    if "pd." in code and "import pandas" not in code:
        lines.insert(0, "import pandas as pd")

    
    # Optionally: ensure numpy exists
    if "np." in code and "import numpy" not in code:
        lines.insert(0, "import numpy as np")

    return "\n".join(lines)