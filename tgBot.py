const TelegramBot = require('node-telegram-bot-api');

// replace 'YOUR_BOT_TOKEN' with the token you received from BotFather
const token = '7498773145:AAFbtAwryLpSjxWQxbmvm6pcSAWhToJDzRA';
const TelegramBot = require('node-telegram-bot-api');

// Create a bot that uses 'polling' to fetch new updates
const bot = new TelegramBot(token, {polling: true});

// Respond to /start command
bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  bot.sendMessage(chatId, 'Hello! I am a simple bot. Try /help to see what I can do.');
});

// Respond to /help command
bot.onText(/\/help/, (msg) => {
  const chatId = msg.chat.id;
  bot.sendMessage(chatId, 'Available commands:\n/start - Start the bot\n/help - Show this help message');
});

// Log errors
bot.on('polling_error', (error) => {
  console.log(error);
});

console.log('Bot is running...');