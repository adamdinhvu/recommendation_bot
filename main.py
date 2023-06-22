from curator import Recbot
from dotenv import load_dotenv

load_dotenv(".env")

if __name__ == "__main__":
    bot = Recbot()
    bot.run()