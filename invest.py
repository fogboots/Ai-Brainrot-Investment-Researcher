from openai import OpenAI
import json
import requests
import time
import os
import sys
from colorama import Fore, Back, Style, init
import datetime
from datetime import date
from dotenv import load_dotenv
import random
import traceback
from PIL import Image

# Patch PIL.Image.ANTIALIAS which is deprecated
# In newer versions of Pillow, ANTIALIAS is replaced with LANCZOS
if not hasattr(Image, 'ANTIALIAS'):
    print(f"{Fore.YELLOW}Patching PIL.Image.ANTIALIAS with PIL.Image.LANCZOS")
    Image.ANTIALIAS = Image.LANCZOS

# Try different import for moviepy
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, ImageClip
    print(f"{Fore.GREEN}Successfully imported moviepy modules.")
except ImportError as e:
    print(f"{Fore.YELLOW}Warning: Could not import moviepy modules: {e}")
    print(f"{Fore.YELLOW}Brain rot video creation will not be available.")
    # Define dummy classes to prevent errors
    class VideoFileClip:
        def __init__(self, *args, **kwargs): pass
        def set_position(self, *args, **kwargs): return self
        def set_duration(self, *args, **kwargs): return self
        def subclip(self, *args, **kwargs): return self
        def set_audio(self, *args, **kwargs): return self
        def close(self, *args, **kwargs): pass
        def write_videofile(self, *args, **kwargs): pass
    class AudioFileClip:
        def __init__(self, *args, **kwargs): 
            self.duration = 0
        def close(self, *args, **kwargs): pass
    class CompositeVideoClip:
        def __init__(self, *args, **kwargs): pass
    class ImageClip:
        def __init__(self, *args, **kwargs): pass
        def resize(self, *args, **kwargs): return self
        def set_position(self, *args, **kwargs): return self
        def set_duration(self, *args, **kwargs): return self
        def close(self, *args, **kwargs): pass


class Config:
    """Configuration and environment management"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize colorama
        init(autoreset=True)
        
        # Check if required API keys are available
        if not os.environ.get("OPENAI_API_KEY"):
            print(f"{Fore.RED}Error: OPENAI_API_KEY not found in environment variables.")
            print(f"{Fore.YELLOW}Please make sure you have a .env file with the required API keys.")
            sys.exit(1)
        
        # Optional API key check with warning
        if not os.environ.get("ALPHA_VANTAGE_API_KEY"):
            print(f"{Fore.YELLOW}Warning: ALPHA_VANTAGE_API_KEY not found. Stock information features will be limited.")
        
        # Optional API key check for Eleven Labs
        if not os.environ.get("ELEVEN_LABS_API_KEY"):
            print(f"{Fore.YELLOW}Warning: ELEVEN_LABS_API_KEY not found. Brain rot mode will not have voice narration.")
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        
        # Define OpenAI tools
        self.tools = [{
            "type": "function",
            "name": "get_stock_info",
            "description": "Get current stock information for a company by ticker symbol",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker_symbol": {
                        "type": "string",
                        "description": "The stock ticker symbol, e.g., AAPL for Apple Inc."
                    }
                },
                "required": ["ticker_symbol"],
                "additionalProperties": False
            },
            "strict": True
        }]
        
        # Store shared data between functions
        self.all_insights = []
        self.all_key_players = []
        self.all_tickers = []


class UIManager:
    """Manages UI elements and screen display"""
    
    def __init__(self):
        pass
    
    @staticmethod
    def clear_screen():
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    @staticmethod
    def display_welcome():
        """Display the welcome banner"""
        UIManager.clear_screen()
        print(f"{Fore.CYAN}")
        print(r"""
    __  __                _            _    _                        
    |  \/  |              | |          | |  | |                       
    | \  / |  __ _  _ __  | | __  ___  | |_ | |      ___  _ __   ___ 
    | |\/| | / _` || '__| | |/ / / _ \ | __|| |     / _ \| '_ \ / __|
    | |  | || (_| || |    |   < |  __/ | |_ | |____ |  __/| | | |\__ \
    |_|  |_| \__,_||_|    |_|\_\ \___|  \__||______| \___||_| |_||___/
                                                                    
    """)
        print(f"{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.YELLOW}{' ' * 25}INVESTMENT RESEARCH ASSISTANT{' ' * 25}")
        print(f"{Fore.CYAN}{'=' * 80}")
        print(f"{Fore.CYAN}{'=' * 80}")
        print(f"\n{Fore.GREEN}This tool helps you analyze investment opportunities by:")
        print(f"{Fore.GREEN}  • Finding relevant news articles")
        print(f"{Fore.GREEN}  • Extracting key insights and players")
        print(f"{Fore.GREEN}  • Identifying related stock tickers")
        print(f"{Fore.GREEN}  • Retrieving current stock prices\n")
    
    @staticmethod
    def display_menu():
        """Display the main menu and get user choice"""
        print(f"\n{Fore.CYAN}{'=' * 40}")
        print(f"{Fore.YELLOW}           MAIN MENU")
        print(f"{Fore.CYAN}{'=' * 40}")
        print(f"{Fore.WHITE}1. {Fore.GREEN}Research an investment topic")
        print(f"{Fore.WHITE}2. {Fore.GREEN}Look up specific stock ticker")
        print(f"{Fore.WHITE}3. {Fore.GREEN}View saved research")
        print(f"{Fore.WHITE}4. {Fore.GREEN}Brain Rot Mode 🧠")
        print(f"{Fore.WHITE}5. {Fore.GREEN}Exit")
        print(f"{Fore.CYAN}{'=' * 40}")
        return input(f"{Fore.YELLOW}Enter your choice (1-5): {Fore.WHITE}")
    
    @staticmethod
    def display_loading(message, iterations=3, delay=0.5):
        """Display a loading animation"""
        for i in range(iterations):
            sys.stdout.write(f"{Fore.YELLOW}{message}{' .' * i}{' ' * (10 - i * 2)}\r")
            sys.stdout.flush()
            time.sleep(delay)
    
    @staticmethod
    def display_insights(insights, key_players, tickers):
        """Display gathered insights in a formatted way"""
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}                KEY INSIGHTS SUMMARY")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        # Display insights
        for i, insight in enumerate(insights, 1):
            print(f"\n{Fore.CYAN}Article {i}: {Fore.WHITE}{insight['url']}")
            print(f"{Fore.YELLOW}Key Insights:")
            for point in insight['insights']:
                print(f"{Fore.GREEN}• {Fore.WHITE}{point}")
            
            if insight['key_players']:
                print(f"\n{Fore.YELLOW}Key Players:")
                for player in insight['key_players']:
                    print(f"{Fore.GREEN}• {Fore.WHITE}{player}")
            
            if insight['tickers']:
                print(f"\n{Fore.YELLOW}Related Tickers:")
                for ticker in insight['tickers']:
                    if isinstance(ticker, str):
                        print(f"{Fore.GREEN}• {Fore.WHITE}{ticker}")
                    elif isinstance(ticker, dict) and 'ticker' in ticker:
                        print(f"{Fore.GREEN}• {Fore.WHITE}{ticker['ticker']}")
        
        # Display summary
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}                OVERALL SUMMARY")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        print(f"\n{Fore.YELLOW}All Key Players Identified:")
        for player in key_players:
            print(f"{Fore.GREEN}• {Fore.WHITE}{player}")
        
        print(f"\n{Fore.YELLOW}All Stock Tickers Identified:")
        for ticker in tickers:
            print(f"{Fore.GREEN}• {Fore.WHITE}{ticker}")
        
        print(f"{Fore.CYAN}{'=' * 60}")


class StockAnalyzer:
    """Handles stock information retrieval and analysis"""
    
    def __init__(self, config):
        self.config = config
    
    def get_stock_info(self, ticker_symbol):
        """Get stock information using Alpha Vantage API"""
        api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker_symbol}&apikey={api_key}"
        
        try:
            response = requests.get(url)
            data = response.json()
            
            if "Global Quote" in data and "05. price" in data["Global Quote"]:
                return data["Global Quote"]["05. price"]
            else:
                return f"Could not retrieve price for {ticker_symbol}"
        
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_stock_info_with_api(self, ticker):
        """Get stock information using OpenAI function calling"""
        print(f"\n{Fore.CYAN}Fetching stock information for: {Fore.WHITE}{ticker}")
        
        # Show loading animation
        UIManager.display_loading("Retrieving data", 3, 0.3)
        
        response = self.config.openai_client.responses.create(
            model="gpt-4o",
            tools=self.config.tools,
            input=f"Get the current stock information for the ticker: {ticker}"
        )
        
        # Check if there are any function calls in the response
        for tool_call in response.output:
            if tool_call.type == "function_call" and tool_call.name == "get_stock_info":
                # Parse the arguments
                args = json.loads(tool_call.arguments)
                ticker_symbol = args.get("ticker_symbol")
                
                # Execute the function
                result = self.get_stock_info(ticker_symbol)
                
                # Create messages with the function call and result
                messages = [
                    {"role": "user", "content": f"Get the current stock information for the ticker: {ticker}"},
                    tool_call,  # Add the model's function call
                    {  # Add the function result
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": str(result)
                    }
                ]
                
                # Get the final response with the function result incorporated
                final_response = self.config.openai_client.responses.create(
                    model="gpt-4o",
                    input=messages,
                    tools=self.config.tools
                )
                
                return final_response.output_text
        
        # If no function was called, return the original response
        return response.output_text
    
    def display_stock_prices(self, tickers):
        """Display stock prices for a list of tickers"""
        print(f"\n{Fore.CYAN}{'=' * 40}")
        print(f"{Fore.YELLOW}        CURRENT STOCK PRICES")
        print(f"{Fore.CYAN}{'=' * 40}")
        
        if not tickers:
            print(f"{Fore.RED}No stock tickers identified to look up prices.")
            return
        
        # Create a dictionary to store ticker analyses
        ticker_analyses = {}
        
        # Process each URL and collect ticker analyses
        for insight in self.config.all_insights:
            for ticker_item in insight.get('tickers', []):
                if isinstance(ticker_item, dict) and 'ticker' in ticker_item and 'analysis' in ticker_item:
                    ticker_symbol = ticker_item['ticker']
                    ticker_analyses[ticker_symbol] = ticker_item['analysis']
        
        for ticker in tickers:
            if ticker:  # Make sure ticker is not empty
                stock_info = self.get_stock_info_with_api(ticker)
                print(f"{Fore.GREEN}[{ticker}] {Fore.WHITE}{stock_info}")
                
                # Display analysis if available
                if ticker in ticker_analyses:
                    print(f"{Fore.YELLOW}Analysis: {Fore.WHITE}{ticker_analyses[ticker]}")
        
        print(f"{Fore.CYAN}{'=' * 40}")
        input(f"\n{Fore.YELLOW}Press Enter to continue...")


class NewsAnalyzer:
    """Handles news retrieval and analysis"""
    
    def __init__(self, config, stock_analyzer):
        self.config = config
        self.stock_analyzer = stock_analyzer
    
    def find_news_stories(self, user_query):
        """Find news stories related to user query"""
        print(f"\n{Fore.CYAN}Searching for news about: {Fore.WHITE}{user_query}")
        print(f"{Fore.CYAN}{'.' * 40}")
        
        # Show loading animation
        UIManager.display_loading("Searching", 3, 0.5)
        
        response = self.config.openai_client.responses.create(
            model="gpt-4o",
            tools=[{
                "type": "web_search_preview",
            }],
            input=f"The current date is {datetime.datetime.now().strftime('%Y-%m-%d')}. All news found should be recent. Find the 3 top and most recent news stories about: {user_query}. Only give top 3, nothing else. Return it in JSON format with the title, description, and url. Don't even include the ```json``` tags.",
        )
        return response.output_text
    
    def extract_insights_from_url(self, url, index):
        """Extract insights from a URL"""
        print(f"\n{Fore.CYAN}Analyzing article {index}: {Fore.WHITE}{url}")
        
        # Show loading animation
        UIManager.display_loading("Extracting insights", 5, 0.5)
        
        response = self.config.openai_client.responses.create(
            model="gpt-4o",
            tools=[{
                "type": "web_search_preview",
            }],
            input=f"Visit this URL: {url} and extract the following information:\n"
                  f"1. Key insights and main points from the article\n"
                  f"2. Key companies/players mentioned\n"
                  f"3. Stock ticker symbols for these companies if applicable. Make sure you are giving stock tickers, not company names. For example, if the company is Apple, the stock ticker is AAPL. If the company is Tesla, the stock ticker is TSLA. Even if there are no stock companies directly, try to think of companies that are indirectly related or will be affected by the news. Only mention the top 3 companies affected and an analysis of why they are affected, how their stock prices might be affected, and what the future might hold for them.\n"
                  f"Format the response as JSON with keys 'insights', 'key_players', and 'tickers'. Make sure you dont include ``` json ``` tags in the response.",
        )
        try:
            return json.loads(response.output_text)
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error: Could not parse the response for URL: {url}")
            return {"insights": [], "key_players": [], "tickers": []}
    
    def process_news_data(self, news_data):
        """Process news data and extract insights"""
        # Display the news articles
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}                NEWS ARTICLES FOUND")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        # Extract URLs from the news data
        urls = []
        for i, article in enumerate(news_data, 1):
            if 'url' in article:
                urls.append(article['url'])
                print(f"{Fore.GREEN}{i}. {Fore.WHITE}{article['title']}")
                print(f"   {Fore.CYAN}{article['url']}")
                if 'description' in article:
                    print(f"   {Fore.YELLOW}{article['description'][:100]}...")
                print()
        
        if not urls:
            print(f"{Fore.RED}No URLs found in the news data.")
            time.sleep(1.5)
            return False
        
        # Reset data for new analysis
        self.config.all_insights = []
        self.config.all_key_players = []
        self.config.all_tickers = []
        
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}                ANALYZING ARTICLES")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        for i, url in enumerate(urls, 1):
            result = self.extract_insights_from_url(url, i)
            
            self.config.all_insights.append({
                "url": url,
                "insights": result.get("insights", []),
                "key_players": result.get("key_players", []),
                "tickers": result.get("tickers", [])
            })
            
            # Add to our overall collections
            for player in result.get("key_players", []):
                if player not in self.config.all_key_players:  # Avoid duplicates
                    self.config.all_key_players.append(player)
            
            for ticker in result.get("tickers", []):
                # Check if ticker is a string before adding to the list
                if isinstance(ticker, str) and ticker not in self.config.all_tickers:
                    self.config.all_tickers.append(ticker)
                elif isinstance(ticker, dict) and 'symbol' in ticker:
                    # If ticker is a dictionary with a 'symbol' key, add the symbol
                    symbol = ticker['symbol']
                    if symbol not in self.config.all_tickers:
                        self.config.all_tickers.append(symbol)
                elif isinstance(ticker, dict) and 'ticker' in ticker:
                    # If ticker is a dictionary with a 'ticker' key, add the ticker
                    ticker_symbol = ticker['ticker']
                    if ticker_symbol not in self.config.all_tickers:
                        self.config.all_tickers.append(ticker_symbol)
        
        return True


class BrainRotGenerator:
    """Handles brain rot content generation and video creation"""
    
    def __init__(self, config):
        self.config = config
    
    def generate_brain_rot_explanation(self):
        """Generate brain rot explanation from insights"""
        print(f"\n{Fore.CYAN}Generating brain rot explanation...")
        print(f"{Fore.CYAN}{'.' * 40}")
        
        # Show loading animation
        UIManager.display_loading("Generating", 3, 0.5)
        
        # Prepare a summary of insights
        insight_summary = []
        for insight in self.config.all_insights:
            for point in insight.get('insights', []):
                insight_summary.append(point)
        
        # Convert tickers to a list if it's a set
        ticker_list = list(self.config.all_tickers) if isinstance(self.config.all_tickers, set) else self.config.all_tickers
        
        # Generate the brain rot explanation
        response = self.config.openai_client.responses.create(
            model="gpt-4o",
            input=f"""
            Create a 'brain rot' style explanation about the following investment information.
            It should be:
            1. Super casual, using slang and internet speak
            2. Simplified to the extreme
            3. Entertaining and slightly absurd
            4. Around 150-200 words maximum
            5. Include emojis
            6. Mention the key players: {', '.join(self.config.all_key_players)}
            7. Mention the stock tickers: {', '.join(ticker_list)}
            8. Include some of these insights: {insight_summary[:3]}


            Here are a list of brainrot terms: skibidi gyatt rizz only in ohio duke dennis did you pray today livvy dunne rizzing up baby gronk sussy imposter pibby glitch in real life sigma alpha omega male grindset andrew tate goon cave freddy fazbear colleen ballinger smurf cat vs strawberry elephant blud dawg shmlawg ishowspeed a whole bunch of turbulence ambatukam bro really thinks he's carti literally hitting the griddy the ocky way kai cenat fanum tax garten of banban no edging in class not the mosquito again bussing axel in harlem whopper whopper whopper whopper 1 2 buckle my shoe goofy ahh aiden ross sin city monday left me broken quirked up white boy busting it down sexual style goated with the sauce john pork grimace shake kiki do you love me huggy wuggy nathaniel b lightskin stare biggest bird omar the referee amogus uncanny wholesome reddit chungus keanu reeves pizza tower zesty poggers kumalala savesta quandale dingle glizzy rose toy ankha zone thug shaker morbin time dj khaled sisyphus oceangate shadow wizard money gang ayo the pizza here PLUH nair butthole waxing t-pose ugandan knuckles family guy funny moments compilation with subway surfers gameplay at the bottom nickeh30 ratio uwu delulu opium bird cg5 mewing fortnite battle pass all my fellas gta 6 backrooms gigachad based cringe kino redpilled no nut november pokénut november foot fetish F in the chat i love lean looksmaxxing gassy social credit bing chilling xbox live mrbeast kid named finger better caul saul i am a surgeon hit or miss i guess they never miss huh i like ya cut g ice spice gooning fr we go gym kevin james josh hutcherson coffin of andy and leyley metal pipe falling
            
            The explanation should sound like a TikTok voiceover that would play over Subway Surfers gameplay.
            """
        )
        
        return response.output_text
    
    def get_eleven_labs_voices(self):
        """Get available Eleven Labs voices"""
        api_key = os.environ.get("ELEVEN_LABS_API_KEY")
        if not api_key:
            print(f"{Fore.RED}Error: ELEVEN_LABS_API_KEY not found.")
            return None
        
        url = "https://api.elevenlabs.io/v1/voices"
        
        headers = {
            "Accept": "application/json",
            "xi-api-key": api_key
        }
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                voices = response.json().get("voices", [])
                return voices
            else:
                print(f"{Fore.RED}Error: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)}")
            return None
    
    def select_voice(self):
        """Let user select an Eleven Labs voice"""
        voices = self.get_eleven_labs_voices()
        
        if not voices:
            print(f"{Fore.YELLOW}Using default voice (Rachel) as no voices could be retrieved.")
            return "21m00Tcm4TlvDq8ikWAM"  # Default to Rachel
        
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}                AVAILABLE VOICES")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        # Display available voices
        for i, voice in enumerate(voices, 1):
            print(f"{Fore.WHITE}{i}. {Fore.GREEN}{voice['name']} {Fore.CYAN}({voice['voice_id']})")
        
        print(f"{Fore.CYAN}{'=' * 60}")
        
        # Let user select a voice
        try:
            choice = input(f"{Fore.YELLOW}Select a voice (1-{len(voices)}) or press Enter for default: {Fore.WHITE}")
            
            if not choice:
                print(f"{Fore.GREEN}Using default voice (Rachel).")
                return "21m00Tcm4TlvDq8ikWAM"  # Default to Rachel
            
            choice = int(choice)
            if 1 <= choice <= len(voices):
                selected_voice = voices[choice-1]
                print(f"{Fore.GREEN}Selected voice: {selected_voice['name']}")
                return selected_voice['voice_id']
            else:
                print(f"{Fore.YELLOW}Invalid choice. Using default voice (Rachel).")
                return "21m00Tcm4TlvDq8ikWAM"  # Default to Rachel
        
        except ValueError:
            print(f"{Fore.YELLOW}Invalid input. Using default voice (Rachel).")
            return "21m00Tcm4TlvDq8ikWAM"  # Default to Rachel
    
    def text_to_speech(self, text, output_file="speech.mp3"):
        """Convert text to speech using Eleven Labs"""
        api_key = os.environ.get("ELEVEN_LABS_API_KEY")
        if not api_key:
            print(f"{Fore.RED}Error: ELEVEN_LABS_API_KEY not found. Cannot generate speech.")
            return None
        
        print(f"\n{Fore.CYAN}Converting text to speech...")
        print(f"{Fore.CYAN}{'.' * 40}")
        
        # Show loading animation
        UIManager.display_loading("Converting", 3, 0.5)
        
        # Let user select a voice
        voice_id = self.select_voice()
        
        # Eleven Labs API endpoint for text-to-speech
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        # Using the standard multilingual model
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.8,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        try:
            print(f"{Fore.CYAN}Sending request to Eleven Labs API...")
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                print(f"{Fore.GREEN}Successfully received audio from Eleven Labs!")
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                return output_file
            else:
                print(f"{Fore.RED}Error: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)}")
            return None
    
    def get_subway_surfers_video(self):
        """Get Subway Surfers video file path"""
        # Check for possible filenames
        possible_filenames = ["subway_surfers.mp4", "subway_surfers.mp4.mp4"]
        
        # Check if any of the possible files exist
        for video_file in possible_filenames:
            if os.path.exists(video_file):
                print(f"{Fore.GREEN}Found Subway Surfers video: {video_file}")
                return video_file
        
        # If no file was found, use the default name
        video_file = "subway_surfers.mp4"
        
        print(f"\n{Fore.CYAN}Looking for Subway Surfers video...")
        print(f"{Fore.CYAN}{'.' * 40}")
        
        # Show loading animation
        UIManager.display_loading("Searching", 5, 0.5)
        
        print(f"{Fore.YELLOW}Note: Could not find a Subway Surfers video.")
        print(f"{Fore.YELLOW}Please place a Subway Surfers video named '{video_file}' in the same directory.")
        
        # Return the expected file name even if it doesn't exist yet
        return video_file
    
    def create_brain_rot_video(self, audio_file, video_file, output_file="brain_rot_result.mp4"):
        """Create a brain rot video with audio and Peter Griffin overlay"""
        print(f"\n{Fore.CYAN}Creating brain rot video...")
        print(f"{Fore.CYAN}{'.' * 40}")
        
        # Show loading animation
        UIManager.display_loading("Creating video", 5, 0.5)
        
        try:
            # Load the video and audio
            video = VideoFileClip(video_file)
            audio = AudioFileClip(audio_file)
            
            # Load Peter Griffin image
            peter_img_path = "peter.png"
            print(f"{Fore.CYAN}Looking for Peter Griffin image at: {peter_img_path}")
            
            peter_img = None
            if os.path.exists(peter_img_path):
                print(f"{Fore.GREEN}Found Peter Griffin image!")
                try:
                    # Create an image clip from the Peter Griffin image
                    peter_img = ImageClip(peter_img_path)
                    
                    try:
                        # Resize the image to a much larger size
                        img_width = video.w * 0.5  # 50% of video width (was 25%)
                        peter_img = peter_img.resize(width=img_width)
                        print(f"{Fore.GREEN}Successfully resized Peter Griffin image")
                    except Exception as resize_error:
                        print(f"{Fore.YELLOW}Warning: Could not resize Peter Griffin image: {resize_error}")
                        print(f"{Fore.YELLOW}Using original image size")
                    
                    # Position in bottom left with some padding
                    peter_img = peter_img.set_position((20, video.h - peter_img.h - 20))
                    
                    # Set the duration to match the video
                    peter_img = peter_img.set_duration(video.duration)
                    
                    print(f"{Fore.GREEN}Peter Griffin overlay configured successfully!")
                except Exception as e:
                    print(f"{Fore.RED}Error setting up Peter Griffin overlay: {str(e)}")
                    peter_img = None
            else:
                print(f"{Fore.RED}Warning: Peter Griffin image not found at {peter_img_path}")
            
            # If the audio is longer than the video, loop the video
            if audio.duration > video.duration:
                # Calculate how many times to loop the video
                loops = int(audio.duration / video.duration) + 1
                print(f"{Fore.CYAN}Audio ({audio.duration:.2f}s) is longer than video ({video.duration:.2f}s). Looping video {loops} times.")
                
                # Set the duration of the video to match the audio
                video = video.set_duration(audio.duration)
            else:
                # If the video is longer than the audio, trim the video
                print(f"{Fore.CYAN}Video ({video.duration:.2f}s) is longer than audio ({audio.duration:.2f}s). Trimming video.")
                video = video.subclip(0, audio.duration)
            
            # Create the final video
            if peter_img is not None:
                print(f"{Fore.GREEN}Adding Peter Griffin overlay to video...")
                # Create composite video with Peter Griffin overlay
                final_video = CompositeVideoClip([video, peter_img])
                print(f"{Fore.GREEN}Composite video created with Peter Griffin overlay.")
            else:
                print(f"{Fore.YELLOW}Creating video without Peter Griffin overlay.")
                final_video = video
            
            # Set the audio of the video
            final_video = final_video.set_audio(audio)
            
            # Write the result to a file
            print(f"{Fore.CYAN}Writing video to file: {output_file}")
            final_video.write_videofile(output_file, codec='libx264', audio_codec='aac')
            
            # Close the clips to free up resources
            print(f"{Fore.CYAN}Closing video resources...")
            video.close()
            audio.close()
            if peter_img is not None:
                peter_img.close()
            final_video.close()
            
            return output_file
        
        except Exception as e:
            print(f"{Fore.RED}Error creating video: {str(e)}")
            traceback_info = traceback.format_exc()
            print(f"{Fore.RED}Traceback: {traceback_info}")
            return None


class InvestmentApp:
    """Main application class"""
    
    def __init__(self):
        self.config = Config()
        self.ui = UIManager()
        self.stock_analyzer = StockAnalyzer(self.config)
        self.news_analyzer = NewsAnalyzer(self.config, self.stock_analyzer)
        self.brain_rot = BrainRotGenerator(self.config)
    
    def do_research(self):
        """Research investment topics"""
        self.ui.clear_screen()
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}                INVESTMENT RESEARCH")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        user_query = input(f"\n{Fore.YELLOW}Enter your investment-related question: {Fore.WHITE}")
        if not user_query:
            print(f"{Fore.RED}No query entered. Returning to main menu.")
            time.sleep(1.5)
            return
        
        # Find news stories
        findings = self.news_analyzer.find_news_stories(user_query)
        
        try:
            # Parse the JSON response
            news_data = json.loads(findings)
            
            # Process news data and extract insights
            if self.news_analyzer.process_news_data(news_data):
                # Display the insights
                self.ui.display_insights(self.config.all_insights, self.config.all_key_players, self.config.all_tickers)
                
                # Ask if user wants to see stock prices
                choice = input(f"\n{Fore.YELLOW}Would you like to see current stock prices for these tickers? (y/n): {Fore.WHITE}")
                if choice.lower() == 'y':
                    self.stock_analyzer.display_stock_prices(self.config.all_tickers)
            
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error: Could not parse the JSON response.")
            time.sleep(1.5)
    
    def lookup_stock(self):
        """Look up specific stock ticker"""
        self.ui.clear_screen()
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}                STOCK TICKER LOOKUP")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        ticker = input(f"\n{Fore.YELLOW}Enter stock ticker symbol (e.g., AAPL): {Fore.WHITE}").strip().upper()
        if not ticker:
            print(f"{Fore.RED}No ticker entered. Returning to main menu.")
            time.sleep(1.5)
            return
        
        stock_info = self.stock_analyzer.get_stock_info_with_api(ticker)
        
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}                STOCK INFORMATION")
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.GREEN}[{ticker}] {Fore.WHITE}{stock_info}")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        input(f"\n{Fore.YELLOW}Press Enter to continue...")
    
    def brain_rot_mode(self):
        """Brain rot mode for generating TikTok-style content"""
        self.ui.clear_screen()
        print(f"{Fore.CYAN}{'=' * 60}")
        print(f"{Fore.YELLOW}                BRAIN ROT MODE")
        print(f"{Fore.CYAN}{'=' * 60}")
        
        user_query = input(f"\n{Fore.YELLOW}Enter your investment-related question: {Fore.WHITE}")
        if not user_query:
            print(f"{Fore.RED}No query entered. Returning to main menu.")
            time.sleep(1.5)
            return
        
        # Find news stories
        findings = self.news_analyzer.find_news_stories(user_query)
        
        try:
            # Parse the JSON response
            news_data = json.loads(findings)
            
            # Process news data and extract insights
            if self.news_analyzer.process_news_data(news_data):
                # Generate the brain rot explanation
                brain_rot_text = self.brain_rot.generate_brain_rot_explanation()
                
                # Display the brain rot explanation
                print(f"\n{Fore.CYAN}{'=' * 60}")
                print(f"{Fore.YELLOW}                BRAIN ROT EXPLANATION")
                print(f"{Fore.CYAN}{'=' * 60}")
                print(f"{Fore.WHITE}{brain_rot_text}")
                print(f"{Fore.CYAN}{'=' * 60}")
                
                # Ask if user wants to create a brain rot video
                choice = input(f"\n{Fore.YELLOW}Would you like to create a brain rot video? (y/n): {Fore.WHITE}")
                if choice.lower() == 'y':
                    # Convert text to speech
                    speech_file = self.brain_rot.text_to_speech(brain_rot_text)
                    
                    if speech_file:
                        # Get the Subway Surfers video
                        video_file = self.brain_rot.get_subway_surfers_video()
                        
                        # Create the brain rot video
                        result_file = self.brain_rot.create_brain_rot_video(speech_file, video_file)
                        
                        if result_file:
                            print(f"\n{Fore.GREEN}Brain rot video created successfully: {Fore.WHITE}{result_file}")
                            print(f"{Fore.YELLOW}You can find it in the current directory.")
                        else:
                            print(f"\n{Fore.RED}Failed to create brain rot video.")
                    else:
                        print(f"\n{Fore.RED}Failed to convert text to speech.")
                
                input(f"\n{Fore.YELLOW}Press Enter to continue...")
                
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error: Could not parse the JSON response.")
            time.sleep(1.5)
    
    def run(self):
        """Run the application"""
        try:
            while True:
                self.ui.display_welcome()
                choice = self.ui.display_menu()
                
                if choice == '1':
                    self.do_research()
                elif choice == '2':
                    self.lookup_stock()
                elif choice == '3':
                    self.ui.clear_screen()
                    print(f"{Fore.YELLOW}Feature coming soon: View saved research")
                    time.sleep(1.5)
                elif choice == '4':
                    self.brain_rot_mode()
                elif choice == '5':
                    self.ui.clear_screen()
                    print(f"{Fore.CYAN}{'=' * 60}")
                    print(f"{Fore.YELLOW}Thank you for using the Investment Research Assistant!")
                    print(f"{Fore.CYAN}{'=' * 60}")
                    time.sleep(1)
                    sys.exit(0)
                else:
                    print(f"{Fore.RED}Invalid choice. Please try again.")
                    time.sleep(1)
        except KeyboardInterrupt:
            self.ui.clear_screen()
            print(f"{Fore.CYAN}{'=' * 60}")
            print(f"{Fore.YELLOW}Program terminated by user. Goodbye!")
            print(f"{Fore.CYAN}{'=' * 60}")
            sys.exit(0)


# Run the program
if __name__ == "__main__":
    app = InvestmentApp()
    app.run()