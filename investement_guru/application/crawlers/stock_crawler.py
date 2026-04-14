import yfinance as yf
from investement_guru.domain.documents.stocks import StockDocument
from investement_guru.application.crawlers.base import BaseCrawler


class StockCrawler(BaseCrawler):
    model = StockDocument

    def fetch(self, ticker: str) -> list[StockDocument]:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info

        if not info or ("symbol" not in info and "shortName" not in info):
            return []

        history_df = ticker_obj.history(period="1y")
        price_history = []

        if not history_df.empty:
            for index, row in history_df.iterrows():
                price_history.append(
                    {
                        "date": index.strftime("%Y-%m-%d"),
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]),
                    }
                )

        doc = StockDocument(
            ticker=ticker.upper(),
            company_name=info.get("shortName") or info.get("longName") or ticker,
            sector=info.get("sector"),
            industry=info.get("industry"),
            business_summary=info.get("longBusinessSummary"),
            current_price=info.get("currentPrice") or info.get("previousClose"),
            fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
            fifty_two_week_low=info.get("fiftyTwoWeekLow"),
            market_cap=info.get("marketCap"),
            trailing_pe=info.get("trailingPE"),
            forward_pe=info.get("forwardPE"),
            revenue_growth=info.get("revenueGrowth"),
            earnings_growth=info.get("earningsGrowth"),
            profit_margins=info.get("profitMargins"),
            return_on_equity=info.get("returnOnEquity"),
            debt_to_equity=info.get("debtToEquity"),
            free_cashflow=info.get("freeCashflow"),
            total_revenue=info.get("totalRevenue"),
            beta=info.get("beta"),
            dividend_yield=info.get("dividendYield"),
            recommendation=info.get("recommendationKey"),
            target_mean_price=info.get("targetMeanPrice"),
            analyst_count=info.get("numberOfAnalystOpinions"),
            price_history=price_history,
        )
        return [doc]

    def get_source_name(self) -> str:
        return "stocks"
