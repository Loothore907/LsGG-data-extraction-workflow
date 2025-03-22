# Scrape Master

A secure web scraping application with AI-powered data extraction capabilities.

## Security First Setup

1. **Environment Setup**
   ```bash
   # Create and edit your .env file (NEVER commit this file)
   cp .env.example .env
   ```
   Edit `.env` with your API keys:
   - Supabase URL and Anon Key
   - Any AI model API keys you plan to use

2. **Docker Setup** (Recommended Secure Method)
   ```bash
   # Build and run with Docker
   docker-compose up --build
   ```
   The application will be available at `http://localhost:8501`

3. **Local Setup** (Alternative)
   ```bash
   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate

   # Install dependencies
   pip install -r requirements.txt

   # Install playwright
   playwright install

   # Run the application
   streamlit run streamlit_app.py
   ```

## Security Notes

- Never commit `.env` files
- Use Docker for isolated execution
- Keep API keys secure and rotate them regularly
- The application runs with minimal permissions in Docker

## Database Setup

1. Create a [Supabase](https://supabase.com/) account
2. Create a new project
3. Run the following SQL in the SQL Editor:
   ```sql
   CREATE TABLE IF NOT EXISTS scraped_data (
     id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
     unique_name TEXT NOT NULL,
     url TEXT,
     raw_data JSONB,
     formatted_data JSONB,
     pagination_data JSONB,
     created_at TIMESTAMPTZ DEFAULT NOW()
   );
   ```

## Features

- Secure containerized execution
- AI-powered data extraction
- Pagination support
- Structured data storage
- Modern web interface

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.