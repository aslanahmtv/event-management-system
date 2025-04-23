# Event Management System Documentation

## System Overview

The Event Management System is a microservice-based platform for managing events with real-time notifications. The system consists of three core microservices that communicate through RabbitMQ message broker, using MongoDB for data persistence and JWT for authentication.

![Architecture Diagram](https://via.placeholder.com/800x400?text=Event+Management+System+Architecture)

### Core Services

1. **Event Service**
   - Manages CRUD operations for events
   - Publishes event changes to the message broker
   - Integrates with MongoDB for event data storage

2. **Notification Service**
   - Subscribes to event changes via message broker
   - Provides WebSocket endpoint for real-time notifications
   - Stores notification history in MongoDB

3. **Authentication Service**
   - Manages user registration and authentication
   - Issues and validates JWT tokens
   - Applies rate limiting to protect authentication endpoints

## Technical Stack

- **Backend Framework**: FastAPI
- **Database**: MongoDB
- **Message Broker**: RabbitMQ
- **Authentication**: JWT
- **WebSockets**: FastAPI's WebSocket support
- **Testing**: Pytest
- **Container Runtime**: Docker
- **API Documentation**: Swagger/OpenAPI

## Service Details

### Authentication Service

The Authentication Service manages user registration, login, and JWT token issuance.

#### Key Features

- User registration with validation
- Login via username/email and password
- JWT token generation and validation
- Password hashing using bcrypt
- Rate limiting for login attempts

#### API Endpoints

- `POST /auth/register` - Register a new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user information
- `GET /users/{user_id}` - Get user details by ID

#### Data Models

```python
class UserDB:
    user_id: str
    email: str
    username: str
    password_hash: str
    full_name: str
    is_active: bool
    is_verified: bool
    role: UserRole
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
```

### Event Service

The Event Service manages all event-related operations and publishes changes to the message broker.

#### Key Features

- CRUD operations for events
- Event validation (time constraints, required fields)
- Publishing event changes to RabbitMQ
- Support for searching and filtering events

#### API Endpoints

- `GET /events` - List all events (with pagination)
- `POST /events` - Create a new event
- `GET /events/{event_id}` - Get event details
- `PUT /events/{event_id}` - Update an event
- `DELETE /events/{event_id}` - Delete an event
- `GET /events/search` - Search for events with filters

#### Data Models

```python
class EventDB:
    event_id: str
    title: str
    description: str
    location: str
    start_time: datetime
    end_time: datetime
    created_by: str
    tags: Optional[List[str]]
    max_attendees: Optional[int]
    status: EventStatus
    attachment_url: Optional[str]
    coordinates: Optional[Dict[str, float]]
    created_at: datetime
    updated_at: datetime
```

### Notification Service

The Notification Service provides real-time notifications via WebSockets and processes messages from the message broker.

#### Key Features

- WebSocket connections for real-time updates
- Subscription to specific events
- Message processing from RabbitMQ
- Notification storage and history

#### API Endpoints

- `GET /notifications` - Get paginated notifications
- `GET /notifications/{notification_id}` - Get specific notification
- `POST /notifications/mark-read/{notification_id}` - Mark notification as read
- `POST /notifications/mark-all-read` - Mark all notifications as read
- `GET /notifications/count` - Get unread notification count
- `WebSocket /ws/ws` - WebSocket endpoint for real-time notifications

#### Data Models

```python
class NotificationDB:
    notification_id: str
    notification_type: NotificationType
    user_id: str
    content: Dict
    delivered_to: List[str]
    read_by: List[str]
    is_read: bool
    timestamp: datetime
```

## Inter-service Communication

The services communicate via RabbitMQ message broker:

1. **Event Service → RabbitMQ**:
   - Publishes messages when events are created, updated, or deleted
   - Message format: `{"type": "event", "action": "created|updated|deleted", "data": {...}}`

2. **RabbitMQ → Notification Service**:
   - Notification service subscribes to event changes
   - Processes messages and sends WebSocket notifications
   - Stores notifications in MongoDB

3. **Authentication Flow**:
   - Services validate JWT tokens issued by Auth Service
   - Token payload contains user ID and role information

## Setting Up Swagger Documentation

To enhance API documentation, Swagger/OpenAPI is integrated in all services. Here's how to implement it:

### For Each Service

1. Update the FastAPI app creation with proper metadata:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def create_app(container=None):
    container = container or AppContainer()
    
    app = FastAPI(
        title="[Service Name]",
        description="[Service Description]",
        version="0.1.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Update with your frontend URL in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    # ...
    
    return app
```

2. Add detailed API documentation in router definitions:

```python
from fastapi import APIRouter, Depends, HTTPException

def get_router():
    router = APIRouter()
    
    @router.get(
        "/items",
        response_model=List[ItemResponse],
        summary="Get all items",
        description="Retrieve a paginated list of all items with optional filtering",
        responses={
            200: {"description": "List of items"},
            401: {"description": "Unauthorized - Invalid or missing token"},
        },
    )
    async def get_items():
        # Implementation
        pass
    
    return router
```

3. Add example responses and request bodies:

```python
from pydantic import BaseModel, Field

class ItemCreate(BaseModel):
    name: str = Field(..., description="Item name", example="Example Item")
    description: str = Field(None, description="Item description", example="This is an example item")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Example Item",
                "description": "This is an example item",
            }
        }
```

## Setup and Installation

### Prerequisites

- Python 3.11+
- MongoDB
- RabbitMQ
- Docker (optional)

### Environment Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/aslanahmtv/event-management-system.git
   cd event-management-system
   ```

2. Setup projects using Poetry for each service:
    ```bash
    # Install Poetry if not already installed
    # curl -sSL https://install.python-poetry.org | python3 -
    
    # Auth Service
    cd auth-service
    poetry install
    poetry shell
    
    # Event Service
    cd ../event-service
    poetry install
    poetry shell
    
    # Notification Service
    cd ../notification-service
    poetry install
    poetry shell
    ```

3. Configure environment variables:
   Create `.env` files in each service directory with appropriate values. Example:
   ```
   # MongoDB
   MONGODB_URL=mongodb://localhost:27017
   DB_NAME=events_service
   
   # JWT
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # RabbitMQ
   RABBITMQ_URL=amqp://guest:guest@localhost:5672/
   
   # Service config
   DEBUG_MODE=True
   API_PREFIX=/api
   REPOSITORY_NAME=MongoRepo
   ```

### Running the Services

#### Without Docker

1. Start each service individually:
   ```bash
   # Auth Service
   cd auth-service
   uvicorn app.main:app --reload --port 8000
   
   # Event Service
   cd event-service
   uvicorn app.main:app --reload --port 8001
   
   # Notification Service
   cd notification-service
   uvicorn app.main:app --reload --port 8002
   ```

#### With Docker

1. Build and start the services:
   ```bash
   docker-compose up -d
   ```

### Running Tests

```bash
# Navigate to service directory
cd [service-name]

# Run all tests
poetry run pytest

# Run specific test category
./scripts/test.sh unit  # Run unit tests
./scripts/test.sh system  # Run system tests
./scripts/test.sh all  # Run all tests
```

## API Usage Examples

### Authentication

#### Register a new user

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "example_user",
    "password": "Example123!",
    "full_name": "Example User"
  }'
```

#### Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "example_user",
    "password": "Example123!"
  }'
```

### Events

#### Create an event

```bash
curl -X POST http://localhost:8001/api/events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "Tech Conference 2025",
    "description": "Annual tech conference",
    "location": "San Francisco",
    "start_time": "2025-06-01T09:00:00Z",
    "end_time": "2025-06-02T18:00:00Z",
    "tags": ["technology", "conference"],
    "max_attendees": 500
  }'
```

### Notifications

#### WebSocket connection

```javascript
// JavaScript client example
const token = "YOUR_JWT_TOKEN";
const socket = new WebSocket(`ws://localhost:8002/ws/ws?token=${token}`);

socket.onopen = (event) => {
  console.log("WebSocket connected");
  
  // Subscribe to event
  socket.send(JSON.stringify({
    action: "subscribe",
    event_id: "some_event_id"
  }));
};

socket.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  console.log("Received notification:", notification);
};
```

## Scaling and Performance Considerations

1. **Horizontal Scaling**
   - Services are designed to be stateless and can be scaled horizontally
   - Use a load balancer to distribute traffic
   - WebSocket connections can be managed with sticky sessions

2. **Database Optimization**
   - Appropriate indexing on MongoDB collections
   - Read-heavy operations use caching where appropriate
   - Write operations are optimized with bulk inserts when possible

3. **Message Broker**
   - RabbitMQ is configured with high availability
   - Message persistence ensures no data loss during service restarts
   - Dead-letter exchanges handle failed message processing

4. **Rate Limiting**
   - Authentication endpoints implement 5 req/min rate limiting
   - API endpoints have appropriate rate limits based on usage patterns

## Security Considerations

1. **Authentication**
   - JWT tokens with proper expiration
   - Secure password hashing with bcrypt
   - Token invalidation on logout

2. **Authorization**
   - Role-based access control
   - Resource-level permissions

3. **Data Protection**
   - Input validation and sanitization
   - HTTPS for all API communications
   - Secure WebSocket connections

## Future Improvements

1. **Features**
   - Email verification for user registration
   - Additional user roles and permissions
   - Event attendance management
   - File upload functionality with S3 integration

2. **Technical**
   - Implement read replicas for MongoDB
   - Add distributed tracing
   - Implement CI/CD pipeline
   - Add comprehensive metrics and monitoring

3. **Design**
   - Implement CQRS pattern for better read/write separation
   - Add event sourcing for complete audit trail
   - Implement GraphQL API for flexible querying

## Conclusion

The Event Management System provides a scalable, microservice-based solution for event management with real-time notifications. The system is designed with modern best practices for performance, security, and maintainability, and can be extended to support additional features as needed.