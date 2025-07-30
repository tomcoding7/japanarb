# Yu-Gi-Oh! Arbitrage Bot

An advanced arbitrage bot that analyzes Yu-Gi-Oh! card prices across multiple platforms to identify profitable buying opportunities.

## Features

### 🔍 Multi-Platform Price Analysis

- **Buyee.jp**: Scrapes current Japanese auction listings
- **130point.com/sales**: Analyzes recent eBay sold prices
- **eBay API**: Official eBay Finding API for sold listings and pricing data
- **Real-time exchange rates**: Yen to USD conversion

### 📊 Advanced Arbitrage Scoring

- **Comprehensive scoring system** (0-100 points)
- **Profit margin analysis** with condition adjustments
- **Risk assessment** based on data reliability
- **Smart recommendations**: STRONG BUY, BUY, CONSIDER, PASS

### 🎯 Intelligent Deal Detection

- **Condition-based pricing**: Adjusts for card condition (new/used/damaged)
- **PSA grading support**: Separate analysis for graded vs raw cards
- **Multi-source validation**: Combines data from multiple sources
- **Automatic filtering**: Focuses on high-probability opportunities

## Installation

1. **Clone the repository**:

```bash
git clone <repository-url>
```

2. **Install dependencies**:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. **Set up environment variables**:

```bash
cp .env.example .env
# Edit .env and add your API keys
```

### eBay API Setup

To use the enhanced eBay API integration:

1. **Get eBay API credentials**:
   - Go to [eBay Developers](https://developer.ebay.com/)
   - Create a new application
   - Get your Client ID, Client Secret, and Dev ID

2. **Configure environment variables**:
```bash
# eBay API Credentials
EBAY_CLIENT_ID=your_app_id_here
EBAY_CLIENT_SECRET=your_cert_id_here
EBAY_DEV_ID=your_dev_id_here
EBAY_REDIRECT_URI=http://localhost:3000/api/auth/ebay/callback

# Environment (use 'sandbox' for testing, 'production' for live)
EBAY_ENVIRONMENT=sandbox
```

3. **Test the eBay API integration**:
```bash
python test_ebay_api.py
```

## Usage

### Quick Start

Run the enhanced arbitrage analysis:

```bash
python run_arbitrage.py --search "青眼の白龍" --max-results 10
```

### Command Line Options

```bash
python run_arbitrage.py [OPTIONS]

Options:
  --search, -s TEXT     Search term (Japanese or English) [required]
  --max-results, -m INT Maximum number of results to analyze (default: 20)
  --output-dir, -o TEXT Output directory for results (default: arbitrage_results)
```

### Example Searches

```bash
# Popular cards
python run_arbitrage.py --search "青眼の白龍" --max-results 15
python run_arbitrage.py --search "ブラック・マジシャン" --max-results 15

# Set-specific searches
python run_arbitrage.py --search "遊戯王 LOB" --max-results 20
python run_arbitrage.py --search "遊戯王 レア" --max-results 25

# English searches (will be translated)
python run_arbitrage.py --search "Blue-Eyes White Dragon" --max-results 10
```

### Testing

Run the test suite to verify functionality:

```bash
python test_arbitrage.py
```

## How It Works

### 1. Data Collection

- **Buyee.jp scraping**: Uses undetected-chromedriver to avoid detection
- **130point.com API**: Fetches recent eBay sold prices
- **eBay API**: Official eBay Finding API for sold listings and pricing data
- **Card identification**: Extracts card names and set codes

### 2. Price Analysis

- **Multi-source aggregation**: Combines data from all sources
- **Condition adjustment**: Applies multipliers based on card condition
- **PSA grading**: Separate analysis for graded cards
- **Exchange rate conversion**: Real-time Yen to USD conversion

### 3. Arbitrage Scoring

The bot calculates a comprehensive score (0-100) based on:

- **Profit Margin (40%)**: Higher margins = higher scores
- **Absolute Profit (30%)**: Larger profits = higher scores
- **Data Reliability (20%)**: Multiple sources = higher scores
- **Risk Assessment (10%)**: Lower risk = higher scores

### 4. Recommendations

Based on the arbitrage score:

- **STRONG BUY**: Score ≥70, margin ≥30%, profit ≥$50
- **BUY**: Score ≥50, margin ≥20%, profit ≥$25
- **CONSIDER**: Score ≥30, margin ≥10%, profit ≥$10
- **PASS**: Below thresholds

## Output

### CSV Results

Detailed analysis saved as `arbitrage_[search]_[timestamp].csv`:

| Column               | Description                  |
| -------------------- | ---------------------------- |
| `title`              | Original Japanese title      |
| `title_en`           | English translation          |
| `price_yen`          | Buyee price in Yen           |
| `price_usd`          | Converted USD price          |
| `condition`          | Card condition               |
| `ebay_raw_prices`    | Raw eBay sold prices         |
| `ebay_psa_prices`    | PSA graded eBay prices       |
| `point130_raw_avg`   | 130point.com raw average     |
| `point130_psa9_avg`  | 130point.com PSA 9 average   |
| `point130_psa10_avg` | 130point.com PSA 10 average  |
| `potential_profit`   | Calculated profit in USD     |
| `profit_margin`      | Profit margin percentage     |
| `arbitrage_score`    | Overall score (0-100)        |
| `recommended_action` | STRONG BUY/BUY/CONSIDER/PASS |

### Console Summary

Real-time analysis summary showing:

- Total listings analyzed
- Profitable opportunities found
- Top recommendations
- Average scores and margins

## Configuration

### Exchange Rate

Update the exchange rate in `card_arbitrage.py`:

```python
self.yen_to_usd = Decimal('0.0067')  # Current rate
```

### Arbitrage Thresholds

Adjust thresholds in `card_arbitrage.py`:

```python
self.min_profit_margin = 30.0  # Minimum 30% profit margin
self.min_profit_usd = 50.0     # Minimum $50 profit
self.max_risk_score = 0.7      # Maximum risk score (0-1)
```

## Advanced Usage

### Custom Analysis

```python
from card_arbitrage import CardArbitrageTool

# Create custom tool
tool = CardArbitrageTool(output_dir="my_results")

# Run analysis
tool.run("青眼の白龍", max_results=15)

# Clean up
tool.cleanup()
```

### Batch Processing

```python
import time
from card_arbitrage import CardArbitrageTool

tool = CardArbitrageTool()

search_terms = [
    "青眼の白龍",
    "ブラック・マジシャン",
    "レッドアイズ・ブラック・ドラゴン"
]

for term in search_terms:
    print(f"Analyzing: {term}")
    tool.run(term, max_results=10)
    time.sleep(5)  # Delay between searches

tool.cleanup()
```

## Troubleshooting

### Common Issues

1. **WebDriver errors**: Install undetected-chromedriver

```bash
pip install undetected-chromedriver
```

2. **Translation errors**: Check internet connection for Google Translate

3. **Rate limiting**: Add delays between requests

```python
time.sleep(2)  # 2-second delay
```

4. **No results found**: Try different search terms or check Buyee.jp availability

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Legal Notice

This bot is for educational purposes only. Please ensure compliance with:

- Buyee.jp Terms of Service
- eBay Terms of Service
- 130point.com Terms of Service
- Local laws and regulations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
