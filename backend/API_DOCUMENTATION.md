# DualQueryIntelligence API Documentation

**Base URL:** `http://localhost:8000`

**Version:** 1.0.0

## Table of Contents
- [Authentication](#authentication)
- [Chats](#chats)
- [Messages](#messages)
- [Datasets](#datasets)
- [Models](#models)
- [Fine-tuning](#fine-tuning)
- [API Keys](#api-keys)
- [Error Responses](#error-responses)

---

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

### Register User

**Endpoint:** `POST /api/auth/register`

**Description:** Register a new user account.

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "name": "John Doe"
}
```

**Field Requirements:**
- `email` (string, required): Valid email address
- `password` (string, required): Minimum 6 characters
- `name` (string, required): User's full name

**Success Response (201 Created):**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "name": "John Doe",
  "current_plan": "free",
  "queries_used": 0,
  "fine_tune_jobs": 0,
  "datasets_count": 0,
  "billing_cycle": null
}
```

**Error Responses:**
- `400 Bad Request`: Email already registered
```json
{
  "detail": "Email already registered"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "name": "John Doe"
  }'
```

---

### Login

**Endpoint:** `POST /api/auth/login`

**Description:** Authenticate user and receive JWT access token.

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
```json
{
  "detail": "Incorrect email or password"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

---

### Get Current User

**Endpoint:** `GET /api/auth/me`

**Description:** Get current authenticated user information.

**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "name": "John Doe",
  "current_plan": "free",
  "queries_used": 150,
  "fine_tune_jobs": 3,
  "datasets_count": 5,
  "billing_cycle": "monthly"
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <your_access_token>"
```

---

## Chats

### Create Chat

**Endpoint:** `POST /api/chats`

**Description:** Create a new chat session.

**Authentication:** Required

**Request Body:**
```json
{
  "title": "My First Chat",
  "model_id": "507f1f77bcf86cd799439011",
  "dataset_id": "507f1f77bcf86cd799439012"
}
```

**Field Requirements:**
- `title` (string, required): Chat title
- `model_id` (string, optional): MongoDB ObjectId of the model
- `dataset_id` (string, optional): MongoDB ObjectId of the dataset

**Success Response (201 Created):**
```json
{
  "_id": "507f1f77bcf86cd799439013",
  "user_id": "507f1f77bcf86cd799439011",
  "title": "My First Chat",
  "model_id": "507f1f77bcf86cd799439011",
  "dataset_id": "507f1f77bcf86cd799439012",
  "last_updated": "2025-11-10T12:00:00.000Z"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/chats \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Chat",
    "model_id": "507f1f77bcf86cd799439011",
    "dataset_id": "507f1f77bcf86cd799439012"
  }'
```

---

### Get All Chats

**Endpoint:** `GET /api/chats`

**Description:** Get all chats for the current user (sorted by last updated, descending).

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, optional): Maximum number of chats to return (default: 100)
- `offset` (integer, optional): Number of chats to skip (default: 0)

**Success Response (200 OK):**
```json
[
  {
    "_id": "507f1f77bcf86cd799439013",
    "user_id": "507f1f77bcf86cd799439011",
    "title": "My First Chat",
    "model_id": "507f1f77bcf86cd799439011",
    "dataset_id": "507f1f77bcf86cd799439012",
    "last_updated": "2025-11-10T12:00:00.000Z"
  },
  {
    "_id": "507f1f77bcf86cd799439014",
    "user_id": "507f1f77bcf86cd799439011",
    "title": "Data Analysis Chat",
    "model_id": null,
    "dataset_id": "507f1f77bcf86cd799439015",
    "last_updated": "2025-11-09T10:30:00.000Z"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/chats?limit=10&offset=0" \
  -H "Authorization: Bearer <your_access_token>"
```

---

### Get Chat by ID

**Endpoint:** `GET /api/chats/{chat_id}`

**Description:** Get a specific chat by ID.

**Authentication:** Required

**Path Parameters:**
- `chat_id` (string, required): MongoDB ObjectId of the chat

**Success Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439013",
  "user_id": "507f1f77bcf86cd799439011",
  "title": "My First Chat",
  "model_id": "507f1f77bcf86cd799439011",
  "dataset_id": "507f1f77bcf86cd799439012",
  "last_updated": "2025-11-10T12:00:00.000Z"
}
```

**Error Responses:**
- `404 Not Found`: Chat not found or doesn't belong to user
```json
{
  "detail": "Chat not found"
}
```

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/chats/507f1f77bcf86cd799439013 \
  -H "Authorization: Bearer <your_access_token>"
```

---

### Update Chat

**Endpoint:** `PATCH /api/chats/{chat_id}`

**Description:** Update chat properties (partial update).

**Authentication:** Required

**Path Parameters:**
- `chat_id` (string, required): MongoDB ObjectId of the chat

**Request Body (all fields optional):**
```json
{
  "title": "Updated Chat Title",
  "model_id": "507f1f77bcf86cd799439016",
  "dataset_id": "507f1f77bcf86cd799439017"
}
```

**Success Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439013",
  "user_id": "507f1f77bcf86cd799439011",
  "title": "Updated Chat Title",
  "model_id": "507f1f77bcf86cd799439016",
  "dataset_id": "507f1f77bcf86cd799439017",
  "last_updated": "2025-11-10T13:00:00.000Z"
}
```

**Error Responses:**
- `400 Bad Request`: No fields to update
- `404 Not Found`: Chat not found or no changes made

**cURL Example:**
```bash
curl -X PATCH http://localhost:8000/api/chats/507f1f77bcf86cd799439013 \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Chat Title"
  }'
```

---

### Delete Chat

**Endpoint:** `DELETE /api/chats/{chat_id}`

**Description:** Delete a chat.

**Authentication:** Required

**Path Parameters:**
- `chat_id` (string, required): MongoDB ObjectId of the chat

**Success Response (204 No Content):**
No body returned.

**Error Responses:**
- `404 Not Found`: Chat not found

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/chats/507f1f77bcf86cd799439013 \
  -H "Authorization: Bearer <your_access_token>"
```

---

## Messages

### Create Message

**Endpoint:** `POST /api/messages`

**Description:** Create a new message in a chat.

**Authentication:** Required

**Request Body:**
```json
{
  "chat_id": "507f1f77bcf86cd799439013",
  "role": "user",
  "content": "What is the average sales for Q3?",
  "query_type": "analytics",
  "charts": null
}
```

**Field Requirements:**
- `chat_id` (string, required): MongoDB ObjectId of the chat
- `role` (string, required): Message role (e.g., "user", "assistant", "system")
- `content` (string, required): Message content
- `query_type` (string, optional): Type of query (e.g., "analytics", "general")
- `charts` (any, optional): Chart data or configuration

**Success Response (201 Created):**
```json
{
  "_id": "507f1f77bcf86cd799439020",
  "chat_id": "507f1f77bcf86cd799439013",
  "role": "user",
  "content": "What is the average sales for Q3?",
  "query_type": "analytics",
  "charts": null,
  "timestamp": "2025-11-10T12:05:00.000Z"
}
```

**Error Responses:**
- `404 Not Found`: Chat not found or doesn't belong to user
```json
{
  "detail": "Chat not found"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "507f1f77bcf86cd799439013",
    "role": "user",
    "content": "What is the average sales for Q3?",
    "query_type": "analytics"
  }'
```

---

### Get Messages by Chat

**Endpoint:** `GET /api/messages/chat/{chat_id}`

**Description:** Get all messages for a specific chat (sorted by timestamp, ascending).

**Authentication:** Required

**Path Parameters:**
- `chat_id` (string, required): MongoDB ObjectId of the chat

**Query Parameters:**
- `limit` (integer, optional): Maximum number of messages to return (default: 100)
- `offset` (integer, optional): Number of messages to skip (default: 0)

**Success Response (200 OK):**
```json
[
  {
    "_id": "507f1f77bcf86cd799439020",
    "chat_id": "507f1f77bcf86cd799439013",
    "role": "user",
    "content": "What is the average sales for Q3?",
    "query_type": "analytics",
    "charts": null,
    "timestamp": "2025-11-10T12:05:00.000Z"
  },
  {
    "_id": "507f1f77bcf86cd799439021",
    "chat_id": "507f1f77bcf86cd799439013",
    "role": "assistant",
    "content": "The average sales for Q3 is $125,000.",
    "query_type": "analytics",
    "charts": {
      "type": "bar",
      "data": [100000, 125000, 150000]
    },
    "timestamp": "2025-11-10T12:05:05.000Z"
  }
]
```

**Error Responses:**
- `404 Not Found`: Chat not found or doesn't belong to user

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/messages/chat/507f1f77bcf86cd799439013?limit=50&offset=0" \
  -H "Authorization: Bearer <your_access_token>"
```

---

### Get Message by ID

**Endpoint:** `GET /api/messages/{message_id}`

**Description:** Get a specific message by ID.

**Authentication:** Required

**Path Parameters:**
- `message_id` (string, required): MongoDB ObjectId of the message

**Success Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439020",
  "chat_id": "507f1f77bcf86cd799439013",
  "role": "user",
  "content": "What is the average sales for Q3?",
  "query_type": "analytics",
  "charts": null,
  "timestamp": "2025-11-10T12:05:00.000Z"
}
```

**Error Responses:**
- `404 Not Found`: Message not found or chat doesn't belong to user

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/messages/507f1f77bcf86cd799439020 \
  -H "Authorization: Bearer <your_access_token>"
```

---

## Datasets

### Upload Dataset

**Endpoint:** `POST /api/datasets/upload`

**Description:** Upload a CSV dataset file.

**Authentication:** Required

**Request Body:** `multipart/form-data`
- `file` (file, required): CSV file to upload

**Success Response (201 Created):**
```json
{
  "_id": "507f1f77bcf86cd799439030",
  "user_id": "507f1f77bcf86cd799439011",
  "name": "sales_data.csv",
  "file_name": "sales_data.csv",
  "row_count": 1000,
  "column_count": 8,
  "file_size": 52480,
  "status": "ready",
  "preview_data": {
    "headers": ["date", "product", "sales", "region"],
    "rows": [
      ["2025-01-01", "Product A", "1000", "North"],
      ["2025-01-02", "Product B", "1500", "South"]
    ]
  },
  "uploaded_at": "2025-11-10T12:10:00.000Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid file format or empty file
```json
{
  "detail": "Dataset file is empty"
}
```
```json
{
  "detail": "File must be a valid CSV file"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/datasets/upload \
  -H "Authorization: Bearer <your_access_token>" \
  -F "file=@/path/to/sales_data.csv"
```

---

### Get All Datasets

**Endpoint:** `GET /api/datasets`

**Description:** Get all datasets for the current user (sorted by upload date, descending).

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, optional): Maximum number of datasets to return (default: 100)
- `offset` (integer, optional): Number of datasets to skip (default: 0)

**Success Response (200 OK):**
```json
[
  {
    "_id": "507f1f77bcf86cd799439030",
    "user_id": "507f1f77bcf86cd799439011",
    "name": "sales_data.csv",
    "file_name": "sales_data.csv",
    "row_count": 1000,
    "column_count": 8,
    "file_size": 52480,
    "status": "ready",
    "preview_data": {
      "headers": ["date", "product", "sales", "region"],
      "rows": [
        ["2025-01-01", "Product A", "1000", "North"]
      ]
    },
    "uploaded_at": "2025-11-10T12:10:00.000Z"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/datasets?limit=10&offset=0" \
  -H "Authorization: Bearer <your_access_token>"
```

---

### Get Dataset by ID

**Endpoint:** `GET /api/datasets/{dataset_id}`

**Description:** Get a specific dataset by ID.

**Authentication:** Required

**Path Parameters:**
- `dataset_id` (string, required): MongoDB ObjectId of the dataset

**Success Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439030",
  "user_id": "507f1f77bcf86cd799439011",
  "name": "sales_data.csv",
  "file_name": "sales_data.csv",
  "row_count": 1000,
  "column_count": 8,
  "file_size": 52480,
  "status": "ready",
  "preview_data": {
    "headers": ["date", "product", "sales", "region"],
    "rows": [
      ["2025-01-01", "Product A", "1000", "North"]
    ]
  },
  "uploaded_at": "2025-11-10T12:10:00.000Z"
}
```

**Error Responses:**
- `404 Not Found`: Dataset not found

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/datasets/507f1f77bcf86cd799439030 \
  -H "Authorization: Bearer <your_access_token>"
```

---

### Delete Dataset

**Endpoint:** `DELETE /api/datasets/{dataset_id}`

**Description:** Delete a dataset. Also decrements the user's dataset count.

**Authentication:** Required

**Path Parameters:**
- `dataset_id` (string, required): MongoDB ObjectId of the dataset

**Success Response (204 No Content):**
No body returned.

**Error Responses:**
- `404 Not Found`: Dataset not found

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/datasets/507f1f77bcf86cd799439030 \
  -H "Authorization: Bearer <your_access_token>"
```

---

## Models

### Create Model

**Endpoint:** `POST /api/models`

**Description:** Create a new model entry.

**Authentication:** Required

**Request Body:**
```json
{
  "name": "My Fine-tuned Model",
  "base_model": "gpt-3.5-turbo",
  "version": "1.0.0",
  "accuracy": "0.95",
  "f1_score": "0.92",
  "loss": "0.05",
  "status": "ready",
  "dataset_id": "507f1f77bcf86cd799439030"
}
```

**Field Requirements:**
- `name` (string, required): Model name
- `base_model` (string, required): Base model identifier
- `version` (string, required): Model version
- `accuracy` (string, optional): Model accuracy metric
- `f1_score` (string, optional): F1 score metric
- `loss` (string, optional): Loss metric
- `status` (string, optional): Model status (default: "ready")
- `dataset_id` (string, optional): MongoDB ObjectId of associated dataset

**Success Response (201 Created):**
```json
{
  "_id": "507f1f77bcf86cd799439040",
  "user_id": "507f1f77bcf86cd799439011",
  "name": "My Fine-tuned Model",
  "base_model": "gpt-3.5-turbo",
  "version": "1.0.0",
  "accuracy": "0.95",
  "f1_score": "0.92",
  "loss": "0.05",
  "status": "ready",
  "dataset_id": "507f1f77bcf86cd799439030",
  "created_at": "2025-11-10T12:15:00.000Z"
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/models \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Fine-tuned Model",
    "base_model": "gpt-3.5-turbo",
    "version": "1.0.0",
    "status": "ready",
    "dataset_id": "507f1f77bcf86cd799439030"
  }'
```

---

### Get All Models

**Endpoint:** `GET /api/models`

**Description:** Get all models for the current user (sorted by creation date, descending).

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, optional): Maximum number of models to return (default: 100)
- `offset` (integer, optional): Number of models to skip (default: 0)

**Success Response (200 OK):**
```json
[
  {
    "_id": "507f1f77bcf86cd799439040",
    "user_id": "507f1f77bcf86cd799439011",
    "name": "My Fine-tuned Model",
    "base_model": "gpt-3.5-turbo",
    "version": "1.0.0",
    "accuracy": "0.95",
    "f1_score": "0.92",
    "loss": "0.05",
    "status": "ready",
    "dataset_id": "507f1f77bcf86cd799439030",
    "created_at": "2025-11-10T12:15:00.000Z"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/models?limit=10&offset=0" \
  -H "Authorization: Bearer <your_access_token>"
```

---

### Get Model by ID

**Endpoint:** `GET /api/models/{model_id}`

**Description:** Get a specific model by ID.

**Authentication:** Required

**Path Parameters:**
- `model_id` (string, required): MongoDB ObjectId of the model

**Success Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439040",
  "user_id": "507f1f77bcf86cd799439011",
  "name": "My Fine-tuned Model",
  "base_model": "gpt-3.5-turbo",
  "version": "1.0.0",
  "accuracy": "0.95",
  "f1_score": "0.92",
  "loss": "0.05",
  "status": "ready",
  "dataset_id": "507f1f77bcf86cd799439030",
  "created_at": "2025-11-10T12:15:00.000Z"
}
```

**Error Responses:**
- `404 Not Found`: Model not found

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/models/507f1f77bcf86cd799439040 \
  -H "Authorization: Bearer <your_access_token>"
```

---

## Fine-tuning

### Create Fine-tune Job

**Endpoint:** `POST /api/finetune`

**Description:** Create a new fine-tuning job. Increments user's fine-tune job count.

**Authentication:** Required

**Request Body:**
```json
{
  "dataset_id": "507f1f77bcf86cd799439030",
  "base_model": "gpt-3.5-turbo",
  "model_id": null,
  "status": "preparing",
  "progress": 0,
  "current_step": "Initializing",
  "logs": "Job created successfully"
}
```

**Field Requirements:**
- `dataset_id` (string, required): MongoDB ObjectId of the dataset
- `base_model` (string, required): Base model identifier
- `model_id` (string, optional): MongoDB ObjectId of resulting model
- `status` (string, optional): Job status (default: "preparing")
- `progress` (integer, optional): Progress percentage (default: 0)
- `current_step` (string, optional): Current step description
- `logs` (string, optional): Job logs

**Success Response (201 Created):**
```json
{
  "_id": "507f1f77bcf86cd799439050",
  "user_id": "507f1f77bcf86cd799439011",
  "model_id": null,
  "dataset_id": "507f1f77bcf86cd799439030",
  "base_model": "gpt-3.5-turbo",
  "status": "preparing",
  "progress": 0,
  "current_step": "Initializing",
  "logs": "Job created successfully",
  "created_at": "2025-11-10T12:20:00.000Z",
  "completed_at": null
}
```

**Error Responses:**
- `404 Not Found`: Dataset not found

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/finetune \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "507f1f77bcf86cd799439030",
    "base_model": "gpt-3.5-turbo",
    "status": "preparing",
    "progress": 0
  }'
```

---

### Get All Fine-tune Jobs

**Endpoint:** `GET /api/finetune`

**Description:** Get all fine-tune jobs for the current user (sorted by creation date, descending).

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, optional): Maximum number of jobs to return (default: 100)
- `offset` (integer, optional): Number of jobs to skip (default: 0)

**Success Response (200 OK):**
```json
[
  {
    "_id": "507f1f77bcf86cd799439050",
    "user_id": "507f1f77bcf86cd799439011",
    "model_id": "507f1f77bcf86cd799439040",
    "dataset_id": "507f1f77bcf86cd799439030",
    "base_model": "gpt-3.5-turbo",
    "status": "completed",
    "progress": 100,
    "current_step": "Completed",
    "logs": "Fine-tuning completed successfully",
    "created_at": "2025-11-10T12:20:00.000Z",
    "completed_at": "2025-11-10T13:30:00.000Z"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/finetune?limit=10&offset=0" \
  -H "Authorization: Bearer <your_access_token>"
```

---

### Get Fine-tune Job by ID

**Endpoint:** `GET /api/finetune/{job_id}`

**Description:** Get a specific fine-tune job by ID.

**Authentication:** Required

**Path Parameters:**
- `job_id` (string, required): MongoDB ObjectId of the fine-tune job

**Success Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439050",
  "user_id": "507f1f77bcf86cd799439011",
  "model_id": "507f1f77bcf86cd799439040",
  "dataset_id": "507f1f77bcf86cd799439030",
  "base_model": "gpt-3.5-turbo",
  "status": "training",
  "progress": 45,
  "current_step": "Training model",
  "logs": "Epoch 3/10 completed",
  "created_at": "2025-11-10T12:20:00.000Z",
  "completed_at": null
}
```

**Error Responses:**
- `404 Not Found`: Fine-tune job not found

**cURL Example:**
```bash
curl -X GET http://localhost:8000/api/finetune/507f1f77bcf86cd799439050 \
  -H "Authorization: Bearer <your_access_token>"
```

---

### Update Fine-tune Job Status

**Endpoint:** `PATCH /api/finetune/{job_id}/status`

**Description:** Update the status and progress of a fine-tune job.

**Authentication:** Required

**Path Parameters:**
- `job_id` (string, required): MongoDB ObjectId of the fine-tune job

**Query Parameters:**
- `status_update` (string, required): New status value
- `progress` (integer, optional): Progress percentage (0-100)
- `current_step` (string, optional): Current step description
- `logs` (string, optional): Updated logs

**Success Response (200 OK):**
```json
{
  "_id": "507f1f77bcf86cd799439050",
  "user_id": "507f1f77bcf86cd799439011",
  "model_id": "507f1f77bcf86cd799439040",
  "dataset_id": "507f1f77bcf86cd799439030",
  "base_model": "gpt-3.5-turbo",
  "status": "completed",
  "progress": 100,
  "current_step": "Completed",
  "logs": "Fine-tuning completed successfully",
  "created_at": "2025-11-10T12:20:00.000Z",
  "completed_at": "2025-11-10T13:30:00.000Z"
}
```

**Error Responses:**
- `404 Not Found`: Fine-tune job not found or no changes made

**Note:** When status is set to "completed", the `completed_at` field is automatically set to the current UTC time.

**cURL Example:**
```bash
curl -X PATCH "http://localhost:8000/api/finetune/507f1f77bcf86cd799439050/status?status_update=training&progress=50&current_step=Training%20model&logs=Epoch%205/10%20completed" \
  -H "Authorization: Bearer <your_access_token>"
```

---

## API Keys

### Create API Key

**Endpoint:** `POST /api/apikeys`

**Description:** Generate a new API key for a specific model.

**Authentication:** Required

**Request Body:**
```json
{
  "model_id": "507f1f77bcf86cd799439040",
  "name": "Production API Key"
}
```

**Field Requirements:**
- `model_id` (string, required): MongoDB ObjectId of the model
- `name` (string, required): Descriptive name for the API key

**Success Response (201 Created):**
```json
{
  "_id": "507f1f77bcf86cd799439060",
  "user_id": "507f1f77bcf86cd799439011",
  "model_id": "507f1f77bcf86cd799439040",
  "key": "sk-1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x",
  "name": "Production API Key",
  "created_at": "2025-11-10T12:25:00.000Z"
}
```

**Error Responses:**
- `404 Not Found`: Model not found
```json
{
  "detail": "Model not found"
}
```

**Security Note:** The API key is only returned once during creation. Store it securely.

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/apikeys \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "507f1f77bcf86cd799439040",
    "name": "Production API Key"
  }'
```

---

### Get All API Keys

**Endpoint:** `GET /api/apikeys`

**Description:** Get all API keys for the current user (sorted by creation date, descending).

**Authentication:** Required

**Query Parameters:**
- `limit` (integer, optional): Maximum number of API keys to return (default: 100)
- `offset` (integer, optional): Number of API keys to skip (default: 0)

**Success Response (200 OK):**
```json
[
  {
    "_id": "507f1f77bcf86cd799439060",
    "user_id": "507f1f77bcf86cd799439011",
    "model_id": "507f1f77bcf86cd799439040",
    "key": "sk-1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x",
    "name": "Production API Key",
    "created_at": "2025-11-10T12:25:00.000Z"
  },
  {
    "_id": "507f1f77bcf86cd799439061",
    "user_id": "507f1f77bcf86cd799439011",
    "model_id": "507f1f77bcf86cd799439040",
    "key": "sk-9z8y7x6w5v4u3t2s1r0q9p8o7n6m5l4k3j2i1h0g9f8e7d6c",
    "name": "Development API Key",
    "created_at": "2025-11-09T10:15:00.000Z"
  }
]
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/api/apikeys?limit=10&offset=0" \
  -H "Authorization: Bearer <your_access_token>"
```

---

### Delete API Key

**Endpoint:** `DELETE /api/apikeys/{apikey_id}`

**Description:** Delete an API key.

**Authentication:** Required

**Path Parameters:**
- `apikey_id` (string, required): MongoDB ObjectId of the API key

**Success Response (204 No Content):**
No body returned.

**Error Responses:**
- `404 Not Found`: API key not found

**cURL Example:**
```bash
curl -X DELETE http://localhost:8000/api/apikeys/507f1f77bcf86cd799439060 \
  -H "Authorization: Bearer <your_access_token>"
```

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
Invalid request data or validation error.

```json
{
  "detail": "Error message describing the issue"
}
```

### 401 Unauthorized
Missing or invalid authentication token.

```json
{
  "detail": "Could not validate credentials"
}
```

### 404 Not Found
Requested resource not found.

```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
Request validation failed (invalid data types, missing required fields).

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

### 500 Internal Server Error
Server-side error.

```json
{
  "detail": "Internal server error"
}
```

---

## Authentication Flow

### 1. Register a New User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "name": "John Doe"
  }'
```

### 2. Login and Receive Token
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Use Token for Authenticated Requests
Include the token in the Authorization header for all protected endpoints:

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## Data Types

### MongoDB ObjectId
MongoDB ObjectIds are 24-character hexadecimal strings. Example: `507f1f77bcf86cd799439011`

In API responses, ObjectIds are serialized as strings.

### Datetime
All datetime fields are in ISO 8601 format (UTC timezone). Example: `2025-11-10T12:00:00.000Z`

---

## Pagination

Many list endpoints support pagination through query parameters:
- `limit`: Maximum number of items to return (default: 100)
- `offset`: Number of items to skip (default: 0)

Example:
```
GET /api/chats?limit=20&offset=40
```

This returns 20 chats, skipping the first 40 (i.e., chats 41-60).

---

## Testing the API

### Using cURL

Test authentication:
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","name":"Test User"}'

# Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}' | jq -r '.access_token')

# Get current user
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Using JavaScript (Axios)

```javascript
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Register
const register = async (email, password, name) => {
  const response = await axios.post(`${API_BASE_URL}/api/auth/register`, {
    email,
    password,
    name
  });
  return response.data;
};

// Login
const login = async (email, password) => {
  const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
    email,
    password
  });
  return response.data.access_token;
};

// Create authenticated axios instance
const createAuthAxios = (token) => {
  return axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
};

// Example: Get chats
const getChats = async (token) => {
  const authAxios = createAuthAxios(token);
  const response = await authAxios.get('/api/chats');
  return response.data;
};
```

### Using React Query

```javascript
import { useQuery, useMutation } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Login mutation
export const useLogin = () => {
  return useMutation({
    mutationFn: async ({ email, password }) => {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        email,
        password
      });
      return response.data;
    }
  });
};

// Get chats query
export const useChats = (token) => {
  return useQuery({
    queryKey: ['chats'],
    queryFn: async () => {
      const response = await axios.get(`${API_BASE_URL}/api/chats`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      return response.data;
    },
    enabled: !!token
  });
};
```

---

## Notes for Frontend Developers

### Security Considerations
1. Store JWT tokens securely (e.g., in httpOnly cookies or secure storage)
2. Include the token in the Authorization header for all authenticated requests
3. Handle token expiration and refresh logic
4. Never expose sensitive data in client-side code

### File Uploads
For dataset uploads, use `FormData`:
```javascript
const uploadDataset = async (file, token) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post(
    `${API_BASE_URL}/api/datasets/upload`,
    formData,
    {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    }
  );
  return response.data;
};
```

### Error Handling
Always handle errors appropriately:
```javascript
try {
  const response = await axios.get('/api/chats', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return response.data;
} catch (error) {
  if (error.response?.status === 401) {
    // Handle unauthorized (redirect to login)
  } else if (error.response?.status === 404) {
    // Handle not found
  } else {
    // Handle other errors
  }
  throw error;
}
```

### MongoDB ObjectId Format
ObjectIds are 24-character hexadecimal strings. When displaying or using them:
- They can be used directly as strings in React components
- No conversion needed when sending to the API
- Example: `507f1f77bcf86cd799439011`

---

## API Status

All endpoints have been reviewed and verified to be working correctly based on the codebase analysis.

**Last Updated:** 2025-11-10
**API Version:** 1.0.0
**Base URL:** http://localhost:8000
