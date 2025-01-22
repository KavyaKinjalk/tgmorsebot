# Morse Code Telegram Bot

This project is a Telegram bot that converts text to and from Morse code and can generate Morse code audio.

## Project Structure

- `bot.py`: Main bot script (contains the Telegram client initialization, command handlers, and `generate_morse_audio` which uses pydub).
- `morse.py`: Contains `encrypt` and `decrypt` functions for Morse code conversion credit to Geeks4Geeks for this code. [Source](https://www.geeksforgeeks.org/morse-code-translator-python/).
- `requirements.txt`: Project dependencies.
- `.env`: Environment variables (API credentials).
- `user_configs.json`: Stores user-specific configuration for generating audio.

## Installation
1. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2. Set up API credentials in .env or rename [sample.env](/sample.env).

    - API ID: Obtain from my.telegram.org
    - API Hash: Obtain from my.telegram.org
    - Bot Token: Obtain from [@BotFather](https://telegram.me/BotFather)

3. Run the app with
    ```bash
    python3 bot.py
    ```
