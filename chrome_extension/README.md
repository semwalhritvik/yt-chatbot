# YouTube RAG Chatbot Chrome Extension

This extension allows you to chat with any YouTube video using RAG (Retrieval-Augmented Generation) directly in the Chrome Side Panel.

## Setup

1.  **Backend Setup**:
    *   Navigate to the project root.
    *   Install dependencies:
        ```bash
        pip install -r requirements.txt
        ```
    *   Start the Flask server:
        ```bash
        python app.py
        ```
    *   The server will run on `http://localhost:5000`.

2.  **Extension Installation**:
    *   Open Google Chrome and navigate to `chrome://extensions`.
    *   Enable **Developer mode** in the top right corner.
    *   Click **Load unpacked**.
    *   Select this `chrome_extension` folder.

## Usage

1.  Go to any YouTube video (e.g., `https://www.youtube.com/watch?v=...`).
2.  Click the **YouTube RAG Chatbot** extension icon in the toolbar.
3.  The **Side Panel** will open on the right side of the browser.
4.  Wait for it to connect (Status: Connected).
5.  Type your question and hit Enter.

## Troubleshooting

-   **Status: error**: Ensure `app.py` is running and you are on a valid YouTube video page.
-   **No Video ID**: Refresh the YouTube page or navigate to a video.
