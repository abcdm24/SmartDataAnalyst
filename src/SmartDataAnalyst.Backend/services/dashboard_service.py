import pandas as pd

def generate_dataset_summary(csv_path: str) -> dict:
    df = pd.read_csv(csv_path)

    columns_info = []
    numeric_summary = []

    for col in df.columns:
        missing = int(df[col].isna().sum())

        if pd.api.types.is_numeric_dtype(df[col]):
            col_type = "numric"

            numeric_summary.append({
                "column": col,
                "min":float(df[col].min()),
                "max": float(df[col].max()),
                "mean": f"{float(df[col].mean()):.2f}",
                "missing": missing
            })
        else:
            col_type = "categorical"    

        columns_info.append({
            "name": col,
            "type": col_type,
            "missing": missing
        })

    return {
        "summary": {
        "file_name": csv_path.split("/")[-1],
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "columns_info": columns_info,
        "numeric_summary": numeric_summary
        },
        "insights": [],
        "warnings": []
    }
    
