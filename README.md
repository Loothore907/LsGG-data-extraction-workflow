# Loots Scraper Service

A modular data collection service for cannabis product information, designed to feed into the Loots Ganja Guide app.

## Project Structure

```
loots-scraper-service/
├── core/                  # Shared utilities and functionality
├── web_scraper/           # Web scraping module
├── output/                # Output files for data service integration
├── docker-compose.yml     # Docker configuration
└── Dockerfile             # Container definition
```

## Modules

### Web Scraper

The web scraper module extracts product information from cannabis websites, including:

- Product names
- Prices
- Categories
- Weights/quantities

### Core Functionality

The core module provides shared utilities for:

- Data export in standardized formats
- Configuration management
- Common utilities for text processing

## Getting Started

1. **Environment Setup**
   ```bash
   # Create and edit your .env file (NEVER commit this file)
   cp .env.example .env
   ```
   Edit `.env` with your API keys

2. **Docker Setup** (Recommended)
   ```bash
   # Build and run with Docker
   docker-compose up --build
   ```
   The application will be available at `http://localhost:8501`

3. **Local Setup** (Alternative)
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment (Windows)
   venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt

   # Install playwright
   playwright install

   # Run the web scraper
   streamlit run web_scraper/app.py
   ```

## Data Integration

The scraped data is exported to JSON files in the `output/web_scraper/` directory with the following structure:

```json
{
  "metadata": {
    "source": "web_scraper",
    "timestamp": "2025-03-22T15:30:45Z",
    "vendor_id": "vendor_123",
    "region": "washington"
  },
  "products": [
    {
      "name": "Product Name",
      "price": "21.00",
      "category": "Category",
      "weight": "0.75",
      "unit": "g"
    }
  ]
}
```

These files can be imported into the Loots Data Service for further processing and database integration.

## Security Notes

- Never commit `.env` files
- Use Docker for isolated execution
- Keep API keys secure and rotate them regularly

## License

This project is licensed under the MIT License - see the LICENSE file for details.