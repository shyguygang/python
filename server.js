require('dotenv').config();
const express = require('express');
const TelegramBot = require('node-telegram-bot-api');
const ton = require('./ton');

const app = express();
const port = process.env.PORT || 3001;

const bot = new TelegramBot(process.env.BOT_TOKEN, { polling: true });

bot.onText(/\/start/, async (msg) => {
  const chatId = msg.chat.id;
  bot.sendMessage(chatId, 'Welcome to the TON Activity Feed Bot! Use /feed to view the latest account activity.');
});

bot.onText(/\/feed/, async (msg) => {
  const chatId = msg.chat.id;
  await showFeed(chatId);
});

async function showFeed(chatId, cursor = null) {
  const { accounts, pageInfo } = await ton.getRecentActivity(cursor);

  if (accounts.length === 0) {
    bot.sendMessage(chatId, 'No recent activity found.');
    return;
  }

  let messageText = 'Recent Account Activity:\n\n';
  accounts.forEach((account, index) => {
    messageText += `${index + 1}. Account: ${account.id}\n`;
    messageText += `   Balance: ${account.balance} nanotons\n`;
    messageText += `   Last Activity: ${new Date(account.lastActivityTime).toLocaleString()}\n\n`;
  });

  const keyboard = [];
  if (pageInfo.hasNextPage) {
    keyboard.push([{ text: 'Load More', callback_data: `more_${pageInfo.endCursor}` }]);
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
    const cursor = data.split('_')[1];
    await showFeed(message.chat.id, cursor);
  }

  bot.answerCallbackQuery(callbackQuery.id);
});

app.get('/', (req, res) => {
  res.send('TON Activity Feed Bot Server is running!');
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});

console.log('Bot is running...');