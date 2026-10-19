@echo off
cd /d "%~dp0"

echo === SmartHire GenAI launcher ===

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Could not create the virtual environment. Is Python installed and on PATH?
        pause
        exit /b 1
    )
)

call venv\Scripts\activate.bat

echo Installing dependencies - first run takes a minute or two...
pip install -q -r requirements.txt
if errorlevel 1 (
    echo Dependency install failed. Check your internet connection and try again.
    pause
    exit /b 1
)

if not exist .env copy .env.example .env >nul

rem --- API key: reuse a saved one, otherwise ask once and remember it ---
findstr /c:"your_actual_key_here" .env >nul
if errorlevel 1 goto :keyok
if defined GEMINI_API_KEY goto :keyok

echo.
echo No API key found yet. Paste your Gemini API key and press Enter.
echo You only need to do this once - it is saved for all future runs.
set /p KEY=API key: 
if "%KEY%"=="" (
    echo No key entered.
    pause
    exit /b 1
)
> .env echo GEMINI_API_KEY=%KEY%
>> .env echo GEMINI_MODEL=gemini-3.8-flash
>> .env echo EMBEDDING_MODEL=gemini-embedding-001
setx GEMINI_API_KEY "%KEY%" >nul
set "GEMINI_API_KEY=%KEY%"
echo Key saved.

:keyok

if not exist vectorstore\jobs.faiss (
    echo Building job index...
    python -m src.search.job_search data\jobs\sample_jobs.csv
    if errorlevel 1 goto :failed
)

if not exist vectorstore\career_notes_faiss (
    echo Building career-notes index...
    python -m src.mentor.rag_chain build
    if errorlevel 1 goto :failed
)

echo Starting SmartHire GenAI - your browser will open shortly...
streamlit run app\streamlit_app.py
goto :end

:failed
echo.
echo Something failed while building an index. Check that your API key is correct.
echo If you saw a 503 error, Gemini was overloaded - just run this file again.

:end
pause
