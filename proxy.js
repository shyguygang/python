const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

app.use('/api', createProxyMiddleware({ 
  target: 'https://api.sandbox.x.immutable.com',
  changeOrigin: true,
  pathRewrite: {'^/api' : ''}
}));

app.listen(8080, () => {
  console.log('Proxy server running on http://localhost:8080');
});