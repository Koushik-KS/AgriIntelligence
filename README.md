# KisanVision AI – Smart Agriculture Intelligence Platform

KisanVision AI is an AI-powered crop health assessment platform designed to help farmers identify crop diseases, analyze plant health, and access useful agricultural information.

The platform combines AI-based image analysis, crop-specific machine learning models, weather information, and farmer-focused recommendations.

## Live Demo

**Live Application:** https://miniproject1-eta-one.vercel.app

Visit the application, create an account using the Sign Up option, and explore the crop health assessment features.

## Live API Services – Render

The backend and crop prediction services are deployed independently on Render.

| Service | Live API URL | Purpose |
|---|---|---|
| Node.js Backend | https://kisanvision-node-api.onrender.com | Authentication, user data and research APIs |
| Coffee API | https://kisanvision-coffee-api.onrender.com | Coffee disease prediction |
| Arecanut API | https://kisanvision-arecanut-api.onrender.com | Arecanut disease prediction |
| Cardamom API | https://kisanvision-cardamom-api.onrender.com | Cardamom disease prediction |
| Ginger API | https://kisanvision-ginger-api.onrender.com | Ginger disease prediction |

### API Documentation

Interactive Swagger documentation is available for the FastAPI services:

- [Coffee API Documentation](https://kisanvision-coffee-api.onrender.com/docs)
- [Arecanut API Documentation](https://kisanvision-arecanut-api.onrender.com/docs)
- [Cardamom API Documentation](https://kisanvision-cardamom-api.onrender.com/docs)
- [Ginger API Documentation](https://kisanvision-ginger-api.onrender.com/docs)

**Node.js Backend Health Check:**

https://kisanvision-node-api.onrender.com/api/health

## Key Features

- **Disease Detection:** Analyze crop leaf images to identify diseases.
- **Plant Identification:** Identify plants using image analysis.
- **Multi-Image Analysis:** Analyze multiple plant images.
- **Crop-Specific AI Models:** Dedicated prediction services for Coffee, Arecanut, Cardamom, and Ginger.
- **Weather Recommendations:** Access current weather information and forecast-based crop recommendations.
- **Prediction History:** View previously saved crop analysis results.
- **Farmer Profile:** Manage farmer account information.
- **Authentication:** Secure user registration and login.
- **Disease Research:** Access research-based crop disease information.
- **Responsive Interface:** Designed for desktop and mobile devices.

## Supported Crops

| Crop | AI Prediction Service |
|---|---|
| Coffee | Available |
| Arecanut | Available |
| Cardamom | Available |
| Ginger | Available |
| Black Pepper | Plant identification / general image analysis; no dedicated crop-specific prediction API currently |

## Technology Stack

### Frontend
- React.js
- Vite
- JavaScript
- HTML5
- CSS3
- Bootstrap
- Tailwind CSS

### Backend
- Node.js
- Express.js
- MongoDB Atlas
- Mongoose
- JWT Authentication

### Artificial Intelligence and Machine Learning
- Python
- TensorFlow
- Keras
- FastAPI
- OpenCV
- Pillow
- MobileNetV2-based crop models

### Deployment and Hosting
- Vercel – Frontend hosting
- Render – Backend and AI API hosting
- MongoDB Atlas – Database hosting
- GitHub – Source code management

## Project Architecture

```text
                 FARMER / USER
                       |
                       v
                REACT FRONTEND
                    VERCEL
                       |
          +------------+-------------+
          |                          |
          v                          v
    NODE.JS BACKEND             CROP AI SERVICES
       RENDER                      RENDER
          |                          |
          v               +----------+----------+
     MONGODB ATLAS         |          |          |
                         COFFEE   ARECANUT   CARDAMOM
                                      |
                                    GINGER
```

## Project Structure

```text
Miniproject/
|
|-- frontend/
|   |-- src/
|   |-- public/
|   |-- package.json
|   |-- vite.config.js
|
|-- server/
|   |-- config/
|   |-- controllers/
|   |-- middleware/
|   |-- models/
|   |-- routes/
|   |-- services/
|   |-- utils/
|   |-- package.json
|   |-- server.js
|
|-- training/
|   |-- coffee/
|   |-- arecanut/
|   |-- cardamom/
|   |-- ginger/
|   |-- requirements.txt
|
|-- .gitignore
|-- README.md
```

## Run the Project Locally

### 1. Clone the Repository

```bash
git clone https://github.com/Koushik-KS/Miniproject.git
cd Miniproject
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 3. Node.js Backend Setup

Open another terminal:

```bash
cd server
npm install
npm run dev
```

Configure the required environment variables in `server/.env`:

```env
NODE_ENV=development
MONGODB_URI=your_mongodb_connection_string
JWT_SECRET=your_jwt_secret
CLIENT_ORIGIN=http://localhost:5173
```

### 4. Python AI Services Setup

From the project root:

```bash
python -m venv .venv-training
```

Activate the environment in Windows PowerShell:

```powershell
.\.venv-training\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r training/requirements.txt
```

Start the individual AI services in separate terminals.

**Coffee**

```bash
python -m uvicorn training.coffee.coffee_api:app --reload --host 127.0.0.1 --port 8000
```

**Arecanut**

```bash
python -m uvicorn training.arecanut.arecanut_api:app --host 127.0.0.1 --port 8001
```

**Cardamom**

```bash
python -m uvicorn training.cardamom.cardamom_api:app --host 127.0.0.1 --port 8002
```

**Ginger**

```bash
python -m uvicorn training.ginger.ginger_api:app --reload --host 127.0.0.1 --port 8003
```

## Production Environment Configuration

Configure the following frontend environment variables in Vercel Project Settings.

```env
VITE_API_URL=https://kisanvision-node-api.onrender.com

VITE_AUTH_API_URL=https://kisanvision-node-api.onrender.com/api

VITE_COFFEE_API_URL=https://kisanvision-coffee-api.onrender.com

VITE_ARECANUT_API_URL=https://kisanvision-arecanut-api.onrender.com

VITE_CARDAMOM_API_URL=https://kisanvision-cardamom-api.onrender.com

VITE_GINGER_API_URL=https://kisanvision-ginger-api.onrender.com

VITE_COFFEE_RESEARCH_URL=https://kisanvision-node-api.onrender.com/api/research/coffee
```

Configure backend secrets and database credentials securely in Render. Never commit `.env` files or credentials to GitHub.

## Security

- Environment variables are excluded from Git tracking.
- Authentication is handled by the backend.
- Passwords are handled using secure password hashing.
- HTTP-only cookies are used for authentication.
- Production frontend origins are configured for API access.

## Developer

**Koushik KS Shetty**

- GitHub: https://github.com/Koushik-KS
- Repository: https://github.com/Koushik-KS/AgriIntelligence.git
- Project: KisanVision AI

## Project Objective

The main objective of KisanVision AI is to support farmers through AI-based crop health assessment, disease identification, weather information, and accessible agricultural insights.

---

**KisanVision AI – Intelligent Crop Health Assessment**
