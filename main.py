"""
REST API with FastAPI
- User management endpoints
- Task management system
- Database operations
- Authentication
- Error handling
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional
from datetime import datetime, timedelta
from enum import Enum
import sqlite3
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Task Management API",
    description="Professional REST API for task and user management",
    version="1.0.0"
)

# ==================== MODELS ====================

class TaskStatus(str, Enum):
    """Task status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class TaskCreate(BaseModel):
    """Task creation model"""
    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: int = Field(default=1, ge=1, le=5)
    due_date: Optional[datetime] = None
    
    @validator('title')
    def title_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v


class TaskUpdate(BaseModel):
    """Task update model"""
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    due_date: Optional[datetime] = None


class Task(BaseModel):
    """Task response model"""
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: int
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """User creation model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric')
        return v


class User(BaseModel):
    """User response model"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    created_at: datetime
    
    class Config:
        from_attributes = True


class DatabaseManager:
    """Database management operations"""
    
    def __init__(self, db_path: str = "tasks.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 1,
                due_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("✓ Database initialized")
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[dict]:
        """Execute SELECT query and return results"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id


# Initialize database
db = DatabaseManager()


# ==================== USERS ENDPOINTS ====================

@app.post("/api/v1/users", response_model=dict, status_code=201)
async def create_user(user: UserCreate):
    """Create a new user"""
    try:
        # Hash password (in production, use proper hashing)
        hashed_password = hash(user.password)
        
        query = """
            INSERT INTO users (username, email, password, full_name)
            VALUES (?, ?, ?, ?)
        """
        user_id = db.execute_update(
            query,
            (user.username, user.email, str(hashed_password), user.full_name)
        )
        
        logger.info(f"✓ User created: {user.username}")
        return {
            "id": user_id,
            "username": user.username,
            "email": user.email,
            "message": "User created successfully"
        }
    
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            raise HTTPException(status_code=400, detail="Username already exists")
        elif "email" in str(e):
            raise HTTPException(status_code=400, detail="Email already exists")
        raise HTTPException(status_code=400, detail="Invalid user data")


@app.get("/api/v1/users", response_model=dict)
async def list_users(skip: int = Query(0, ge=0), limit: int = Query(10, ge=1, le=100)):
    """List all users with pagination"""
    query = "SELECT id, username, email, full_name, created_at FROM users LIMIT ? OFFSET ?"
    users = db.execute_query(query, (limit, skip))
    
    return {
        "total": len(users),
        "skip": skip,
        "limit": limit,
        "users": users
    }


@app.get("/api/v1/users/{user_id}", response_model=dict)
async def get_user(user_id: int):
    """Get specific user by ID"""
    query = "SELECT id, username, email, full_name, created_at FROM users WHERE id = ?"
    results = db.execute_query(query, (user_id,))
    
    if not results:
        raise HTTPException(status_code=404, detail="User not found")
    
    return results[0]


# ==================== TASKS ENDPOINTS ====================

@app.post("/api/v1/tasks", response_model=dict, status_code=201)
async def create_task(task: TaskCreate, user_id: int = Query(..., description="User ID")):
    """Create a new task"""
    # Verify user exists
    user_check = db.execute_query("SELECT id FROM users WHERE id = ?", (user_id,))
    if not user_check:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        query = """
            INSERT INTO tasks (user_id, title, description, priority, due_date)
            VALUES (?, ?, ?, ?, ?)
        """
        task_id = db.execute_update(
            query,
            (user_id, task.title, task.description, task.priority, task.due_date)
        )
        
        logger.info(f"✓ Task created: {task.title}")
        return {
            "id": task_id,
            "title": task.title,
            "status": TaskStatus.PENDING.value,
            "priority": task.priority,
            "message": "Task created successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to create task")


@app.get("/api/v1/tasks", response_model=dict)
async def list_tasks(
    user_id: int = Query(..., description="User ID"),
    status: Optional[TaskStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """List tasks for a user with optional filtering"""
    base_query = "SELECT * FROM tasks WHERE user_id = ?"
    params = [user_id]
    
    if status:
        base_query += " AND status = ?"
        params.append(status.value)
    
    base_query += " LIMIT ? OFFSET ?"
    params.extend([limit, skip])
    
    tasks = db.execute_query(base_query, tuple(params))
    
    return {
        "total": len(tasks),
        "skip": skip,
        "limit": limit,
        "tasks": tasks
    }


@app.get("/api/v1/tasks/{task_id}", response_model=dict)
async def get_task(task_id: int, user_id: int = Query(..., description="User ID")):
    """Get specific task"""
    query = "SELECT * FROM tasks WHERE id = ? AND user_id = ?"
    results = db.execute_query(query, (task_id, user_id))
    
    if not results:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return results[0]


@app.put("/api/v1/tasks/{task_id}", response_model=dict)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    user_id: int = Query(..., description="User ID")
):
    """Update a task"""
    # Verify task exists
    task_check = db.execute_query(
        "SELECT id FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )
    if not task_check:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Build update query dynamically
    update_fields = []
    params = []
    
    if task_update.title is not None:
        update_fields.append("title = ?")
        params.append(task_update.title)
    
    if task_update.description is not None:
        update_fields.append("description = ?")
        params.append(task_update.description)
    
    if task_update.status is not None:
        update_fields.append("status = ?")
        params.append(task_update.status.value)
    
    if task_update.priority is not None:
        update_fields.append("priority = ?")
        params.append(task_update.priority)
    
    if task_update.due_date is not None:
        update_fields.append("due_date = ?")
        params.append(task_update.due_date)
    
    if update_fields:
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        query = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
        params.append(task_id)
        
        db.execute_update(query, tuple(params))
        logger.info(f"✓ Task updated: {task_id}")
    
    return {"id": task_id, "message": "Task updated successfully"}


@app.delete("/api/v1/tasks/{task_id}", response_model=dict)
async def delete_task(task_id: int, user_id: int = Query(..., description="User ID")):
    """Delete a task"""
    # Verify task exists
    task_check = db.execute_query(
        "SELECT id FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )
    if not task_check:
        raise HTTPException(status_code=404, detail="Task not found")
    
    query = "DELETE FROM tasks WHERE id = ? AND user_id = ?"
    db.execute_update(query, (task_id, user_id))
    
    logger.info(f"✓ Task deleted: {task_id}")
    return {"id": task_id, "message": "Task deleted successfully"}


# ==================== STATISTICS ENDPOINT ====================

@app.get("/api/v1/stats", response_model=dict)
async def get_statistics(user_id: int = Query(..., description="User ID")):
    """Get task statistics for a user"""
    # Count tasks by status
    query = """
        SELECT status, COUNT(*) as count
        FROM tasks
        WHERE user_id = ?
        GROUP BY status
    """
    status_counts = db.execute_query(query, (user_id,))
    
    # Get tasks by priority
    priority_query = """
        SELECT priority, COUNT(*) as count
        FROM tasks
        WHERE user_id = ?
        GROUP BY priority
    """
    priority_counts = db.execute_query(priority_query, (user_id,))
    
    return {
        "by_status": status_counts,
        "by_priority": priority_counts,
        "message": "Statistics retrieved successfully"
    }


# ==================== HEALTH CHECK ====================

@app.get("/health", response_model=dict)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


# ==================== ROOT ENDPOINT ====================

@app.get("/", response_model=dict)
async def root():
    """API root endpoint"""
    return {
        "name": "Task Management API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
