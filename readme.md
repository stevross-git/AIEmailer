# AI Email Assistant

A comprehensive AI-powered email management system with Microsoft 365 integration, intelligent analysis, and chat-based assistance.

## 🚀 Features

### Core Email Management
- **Microsoft 365 Integration**: Seamless sync with Outlook/Exchange emails
- **Real-time Email Sync**: Automatic synchronization of up to 50 emails per session
- **Email Status Management**: Mark emails as read/unread with instant updates
- **Email Sending**: Send emails directly through Microsoft Graph API
- **Individual Email Views**: Detailed email pages with full content display

### AI-Powered Intelligence
- **Smart Email Analysis**: Automatic categorization, tagging, and sentiment analysis
- **Priority Scoring**: Intelligent priority assessment based on content and context
- **AI Chat Assistant**: Context-aware chat interface for email-specific assistance
- **Email Summarization**: AI-generated summaries and key insights
- **Action Item Detection**: Automatic identification of tasks and follow-ups

### Advanced Features
- **Vector Database**: ChromaDB integration for semantic email search
- **Thread Management**: Automatic email thread organization
- **Real-time Updates**: WebSocket support for live notifications
- **Responsive UI**: Modern, mobile-friendly interface
- **Secure Authentication**: OAuth 2.0 with Microsoft Azure AD

## 🛠 Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: Database ORM with SQLite/PostgreSQL support
- **Microsoft Graph SDK**: Email and calendar integration
- **ChromaDB**: Vector database for semantic search
- **Sentence Transformers**: AI embeddings for email analysis

### Frontend
- **Jinja2 Templates**: Server-side rendering
- **Bootstrap**: Responsive CSS framework
- **JavaScript**: Interactive UI components
- **WebSocket**: Real-time communication

### AI & ML
- **Ollama**: Local AI model integration (DeepSeek R1)
- **Sentence Transformers**: Text embeddings
- **Custom NLP**: Email classification and analysis

### Infrastructure
- **Docker**: Containerized deployment
- **PostgreSQL**: Production database (optional)
- **Redis**: Session management and caching
- **Azure AD**: Authentication provider

## 📋 Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Microsoft Azure App Registration
- Ollama (for AI features)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd ai-email-assistant
cp .env.example .env
```

### 2. Configure Environment
Edit `.env` with your settings:
```env
SECRET_KEY=your-secret-key
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-azure-tenant-id
AZURE_REDIRECT_URI=http://localhost:5000/auth/callback
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:7b
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup AI Model (Optional)
```bash
# Install Ollama from https://ollama.ai
ollama pull deepseek-r1:7b
```

### 5. Start Services
```bash
# Option 1: Docker (Recommended)
python start_docker_db.py
python docker_run.py

# Option 2: Local Development
python run.py
```

### 6. Access Application
Open http://localhost:5000 and sign in with your Microsoft 365 account.

## 🔧 Configuration

### Azure App Registration
1. Go to [Azure Portal](https://portal.azure.com)
2. Register a new application
3. Configure redirect URI: `http://localhost:5000/auth/callback`
4. Add required permissions:
   - `User.Read`
   - `Mail.Read`
   - `Mail.Send`
   - `Mail.ReadWrite`

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key | Yes |
| `AZURE_CLIENT_ID` | Azure app client ID | Yes |
| `AZURE_CLIENT_SECRET` | Azure app secret | Yes |
| `AZURE_TENANT_ID` | Azure tenant ID | Yes |
| `AZURE_REDIRECT_URI` | OAuth redirect URI | Yes |
| `OLLAMA_BASE_URL` | Ollama API endpoint | No |
| `OLLAMA_MODEL` | AI model name | No |
| `DATABASE_URL` | Database connection string | No |

## 📁 Project Structure

```
ai-email-assistant/
├── app/
│   ├── models/          # Database models
│   │   ├── user.py      # User model
│   │   ├── email.py     # Email model
│   │   └── chat.py      # Chat message model
│   ├── routes/          # Flask blueprints
│   │   ├── main.py      # Main routes
│   │   ├── auth.py      # Authentication
│   │   ├── email.py     # Email management
│   │   └── chat.py      # AI chat interface
│   ├── services/        # Business logic
│   │   ├── ms_graph.py  # Microsoft Graph integration
│   │   ├── email_processor.py  # Email analysis
│   │   ├── vector_db.py # ChromaDB operations
│   │   └── chat_processor.py   # AI chat logic
│   ├── templates/       # HTML templates
│   └── static/          # CSS, JS, images
├── docker/              # Docker configuration
├── data/               # Application data
├── logs/               # Application logs
├── requirements.txt    # Python dependencies
├── run.py             # Application entry point
└── README.md          # This file
```

## 🎯 Usage Guide

### Email Synchronization
1. Sign in with Microsoft 365 account
2. Visit the dashboard to trigger automatic sync
3. View up to 50 recent emails with full metadata

### AI Chat Assistant
1. Navigate to any email detail page
2. Use the chat sidebar for email-specific assistance
3. Try commands like:
   - "Summarize this email"
   - "Help me reply"
   - "What action items are in this email?"
   - "Is this email urgent?"

### Email Management
- **Mark as Read/Unread**: Click buttons on email cards
- **Send Emails**: Use the compose interface
- **Search Emails**: Use semantic search powered by AI
- **View Threads**: Automatic thread organization

## 🧪 Testing

### Setup Verification
```bash
python setup_check.py
```

### Test Email Sync
```bash
# Open enhanced_sync_test.html in browser
# Or run manual sync
python enhanced_microsoft_sync.py
```

### Test Individual Features
- Visit `http://localhost:5000/emails/<id>` for email details
- Use chat interface for AI assistance
- Test mark as read/unread functionality

## 🐳 Docker Deployment

### Development with Docker
```bash
python start_docker_db.py  # Start PostgreSQL, Redis, ChromaDB
python docker_run.py       # Start Flask app
```

### Production Deployment
```bash
docker-compose up -d
```

### Database Services
- **PostgreSQL**: Port 5432
- **Redis**: Port 6379  
- **ChromaDB**: Port 8000

## 🔍 API Endpoints

### Authentication
- `GET /auth/login` - Initiate OAuth login
- `GET /auth/callback` - OAuth callback
- `POST /auth/logout` - Sign out user

### Email Management
- `GET /api/email/sync` - Sync emails from Microsoft 365
- `GET /api/email/<id>` - Get email details
- `POST /api/email/<id>/mark-read` - Mark email as read
- `POST /api/email/<id>/mark-unread` - Mark email as unread
- `POST /api/email/<id>/chat` - AI chat for specific email

### Chat Interface
- `POST /api/chat/message` - Send chat message
- `GET /api/chat/history` - Get chat history

## 🚨 Troubleshooting

### Common Issues

**"ModuleNotFoundError" during startup:**
```bash
pip install -r requirements.txt
python setup_check.py
```

**Azure authentication fails:**
- Verify Azure app registration settings
- Check redirect URI matches exactly
- Ensure required permissions are granted

**Database errors:**
```bash
python start_docker_db.py  # Restart database services
rm -rf instance/app.db     # Reset SQLite database
```

**AI features not working:**
```bash
ollama pull deepseek-r1:7b  # Install AI model
ollama serve                # Start Ollama service
```

### Logs and Debugging
- Application logs: `logs/app.log`
- Set `DEBUG=True` in `.env` for verbose logging
- Check Docker container logs: `docker-compose logs`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Microsoft Graph API for email integration
- Ollama for local AI model support
- ChromaDB for vector database capabilities
- Flask ecosystem for web framework

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `logs/` directory
3. Run `python setup_check.py` for diagnostics
4. Open an issue on the repository

---

**Note**: This application requires a Microsoft 365 account and Azure app registration for full functionality. The AI features are optional but recommended for the best experience.