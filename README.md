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
| Frontend | React 18, Leaflet.js, Tailwind CSS, Capacitor |
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

## Mobile Build (Android & iOS)
The frontend is wrapped with [Capacitor](https://capacitorjs.com/) so the same React code runs as a native Android/iOS app.

```bash
cd frontend

# 1. Build the web assets
npm run build

# 2. Sync to native platforms
npx cap sync

# 3. Open Android Studio / Xcode
npx cap open android
npx cap open ios

# Or run directly on a connected device / emulator
npx cap run android
npx cap run ios
```

### Added scripts
- `npm run sync` — sync web assets to Android & iOS
- `npm run open:android` — open Android Studio
- `npm run open:ios` — open Xcode
- `npm run android` — run on Android device/emulator
- `npm run ios` — run on iOS simulator/device

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
- [x] Mobile app (Android & iOS via Capacitor)
- [ ] XGBoost model upgrade
- [ ] Kubernetes deployment
