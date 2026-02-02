# 🎯 Finance Analyzer - Production Ready

A secure, production-ready AI-powered financial analysis system that extracts structured financial information from Arabic and English voice recordings and text input.

## ✨ Features

- � **Voice Analysis**: Upload audio files for automatic transcription and financial analysis
- � **Text Analysis**: Direct text input for financial transaction extraction
- 🌍 **Multi-Language**: Supports Arabic and English with intelligent detection
- � **Security First**: Comprehensive content filtering and input validation
- ⚡ **High Performance**: Async processing with intelligent caching
- � **Structured Output**: Detailed transaction categorization and summaries

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Update .env with your API keys
nano .env
```

### 2. Configure API Keys
```bash
# Required: Get your AssemblyAI API key from https://www.assemblyai.com/
ASSEMBLYAI_API_KEY=your_api_key_here

# Generate a secure secret key
SECRET_KEY=your_secure_secret_key_here
```

### 3. Run Application
```bash
# Development
python main.py

# Production
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
```

### 4. Test the API
```bash
# Health check
curl http://localhost:8000/health

# Text analysis
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "دفعت 50 جنيه في كارفور على خضار"}'

# Voice analysis
curl -X POST http://localhost:8000/voice \
  -F "file=@audio.wav"
```

## 🏗️ Architecture

```
app/
├── api/              # REST API endpoints
├── core/             # Security, logging, utilities
├── models/           # Data models and schemas
├── services/         # Business logic (NLP, audio, transcription)
├── utils/            # Helper functions and utilities
└── middleware/       # Custom middleware
```

## � Security Features

- **Content Filtering**: Blocks illegal substances, activities, and weapons
- **Input Validation**: Comprehensive sanitization and validation
- **File Security**: Magic byte validation and secure temp file handling
- **Rate Limiting**: Per-endpoint request limiting
- **CORS Protection**: Configurable domain restrictions
- **Error Handling**: Secure error responses without information leakage

## 📊 API Endpoints

### Text Analysis
```http
POST /analyze
Content-Type: application/json

{
  "text": "دفعت 50 جنيه في كارفور على خضار",
  "language": "ar"
}
```

### Voice Analysis
```http
POST /voice
Content-Type: multipart/form-data

file: audio.wav (max 10MB, supported: wav, mp3, m4a, ogg, webm, flac)
```

### Health Check
```http
GET /health
```

## 🐳 Production Deployment

### Docker
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Or build manually
docker build -f Dockerfile.prod -t finance-analyzer .
docker run -p 8000:8000 --env-file .env finance-analyzer
```

### Manual Deployment
```bash
# Use the deployment script
./scripts/deploy.sh

# Or run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## ⚙️ Configuration

### Environment Variables
```bash
# API Configuration
ASSEMBLYAI_API_KEY=your_api_key_here
SECRET_KEY=your_secret_key_here

# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Security
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Performance
RATE_LIMIT_REQUESTS=60
VOICE_RATE_LIMIT=5/minute
CACHE_TTL=3600
```

### File Limits
- **Max file size**: 10MB
- **Supported formats**: WAV, MP3, M4A, OGG, WebM, FLAC
- **Text length**: 3-1000 characters

## 📈 Monitoring

### Health Checks
```bash
curl http://localhost:8000/health
```

### Logs
- **Format**: Structured JSON logging
- **Location**: `app.log` and console
- **Levels**: INFO, WARNING, ERROR

### Metrics
- Request duration and count
- Error rates by endpoint
- Cache hit/miss ratios
- Content filtering events

## �️ Development

### Testing
```bash
# Test content filtering
python test_content_filter.py

# Manual API testing
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "استلمت مرتب 5000 جنيه"}'
```

### Adding Features
1. Create new service in `app/services/`
2. Add API endpoint in `app/api/endpoints.py`
3. Update models in `app/models/`
4. Add tests and documentation

## 🚨 Security Guidelines

### Content Policy
This service only processes legitimate financial transactions. The following content is automatically blocked:
- Illegal substances and drugs
- Weapons and explosives
- Illegal activities (money laundering, fraud, etc.)
- Non-financial content

### Data Protection
- No sensitive data is stored permanently
- Temporary files are encrypted and auto-deleted
- All requests are logged with anonymized IPs
- GDPR and privacy compliance built-in

## � Support

### Common Issues
1. **API Key Error**: Ensure `ASSEMBLYAI_API_KEY` is set correctly
2. **File Upload Error**: Check file format and size limits
3. **Content Blocked**: Ensure content is legitimate financial transactions only

### Troubleshooting
```bash
# Check logs
tail -f app.log

# Verify configuration
python -c "from app.config import settings; print(settings.dict())"

# Test content filter
python test_content_filter.py
```

## 📄 License

MIT License - see LICENSE file for details.

## 🔄 Updates

To update the application:
```bash
git pull origin main
pip install -r requirements.txt
python main.py
```

---

**Built with security, performance, and reliability in mind for production financial applications.**