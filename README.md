
## Setup Instruction
1. **Clone this repository/branch**

    Make sure you are using the latest version of Python: `Python 3.14.6`. Check using `python --version`
   
    <br>
    
2. **Create a virtual environment (OPTIONAL)**


   In VSCode `ctrl+shift+p -> python: select interpreter -> Create Virtual Environment`
   
    <br>
   
   alternatively, run the following in a terminal to manually set up the virtual environment:

    `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` | Allows scripts to run

    `python -m venv venv` | Creates Virtual Environment named venv

    `venv\Scripts\activate` | Activates the Virtual Environment

   <br>

3. **Install dependencies**
    
    `pip install -r requirements.txt`
   
    <br>
    
4. **Server Setup**

    Create a file on the same level as this `README.md` titled `.env`
    
    Now the following steps are inside your terminal to generate a Django Secret Key:
    1. Navigate inside the config folder (config/config): `cd config`
    2. Start the Django Shell: `python manage.py shell`
    3. Run the following commands: `from django.core.management.utils import get_random_secret_key` `print(get_random_secret_key())`
    4. Copy the output key into you .env file like so: `SECRET_KEY = REPLACE_THIS_WITH_YOUR_KEY`
    5. in the terminal, type `quit()` to end the Django Shell.

    Now the following steps are to generate you Google Gemini API Key:
    1. Visit https://aistudio.google.com/
    2. If you are not logged in, click "Get Started" in the top right and log in with your Google Account
    3. In the bottom-left corner, click the key symbol
    4. Click the blue text underneat "Key" and click "Copy key"
    5. paste the key in your .env file like so: `GEMINI_API_KEY = REPLACE_THIS_WITH_YOUR_KEY`

    Finally, save the .env file.

    Then run the migrate command to generate the sqlite3 file: 
    `python manage.py migrate`
   
    <br>
    
5. **Run the server**
    
    `python manage.py runserver`

    Open the application at
    http://127.0.0.1:8000/

   
    <br>
    
6. **Test Insert data (OPTIONAL)**
    
    Go to http://127.0.0.1:8000/Test_Insert/

    This will insert 2 test user data. Navigate to 
    config/studybuddy_cms/pages/views.py
    to add/change test users (under test_insert function)

    |Username|Email|Password|
    |--------|--------|--------|
    |`Bruhdy`|`Bruhdy@email.com`|`letmeinplease`|
    |`Donny`|`Donny@email.com`|`Passingword`|
   
    <br>
     
<hr>

## Project Structure
```
└── 📁config
    └── 📁apps
        └── 📁accounts
            └── 📁migrations
                ├── __init__.py
                ├── 0001_initial.py
                ├── 0002_alter_user_email.py
            └── 📁templates
                ├── login.html
                ├── registration.html
                ├── Test_Insert.html
                ├── user-settings.html
            ├── __init__.py
            ├── apps.py
            ├── backends.py
            ├── forms.py
            ├── models.py
            ├── signals.py
            ├── tests.py
            ├── urls.py
            ├── views.py
        └── 📁studybuddy_cms
            └── 📁management
                └── 📁commands
                    ├── __init__.py
                    ├── check_due_assessments.py
                ├── __init__.py
            └── 📁migrations
                ├── __init__.py
                ├── 0001_initial.py
                ├── 0002_alter_note_options_note_content_item_note_pinned_and_more.py
                ├── 0003_savedflashcards_savedquiz_savedsummary.py
                ├── 0004_savedquiz_subject.py
                ├── 0005_rename_title_savedflashcards_flashcard_title_and_more.py
            └── 📁services
                ├── __init__.py
                ├── assessment_services.py
                ├── gemini_service.py
            └── 📁templates
                ├── home.html
                ├── main.html
                ├── my-study.html
            ├── __init__.py
            ├── admin.py
            ├── apps.py
            ├── models.py
            ├── serializers.py
            ├── SETTINGS_SNIPPET.py
            ├── tests.py
            ├── urls.py
            ├── views.py
        └── 📁studybuddy_quiz
            └── 📁migrations
                ├── __init__.py
                ├── 0001_initial.py
                ├── 0002_remove_generatedquiz_studybuddy__user_id_a0c9dd_idx_and_more.py
                ├── 0003_remove_quizresult_studybuddy__owner_i_5279b9_idx_and_more.py
            └── 📁templates
                ├── quiz-history.html
                ├── quiz-results.html
                ├── quiz.html
            └── 📁Test Quizes
                ├── test_quizes.py
            ├── admin.py
            ├── apps.py
            ├── db_schema_quiz.sql
            ├── models.py
            ├── quiz_generator.py
            ├── quiz_history.py
            ├── study_recommendations.py
            ├── study_stats.py
            ├── tests.py
            ├── urls.py
            ├── views.py
        ├── __init__.py
    └── 📁config
        ├── __init__.py
        ├── asgi.py
        ├── settings.py
        ├── urls.py
        ├── wsgi.py
    └── 📁media
        └── 📁profile_pictures
            ├── .gitignore
    └── 📁static
        └── 📁css
            ├── home.css
            ├── main.css
            ├── my-study.css
            ├── quiz-history.css
            ├── quiz.css
            ├── registration.css
            ├── user-settings.css
        └── 📁images
            ├── EmptyProfilePic.jpg
            ├── SB_logo.png
        └── 📁js
            ├── home.js
            ├── my-study.js
            ├── quiz.js
    └── manage.py
```
