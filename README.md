# 🌱 GreenPulse: Smart Energy Management Platform

**Real-time energy insights for a sustainable tomorrow**

## 🚀 **INSTANT DEPLOY** (5 minutes, completely FREE!)

### Backend + Database (Render)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/surajsk2003/GreenPulse)

### Frontend (Vercel)  
[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/surajsk2003/GreenPulse&project-name=greenpulse-frontend&root-directory=frontend/greenpulse-dashboard)

**🎯 Click both buttons above → Get live URLs in 5 minutes!**

---

GreenPulse is an intelligent energy monitoring and management platform designed for educational and corporate campuses. It provides real-time energy usage tracking, AI-powered insights, and gamified conservation challenges to help institutions reduce energy costs and environmental impact.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### One-Command Setup
```bash
./setup.sh
```

This will:
- Build and start all services
- Initialize the database
- Process the ASHRAE dataset
- Open the dashboard in your browser

### Manual Setup

1. **Start Services**
   ```bash
   cd docker-config
   docker-compose up -d --build
   ```

2. **Process Data**
   ```bash
   docker-compose exec backend python data-pipeline/ashrae_processor.py
   ```

3. **Access Application**
   - Dashboard: http://localhost:4200
   - API Docs: http://localhost:8000/docs

## ✨ Features

### 🏢 Building Management
- **Real-time Monitoring**: Live energy consumption tracking
- **Multi-building Support**: Manage entire campus energy usage
- **Building Profiles**: Detailed information and historical data

### 🤖 AI-Powered Analytics
- **Anomaly Detection**: Automatic identification of unusual energy patterns
- **Energy Forecasting**: Predict future consumption using Prophet ML
- **Smart Insights**: AI-generated recommendations for energy savings

### 📊 Interactive Dashboard
- **Real-time Charts**: Live energy consumption visualization
- **Comparative Analysis**: Compare buildings and time periods
- **Mobile Responsive**: Access from any device

### 🏆 Gamification
- **Efficiency Leaderboard**: Building and department rankings
- **Conservation Challenges**: Encourage energy-saving behavior
- **Achievement System**: Track and reward sustainability efforts

### 💡 Smart Recommendations
- **Peak Usage Analysis**: Identify and optimize high-consumption periods
- **Equipment Scheduling**: Optimize operation schedules
- **HVAC Optimization**: Improve heating and cooling efficiency
- **Weekend Waste Detection**: Find unnecessary energy usage

## 🏗️ Architecture

### Backend Stack
- **FastAPI**: High-performance Python web framework
- **PostgreSQL + TimescaleDB**: Time-series optimized database
- **Redis**: Caching and real-time data
- **SQLAlchemy**: Database ORM
- **scikit-learn**: Anomaly detection
- **Prophet**: Time series forecasting

### Frontend Stack
- **Angular 17**: Modern web framework
- **Chart.js**: Interactive data visualization
- **Angular Material**: UI components
- **Bootstrap**: Responsive design utilities

### ML Pipeline
- **Isolation Forest**: Unsupervised anomaly detection
- **Prophet**: Automated time series forecasting
- **Feature Engineering**: Advanced pattern recognition
- **Model Management**: Automated training and deployment

## 📈 Data Sources

The platform uses the **ASHRAE Great Energy Predictor III** dataset:
- **1,400+ buildings** across multiple sites
- **Hourly energy readings** for electricity, chilled water, steam, hot water
- **Weather data** integration
- **Building metadata** including type, size, and year built

## 🛠️ Development

### Local Backend Development
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Local Frontend Development
```bash
cd frontend/greenpulse-dashboard
npm install
ng serve
```

### Running ML Models
```bash
cd ml-models
python anomaly_detector.py
python energy_forecaster.py
```

### Data Processing
```bash
cd data-pipeline
python ashrae_processor.py
```

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| Frontend (Angular) | 4200 | Web dashboard |
| Backend (FastAPI) | 8000 | REST API |
| Database (PostgreSQL) | 5432 | Time-series data |
| Cache (Redis) | 6379 | Caching layer |

## 📊 API Endpoints

### Buildings
- `GET /api/buildings` - List all buildings
- `GET /api/buildings/{id}` - Get building details
- `GET /api/buildings/{id}/summary` - Get building summary

### Energy Data
- `GET /api/energy/buildings/{id}/current` - Current energy usage
- `GET /api/energy/buildings/{id}/historical` - Historical data
- `GET /api/energy/buildings/{id}/comparison` - Usage comparison
- `GET /api/energy/campus/overview` - Campus overview

### Analytics
- `GET /api/analytics/buildings/{id}/anomalies` - Anomaly detection
- `GET /api/analytics/buildings/{id}/forecast` - Energy forecasting
- `GET /api/analytics/efficiency/leaderboard` - Efficiency rankings
- `POST /api/analytics/buildings/compare` - Building comparison

### Insights
- `GET /api/insights/buildings/{id}` - AI-generated insights
- `GET /api/insights/campus/summary` - Campus insights summary
- `GET /api/insights/types` - Available insight types

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend/greenpulse-dashboard
ng test
```

## 📦 Deployment

### Production Docker Compose
```bash
cd docker-config
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables
Create `.env` file:
```env
DATABASE_URL=postgresql://user:password@db:5432/greenpulse
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key
```

## 🤝 Demo Strategy

### Hackathon Presentation (5 minutes)
1. **Problem Hook** (30s): "$2M annual energy costs, 30% waste"
2. **Live Demo** (3m): Real-time dashboard, anomaly detection, AI insights
3. **Technical Innovation** (1m): ML pipeline, scalable architecture
4. **Business Impact** (30s): "$500K savings, 40% carbon reduction"

### Key Demo Points
- ✅ Real-time energy monitoring
- ✅ AI anomaly detection in action
- ✅ Predictive forecasting
- ✅ Actionable insights with ROI
- ✅ Gamification for behavior change
- ✅ Mobile-responsive design

## 🏆 Competitive Advantages

1. **AI-First Approach**: Advanced ML for anomaly detection and forecasting
2. **Gamification**: Behavioral change through competition
3. **Real-time Processing**: Live data with TimescaleDB optimization
4. **Scalable Architecture**: Microservices with Docker
5. **Production Ready**: Complete CI/CD pipeline

## 📈 Business Model

### Revenue Streams
- **SaaS Subscriptions**: $5-50/building/month
- **Professional Services**: Implementation and consulting
- **Data Analytics**: Advanced reporting and insights
- **API Access**: Third-party integrations

### Market Opportunity
- **$2.8B** energy management market
- **1M+** potential building customers
- **Growing demand** for sustainability solutions

## 🛣️ Roadmap

### Phase 1: MVP (2-3 months)
- [x] Core energy monitoring
- [x] Basic anomaly detection
- [x] Interactive dashboard
- [ ] Pilot deployment (5 buildings)

### Phase 2: Scale (6 months)
- [ ] Advanced ML models
- [ ] Mobile application
- [ ] API for third-party integrations
- [ ] Multi-campus support

### Phase 3: Market (12 months)
- [ ] SaaS platform launch
- [ ] Partner ecosystem
- [ ] Enterprise features
- [ ] International expansion

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **ASHRAE** for the energy dataset
- **Open source community** for amazing tools
- **Hackathon organizers** for the opportunity

---

**Built with ❤️ for a sustainable future 🌱**

For questions or support, please open an issue or contact the development team.