from zenml import pipeline
from steps.etl.tickers import fetch_tickers, log_tickers


@pipeline
def feature_pipeline():
    tickers = fetch_tickers()
    log_tickers(tickers)


if __name__ == "__main__":
    feature_pipeline()
