import yaml
import os
from zenml import pipeline
from steps.etl.crawl import crawl_stocks_step, crawl_news_step, crawl_sec_filings_step


@pipeline
def feature_pipeline(tickers: list[str]):
    # Parallelize execution for each independent crawler source branch
    crawl_stocks_step(tickers)
    crawl_news_step(tickers)
    crawl_sec_filings_step(tickers)


if __name__ == "__main__":
    # Load tickers securely from external YAML configuration
    # Assuming config.yaml is in the project root path
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)
        
    target_tickers = config.get("tickers", [])
    
    if not target_tickers:
        print("Warning: No tickers defined in config.yaml")

    feature_pipeline(target_tickers)
