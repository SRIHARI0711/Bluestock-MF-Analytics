
from pathlib import Path
import requests

# Project directory
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = (
    "https://assets.validstep.com/workspace/shared-datasets/"
    "3430cd3b-bd90-492f-8c47-7d03c166b37c/"
)

DATASETS = {
    "01_fund_master.csv":
        "1788499983024-b042c300-01_fund_master.csv",
    "02_nav_history.csv":
        "1788499983331-4389156d-02_nav_history.csv",
    "03_aum_by_fund_house.csv":
        "1788499984134-b0cbf625-03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv":
        "1788499984405-d702a6c6-04_monthly_sip_inflows.csv",
    "05_category_inflows.csv":
        "1788499984721-4b860901-05_category_inflows.csv",
    "06_industry_folio_count.csv":
        "1788499985036-da4a0c4a-06_industry_folio_count.csv",
    "07_scheme_performance.csv":
        "1788499985420-bb134abf-07_scheme_performance.csv",
    "08_investor_transactions.csv":
        "1788499980509-304c1255-08_investor_transactions.csv",
    "09_portfolio_holdings.csv":
        "1788499982117-e3d6ab98-09_portfolio_holdings.csv",
    "10_benchmark_indices.csv":
        "1788499982615-f9647ab2-10_benchmark_indices.csv",
}


def download_datasets():
    success = 0

    with requests.Session() as session:
        for filename, source_filename in DATASETS.items():
            url = BASE_URL + source_filename
            destination = RAW_DIR / filename
            temp_destination = RAW_DIR / (filename + ".tmp")

            try:
                print(f"\nDownloading: {filename}")

                response = session.get(
                    url,
                    timeout=60,
                    stream=True
                )
                response.raise_for_status()

                total_bytes = 0

                with open(temp_destination, "wb") as file:
                    for chunk in response.iter_content(
                        chunk_size=1024 * 1024
                    ):
                        if chunk:
                            file.write(chunk)
                            total_bytes += len(chunk)

                # Avoid accepting an empty or obvious HTML error page.
                if total_bytes == 0:
                    raise ValueError("Downloaded file is empty")

                with open(temp_destination, "rb") as file:
                    first_bytes = file.read(512).lstrip()

                if first_bytes.lower().startswith(
                    (b"<!doctype html", b"<html")
                ):
                    raise ValueError(
                        "Received HTML instead of a CSV file"
                    )

                temp_destination.replace(destination)

                print(
                    f"SUCCESS | {total_bytes:,} bytes | "
                    f"{destination.name}"
                )
                success += 1

            except (requests.RequestException, OSError, ValueError) as error:
                if temp_destination.exists():
                    temp_destination.unlink()

                print(f"FAILED  | {filename} | {error}")

    print(f"\nDownload summary: {success}/{len(DATASETS)} files")
    print(f"Raw data folder: {RAW_DIR.resolve()}")

    if success != len(DATASETS):
        print("Check failed downloads before proceeding.")
    else:
        print("All 10 datasets downloaded successfully.")


if __name__ == "__main__":
    download_datasets()
