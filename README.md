# Investment Research Assistant

A powerful CLI tool that helps you analyze investment opportunities using AI and real-time data.

![Investment Research Assistant](https://img.shields.io/badge/Investment-Research-blue)

## Features

- **Investment Research**: Find and analyze recent news articles about any investment topic
- **Key Insights Extraction**: Automatically extract key insights, players, and related stock tickers
- **Stock Information**: Look up current stock prices and basic information
- **Brain Rot Mode**: Generate entertaining TikTok-style explanations of complex financial topics with optional video creation

## Requirements

- Python 3.8+
- OpenAI API key
- Alpha Vantage API key (optional, for enhanced stock information)
- Eleven Labs API key (optional, for text-to-speech in Brain Rot mode)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/investment-research-assistant.git
   cd investment-research-assistant
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API keys:
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

### Main Menu Options

1. **Research an investment topic**: Enter any investment-related question to find recent news and analysis
2. **Look up specific stock ticker**: Get current information about a specific stock
3. **View saved research**: (Coming soon)
4. **Brain Rot Mode**: Generate entertaining TikTok-style explanations of financial topics

### Brain Rot Video Creation

For the full Brain Rot experience with video:

1. Place a Subway Surfers gameplay video named `subway_surfers.mp4` in the project directory
2. (Optional) Place a Peter Griffin image named `peter.png` in the project directory
3. Select Brain Rot Mode and follow the prompts

## API Keys

- **OpenAI API Key**: Required for all functionality. Get one at [OpenAI](https://platform.openai.com/)
- **Alpha Vantage API Key**: Optional, for enhanced stock information. Get one at [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
- **Eleven Labs API Key**: Optional, for text-to-speech in Brain Rot mode. Get one at [Eleven Labs](https://elevenlabs.io/)

## License

MIT

## Disclaimer

This tool is for educational and entertainment purposes only. Always do your own research before making investment decisions. The information provided by this tool should not be considered financial advice.
