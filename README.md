# Code Checker: AI-Powered Programming Assessment Platform

[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/django-4.1-green.svg)](https://www.djangoproject.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-lightgrey)](https://openai.com/)

Code Checker is an advanced programming assessment platform powered by OpenAI's GPT models to generate, evaluate, and provide feedback on programming challenges across multiple languages and difficulty levels.

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Setup & Installation](#setup--installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Development](#development)
- [Production Deployment](#production-deployment)
- [Testing](#testing)
- [Troubleshooting & Common Issues](#troubleshooting--common-issues)
- [Contributing](#contributing)
- [License](#license)

## 🔍 Overview

Code Checker is a Django-based web application that leverages OpenAI's GPT models to provide a comprehensive programming assessment platform. The system can generate unique coding questions, theory questions, and multiple-choice questions (MCQs) across various programming languages and difficulty levels. It evaluates submitted code, provides feedback, and tracks user progress.

The platform uses vector embeddings for semantic similarity checks to prevent duplicate questions and features a robust leaderboard system to encourage friendly competition among users.

## ✨ Features

- **User Authentication & Management**
  - Email-based signup with verification
  - Password reset and change functionality
  - Google OAuth integration
  - User profile management

- **Question Generation**
  - AI-generated coding challenges (with automatic test case creation)
  - Theory questions for conceptual understanding
  - Multiple-choice questions for quick assessments
  - Support for multiple programming languages
  - Three difficulty levels: Easy, Medium, Hard
  - Semantic duplicate detection using OpenAI embeddings

- **Quiz System**
  - Create customized quizzes based on language and difficulty
  - Track quiz progress and completion
  - Automatic or manual quiz completion
  - View detailed quiz history

- **Code Evaluation**
  - Syntax validation for submitted code
  - Secure code execution in controlled environments
  - Testing against predefined test cases
  - AI-powered feedback for incorrect submissions

- **Progress Tracking & Leaderboards**
  - Individual progress tracking
  - Global leaderboards based on accuracy
  - Quiz-specific leaderboards
  - User submission history and review
  - Friend comparison feature

## 🏗️ System Architecture

The system follows a standard Django architecture with the following key components:

### Core Components

1. **Authentication Module** (built on django-rest-authemail and social-auth)
   - Handles user signup, verification, and login
   - Supports OAuth integration for Google login

2. **Question Generation System** 
   - Uses OpenAI GPT-4 to generate programming questions
   - Implements semantic similarity checks using embeddings
   - Supports multiple question types (coding, theory, MCQ)

3. **Quiz Management System**
   - Creates and manages quizzes
   - Tracks quiz progress and completion
   - Handles question sequencing and scoring

4. **Code Execution & Evaluation System**
   - Validates code syntax
   - Runs code against test cases
   - Provides feedback on submissions

5. **Progress & Leaderboard System**
   - Tracks individual and comparative progress
   - Generates leaderboards based on various metrics

### Database Models

- `MyUser`: Extended user model for authentication
- `ProgrammingLanguage`: Supported programming languages
- `ExpertiseLevel`: Difficulty levels for questions
- `QuizQuestion`, `TheoryQuestion`, `MCQQuestion`: Different question types
- `TestCase`: Input/output test cases for coding questions
- `QuestionEmbedding`: Vector embeddings for semantic similarity checks
- `Quiz` and `QuizQuestionResponse`: Quiz management and tracking
- `UserProgress` and `UserSubmission`: User performance tracking

## 🛠️ Setup & Installation

### Prerequisites

- Python 3.8+
- PostgreSQL with pgvector extension (recommended for production)
- OpenAI API key

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/code-checker.git
   cd code-checker
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
    source venv/bin/activate
```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a .env file based on env-sample**
   ```bash
   cp env-sample .env
   ```

6. **Update the .env file with your configuration**
   - Add your OpenAI API key
   - Configure database settings
   - Set up email settings for verification
   - Add Google OAuth credentials (if using)

7. **Apply migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

8. **Run the server**
   ```bash
   python manage.py runserver
   ```

## ⚙️ Configuration

### Environment Variables

Edit the `.env` file with the following configurations:

```
# Django Settings
SECRET_KEY=your_secret_key

# Database Settings
DB_ENGINE=django.db.backends.postgresql
DB_NAME=code_checker_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432


# OpenAI Settings
open_ai_key=your_openai_api_key
```

## 🗃️ Database Setup

The application can work with SQLite (default for development) or PostgreSQL (recommended for production).

### PostgreSQL Setup with pgvector (Recommended)

1. **Install PostgreSQL and pgvector extension**

2. **Create a database**
   ```sql
   CREATE DATABASE code_checker_db;
   ```

3. **Enable pgvector extension**
   ```sql
   \c code_checker_db
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

4. **Update .env file with PostgreSQL settings**
   ```
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=code_checker_db
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=5432
   ```

### Initial Data

To create initial programming languages and expertise levels:

```bash
python manage.py shell
```

```python
from interface.models import ProgrammingLanguage, ExpertiseLevel

# Add programming languages
languages = ["Python", "JavaScript", "Java", "C++", "C#"]
for lang in languages:
    ProgrammingLanguage.objects.get_or_create(name=lang)

# Add expertise levels
levels = ["Easy", "Medium", "Hard"]
for level in levels:
    ExpertiseLevel.objects.get_or_create(level=level)
```

## 🚀 Usage

### Starting the Server

```bash
python manage.py runserver
```

### Generating Embeddings for Questions

To enable semantic similarity checks, generate embeddings for existing questions:

```bash
python manage.py generate_embeddings --types all
```

Options:
- `--types`: Question types to process (coding,theory,mcq,all)
- `--batch-size`: Number of questions per batch (default: 50)
- `--sleep-time`: Wait time between batches in seconds (default: 10.0)
- `--force`: Regenerate embeddings for all questions

## 🔌 API Endpoints

> **Authentication Note**: Most endpoints require a JWT authentication token. Include the token in the request header as:
> ```
> Authorization: Bearer <your_jwt_token>
> ```
> 
> To obtain this token, use the `/api/token/` endpoint.

### Authentication

- `POST /api/token/`
  - **Description**: Obtain a JWT token for authentication
  - **Request Body**:
    ```json
    {
      "email": "user@example.com",
      "password": "your_password"
    }
    ```
  - **Response**:
    ```json
    {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    ```
  - **Authentication**: None required

- `POST /api/token/refresh/`
  - **Description**: Refresh an expired JWT token
  - **Request Body**:
    ```json
    {
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    ```
  - **Response**:
    ```json
    {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    ```
  - **Authentication**: None required

- `POST /api/signup/`
  - **Description**: Register a new user
  - **Request Body**:
    ```json
    {
      "email": "user_1234@gmail.com",
      "password": "Test@1234",
      "first_name": "John",
      "last_name": "Doe"
    } 
    ```
  - **Response**:
    ```json
    {
      "email": "user_1234@gmail.com",
      "first_name": "John",
      "last_name": "Doe"
    }
    ```
  - **Authentication**: None required

- `POST /api/password/change/`
  - **Description**: Change password (for authenticated users)
  - **Request Body**:
    ```json
    {
      "password": "current_password",
      "new_password": "new_secure_password"
    }
    ```
  - **Response**:
    ```json
    {
      "success": "Password changed."
    }
    ```
  - **Authentication**: JWT token required

### Question Generation

- `POST /api/generate-quiz-question/`
  - **Description**: Generate a coding question
  - **Request Body**:
    ```json
    {
      "language_id": 1,
      "level_id": 2
    }
    ```
  - **Response**:
    ```json
    {
      "question_id": 48,
      "question": "Generated question will come here"
    }
    ```
  - **Authentication**: None required

- `POST /api/generate-mcq-question/`
  - **Description**: Generate a multiple-choice question
  - **Request Body**:
    ```json
    {
      "language_id": 2,
      "level_id": 1
    }
    ```
  - **Response**:
    ```json
    {
      "id": 56,
      "question": "What is the output of the following expression 3 + 2 * 4 in Python?",
      "options": {
          "A": "14",
          "B": "11",
          "C": "10",
          "D": "8"
      },
      "correct_option": "B"
    }
    ```
  - **Authentication**: None required

- `POST /api/generate-theory-question/`
  - **Description**: Generate a theory question
  - **Request Body**:
    ```json
    {
      "language_id": 2,
      "level_id": 1
    }
    ```
  - **Response**:
    ```json
    {
      "id": 35,
      "question": "What is the difference between a list and a tuple in Python?"
    }
    ```
  - **Authentication**: None required

### Quiz Management

- `POST /api/create-quiz/`
  - **Description**: Create a new quiz
  - **Request Body**:
    ```json
    {
      "language_id": 1,
      "level_id": 2,
      "num_questions": 5
    }
    ```
  - **Response**:
    ```json
    {
      "quiz_id": 12,
      "language": "PHP",
      "level": "Intermediate",
      "num_questions": 5,
      "available_questions": {
          "coding": 2,
          "theory": 2,
          "mcq": 1,
          "total": 5
      }
    }
    ```
  - **Authentication**: JWT token required

- `GET /api/quiz/<quiz_id>/next-question/`
  - **Description**: Get the next question in a quiz
  - **Path Parameters**: `quiz_id` - ID of the quiz
  - **Response**:
    ```json
    {
      "question_id": 48,
      "question_type": "coding",
      "question_text": "Quiz Question"
    }
    ```
  - **Authentication**: JWT token required

- `POST /api/quiz/<quiz_id>/submit-answer/`
  - **Description**: Submit an answer for a quiz question
  - **Path Parameters**: `quiz_id` - ID of the quiz
  - **Request Body** (for coding question):
    ```json
    {
      "question_id": 48,
      "answer": "Submit Answer here",
      "question_type": "Type of question here",
      "start_time": "Current time here"
    }
    ```
  - **Response**:
    ```json
    {
      "is_correct": false,
      "feedback": "The submitted code does not implement the required functionality. It appears to be a placeholder or an incorrect statement. The function 'wordCount' is not defined, and there is no logic to count words or handle the input string as specified in the problem description."
    }
    ```
  - **Authentication**: JWT token required

- `POST /api/quiz/<quiz_id>/complete/`
  - **Description**: Complete a quiz
  - **Path Parameters**: `quiz_id` - ID of the quiz
  - **Response**:
    ```json
    {
      "quiz_id": 12,
      "total_questions": 1,
      "correct_answers": 0,
      "score": 0,
      "completed_at": "2025-04-17T10:33:43.074715Z"
    }
    ```
  - **Authentication**: JWT token required

- `GET /api/quiz/<quiz_id>/details/`
  - **Description**: Get quiz details
  - **Path Parameters**: `quiz_id` - ID of the quiz
  - **Response**:
    ```json
    {
      "quiz_id": 12,
      "language": "PHP",
      "level": "Intermediate",
      "created_at": "2025-04-17T10:21:15.259850Z",
      "completed_at": "2025-04-17T10:33:43.074715Z",
      "score": 0,
      "total_questions": 1,
      "score_percentage": 0,
      "progress": 100,
      "remaining_questions": 0,
      "responses": [
          {
              "id": 34,
              "question_type": "coding",
              "question_id": 48,
              "question_text": "Question here",
              "options": null,
              "user_response": "USer Answer here",
              "is_correct": false,
              "created_at": "2025-04-17T10:27:52.514873Z"
          }
      ],
      "is_completed": true
    }
    ```
  - **Authentication**: JWT token required

- `GET /api/quiz-history/`
  - **Description**: Get user's quiz history
  - **Query Parameters**:
    - `page` (optional): Page number for pagination
    - `page_size` (optional): Number of results per page
  - **Response**:
    ```json
    [
      {
        "quiz_id": 12,
        "language": "PHP",
        "level": "Intermediate",
        "created_at": "2025-04-17T10:21:15.259850Z",
        "completed_at": "2025-04-17T10:33:43.074715Z",
        "total_questions": 1,
        "correct_answers": 0,
        "score": 0,
        "is_completed": true
      }
    ]
    ```
  - **Authentication**: JWT token required

### Leaderboards & Progress

- `GET /api/leaderboard/`
  - **Description**: Get global leaderboard
  - **Query Parameters**:
    - `type` (optional): Metric type (accuracy, quiz_score), default is accuracy
    - `period` (optional): Time period (all, month, week), default is all
  - **Response**:
    ```json
    {
      "leaderboard_type": "accuracy",
      "time_period": "all",
      "leaderboard": [
          {
          "user_id": 2,
          "user_email": "dev@gmail.com",
          "accuracy": 78.57,
          "correct_answers": 11,
          "total_attempts": 14
          }
      ]
    }
    ```
  - **Authentication**: JWT token required

- `GET /api/quiz-leaderboard/`
  - **Description**: Get quiz-specific leaderboard
  - **Query Parameters**:
    - `language` (optional): Filter by programming language ID (e.g., 1 for Python)
    - `level` (optional): Filter by expertise level ID (e.g., 2 for Medium)
  - **Response**:
    ```json
    {
    "leaderboard": [
        {
            "quiz_id": 1,
            "user_id": 2,
            "user_email": "dev@gmail.com",
            "language": "C#",
            "level": "Easy",
            "score": 5,
            "correct_answers": 0,
            "total_questions": 0,
            "completion_time": 0,
            "completed_at": "2025-04-16T16:51:55.979099Z"
        },
        {
            "quiz_id": 8,
            "user_id": 2,
            "user_email": "dev@gmail.com",
            "language": "Python",
            "level": "Easy",
            "score": 5,
            "correct_answers": 0,
            "total_questions": 0,
            "completion_time": 0,
            "completed_at": "2025-04-16T18:05:53.717722Z"
        },
        {
            "quiz_id": 9,
            "user_id": 2,
            "user_email": "dev@gmail.com",
            "language": "Python",
            "level": "Easy",
            "score": 1,
            "correct_answers": 0,
            "total_questions": 0,
            "completion_time": 0,
            "completed_at": "2025-04-16T18:14:28.859032Z"
        },
        {
            "quiz_id": 12,
            "user_id": 1,
            "user_email": "admin@gmail.com",
            "language": "C#",
            "level": "Intermediate",
            "score": 0,
            "correct_answers": 0,
            "total_questions": 0,
            "completion_time": 0,
            "completed_at": "2025-04-17T10:33:43.074715Z"
        },
        {
            "quiz_id": 15,
            "user_id": 1,
            "user_email": "admin@gmail.com",
            "language": "Python",
            "level": "Easy",
            "score": 0,
            "correct_answers": 0,
            "total_questions": 0,
            "completion_time": 0,
            "completed_at": "2025-04-24T17:14:14.381745Z"
        }
    ]
  } 
    ```
  - **Authentication**: JWT token required

- `GET /api/user-submissions/`
  - **Description**: Get current user's submissions
  - **Query Parameters**:
    - `question_type` (optional): Filter by question type (coding, theory, mcq)
    - `language` (optional): Filter by programming language ID (e.g., 1 for Python)
    - `level` (optional): Filter by expertise level ID (e.g., 2 for Medium)
    - `page` (optional): Page number for pagination
  - **Response**:
    ```json
    {
      "user_id": 1,
      "user_email": "admin@gmail.com",
      "progress": {
        "accuracy": 0,
        "correct_answers": 0,
        "total_attempts": 0,
        "average_time": 0
      },
      "quizzes": [
          {
            "quiz_id": 12,
            "language": "PHP",
            "level": "Intermediate",
            "score": 0,
            "created_at": "2025-04-17T10:21:15.259850Z",
            "completed_at": "2025-04-17T10:33:43.074715Z",
            "correct_answers": 0,
            "total_questions": 1,
            "duration_seconds": 0.0
          }
      ],
      "recent_submissions": [
          {
            "question_text": "Write a python code for the sum of two numbers.",
            "language": "Python",
            "level": "Easy",
            "time_taken": 0.0,
            "created_at": "2025-04-15T16:26:05.979341Z"
          },
          {
            "question_text": "Write a python code for the sum of two numbers.",
            "language": "Python",
            "level": "Easy",
            "time_taken": 0.0,
            "created_at": "2025-04-15T16:23:54.128467Z"
          },
          {
            "question_text": "Write a python code for the sum of two numbers.",
            "language": "Python",
            "level": "Easy",
            "time_taken": 0.0,
            "created_at": "2025-04-15T16:04:24.842718Z"
          },
          {
            "question_text": "Write a python code for the sum of two numbers.",
            "language": "Python",
            "level": "Easy",
            "time_taken": 0.0,
            "created_at": "2025-04-15T13:26:54.642401Z"
          },
          {
            "question_text": "What is the purpose of the \"echo\" function in PHP?",
            "language": "PHP",
            "level": "Easy",
            "time_taken": 0.0,
            "created_at": "2025-04-15T08:48:43.427989Z"
          }
      ],
        "language_proficiency": {
        "PHP": {
          "total": 2,
          "correct": 1,
          "proficiency": 50.0
        },
          "Python": {
            "total": 4,
            "correct": 4,
            "proficiency": 100.0
        }
      }
    }
    ```
  - **Authentication**: JWT token required

- `GET /api/user-submissions/<user_id>/`
  - **Description**: Get specific user's submissions
  - **Path Parameters**: `user_id` - ID of the user to view
  - **Query Parameters**: Same as `/api/user-submissions/`
  - **Response**: Same format as `/api/user-submissions/`
  - **Authentication**: JWT token required


### Answers Submission (Outside of Quiz)

- `POST /api/submit-answer/`
  - **Description**: Submit an answer for a coding question (outside of a quiz)
  - **Request Body**:
    ```json
    {
      "question_id": 21,
      "language": "C++",
      "code": "Purpose of `cout` is to print output.",
      "start_time": "2025-04-17T08:37:33.688739Z"
    }
    ```
  - **Response**:
    ```json
    {
      "submission_id": 25,
      "is_correct": false,
      "feedback": "Reason for the correct/incorrect.",
      "time_taken": 9302.942288,
      "failed_test_cases": []
    }
    ```
  - **Authentication**: JWT token required

- `POST /api/submit-theory-answer/`
  - **Description**: Submit an answer for a theory question (outside of a quiz)
  - **Request Body**:
    ```json
    {
      "question_id": 35,
      "answer": "Add Answer here"
    }
    ```
  - **Response**:
    ```json
    {
      "feedback": "Correct Answer"
    }
    ```
  - **Authentication**: JWT token required

### Programming Languages

#### List Programming Languages
- **Endpoint:** `GET /api/programming-languages/`
- **Description:** Retrieve a list of all programming languages.

#### Create Programming Language
- **Endpoint:** `POST /api/programming-languages/`
- **Description:** Create a new programming language.
- **Request Body:**
  ```json
  {
      "name": "string",
  }
  ```

#### Retrieve Programming Language
- **Endpoint:** `GET /api/programming-languages/{id}/`
- **Description:** Retrieve details of a specific programming language by ID.

#### Update Programming Language
- **Endpoint:** `PATCH /api/programming-languages/{id}/`
- **Description:** Update an existing programming language by ID.
- **Request Body:**
  ```json
  {
    "name": "C#"
  }
  ```
  - **Response**:
    ```json
    {
      "id": 1,
      "name": "C#"
    }

#### Delete Programming Language
- **Endpoint:** `DELETE /api/programming-languages/{id}/`
- **Description:** Delete a specific programming language by ID.
---
  - **Response**:
    ```json
    {
      "id": 1,
      "name": "C#"
    }
### Expertise Levels

#### List Expertise Levels
- **Endpoint:** `GET /api/expertise-levels/`
- **Description:** Retrieve a list of all expertise levels.
---
  - **Response**:
    ```json
  {
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 1,
        "level": "Easy"
      },
      {
        "id": 2,
        "level": "Intermediate"
      },
      {
        "id": 3,
        "level": "Hard"
      }
    ]
  }

#### Create Expertise Level
- **Endpoint:** `POST /api/expertise-levels/`
- **Description:** Create a new expertise level.
- **Request Body:**
  ```json
  {
    "level": "Expert"
  }
  ```
---
  - **Response**:
  ```json
  {
    "id": 6,
    "level": "Expert"
  }
  ```  

#### Retrieve Expertise Level
- **Endpoint:** `GET /api/expertise-levels/{id}/`
- **Description:** Retrieve details of a specific expertise level by ID.
---
  - **Response**:
  ```json
  {
    "id": 1,
    "level": "Easy"
  }
  ```
#### Update Expertise Level
- **Endpoint:** `PATCH /api/expertise-levels/{id}/`
- **Description:** Update an existing expertise level by ID.
- **Request Body:**
  ```json
  {
    "level": "Begineer"
  }
---
- **Response**:
```json
{
  "id": 1,
  "level": "Begineer"
}
```
#### Generate Assignment
- **Endpoint:** `POST /api/assignments/generate/`
- **Description:** Generate Assignment
- **Request Body:**
  ```json
  {
    "language_id": 1,
    "level_id": 1    
  }
---
- **Response**:
```json
{
    "assignment_id": 2,
     "coding_questions": [
        {
            "id": 55,
            "question_text":"Question",
            "programming_language": 1,
            "expertise_level": 1,
            "created_at": "2025-05-03T20:52:04.275685Z"
        },
        .....
      ],
      "theory_questions": [
        {
            "id": 39,
            "question_text": "What is the purpose of the `using` statement in C#, and how does it help in resource management?",
            "programming_language": 1,
            "expertise_level": 1,
            "created_at": "2025-05-03T20:53:19.122515Z"
        },
        ....
      ]
}
            
```
#### Submit Assignment
- **Endpoint:** `POST /api/assignments/assignment_id/submit/`
- **Description:** Submit Assingment by ID
- **Request Body:**
  ```json
   {
      "answers": [
        {
          "question_type": "coding",
          "question_id": 55,
          "answer": "<your code string>"
        },
        {
          "question_type": "coding",
          "question_id": 56,
          "answer": "<your theory answer text>"
        },
        {
          "question_type": "coding",
          "question_id": 57,
          "answer": "<your theory answer text>"
        },
        {
          "question_type": "coding",
          "question_id": 58,
          "answer": "<your theory answer text>"
        },
        {
          "question_type": "coding",
          "question_id": 59,
          "answer": "<your theory answer text>"
        },
        {
          "question_type": "coding",
          "question_id": 60,
          "answer": "<your theory answer text>"
        },
        {
          "question_type": "coding",
          "question_id": 61,
          "answer": "<your theory answer text>"
        },
        {
          "question_type": "coding",
          "question_id": 62,
          "answer": "<your theory answer text>"
        },
        {
          "question_type": "theory",
          "question_id": 39,
          "answer": "The `using` statement in C# is used to ensure that an object implementing the `IDisposable` interface is automatically disposed of when it's no longer needed. It helps in resource management by guaranteeing that the `Dispose()` method is called, releasing unmanaged resources like file handles, database connections, or network streams as soon as they go out of scope—either normally or due to an exception. This prevents resource leaks and promotes clean, efficient code without requiring manual cleanup in `try...finally` blocks."
        },
        {
          "question_type": "theory",
          "question_id": 40,
          "answer": "The using statement in C# ensures automatic disposal of objects that implement IDisposable, guaranteeing deterministic cleanup of unmanaged resources (e.g., file handles, database connections). It simplifies resource management by calling Dispose() implicitly when exiting the block, even during exceptions, avoiding leaks. Variables declared in a using block are scoped to it, preventing misuse afterward. Available as a concise statement (C# 8.0+) or traditional block syntax, it streamlines code while enforcing safe, efficient resource handling."
        }
      ]
    }
---
- **Response**:
```json
{
    "assignment_id": 1,
    "score": 2,
    "total_questions": 10,
    "results": [
        {
            "question_id": 55,
            "question_type": "coding",
            "is_correct": false
        },
        {
            "question_id": 56,
            "question_type": "coding",
            "is_correct": false
        },
        {
            "question_id": 57,
            "question_type": "coding",
            "is_correct": false
        },
        {
            "question_id": 58,
            "question_type": "coding",
            "is_correct": false
        },
        {
            "question_id": 59,
            "question_type": "coding",
            "is_correct": false
        },
        {
            "question_id": 60,
            "question_type": "coding",
            "is_correct": false
        },
        {
            "question_id": 61,
            "question_type": "coding",
            "is_correct": false
        },
        {
            "question_id": 62,
            "question_type": "coding",
            "is_correct": false
        },
        {
            "question_id": 39,
            "question_type": "theory",
            "is_correct": true
        },
        {
            "question_id": 40,
            "question_type": "theory",
            "is_correct": true
        }
    ],
    "evaluation_warnings": []
}
```
#### Get All Assignment 
- **Endpoint:** `GET /api/assignments/`
- **Description:** Get all Assignments.
---
- **Response**:
```json
{
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 2,
            "user": {
                "id": 1,
                "last_login": "2025-05-03T21:53:08.836757Z",
                "is_superuser": true,
                "first_name": "admin",
                "last_name": "admin",
                "email": "admin@gmail.com",
                "is_staff": true,
                "is_active": true,
                "date_joined": "2025-04-10T20:47:32.619579Z",
                "is_verified": true,
                "groups": [],
                "user_permissions": []
            },
            "programming_language": {
                "id": 1,
                "name": "C#"
            },
            "expertise_level": {
                "id": 1,
                "level": "Easy"
            },
            "created_at": "2025-05-03T22:38:36.905797Z",
            "completed_at": null,
            "score": 0,
            "total_questions": 10,
            "responses": []
        },
        {
            "id": 1,
            "user": {
                "id": 1,
                "last_login": "2025-05-03T21:53:08.836757Z",
                "is_superuser": true,
                "first_name": "admin",
                "last_name": "admin",
                "email": "admin@gmail.com",
                "is_staff": true,
                "is_active": true,
                "date_joined": "2025-04-10T20:47:32.619579Z",
                "is_verified": true,
                "groups": [],
                "user_permissions": []
            },
            "programming_language": {
                "id": 1,
                "name": "C#"
            },
            "expertise_level": {
                "id": 1,
                "level": "Easy"
            },
            "created_at": "2025-05-03T21:27:56.339034Z",
            "completed_at": "2025-05-03T21:42:32.136650Z",
            "score": 2,
            "total_questions": 10,
            "responses": [
                {
                    "id": 1,
                    "question_type": "coding",
                    "question_id": 55,
                    "user_response": "<your code string>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 2,
                    "question_type": "coding",
                    "question_id": 56,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 3,
                    "question_type": "coding",
                    "question_id": 57,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 4,
                    "question_type": "coding",
                    "question_id": 58,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 5,
                    "question_type": "coding",
                    "question_id": 59,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 6,
                    "question_type": "coding",
                    "question_id": 60,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 7,
                    "question_type": "coding",
                    "question_id": 61,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 8,
                    "question_type": "coding",
                    "question_id": 62,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 9,
                    "question_type": "theory",
                    "question_id": 39,
                    "user_response": "The `using` statement in C# is used to ensure that an object implementing the `IDisposable` interface is automatically disposed of when it's no longer needed. It helps in resource management by guaranteeing that the `Dispose()` method is called, releasing unmanaged resources like file handles, database connections, or network streams as soon as they go out of scope—either normally or due to an exception. This prevents resource leaks and promotes clean, efficient code without requiring manual cleanup in `try...finally` blocks.",
                    "is_correct": true,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 10,
                    "question_type": "theory",
                    "question_id": 40,
                    "user_response": "The using statement in C# ensures automatic disposal of objects that implement IDisposable, guaranteeing deterministic cleanup of unmanaged resources (e.g., file handles, database connections). It simplifies resource management by calling Dispose() implicitly when exiting the block, even during exceptions, avoiding leaks. Variables declared in a using block are scoped to it, preventing misuse afterward. Available as a concise statement (C# 8.0+) or traditional block syntax, it streamlines code while enforcing safe, efficient resource handling.",
                    "is_correct": true,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                }
            ]
        }
    ]
}
```
#### Get Assignment By User
- **Endpoint:** `GET /api/assignments/my/`
- **Description:** Get assignments of the current user.
- **Response**:
```json
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": {
                "id": 1,
                "last_login": "2025-05-03T21:53:08.836757Z",
                "is_superuser": true,
                "first_name": "admin",
                "last_name": "admin",
                "email": "admin@gmail.com",
                "is_staff": true,
                "is_active": true,
                "date_joined": "2025-04-10T20:47:32.619579Z",
                "is_verified": true,
                "groups": [],
                "user_permissions": []
            },
            "programming_language": {
                "id": 1,
                "name": "C#"
            },
            "expertise_level": {
                "id": 1,
                "level": "Easy"
            },
            "created_at": "2025-05-03T21:27:56.339034Z",
            "completed_at": "2025-05-03T21:42:32.136650Z",
            "score": 2,
            "total_questions": 10,
            "responses": [
                {
                    "id": 1,
                    "question_type": "coding",
                    "question_id": 55,
                    "user_response": "<your code string>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 2,
                    "question_type": "coding",
                    "question_id": 56,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 3,
                    "question_type": "coding",
                    "question_id": 57,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 4,
                    "question_type": "coding",
                    "question_id": 58,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 5,
                    "question_type": "coding",
                    "question_id": 59,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 6,
                    "question_type": "coding",
                    "question_id": 60,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 7,
                    "question_type": "coding",
                    "question_id": 61,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 8,
                    "question_type": "coding",
                    "question_id": 62,
                    "user_response": "<your theory answer text>",
                    "is_correct": false,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 9,
                    "question_type": "theory",
                    "question_id": 39,
                    "user_response": "The `using` statement in C# is used to ensure that an object implementing the `IDisposable` interface is automatically disposed of when it's no longer needed. It helps in resource management by guaranteeing that the `Dispose()` method is called, releasing unmanaged resources like file handles, database connections, or network streams as soon as they go out of scope—either normally or due to an exception. This prevents resource leaks and promotes clean, efficient code without requiring manual cleanup in `try...finally` blocks.",
                    "is_correct": true,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                },
                {
                    "id": 10,
                    "question_type": "theory",
                    "question_id": 40,
                    "user_response": "The using statement in C# ensures automatic disposal of objects that implement IDisposable, guaranteeing deterministic cleanup of unmanaged resources (e.g., file handles, database connections). It simplifies resource management by calling Dispose() implicitly when exiting the block, even during exceptions, avoiding leaks. Variables declared in a using block are scoped to it, preventing misuse afterward. Available as a concise statement (C# 8.0+) or traditional block syntax, it streamlines code while enforcing safe, efficient resource handling.",
                    "is_correct": true,
                    "created_at": "2025-05-03T21:42:32.132651Z"
                }
            ]
        }
    ]
}
```
#### Get Assignment by ID
- **Endpoint:** `GET /api/assignments/1/`
- **Description:** Get Assignment scores by ID.
- **Response**:
```json
{
    "id": 1,
    "user": {
        "id": 1,
        "last_login": "2025-05-03T21:53:08.836757Z",
        "is_superuser": true,
        "first_name": "admin",
        "last_name": "admin",
        "email": "admin@gmail.com",
        "is_staff": true,
        "is_active": true,
        "date_joined": "2025-04-10T20:47:32.619579Z",
        "is_verified": true,
        "groups": [],
        "user_permissions": []
    },
    "programming_language": {
        "id": 1,
        "name": "C#"
    },
    "expertise_level": {
        "id": 1,
        "level": "Easy"
    },
    "created_at": "2025-05-03T21:27:56.339034Z",
    "completed_at": "2025-05-03T21:42:32.136650Z",
    "score": 2,
    "total_questions": 10,
    "responses": [
        {
            "id": 1,
            "question_type": "coding",
            "question_id": 55,
            "user_response": "<your code string>",
            "is_correct": false,
            "created_at": "2025-05-03T21:42:32.132651Z"
        },
        {
            "id": 2,
            "question_type": "coding",
            "question_id": 56,
            "user_response": "<your theory answer text>",
            "is_correct": false,
            "created_at": "2025-05-03T21:42:32.132651Z"
        },
        {
            "id": 3,
            "question_type": "coding",
            "question_id": 57,
            "user_response": "<your theory answer text>",
            "is_correct": false,
            "created_at": "2025-05-03T21:42:32.132651Z"
        },
        {
            "id": 4,
            "question_type": "coding",
            "question_id": 58,
            "user_response": "<your theory answer text>",
            "is_correct": false,
            "created_at": "2025-05-03T21:42:32.132651Z"
        },
        {
            "id": 5,
            "question_type": "coding",
            "question_id": 59,
            "user_response": "<your theory answer text>",
            "is_correct": false,
            "created_at": "2025-05-03T21:42:32.132651Z"
        },
        {
            "id": 6,
            "question_type": "coding",
            "question_id": 60,
            "user_response": "<your theory answer text>",
            "is_correct": false,
            "created_at": "2025-05-03T21:42:32.132651Z"
        },
        {
            "id": 7,
            "question_type": "coding",
            "question_id": 61,
            "user_response": "<your theory answer text>",
            "is_correct": false,
            "created_at": "2025-05-03T21:42:32.132651Z"
        },
        {
            "id": 8,
            "question_type": "coding",
            "question_id": 62,
            "user_response": "<your theory answer text>",
            "is_correct": false,
            "created_at": "2025-05-03T21:42:32.132651Z"
        },
        {
            "id": 9,
            "question_type": "theory",
            "question_id": 39,
            "user_response": "The `using` statement in C# is used to ensure that an object implementing the `IDisposable` interface is automatically disposed of when it's no longer needed. It helps in resource management by guaranteeing that the `Dispose()` method is called, releasing unmanaged resources like file handles, database connections, or network streams as soon as they go out of scope—either normally or due to an exception. This prevents resource leaks and promotes clean, efficient code without requiring manual cleanup in `try...finally` blocks.",
            "is_correct": true,
            "created_at": "2025-05-03T21:42:32.132651Z"
        },
        {
            "id": 10,
            "question_type": "theory",
            "question_id": 40,
            "user_response": "The using statement in C# ensures automatic disposal of objects that implement IDisposable, guaranteeing deterministic cleanup of unmanaged resources (e.g., file handles, database connections). It simplifies resource management by calling Dispose() implicitly when exiting the block, even during exceptions, avoiding leaks. Variables declared in a using block are scoped to it, preventing misuse afterward. Available as a concise statement (C# 8.0+) or traditional block syntax, it streamlines code while enforcing safe, efficient resource handling.",
            "is_correct": true,
            "created_at": "2025-05-03T21:42:32.132651Z"
        }
    ]
}
```
#### Delete Expertise Level
- **Endpoint:** `DELETE /api/expertise-levels/{id}/`
- **Description:** Delete a specific expertise level by ID.

## 💻 Development

### Running in Debug Mode

Set `DEBUG=1` in your `.env` file and run:

```bash
python manage.py runserver
```

### Code Structure

- `interface/`: Main application
  - `models.py`: Database models
  - `views.py`: API view functions
  - `urls.py`: URL routing
  - `generation_utils.py`: Question generation utilities
  - `embeddings.py`: Vector embedding utilities
  - `management/commands/`: Custom management commands

- `project/`: Django project configuration
  - `settings.py`: Global settings
  - `urls.py`: Root URL configuration

## 🌐 Production Deployment

### Using Gunicorn

```bash
gunicorn project.wsgi -b 0.0.0.0:8000
```

### Docker Deployment

1. **Copy deployment files**
```bash
cp deploy/dev/* .
```

2. **Start containers with database**
```bash
docker-compose -f docker-compose-sql.yml up -d
```
   
Or without database if configured externally:
```bash
docker-compose -f docker-compose.yml up -d
```

3. **Stop containers**
```bash
docker-compose down
```

## 🧪 Testing

The project uses pytest for testing:

```bash
pytest
```

Test configuration is in `pytest.ini`. Environment variables for testing can be set in `.test.env`.

## 🔧 Troubleshooting & Common Issues

### OpenAI API Errors

If you encounter errors with OpenAI embeddings, check:
1. Your API key is valid and has sufficient credits
2. You're using the correct OpenAI library version
   - For v1.0.0+: Update `embeddings.py` to use the client-based approach
   - For older versions: Downgrade to v0.28 with `pip install openai==1.63.2`

### pgvector Format Issues

If you see errors like "invalid input syntax for type vector", ensure:
1. The embedding format uses square brackets `[...]` instead of curly braces `{...}`
2. The pgvector extension is properly installed in PostgreSQL

### Quiz Generation Issues

If quiz creation fails, check:
1. Sufficient questions exist for the selected language/level
2. The OpenAI API is responding correctly
3. Database connections are working

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Open a pull request

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🔗 Useful Links

- [Django Documentation](https://www.djangoproject.com/)
- [Django REST Framework Documentation](https://www.django-rest-framework.org/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [JWT Authentication](https://django-rest-framework-simplejwt.readthedocs.io/)
