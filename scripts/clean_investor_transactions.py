
from pathlib import Path
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = PROJECT_DIR / "data" / "raw" / "08_investor_transactions.csv"
OUTPUT_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "clean_investor_transactions.csv"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(RAW_FILE)

print("Original shape:", df.shape)
print("Columns:", df.columns.tolist())
print("\nMissing values before cleaning:")
print(df.isna().sum())

required = {
    "investor_id",
    "transaction_date",
    "amfi_code",
    "transaction_type",
    "amount_inr",
    "kyc_status",
}
missing_columns = required - set(df.columns)

if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

# Standardise text fields
for col in ["investor_id", "amfi_code"]:
    df[col] = df[col].astype("string").str.strip()

# Parse dates; unparseable values become NaT
df["transaction_date"] = pd.to_datetime(
    df["transaction_date"], errors="coerce"
)

# Standardise transaction types
type_map = {
    "sip": "SIP",
    "lumpsum": "Lumpsum",
    "lump sum": "Lumpsum",
    "lump-sum": "Lumpsum",
    "redemption": "Redemption",
}

df["transaction_type"] = (
    df["transaction_type"]
    .astype("string")
    .str.strip()
    .str.lower()
    .map(type_map)
)

# Convert transaction amounts to numeric
df["amount_inr"] = pd.to_numeric(
    df["amount_inr"], errors="coerce"
)

# Standardise KYC values
kyc_map = {
    "verified": "Verified",
    "pending": "Pending",
}

df["kyc_status"] = (
    df["kyc_status"]
    .astype("string")
    .str.strip()
    .str.lower()
    .map(kyc_map)
)

# Report invalid records before filtering
invalid_date = df["transaction_date"].isna()
invalid_type = df["transaction_type"].isna()
invalid_amount = (
    df["amount_inr"].isna() | (df["amount_inr"] <= 0)
)
invalid_kyc = df["kyc_status"].isna()
invalid_identity = (
    df["investor_id"].isna()
    | df["investor_id"].eq("")
    | df["amfi_code"].isna()
    | df["amfi_code"].eq("")
)

print("\nInvalid dates:", invalid_date.sum())
print("Invalid transaction types:", invalid_type.sum())
print("Invalid amounts:", invalid_amount.sum())
print("Invalid KYC statuses:", invalid_kyc.sum())
print("Missing investor/fund identifiers:", invalid_identity.sum())

# Keep only rows satisfying required validation rules
invalid = (
    invalid_date
    | invalid_type
    | invalid_amount
    | invalid_kyc
    | invalid_identity
)

clean = df.loc[~invalid].copy()

# Remove exact duplicate records
before_dedup = len(clean)
clean = clean.drop_duplicates()
print("Exact duplicates removed:", before_dedup - len(clean))

# Save dates in ISO format
clean["transaction_date"] = (
    clean["transaction_date"].dt.strftime("%Y-%m-%d")
)

clean.to_csv(OUTPUT_FILE, index=False)

print("\nTransaction cleaning completed.")
print("Original rows:", len(df))
print("Cleaned rows:", len(clean))
print("Rows excluded:", len(df) - len(clean))
print("Output:", OUTPUT_FILE)

print("\nTransaction types:")
print(clean["transaction_type"].value_counts(dropna=False))

print("\nKYC statuses:")
print(clean["kyc_status"].value_counts(dropna=False))

print("\nRemaining missing values:")
print(clean.isna().sum())

print(
    "\nAll amounts positive:",
    (clean["amount_inr"] > 0).all()
)
print(
    "All transaction types valid:",
    clean["transaction_type"].isin(
        ["SIP", "Lumpsum", "Redemption"]
    ).all()
)
print(
    "All KYC statuses valid:",
    clean["kyc_status"].isin(["Verified", "Pending"]).all()
)
