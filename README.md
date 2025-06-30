# MedSutra Backend

This repository contains the backend services for the MedSutra application, built with FastAPI and leveraging AI for intelligent processing of health reports.

## Getting Started

Follow these steps to set up and run the backend locally.

### Prerequisites

* Python 3.9+
* `pip` (Python package installer)

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  **Create a virtual environment:**
    It's highly recommended to use a virtual environment to manage project dependencies.
    ```bash
    python -m venv env
    ```

3.  **Activate the virtual environment:**
    * **On macOS/Linux:**
        ```bash
        source env/bin/activate
        ```
    * **On Windows:**
        ```bash
        .\env\Scripts\activate
        ```

4.  **Install dependencies:**
    Once your virtual environment is active, install all required packages using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Start the FastAPI server:**
    Ensure your virtual environment is activated. Then, run the application using `uvicorn`:
    ```bash
    uvicorn app.main:app --reload
    ```
    The `--reload` flag enables auto-reloading of the server on code changes, which is useful for development.

2.  **Access API Documentation:**
    Once the server is running, you can access the interactive API documentation (Swagger UI) in your web browser:
    ```
    http://localhost:8000/docs
    ```
    This interface allows you to explore available endpoints, test them, and understand the request/response schemas.
