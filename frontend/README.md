# RAG Chat UI

A modern, beautiful chat interface for your RAG system built with Next.js 14. Users can ask questions and receive AI-powered responses grounded in your documents.

## Features

- **Modern Chat Interface**: Clean, responsive UI with markdown support
- **Real-time Responses**: Powered by Langflow and OpenSearch
- **Session Management**: Maintains conversation context
- **Error Handling**: Graceful error messages and loading states

## Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Next.js UI    │────▶│   Langflow   │────▶│  OpenSearch │
│   (port 3000)   │     │  (port 7860) │     │ (port 9200) │
└─────────────────┘     └──────────────┘     └─────────────┘
```

## Quick Start

### Prerequisites

- Node.js 18+
- Langflow running with your RAG flow
- OpenSearch running (via Docker)

### Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment template
cp env-example.txt .env.local

# Edit .env.local with your values
# Required:
#   LANGFLOW_FLOW_ID - Your Langflow flow ID
# Optional:
#   LANGFLOW_URL - Default: http://localhost:7860
#   LANGFLOW_API_KEY - If your Langflow requires authentication
```

### Run Development Server

```bash
npm run dev
```

Open http://localhost:3000 in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LANGFLOW_URL` | Langflow API URL | `http://localhost:7860` | No |
| `LANGFLOW_FLOW_ID` | Your Langflow flow ID | - | Yes |
| `LANGFLOW_API_KEY` | API key if Langflow auth is enabled | - | No |

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   └── chat/
│   │   │       └── route.ts          # Chat API endpoint
│   │   ├── globals.css               # Global styles
│   │   ├── layout.tsx                # Root layout
│   │   └── page.tsx                  # Main chat interface
│   └── lib/
│       └── opensearch.ts             # OpenSearch client (utility)
├── package.json
└── tailwind.config.ts
```

## API Endpoints

### POST /api/chat

Send a message to the RAG system.

**Request:**
```json
{
  "message": "What is the daily ATM limit?",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "answer": "The daily ATM withdrawal limit is $500...",
  "session_id": "abc-123"
}
```

**Error Response:**
```json
{
  "error": "Failed to get response from Langflow"
}
```

## Customization

### Styling

The UI uses Tailwind CSS with a custom color scheme. Edit `src/app/globals.css` to customize:

- Color palette (teal-accent, ocean, coral, etc.)
- Glassmorphism effects
- Typography
- Animations

### Chat Interface

Edit `src/app/page.tsx` to customize:

- Welcome message
- Suggested questions
- Message display format
- Loading states

### Langflow Integration

Edit `src/app/api/chat/route.ts` to customize:

- Request/response format
- Error handling
- Session management
- Response parsing logic

## Development

```bash
# Run development server with hot reload
npm run dev

# Type checking
npx tsc --noEmit

# Lint code
npm run lint

# Build for production
npm run build

# Start production server
npm start
```

## Troubleshooting

### "Failed to connect to Langflow"

**Solution:**
- Verify Langflow is running: http://localhost:7860
- Check `LANGFLOW_FLOW_ID` in `.env.local` matches your flow
- Ensure Langflow is accessible from Next.js server

### "Langflow returned an error page"

**Solution:**
- The flow ID is incorrect or doesn't exist
- In Langflow, go to your flow → Settings → Copy the Flow ID
- Update `LANGFLOW_FLOW_ID` in `.env.local`

### Chat shows no response

**Solution:**
- Check browser console for errors
- Verify OpenSearch is running: http://localhost:9200
- Ensure documents are ingested into OpenSearch
- Check Langflow flow is properly configured

### Build errors

**Solution:**
```bash
# Clear cache and reinstall
rm -rf node_modules .next
npm install
npm run build
```

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Markdown**: react-markdown
- **HTTP Client**: Fetch API
- **TypeScript**: Full type safety

## Performance

- Server-side API routes prevent CORS issues
- Streaming responses for real-time feel
- Optimized bundle size with Next.js
- Static generation where possible

## Security

- API keys stored in environment variables (server-side only)
- No client-side exposure of sensitive data
- CORS properly configured
- Input sanitization on API routes
