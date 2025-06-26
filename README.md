# Fuel Route Optimizer API

Django REST API for optimizing fuel stops along driving routes within the USA.

## Setup

### Prerequisites
- Python 3.8+
- [uv](https://docs.astral.sh/uv/) package manager

### 1. Clone and Setup Environment
```bash
cd fuel_route_optimizer/
```

### 2. Create Virtual Environment
```bash
uv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
uv sync
```

### 5. Environment Configuration
Create `.env` file:
```bash
OPENROUTE_API_KEY=your-openroute-api-key
```

**Get OpenRouteService API Key (Free):**
- Sign up at: https://openrouteservice.org/dev/#/signup
- Copy API key to `.env` file

### 6. Database Setup
```bash
python manage.py migrate
python manage.py createcachetable
```

### 7. Create Admin User (Optional)
```bash
python manage.py createsuperuser
```

### 8. Load Fuel Station Data (Once)
```bash
# This geocodes all fuel stations into a database for faster lookups
# Takes ~1-2 hours for 8K+ stations
python manage.py geocode_stations fuel_optimizer/data/fuel-prices-for-be-assessment.csv
```

### 9. Start Server
```bash
python manage.py runserver
```

Server runs at: `http://127.0.0.1:8000/`

## API Endpoints

### Health Check
```http
GET /api/health/
```

**Response:**
```json
{
    "status": "healthy"
}
```

### Route Optimization
```http
POST /api/optimize/
Content-Type: application/json

{
    "start": "New York, NY",
    "end": "Los Angeles, CA"
}
```

**Sample Response:**
```json
{
    "route_geometry": {
        "type": "LineString",
        "coordinates": [[-74.006, 40.7128], [-118.2437, 34.0522]]
    },
    "fuel_stops": [
        {
            "name": "Travel Center Denver",
            "city": "Denver",
            "state": "CO",
            "price": 3.45,
            "coordinates": [39.7392, -104.9903]
        }
    ],
    "total_distance_miles": 2789.5,
    "total_fuel_cost": 967.23,
    "estimated_gallons": 278.9,
    "stops_count": 6
}
```

### Admin Interface (Optional)
- **URL:** `http://127.0.0.1:8000/admin/`
- View and manage fuel stations
- Requires superuser account

### Running Tests (Optional)
**Install Test Dependencies**
```bash
uv sync --group test
```
```bash
python manage.py test fuel_optimizer.tests
```