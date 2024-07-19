require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const axios = require('axios');

const bot = new TelegramBot(process.env.BOT_TOKEN, { polling: true });
const UNITON_BOT = '@unitonaibot';

let userFeed = [];

bot.onText(/\/start/, (msg) => {
  const chatId = msg.chat.id;
  bot.sendMessage(chatId, 'Welcome! Use /post to create a new post, or /feed to view your feed.');
});

bot.onText(/\/post (.+)/, async (msg, match) => {
  const chatId = msg.chat.id;
  const postContent = match[1];

  try {
    // Send post to @unitonai
    await bot.sendMessage(UNITON_BOT, `/create_post ${postContent}`);
    
    // Add post to local feed
    userFeed.unshift({ content: postContent, timestamp: new Date() });
    
    bot.sendMessage(chatId, 'Post created successfully!');
  } catch (error) {
    console.error('Error creating post:', error);
    bot.sendMessage(chatId, 'Sorry, there was an error creating your post.');
  }
});

bot.onText(/\/feed/, async (msg) => {
  const chatId = msg.chat.id;
  await showFeed(chatId);
});

async function showFeed(chatId, page = 0, pageSize = 5) {
  const start = page * pageSize;
  const end = start + pageSize;
  const feedItems = userFeed.slice(start, end);

  if (feedItems.length === 0) {
    bot.sendMessage(chatId, 'Your feed is empty. Use /post to create a new post.');
    return;
  }

  let messageText = 'Your Feed:\n\n';
  feedItems.forEach((item, index) => {
    messageText += `${start + index + 1}. ${item.content}\n`;
    messageText += `   Posted at: ${item.timestamp.toLocaleString()}\n\n`;
  });

  const keyboard = [];
  if (end < userFeed.length) {
    keyboard.push([{ text: 'Load More', callback_data: `more_${page + 1}` }]);
  }

  const options = {
    reply_markup: {
      inline_keyboard: keyboard
    }
  };

  bot.sendMessage(chatId, messageText, options);
}

bot.on('callback_query', async (callbackQuery) => {
  const message = callbackQuery.message;
  const data = callbackQuery.data;

  if (data.startsWith('more_')) {
    const page = parseInt(data.split('_')[1]);
    await showFeed(message.chat.id, page);
  }

  bot.answerCallbackQuery(callbackQuery.id);
});

console.log('Bot is running...');