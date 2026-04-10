from zenml import step


@step
def fetch_tickers() -> list[str]:
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]
    print(f"Fetched {len(tickers)} tickers")
    return tickers


@step
def log_tickers(tickers: list[str]) -> None:
    for ticker in tickers:
        print("Will Process: ", ticker)
    print("Tickers processed")
