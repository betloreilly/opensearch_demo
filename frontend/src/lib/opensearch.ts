import { Client } from '@opensearch-project/opensearch'

// OpenSearch client singleton
let client: Client | null = null

export function getOpenSearchClient(): Client {
  if (!client) {
    client = new Client({
      node: process.env.OPENSEARCH_URL || 'http://localhost:9200',
      ssl: {
        rejectUnauthorized: false,
      },
    })
  }
  return client
}
