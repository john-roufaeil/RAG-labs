# AI Chef Frontend

A beautiful React application for interacting with the AI Chef backend API.

## Features

- 💬 Real-time chat with AI Chef
- 🎨 Adjustable chef personality (creativity level)
- 📝 Verbosity control (concise to detailed)
- 📊 Session tracking with ingredient collection
- 🎯 Step-by-step guidance through cooking process
- 📱 Responsive design (works on mobile and desktop)

## Prerequisites

- Node.js 14+ and npm
- Backend API running on http://localhost:8000

## Installation

```bash
cd frontend
npm install
```

## Configuration

Copy `.env.example` to `.env` and update the API URL if needed:

```bash
cp .env.example .env
```

**Default .env:**
```
REACT_APP_API_URL=http://localhost:8000
```

## Running the App

```bash
npm start
```

The app will open at `http://localhost:3000`

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatWindow.jsx      # Message display
│   │   ├── ChatInput.jsx       # User input area
│   │   └── Sidebar.jsx         # Settings & info
│   ├── services/
│   │   └── chefAPI.js          # API calls
│   ├── styles/
│   │   ├── App.css
│   │   ├── ChatWindow.css
│   │   ├── ChatInput.css
│   │   └── Sidebar.css
│   ├── App.jsx                 # Main app component
│   └── index.js                # React entry point
├── public/
│   └── index.html              # HTML template
├── package.json                # Dependencies
└── .env                        # Environment variables
```

## Usage

1. **Start a Conversation**: Greet the chef and tell them what you want to cook
2. **List Ingredients**: Provide all available ingredients
3. **Adjust Personality**: Use sidebar to set creativity and verbosity levels
4. **Get Guidance**: Follow the chef's step-by-step instructions
5. **Reset**: Click "Reset Session" to start over

## API Integration

The app communicates with the backend via the `chefAPI` service:

- `GET /health` - Check API health
- `POST /chat` - Send message to chef
- `POST /set-personality` - Configure chef behavior
- `GET /session/{id}` - Get session history
- `POST /reset/{id}` - Reset session

## Troubleshooting

### "Failed to fetch" error
- Ensure backend is running on http://localhost:8000
- Check REACT_APP_API_URL in .env

### Chef doesn't respond
- Check browser console for errors
- Verify OpenAI API key is set in backend
- Check backend logs for issues

### Styles not loading
- Clear browser cache
- Run `npm install` again
- Try `npm start` in a new terminal

## Building for Production

```bash
npm run build
```

Builds the app for production in the `build` folder.

## Technologies

- React 18
- Axios for HTTP requests
- CSS3 for styling
- React Scripts for build tooling
