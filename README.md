# Investment Research Assistant

A CLI tool that helps you research investments using OpenAI's web search and AI analysis.

![Investment Research Assistant](https://img.shields.io/badge/Investment-Research-blue)

## Features

- **Investment News Search**: Uses OpenAI web search to find recent articles about investment topics
- **Insight Extraction**: Automatically pulls out key insights, players, and related stock tickers
- **Stock Price Lookup**: Check current prices without leaving the app
- **Brain Rot Mode**: Creates TikTok-style explanations with Subway Surfers gameplay

## Requirements

- Python 3.8+
- OpenAI API key
- Alpha Vantage API key (optional, for better stock info)
- Eleven Labs API key (optional, for text-to-speech in Brain Rot mode)

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/investment-research-assistant.git
   cd investment-research-assistant
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
   ELEVEN_LABS_API_KEY=your_eleven_labs_api_key
   ```

## Usage

Run the application:
```
python invest.py
```

### Menu Options

1. **Research Mode**: Enter any investment question to find and analyze recent news
2. **Stock Lookup**: Look up information about a specific stock ticker
3. **Saved Research**: Coming soon
4. **Brain Rot Mode**: Get investment explanations in TikTok format

### Brain Rot Mode

This feature creates videos explaining investment concepts with Subway Surfers gameplay in the background.

All necessary media files are included in the repository:
- Subway Surfers gameplay video
- Peter Griffin image for overlay

  ** YOU HAVE TO CREATE A CUSTOM PETER GRIFFIN VOICE ON THE ELEVENLABS DASHBOARD. [THERE ARE YOUTUBE VIDEOS ON HOW TO DO IT. ](https://www.youtube.com/watch?v=BG89ZrplAis&t=68s) **

Just select Brain Rot Mode from the menu and follow the prompts.

## API Keys

- **OpenAI API Key**: Available at [OpenAI](https://platform.openai.com/)
- **Alpha Vantage API Key**: Available at [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
- **Eleven Labs API Key**: Available at [Eleven Labs](https://elevenlabs.io/)

## License & Disclaimer

MIT License

**Disclaimer**: This tool is for educational and entertainment purposes only. The information provided should not be considered financial advice.
