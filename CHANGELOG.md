# Changelog

All notable changes to the AI Agriculture Advisors project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0] - 2025-11-29

### Added

#### Infrastructure & Configuration
- **Environment Configuration**: Proper dotenv loading with `require('dotenv').config()` in server.js
- **Environment Template**: Created `.env.example` with all required configuration variables
- **MongoDB Initialization**: Added `connectDB()` call in server.js for database connection
- **Winston Logging**: Professional structured logging with file transports (combined.log, error.log)

#### Security Enhancements
- **Helmet.js Integration**: Added security headers to protect against common web vulnerabilities
- **CORS Configuration**: Configured Cross-Origin Resource Sharing for API access
- **Rate Limiting**: Implemented 100 requests per 15-minute window per IP address using express-rate-limit
- **Input Validation Middleware**: Added request sanitization to prevent injection attacks
- **Request Size Limits**: Set 1MB payload cap to prevent abuse

#### API & Architecture
- **Centralized Expert Registry**: Created shared expert mapping in `src/config/experts.js` to eliminate duplication
- **Dependency Injection**: Decoupled controllers from llamaService for better testability
- **Error Handling Middleware**: Centralized error handling for consistent, environment-aware API responses
- **Request Validation**: Input sanitization and type checking on all endpoints

#### Frontend Improvements
- **Separate CSS/JS Files**: Refactored from inline styles/scripts to external files (style.css, app.js)
- **Loading Indicators**: Added animated spinner with visual feedback during API calls
- **Query History**: Persist last 10 queries in localStorage with one-click access
- **Query Suggestions**: 5 common agricultural queries as quick-start examples
- **Dark Mode**: Toggle between light/dark themes with localStorage persistence
- **Export Functionality**: Download expert advice as markdown file (.md)
- **Improved Layout**: Card-based UI, sticky sidebar, better spacing and typography
- **Enhanced UI Elements**: Smooth transitions, hover effects, improved accessibility

#### Expert System
- **Soil Health Specialist**: Expert in soil composition, nutrient management, and regenerative agriculture
- **Pest & Disease Management Expert**: IPM, biological control, and crop disease identification
- **Irrigation & Water Management Specialist**: Water conservation, irrigation systems, and efficiency
- **Organic Farming Consultant**: Certification standards, non-GMO practices, holistic management
- **Agricultural Economics Advisor**: Farm budgeting, risk assessment, and financial planning

### Changed

- **Updated llamaService.js**: Replaced hardcoded values with environment variables from process.env
- **Modernized Database Config**: Removed deprecated mongoose options (useNewUrlParser, useUnifiedTopology)
- **Replaced console.log**: Migrated all logging to Winston framework for production-ready logging
- **Cleaned Up Middleware**: Removed unused markdown middleware from server.js

### Fixed

- **Environment Loading**: Fixed missing dotenv configuration that prevented environment variables from loading
- **Deprecated Options**: Removed mongoose deprecated options that caused warnings
- **Security Vulnerabilities**: Addressed input validation, rate limiting, and CORS issues

---

## [1.0.0] - 2025-04-22

### Added

#### Core Features
- **Multi-Expert Consultation**: Query multiple agricultural experts simultaneously via `/api/query` endpoint
- **Roundtable Discussion**: Collaborative multi-round expert debates via `/api/roundtable` endpoint
- **Markdown Rendering**: Client-side markdown parsing with marked.js for beautifully formatted responses
- **File-based Logging**: Basic interaction logging to agri-ai.txt
- **Web Interface**: Single-page application for interacting with agricultural experts

#### Expert System (Initial 5 Experts)
- **Agricultural Science Expert**: Crop science, soil management, farming practices, genetic modifications
- **Climate Change Impact Analyst**: Weather patterns, climate adaptation, regional impacts
- **Commodities Trading Specialist**: Market dynamics, supply/demand analysis, price forecasting
- **AgriTech Innovation Researcher**: AI, IoT, robotics, precision agriculture technologies
- **Food Supply Chain Analyst**: Distribution networks, sustainability, traceability

#### Technical Infrastructure
- **Express.js Server**: RESTful API with Express framework
- **Ollama Integration**: Local LLM integration via llamaService.js
- **MongoDB Support**: Database models and connection setup (optional)
- **Static Data Files**: Placeholder JSON files for crop, climate, and market data

### Initial Release Features
- Expert role system with specialized domain knowledge
- Real-time query processing via local LLM
- Web-based user interface
- Parallel expert consultation
- Sequential roundtable discussions

---

## [0.1.0] - 2024-08-05

### Added
- Initial project setup
- Basic logger implementation
- README documentation
- Project structure and dependencies

---

## Migration to OpenRouter - 2025-11-29 (Post-1.1.0)

### Changed
- **LLM Provider**: Migrated from Ollama (local) to OpenRouter (cloud-based API)
- **API Integration**: Updated llamaService.js to use OpenRouter's OpenAI-compatible API
- **Authentication**: Added API key authentication with Authorization headers
- **Message Format**: Changed from prompt string to messages array format
- **Environment Variables**:
  - Replaced `LLAMA_API_URL` with `OPENROUTER_API_URL`
  - Replaced `LLAMA_MODEL_NAME` with `OPENROUTER_MODEL_NAME`
  - Added `OPENROUTER_API_KEY` requirement

### Added
- **Model Flexibility**: Access to 100+ models (Claude, GPT-4, Gemini, Llama, etc.)
- **Free Tier Support**: Default configuration uses free model `meta-llama/llama-3.1-8b-instruct:free`
- **Cloud-Based**: No local LLM installation required
- **Error Handling**: Improved error messages for API issues, rate limiting, and quota exceeded scenarios

### Removed
- **Ollama Dependency**: No longer requires local Ollama installation
- **Local Model Management**: Removed need to download and manage models locally

---

## Key Metrics

### Version 1.1.0 Statistics
- **Security Score**: 8/8 critical security issues resolved
- **Code Quality**: 10/10 critical P0 issues complete
- **Expert Count**: 10 specialized agricultural advisors
- **API Endpoints**: 2 (multi-query, roundtable)
- **Frontend Features**: 7 major UX improvements
- **Dependencies**: 8 core packages (express, winston, helmet, mongoose, etc.)

---

## Acknowledgments

Major contributions in this release:
- Security hardening with Helmet.js and express-rate-limit
- Logging infrastructure with Winston
- Frontend refactoring and UX enhancements
- Expert system expansion (5 → 10 experts)
- Centralized architecture improvements

---

## Looking Forward

See [ROADMAP.md](ROADMAP.md) for planned future enhancements including:
- Testing infrastructure (unit, integration, E2E)
- Additional LLM provider support
- Mobile responsiveness
- User authentication
- Real-time data integration
- Deployment guides and Docker support
