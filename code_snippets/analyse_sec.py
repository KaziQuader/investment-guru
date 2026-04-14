from sec_edgar_downloader import Downloader
import os


def explore_sec():
    dl = Downloader("InvestmentGuru", "zunayedquader@email.com", "/tmp/sec_filings")
    dl.get("10-K", "AAPL", limit=1)

    # Find what got downloaded
    for root, dirs, files in os.walk("/tmp/sec_filings"):
        for file in files:
            filepath = os.path.join(root, file)
            print(filepath)

            # Print first 500 chars of each file
            if file.endswith(".txt") or file.endswith(".htm"):
                with open(filepath, "r", errors="ignore") as f:
                    print(f.read(500))
                print("---")


if __name__ == "__main__":
    explore_sec()
