const axios = require('axios');

const GRAPHQL_ENDPOINT = process.env.GRAPHQL_ENDPOINT;

async function queryGraphQL(query, variables = {}) {
  try {
    const response = await axios.post(GRAPHQL_ENDPOINT, { query, variables });
    return response.data.data;
  } catch (error) {
    console.error('GraphQL Error:', error.response ? error.response.data : error.message);
    throw new Error('Failed to fetch data from TON');
  }
}

async function getRecentActivity(cursor = null, limit = 10) {
  const query = `
    query ($cursor: Cursor, $limit: Int!) {
      allAccounts(first: $limit, after: $cursor, orderBy: LAST_ACTIVITY_TIME_DESC) {
        edges {
          cursor
          node {
            id
            balance
            lastActivityTime
          }
        }
        pageInfo {
          hasNextPage
          endCursor
        }
      }
    }
  `;

  try {
    const data = await queryGraphQL(query, { cursor, limit });
    return {
      accounts: data.allAccounts.edges.map(edge => ({
        id: edge.node.id,
        balance: edge.node.balance,
        lastActivityTime: edge.node.lastActivityTime,
        cursor: edge.cursor
      })),
      pageInfo: data.allAccounts.pageInfo
    };
  } catch (error) {
    console.error('Failed to fetch recent activity:', error);
    return { accounts: [], pageInfo: { hasNextPage: false, endCursor: null } };
  }
}

module.exports = {
  getRecentActivity
};