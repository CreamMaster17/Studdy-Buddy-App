
## Setup Instruction
1. **Clone this repository/branch**

    Make sure you are using the latest version of Python: `Python 3.14.6`. Check using `python --version`
   
    <br>
    
3. **Create a virtual environment**


   In VSCode `ctrl+shift+p -> python: select interpreter -> Create Virtual Environment`
   
    <br>
   
   alternatively, run the following in a terminal to manually set up the virtual environment:

   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` | Allows scripts to run

    `python -m venv venv` | Creates Virtual Environment named venv

    `venv\Scripts\activate` | Activates the Virtual Environment

   <br>

5. **Install dependencies**
    
    `pip install -r requirements.txt`
   
    <br>
    
6. **Apply database migrations**
    
    Navigate inside the config folder (config/config): 
    `cd config`

    Then run the migrate command to generate the sqlite3 file: 
    `python manage.py migrate`
   
    <br>
    
7. **Run the server**
    
    `python manage.py runserver`

    Open the application at
    http://127.0.0.1:8000/

    Nothing should show or you should get an error as this is the root and there isn't anything set up for it
   
    <br>
    
8. **Test Insert data**
    
    Go to http://127.0.0.1:8000/Test_Insert/

    This will insert 2 test user data. Navigate to 
    config/studybuddy_cms/pages/views.py
    to add/change test users (under test_insert function)

    |Username|Password|
    |--------|--------|
    |`Bruhdy`|`letmeinplease`|
    |`Donny`|`Passingword`|
   
    <br>
    
9. **Login**
    
    Go to http://127.0.0.1:8000/login/

    This will allow you to enter the login information
    to access the account and enter the main page.
    More pages will be added throughout the week.
   
    <br>
    
<hr>

## Project Structure
```
└── 📁config
    └── 📁config
        ├── __init__.py
        ├── asgi.py
        ├── settings.py
        ├── urls.py
        ├── wsgi.py
    └── 📁static
        └── 📁css
            ├── home.css
            ├── registration.css
        └── 📁js
            ├── home.js
    └── 📁studybuddy_cms
        └── 📁management
            └── 📁commands
                ├── __init__.py
                ├── check_due_assessments.py
            ├── __init__.py
        └── 📁migrations
            ├── __init__.py
            ├── 0001_initial.py
        └── 📁pages
            ├── urls.py
            ├── views.py
        └── 📁services
            ├── __init__.py
            ├── assessment_services.py
            ├── geminiservice.py
        └── 📁templates
            ├── home.html
            ├── login.html
            ├── registration.html
            ├── Test_Insert.html
        ├── __init__.py
        ├── admin.py
        ├── apps.py
        ├── models.py
        ├── serializers.py
        ├── SETTINGS_SNIPPET.py
        ├── urls.py
        ├── views.py
    └── 📁studybuddy_quiz
        └── 📁Test Quizes
            ├── test_quizes.py
        ├── db_schema_quiz.sql
        ├── quiz_generator.py
        ├── quiz_history.py
        ├── study_recommendations.py
        ├── study_stats.py
    └── manage.py
└── requirements.txt
```
