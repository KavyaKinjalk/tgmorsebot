import asyncio
from pyrogram import Client, filters, enums
import os
import json
from dotenv import load_dotenv
from pydub import AudioSegment
from pydub.generators import Sine
import morse
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.types import ForceReply 

# Load environment variables
load_dotenv()
api_id = os.environ['api_id']
api_hash = os.environ['api_hash']
bot_token = os.environ['bot_token']

# Initialize bot
app = Client(
    "my_bot",
    api_id=api_id, api_hash=api_hash,
    bot_token=bot_token
)

# Default configuration
default_config = {
    "dd": 100,  
    "dashd": 300,
    "FREQ": 440,  
    "VOL": -10,  
    "DBW": 1000  # Gap between words in ms
}

config_file = "user_configs.json"
if os.path.exists(config_file):
    with open(config_file, "r") as f:
        user_configs = json.load(f)
else:
    user_configs = {}

def get_user_config(user_id):
    if str(user_id) not in user_configs:
        user_configs[str(user_id)] = default_config.copy()
        save_user_configs()
    return user_configs[str(user_id)]

def save_user_configs():
    with open(config_file, "w") as f:
        json.dump(user_configs, f)

# Generate Morse code audio
def generate_morse_audio(text, config):
    dot = Sine(config["FREQ"]).to_audio_segment(duration=config["dd"]).apply_gain(config["VOL"])
    dash = Sine(config["FREQ"]).to_audio_segment(duration=config["dashd"]).apply_gain(config["VOL"])
    intra_char_gap = AudioSegment.silent(duration=config["dd"])  
    inter_char_gap = AudioSegment.silent(duration=config["dashd"])
    word_gap = AudioSegment.silent(duration=config["DBW"])

    MORSE_CODE_DICT = morse.MORSE_CODE_DICT 

    audio = AudioSegment.silent(duration=0)

    for char in text.upper():
        if char in MORSE_CODE_DICT:
            morse_code = MORSE_CODE_DICT[char]
            for symbol in morse_code:
                if symbol == '.':
                    audio += dot + intra_char_gap
                elif symbol == '-':
                    audio += dash + intra_char_gap
            audio = audio[:-len(intra_char_gap)] + inter_char_gap
        elif char == ' ':
            audio += word_gap
    return audio

# Start message
@app.on_message(filters.command("start"))
async def startmsg(client, message):
    await message.reply(
        "Hello! I'm your Morse encoder/decoder bot. I can also generate Morse code audio.\n"
        "Use `/help` to learn more.",
        parse_mode=enums.ParseMode.MARKDOWN,
    )

# Help message
@app.on_message(filters.command("help"))
async def helpmsg(client, message):
    await message.reply(
        "Commands:\n"
        "`/en <message>`: Encode a message to Morse code.\n"
        "`/de <message>`: Decode a Morse code message.\n"
        "/config: Configure parameters like dot, dash, frequency, volume, or word gap.",
        "/showconfig: Show current configuration.",
        parse_mode=enums.ParseMode.MARKDOWN,
    )

# Encode to Morse code
@app.on_message(filters.command("en"))
async def encode(client, message):
    user_id = message.from_user.id
    actualtext = message.text[4:]
    morse_code = morse.encrypt(actualtext)
    text = f"In Morse code:`{morse_code}`"
    await message.reply(text, parse_mode=enums.ParseMode.MARKDOWN)

    audio = generate_morse_audio(actualtext, get_user_config(user_id))
    output_file = f"{actualtext}.wav"
    audio.export(output_file, format="wav")
    await app.send_document(message.chat.id, output_file)
    os.remove(output_file)

# Decode from Morse code
@app.on_message(filters.command("de"))
async def decode(client, message):
    actualtext = message.text[4:]
    english_text = morse.decrypt(actualtext).lower()
    text = f"In English: `{english_text}`"
    await message.reply(text, parse_mode=enums.ParseMode.MARKDOWN)

## TODO: DECODE MORSE CODE AUDIO HERE AT SOME POINT IN LIFE

@app.on_message(filters.command("showconfig"))
async def show_config_command(client, message):
    user_id = message.from_user.id
    user_config = get_user_config(user_id)
    config_lines = [f"**{k}**: {v}" for k, v in user_config.items()]
    config_text = "\n".join(config_lines)
    await message.reply(
        f"**Your current configuration:**\n{config_text}"
    )

# Set configuration values
@app.on_message(filters.command("config"))
async def set_config(client, message):
    user_id = message.from_user.id
    user_config = get_user_config(user_id)
    
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Dot Duration", callback_data="config_dd")],
            [InlineKeyboardButton("Dash Duration", callback_data="config_dashd")],
            [InlineKeyboardButton("Frequency", callback_data="config_FREQ")],
            [InlineKeyboardButton("Volume", callback_data="config_VOL")],
            [InlineKeyboardButton("Word Gap", callback_data="config_DBW")],
        ]
    )
    
    await message.reply("Choose a configuration to set: \n"
                        "Dot Duration (in ms): Duration of a dot in Morse code.\n"
                        "Dash Duration (in ms): Duration of a dash in Morse code.\n"
                        "Frequency (in Hz): Frequency of the Morse code tone.\n"
                        "Volume (in dB): Volume of the Morse code tone.\n"
                        "Word Gap (in ms): Gap between words in Morse code.\n"
                        , reply_markup=keyboard)

@app.on_callback_query(filters.regex(r"config_"))
async def on_callback_query(client, callback_query):
    user_id = callback_query.from_user.id
    user_config = get_user_config(user_id)
    config_key = callback_query.data.split("_")[1]
   # await callback_query.message.edit_text(f"Enter new value for {config_key}.", reply_markup=ForceReply())
    await app.send_message(callback_query.message.chat.id, f"Enter new value for {config_key}. ", reply_to_message_id=callback_query.message.id, reply_markup=ForceReply(selective=True))

    

@app.on_message(filters.reply & filters.text)
async def on_reply(client, message):
    if not message.reply_to_message:
        await message.reply("Please reply to a valid configuration prompt.")
        return

    user_id = message.from_user.id
    user_config = get_user_config(user_id)
    
    try:
        parts = message.reply_to_message.text.split()
        #probably a better way to do this. idk how
        config_key = parts[4].rstrip(".")
        value = message.text

        if config_key in ["dd", "dashd", "FREQ", "DBW"]:
            value = int(value)
        elif config_key == "VOL":
            value = float(value)

        if config_key in user_config:
            user_config[config_key] = value
            save_user_configs()
            await message.reply(f"Configuration `{config_key}` updated to `{value}`.")
        else:
            await message.reply(f"Invalid configuration key: `{config_key}`.")
    except (IndexError, ValueError) as e:
        print(f"Error: {e}")
        await message.reply("Invalid input. Please enter a valid value.")

app.run()
