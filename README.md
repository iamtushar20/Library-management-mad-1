# Setting Up Virtual Environment in VS Code

To work with a virtual environment in VS Code, follow these steps:

1. **Open the Folder in VS Code**
   - Open your project folder in Visual Studio Code.

2. **Create a Virtual Environment**
   - Open the terminal in VS Code.
   - Run the following command to create a virtual environment:
     ```bash
     python -m venv venv
     ```

3. **Activate the Virtual Environment**
   - For macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - For Windows PowerShell:
     ```powershell
     .\venv\Scripts\Activate
     ```

4. **Install Required Libraries**
   - Ensure you are in the activated virtual environment.
   - Install the required libraries from the `requirements.txt` file using pip:
     ```bash
     pip install -r requirements.txt
     ```

By following these steps, you'll have a virtual environment set up in VS Code with the necessary libraries installed.



# Project Setup and Execution

This guide provides step-by-step instructions to set up and run the project, which includes both frontend and backend components, as well as additional services such as MailHog, Redis, and Celery.

## Prerequisites

- [Windows Subsystem for Linux (WSL)](https://docs.microsoft.com/en-us/windows/wsl/install)
- [Node.js and npm](https://nodejs.org/)
- [Python 3](https://www.python.org/)
- [Redis](https://redis.io/)
- [MailHog](https://github.com/mailhog/MailHog)
- [Celery](https://docs.celeryproject.org/)

## Setup and Execution Steps

### 1. Activate Virtual Environment

1. Open WSL terminal.
2. Navigate to your project directory.
3. Activate the Python virtual environment:

    ```sh
    source venv/bin/activate
    ```

### 2. Start Frontend Development Server

1. In the same WSL terminal, navigate to the frontend directory:

    ```sh
    cd frontend
    ```

2. Run the frontend development server:

    ```sh
    npm run dev
    ```

### 3. Start Backend Server

1. Open a new WSL terminal.
2. Navigate to the backend directory:

    ```sh
    cd backend
    ```

3. Start the backend server:

    ```sh
    python3 app.py
    ```

### 4. Start MailHog

1. Open a new WSL terminal.
2. Navigate to the MailHog directory:

    ```sh
    cd $HOME/go/bin
    ```

3. Start MailHog:

    ```sh
    ./MailHog
    ```

### 5. Start Redis Server

1. Open a new WSL terminal.
2. Start the Redis server on the specified port:

    ```sh
    redis-server --port 6380
    ```

### 6. Start Celery Worker

1. Open a new WSL terminal.
2. Navigate to the backend directory:

    ```sh
    cd backend
    ```

3. Start the Celery worker:

    ```sh
    celery -A tasks.celery worker --loglevel="info"
    ```

### 7. Start Celery Beat

1. Open a new WSL terminal.
2. Navigate to the backend directory:

    ```sh
    cd backend
    ```

3. Start Celery beat:

    ```sh
    celery -A tasks.celery beat
    ```

## Summary

To summarize, you need to have multiple WSL terminals open for different services:

1. One for activating the virtual environment and running the frontend.
2. One for running the backend server.
3. One for MailHog.
4. One for the Redis server.
5. One for the Celery worker.
6. One for Celery beat.

By following these steps, you will have all the necessary components running for your project.
