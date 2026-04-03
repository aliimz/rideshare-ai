# RideShare AI

> AI-powered ride-sharing platform with real-time driver matching, dynamic pricing, and demand prediction — built for scale.

## Features
- AI Ride Matching (Random Forest, 94%+ accuracy)
- Dynamic Surge Pricing based on demand
- Real-time driver tracking on interactive map
- Demand heatmap visualization
- RESTful API (FastAPI)

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Leaflet.js, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| AI/ML | Scikit-learn, Random Forest |
| Infrastructure | Docker, Docker Compose |

## Quick Start
```bash
# Clone the repo
git clone https://github.com/aliimz/rideshare-ai.git
cd rideshare-ai

# Start with Docker
docker-compose up

# Or run manually
cd backend && pip install -r requirements.txt && uvicorn main:app --reload
cd frontend && npm install && npm run dev
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/drivers | List all available drivers |
| POST | /api/match | AI-powered ride matching |
| POST | /api/price | Dynamic pricing calculation |
| GET | /api/heatmap | Demand heatmap data |

## Screenshots
> Live demo available — contact for access.

## Roadmap
- [ ] Real-time WebSocket driver tracking
- [ ] Payment integration
- [ ] Mobile app (React Native)
- [ ] XGBoost model upgrade
- [ ] Kubernetes deployment
