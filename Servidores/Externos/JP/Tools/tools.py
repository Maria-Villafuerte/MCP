from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "Name","Platform","Year_of_Release","Genre","Publisher",
    "NA_Sales","EU_Sales","JP_Sales","Other_Sales","Global_Sales",
    "Critic_Score","User_Score"
]

def init_data(csv_path: Path, state: Dict[str, Any]) -> None:
    df = pd.read_csv(csv_path)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in dataset: {missing}")

    for c in ["Name", "Platform", "Genre", "Publisher"]:
        df[c] = df[c].astype(str).str.strip()

    state["df"] = df

def _safe_value(val):
    """Return NaN if value is null or empty string."""
    if pd.isna(val) or str(val).strip() == "":
        return np.nan
    return val

# ---------- Existing tools ----------
def tool_count_games_by_genre(df: pd.DataFrame, args: Dict[str, Any]) -> Dict[str, Any]:
    q = df
    if "platform" in args and args["platform"]:
        q = q[q["Platform"].str.lower() == args["platform"].lower()]
    counts = {genre: int(count) for genre, count in q["Genre"].value_counts().items()}
    return {"platform": args.get("platform"), "count_by_genre": counts}

def tool_best_publisher_by_sales(df: pd.DataFrame, args: Dict[str, Any]) -> Dict[str, Any]:
    q = df
    if args.get("year_min") is not None:
        q = q[q["Year_of_Release"] >= int(args["year_min"])]
    if args.get("year_max") is not None:
        q = q[q["Year_of_Release"] <= int(args["year_max"])]
    if q.empty:
        return {"message": "No games found in the specified range"}
    grouped = (q.groupby("Publisher", dropna=True)
                 .agg(total_sales=("Global_Sales","sum"), titles=("Name","count"))
                 .sort_values("total_sales", ascending=False))
    top = grouped.head(1)
    best_pub = {idx: {"Global_Sales": float(row.total_sales), "titles": int(row.titles)}
                for idx, row in top.iterrows()}
    return {"year_min": args.get("year_min"), "year_max": args.get("year_max"), "best_publisher": best_pub}

def tool_game_info(df: pd.DataFrame, args: Dict[str, Any]) -> Dict[str, Any]:
    name = args.get("name", "").strip().lower()
    if not name:
        return {"game_info": {"error": "Provide the exact game name in 'name'."}}
    q = df[df["Name"].str.lower() == name]
    if q.empty:
        return {"game_info": {"Name": args.get("name"), "error": "Game not found"}}
    row = q.iloc[0]
    info = {
        "Name": _safe_value(row["Name"]),
        "Platform": _safe_value(row["Platform"]),
        "Year_of_Release": _safe_value(row["Year_of_Release"]),
        "Genre": _safe_value(row["Genre"]),
        "Publisher": _safe_value(row["Publisher"]),
        "NA_Sales": _safe_value(row["NA_Sales"]),
        "EU_Sales": _safe_value(row["EU_Sales"]),
        "JP_Sales": _safe_value(row["JP_Sales"]),
        "Other_Sales": _safe_value(row["Other_Sales"]),
        "Global_Sales": _safe_value(row["Global_Sales"]),
        "Critic_Score": _safe_value(row["Critic_Score"]),
        "User_Score": _safe_value(row["User_Score"]),
    }
    return {"game_info": info}

# ---------- New tools ----------
def _apply_common_filters(df: pd.DataFrame, args: Dict[str, Any]) -> pd.DataFrame:
    q = df
    if args.get("year_min") is not None:
        q = q[q["Year_of_Release"] >= int(args["year_min"])]
    if args.get("year_max") is not None:
        q = q[q["Year_of_Release"] <= int(args["year_max"])]
    if args.get("genre"):
        q = q[q["Genre"].str.lower() == str(args["genre"]).lower()]
    if args.get("platform"):
        q = q[q["Platform"].str.lower() == str(args["platform"]).lower()]
    if args.get("publisher"):
        q = q[q["Publisher"].str.lower() == str(args["publisher"]).lower()]
    return q




def tool_top_games_by_sales(df: pd.DataFrame, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Top games by Global_Sales with optional filters.
    Inputs: limit (int, default 10), year_min, year_max, genre, platform, publisher
    """
    limit = int(args.get("limit", 10))
    q = _apply_common_filters(df, args)
    if q.empty:
        return {"message": "No games match the provided filters", "results": []}
    cols = ["Name","Platform","Year_of_Release","Genre","Publisher","Global_Sales"]
    out_rows = (q.sort_values("Global_Sales", ascending=False)[cols]
                  .head(limit)
                  .to_dict(orient="records"))
    # Ensure numeric JSON-serializable
    for r in out_rows:
        r["Global_Sales"] = float(r["Global_Sales"]) if not pd.isna(r["Global_Sales"]) else None
    return {
        "filters": {k:v for k,v in args.items() if k in ["year_min","year_max","genre","platform","publisher"] and v is not None},
        "limit": limit,
        "results": out_rows,
    }

def tool_publisher_leaderboard(df: pd.DataFrame, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Publishers ranked by summed Global_Sales (optional: year_min, year_max, genre).
    Inputs: limit (int, default 10), year_min, year_max, genre
    """
    limit = int(args.get("limit", 10))
    q = _apply_common_filters(df, args)  # uses genre/year filters; ignores platform/publisher
    if q.empty:
        return {"message": "No rows after applying filters", "results": []}
    grouped = (q.groupby("Publisher", dropna=True)
                 .agg(total_sales=("Global_Sales","sum"), titles=("Name","count"))
                 .sort_values("total_sales", ascending=False)
                 .head(limit)
                 .reset_index())
    results = [{
        "Publisher": _safe_value(row["Publisher"]),
        "Global_Sales": float(row["total_sales"]),
        "titles": int(row["titles"]),
    } for _, row in grouped.iterrows()]
    return {
        "filters": {k:v for k,v in args.items() if k in ["year_min","year_max","genre"] and v is not None},
        "limit": limit,
        "results": results,
    }

def tool_top_genres_by_platform(df: pd.DataFrame, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Top genres on a given platform by Global_Sales.
    Inputs: platform (str, required), limit (int, default 5)
    """
    platform = args.get("platform")
    if not platform:
        return {"error": "platform is required"}
    limit = int(args.get("limit", 5))
    q = df[df["Platform"].str.lower() == str(platform).lower()]
    if q.empty:
        return {"message": f"No rows for platform '{platform}'", "results": []}
    grouped = (q.groupby("Genre", dropna=True)
                 .agg(total_sales=("Global_Sales","sum"), titles=("Name","count"))
                 .sort_values("total_sales", ascending=False)
                 .head(limit)
                 .reset_index())
    results = [{
        "Genre": _safe_value(row["Genre"]),
        "Global_Sales": float(row["total_sales"]),
        "titles": int(row["titles"]),
    } for _, row in grouped.iterrows()]
    return {"platform": platform, "limit": limit, "results": results}

def tool_top_sales_by_platform(df: pd.DataFrame, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Top games on a specific platform ranked by Global_Sales.
    Required: platform (str)
    Optional: year_min, year_max, genre
    """
    platform = args.get("platform")
    if not platform:
        return {"error": "platform is required"}

    limit = int(args.get("limit", 10))
    q = _apply_common_filters(df, args)
    q = q[q["Platform"].str.lower() == platform.lower()]

    if q.empty:
        return {"message": f"No games found for platform '{platform}' with the given filters", "results": []}

    cols = ["Name", "Platform", "Year_of_Release", "Genre", "Publisher", "Global_Sales"]
    out_rows = (
        q.sort_values("Global_Sales", ascending=False)[cols]
        .head(limit)
        .to_dict(orient="records")
    )

    # asegurar que los valores sean JSON-serializables
    for r in out_rows:
        r["Global_Sales"] = float(r["Global_Sales"]) if not pd.isna(r["Global_Sales"]) else None

    return {
        "platform": platform,
        "filters": {k: v for k, v in args.items() if k in ["year_min", "year_max", "genre"] and v is not None},
        "limit": limit,
        "results": out_rows,
    }
def tool_publisher_genre_breakdown(df: pd.DataFrame, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Breakdown of sales by genre for a specific publisher.
    Required: publisher (str)
    Optional: year_min, year_max
    """
    publisher = args.get("publisher")
    if not publisher:
        return {"error": "publisher is required"}

    q = _apply_common_filters(df, args)
    q = q[q["Publisher"].str.lower() == publisher.lower()]

    if q.empty:
        return {"message": f"No games found for publisher '{publisher}'", "results": []}

    grouped = (
        q.groupby("Genre", dropna=True)
         .agg(total_sales=("Global_Sales", "sum"), titles=("Name", "count"))
         .sort_values("total_sales", ascending=False)
         .reset_index()
    )

    results = [{
        "Genre": _safe_value(row["Genre"]),
        "Global_Sales": float(row["total_sales"]),
        "titles": int(row["titles"])
    } for _, row in grouped.iterrows()]

    return {
        "publisher": publisher,
        "filters": {k: v for k, v in args.items() if k in ["year_min", "year_max"] and v is not None},
        "results": results,
    }
def tool_top_games_by_region(df: pd.DataFrame, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ranking of top-selling games in a specific region.
    Required: region (str: 'NA', 'EU', 'JP', 'Other')
    Optional: limit (int, default 10), year_min, year_max, platform, genre, publisher
    """
    region = args.get("region")
    if not region:
        return {"error": "region is required"}
    
    region_col = None
    if region.upper() == "NA":
        region_col = "NA_Sales"
    elif region.upper() == "EU":
        region_col = "EU_Sales"
    elif region.upper() == "JP":
        region_col = "JP_Sales"
    elif region.upper() == "OTHER":
        region_col = "Other_Sales"
    else:
        return {"error": f"Invalid region '{region}'. Use one of: NA, EU, JP, Other."}

    limit = int(args.get("limit", 10))
    q = _apply_common_filters(df, args)

    if q.empty:
        return {"message": "No games match the provided filters", "results": []}

    cols = ["Name", "Platform", "Year_of_Release", "Genre", "Publisher", region_col]
    out_rows = (
        q.sort_values(region_col, ascending=False)[cols]
         .head(limit)
         .to_dict(orient="records")
    )

    for r in out_rows:
        r[region_col] = float(r[region_col]) if not pd.isna(r[region_col]) else None

    return {
        "region": region.upper(),
        "filters": {k: v for k, v in args.items() if k in ["year_min", "year_max", "platform", "genre", "publisher"] and v is not None},
        "limit": limit,
        "results": out_rows,
    }


