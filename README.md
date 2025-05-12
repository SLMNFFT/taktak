# taktak
taktk is a PDF Reader with Multilingual Audio Assistance

This is a web-based PDF reader application built with **Streamlit**, which allows users to upload PDFs and read the text aloud in different languages. The app supports multiple voice options for text-to-speech (TTS) synthesis using **pyttsx3** and also includes a language detection feature. Additionally, you can interact with the app through a Q&A section powered by **Ollama** for advanced question-answering functionality on the PDF content.

## Features

- **PDF Upload & Viewing**: Upload your PDF documents and view them directly in the app.
- **Text-to-Speech (TTS)**: Select different voices and adjust speech rate and volume to have the PDF text read aloud.
- **Language Detection**: Automatically detects the language of the text in the PDF and provides an option to choose the corresponding voice.
- **Q&A with PDF Content**: Ask questions about the content in the PDF using **Ollama** for question-answering functionality.
- **Multi-Page Selection**: Choose which pages of the PDF to read aloud or view the text from.

## Technologies Used

- **Streamlit**: Framework for building interactive web applications.
- **pyttsx3**: Text-to-Speech (TTS) engine for generating audio from text.
- **PyPDF2**: Extracts text content from PDF files.
- **LangDetect**: Detects the language of the PDF content.
- **Ollama**: Language model for question answering.
- **streamlit-pdf-viewer**: Displays the PDF directly within the Streamlit app.

## How to Run Locally

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/pdf-reader-with-audio-assistance.git
    cd pdf-reader-with-audio-assistance
    ```

2. Set up a virtual environment (optional but recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate   # For Windows use: venv\Scripts\activate
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the Streamlit app:

    ```bash
    streamlit run app.py
    ```

5. Open your browser and go to `http://localhost:8501` to see the app running.

## How to Deploy

You can deploy this app on **Streamlit Cloud** or **Heroku**.

### Deploy on Streamlit Cloud:

1. Create a new repository on **GitHub** and push the code to your repository.
2. Sign up/log in to **Streamlit Cloud** (https://streamlit.io/cloud).
3. Click "New app", choose your repository, and click "Deploy".

### Deploy on Heroku:

1. Install the **Heroku CLI**.
2. Push the code to a **GitHub repository** and link it to **Heroku**.
3. Create a `Procfile` with the following content:
    ```
    web: streamlit run app.py
    ```
4. Create a `runtime.txt` to specify the Python version (optional):
    ```
    python-3.9.10
    ```
5. Deploy the app on Heroku using the **Heroku Dashboard** or the **CLI**.

## Customization

- You can modify the `requirements.txt` file to add or update Python packages.
- To customize the voices, you can change the `pyttsx3` initialization parameters in the `app.py` file.
- You can also modify the `langdetect` function to improve language detection or add new languages.

## Limitations

- **Language Detection**: The app uses the `langdetect` library, which may not be 100% accurate for all languages.
- **PDF Parsing**: The text extraction is based on PyPDF2, which may not work well with scanned PDFs or images.
- **Ollama Q&A**: This feature requires an active **Ollama API** subscription.

## Contributing

Feel free to fork this repository and submit issues or pull requests for enhancements.

## License

This project is open-source and available under the [MIT License](LICENSE).

## Acknowledgments

- **Streamlit**: For making web app development simple and fast.
- **pyttsx3**: For providing the text-to-speech functionality.
- **PyPDF2**: For extracting text from PDF files.
- **LangDetect**: For language detection.
- **Ollama**: For providing the Q&A capabilities.

