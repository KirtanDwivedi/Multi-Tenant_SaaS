# Multi-Tenant API Connector & RAG Chatbot

A Single Page Application (SPA) that connects to third-party APIs (GitHub, Notion, Discord, StackOverflow), scrapes their data into local JSON storage, and allows an AI chatbot to answer queries based on that data.

## Features

- **Multi-Tenant API Connections**: Connect multiple APIs (GitHub, Notion, Discord, StackOverflow)
- **Local RAG Storage**: Data is stored in local JSON files for privacy
- **AI-Powered Chat**: Chat with your connected data sources (Gemini API ready)
- **OpenAI-Style UI**: Modern, clean interface with dark theme
- **No Database Required**: Everything stored locally in JSON files

## Tech Stack

- **Frontend**: React + Vite, Tailwind CSS, Lucide React Icons
- **Backend**: FastAPI (Python), Uvicorn
- **AI**: Google Gemini API (gemini-1.5-flash) - ready to configure
- **Storage**: Local JSON files (data.json, content.json)

## Project Structure

```
multi_tenate/
├── client/                 # React Frontend
│   ├── src/
│   │   ├── components/     
│   │   │   ├── ApiDropdown.jsx    # API selector dropdown
│   │   │   ├── LoginModal.jsx     # Authentication popup
│   │   │   └── DocsOverlay.jsx    # Documentation overlay
│   │   ├── App.jsx         # Main application
│   │   ├── index.css       # Styles & theme
│   │   └── main.jsx        # Entry point
│   └── package.json
├── server/                 # FastAPI Backend
│   ├── data/               
│   │   ├── data.json       # API connection metadata
│   │   └── content.json    # Scraped content for RAG
│   ├── main.py             # FastAPI server & routes
│   ├── auth.py             # Authentication (to be implemented)
│   ├── scrapers.py         # Scraping logic (to be implemented)
│   └── .env                # Environment variables
├── agent.md                # Project requirements
└── README.md               # This file
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- pip

### Installation

#### 1. Install Backend Dependencies

```bash
cd server
pip install fastapi uvicorn python-dotenv pydantic google-generativeai
```

#### 2. Install Frontend Dependencies

```bash
cd client
npm install
```

### Running the Application

#### Start the Backend Server

```bash
cd server
python main.py
```

The server will start at `http://localhost:8000`

#### Start the Frontend (in a new terminal)

```bash
cd client
npm run dev
```

The frontend will start at `http://localhost:5173`

## API Configuration

### Setting up Gemini API

1. Get your Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Update `server/.env`:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### Setting up Google OAuth (Optional)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add the credentials to your frontend LoginModal component

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Server status |
| GET | `/api/links` | Get all connected APIs |
| POST | `/api/add-api` | Add a new API connection |
| POST | `/api/chat` | Send a chat message |
| POST | `/api/login` | User login |
| DELETE | `/api/link/{index}` | Remove an API connection |
| GET | `/api/content` | Get all stored RAG content |

## Usage

### Adding an API Connection

1. Click "Add API" button in the top right
2. Select the platform (GitHub, Notion, etc.)
3. Enter your API key
4. Give it a display name
5. Click "Connect"

### Chatting with Your Data

1. Start a new conversation or click on a connected API in the sidebar
2. Type your question in the input box
3. The AI will respond based on your connected data sources

### Renaming Conversations

Click on the conversation title in the sidebar to edit it.

## Data Storage

All data is stored locally in the `server/data/` directory:

- **data.json**: Stores API connection metadata (platform, API key, display name)
- **content.json**: Stores scraped content for RAG (source, text, timestamps)

## Customization

### Theme Colors

The app uses OpenAI-style colors defined in `client/src/index.css`:
- Main Background: `#212121`
- Sidebar Background: `#171717`
- Input Background: `#303030`

### Adding New Platforms

To add support for new platforms:

1. Add the platform to the dropdown in `client/src/App.jsx`
2. Implement scraping logic in `server/scrapers.py`
3. Add appropriate API handling in `server/main.py`

## Troubleshooting

### Server won't start

- Make sure Python 3.9+ is installed
- Check if port 8000 is available
- Verify all dependencies are installed: `pip install -r requirements.txt`

### Frontend can't connect to backend

- Ensure the backend is running on port 8000
- Check CORS settings in `server/main.py`
- Verify `API_BASE` in `client/src/App.jsx` matches your server URL

### Chat responses not working

- Check if `server/data/content.json` has data
- Verify Gemini API key is set in `.env`
- Check browser console for errors

## Future Enhancements

- [ ] Implement actual GitHub scraping in `scrapers.py`
- [ ] Implement actual Notion scraping in `scrapers.py`
- [ ] Add Google OAuth authentication
- [ ] Implement Gemini RAG integration in chat endpoint
- [ ] Add file upload support
- [ ] Add conversation history persistence
- [ ] Add settings panel for API management

## License

MIT License