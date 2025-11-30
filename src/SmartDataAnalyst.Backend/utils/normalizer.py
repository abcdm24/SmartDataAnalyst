import pandas as pd
import numpy as np
from datetime import datetime

def normalize_dataframe(df: pd.DataFrame, sample_size: int = 10) -> pd.DataFrame:
    """
    Universal intelligent DataFrame normalizer.
    Performs type inference using the first N non-null values of each column.
    
    Rules:
    - Detects integers, floats, decimals inside string columns.
    - Detects Unix timestamps (seconds or milliseconds).
    - Detects dates (YYYY-MM-DD, DD/MM/YYYY, etc.)
    - Cleans whitespace.
    - Replaces empty strings with NaN.
    """

    df = df.copy()

    # Replace empty or whitespace-only entries with NaN
    df = df.replace(r"^\s*$", np.nan, regex=True)

    for col in df.columns:
        series = df[col]

        # Clean string values
        if series.dtype == "object":
            series = series.str.strip().str.replace(",", "", regex=False)
            df[col] = series

        # Gather sample values
        non_null = series.dropna().head(sample_size).astype(str)

        # ---- 1. Try pure integers ----
        if non_null.apply(lambda x: x.isdigit() or (x.startswith("-") and x[1:].isdigit())).all():
            try:
                df[col] = pd.to_numeric(series, errors="coerce").astype("Int64")
                continue
            except:
                pass

        # ---- 2. Try floats ----
        def is_float(x: str) -> bool:
            try:
                float(x)
                return True
            except:
                return False

        if non_null.apply(is_float).all():
            try:
                df[col] = pd.to_numeric(series, errors="coerce")
                continue
            except:
                pass

        # ---- 3. Detect Unix timestamps (seconds or ms) ----
        # Heuristic: numeric, large numbers
        if pd.api.types.is_numeric_dtype(series):
            max_val = series.max()
            if pd.notna(max_val):
                if 10_000_000 < max_val < 2_000_000_000:
                    # Likely seconds
                    try:
                        df[col] = pd.to_datetime(series, unit="s", errors="coerce")
                        continue
                    except:
                        pass

                if 1_000_000_000_000 < max_val < 10_000_000_000_000:
                    # Likely milliseconds
                    try:
                        df[col] = pd.to_datetime(series, unit="ms", errors="coerce")
                        continue
                    except:
                        pass

        # ---- 4. Detect date strings ----
        def is_date(x: str) -> bool:
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y",
                        "%Y/%m/%d", "%Y.%m.%d", "%d.%m.%Y"):
                try:
                    datetime.strptime(x, fmt)
                    return True
                except:
                    pass
            return False

        if non_null.apply(is_date).all():
            try:
                df[col] = pd.to_datetime(series, errors="coerce")
                continue
            except:
                pass

        # ---- 5. Text fallback ----
        # Keep as string (object)
        df[col] = series.astype(str)

    return df
