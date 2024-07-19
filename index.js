require('dotenv').config();
const { program } = require('commander');
const { ImmutableX, Config } = require('@imtbl/sdk');
const fs = require('fs').promises;
const path = require('path');

let client;

async function connectWallet() {
  const config = {
    ...Config.SANDBOX,
    apiAddress: process.env.PROXY_URL || 'http://localhost:8080/api/v1'
  };
  client = await ImmutableX.build({ config });
  const { address } = await client.getWallet().connect({});
  console.log(`Wallet connected: ${address}`);
}

async function uploadToIPFS(filePath) {
  // This is a placeholder function
  console.log(`Simulating upload of ${filePath} to IPFS`);
  return `ipfs://QmSimulatedHash${Date.now()}`;
}

async function mintNFT(tokenName, description, imagePath) {
  if (!client) {
    console.log('Please connect wallet first.');
    return;
  }

  const imageUri = await uploadToIPFS(imagePath);
  const metadata = {
    name: tokenName,
    description: description,
    image: imageUri
  };

  const metadataUri = await uploadToIPFS(JSON.stringify(metadata));

  try {
    const result = await client.mintNFT({
      tokenName,
      tokenDescription: description,
      tokenURI: metadataUri,
      // Add other required parameters
    });
    console.log(`NFT minted successfully! Transaction ID: ${result.txHash}`);
  } catch (error) {
    console.error('Error minting NFT:', error);
  }
}

async function createCollection(name, description, iconPath) {
  if (!client) {
    console.log('Please connect wallet first.');
    return;
  }

  const iconUri = await uploadToIPFS(iconPath);

  try {
    const result = await client.createCollection({
      name,
      description,
      iconUrl: iconUri,
      // Add other required parameters
    });
    console.log(`Collection created successfully! Collection address: ${result.address}`);
  } catch (error) {
    console.error('Error creating collection:', error);
  }
}

program
  .command('connect')
  .description('Connect wallet')
  .action(connectWallet);

program
  .command('mint <tokenName> <description> <imagePath>')
  .description('Mint an NFT')
  .action(mintNFT);

program
  .command('create-collection <name> <description> <iconPath>')
  .description('Create a collection')
  .action(createCollection);

program.parse(process.argv);