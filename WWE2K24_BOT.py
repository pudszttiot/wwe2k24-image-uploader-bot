import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from PIL import Image
from io import BytesIO

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Define the resizing options
resize_options = {
    'face': (512, 512),
    'logo': (1024, 1024),
    'banner': (1024, 256)
}

# Max file size (Telegram limit)
TELEGRAM_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Yo! Send me an image and I'll resize it for WWE 2K24!\n\n"
        "After you send an image, you'll pick what type it is (Face, Logo, Banner)."
    )

async def help_command(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "How to use me:\n\n"
        "1. Send me an image.\n"
        "2. Choose whether it's a Face, Logo, or Banner.\n"
        "3. I'll resize it to the correct WWE 2K24 dimensions.\n"
        "4. If it's too big, I'll compress it for you under 20MB!\n\n"
        "Supported sizes:\n"
        "• Face: 512x512\n"
        "• Logo: 1024x1024\n"
        "• Banner: 1024x256"
    )

async def handle_image(update: Update, context: CallbackContext):
    photo = update.message.photo[-1]  # Get the highest resolution photo
    file = await photo.get_file()
    file_bytes = await file.download_as_bytearray()

    context.user_data['image'] = file_bytes

    keyboard = [
        [InlineKeyboardButton("Face (512x512)", callback_data='face')],
        [InlineKeyboardButton("Logo (1024x1024)", callback_data='logo')],
        [InlineKeyboardButton("Banner (1024x256)", callback_data='banner')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('What type of image is this?', reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    choice = query.data
    size = resize_options.get(choice)

    if 'image' not in context.user_data:
        await query.edit_message_text("No image found. Please send an image first.")
        return

    # Show processing message
    await query.edit_message_text("Processing your image... please wait!")

    original_image = Image.open(BytesIO(context.user_data['image']))

    resized_image = original_image.resize(size, Image.LANCZOS)

    # Save initially as PNG
    buffer = BytesIO()
    buffer.name = f"wwe2k24_{choice}.png"
    resized_image.save(buffer, format='PNG')
    buffer.seek(0)

    # If bigger than Telegram limit, compress it as JPEG
    if buffer.getbuffer().nbytes > TELEGRAM_MAX_FILE_SIZE:
        await query.message.reply_text("Image is too large! Compressing...")

        # Try saving as JPEG with reduced quality
        compressed_buffer = BytesIO()
        compressed_buffer.name = f"wwe2k24_{choice}.jpg"

        quality = 90
        while True:
            compressed_buffer.seek(0)
            compressed_buffer.truncate()
            resized_image.save(compressed_buffer, format='JPEG', quality=quality)
            compressed_buffer.seek(0)

            if compressed_buffer.getbuffer().nbytes <= TELEGRAM_MAX_FILE_SIZE or quality <= 30:
                break
            quality -= 10

        await query.message.reply_document(compressed_buffer, filename=compressed_buffer.name)
    else:
        await query.message.reply_document(buffer, filename=buffer.name)

    # Confirm it's done
    await query.message.reply_text("Done! Here you go, ready for WWE 2K24!")

def main():
    app = ApplicationBuilder().token('7877122235:AAHMaF46El0rkyoY9IM8I_S5Jx5uOUtQRxg').build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(CallbackQueryHandler(button))

    app.run_polling()

if __name__ == '__main__':
    main()
