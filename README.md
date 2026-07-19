
## Setup Instruction
1. **Clone the repository**

2. **Create a virtual environment**

    `python -m venv venv`

    `venv\Scripts\activate`

3. **Install dependencies**
    
    `pip install -r requirements.txt`

4. **Apply database migrations**
    
    Navigate inside the config folder (config/config): 
    `cd config`

    Then run the migrate command to generate the sqlite3 file: 
    `python manage.py migrate`

5. **Run the server**
    
    `python manage.py runserver`

    Open the application at
    http://127.0.0.1:8000/

6. **Test Insert data**
    
    go to http://127.0.0.1:8000/Test_Insert/

    This will insert 2 test user data. Navigate to 
    config/studybuddy_cms/pages/views.py
    to add/change test users (under test_insert function)

    |Username|Password|
    |--------|--------|
    |`Bruhdy`|`letmeinplease`|
    |`Donny`|`Passingword`|

7. **Login**
    
    go to http://127.0.0.1:8000/login/

    This will allow you to enter the login information
    to access the account and enter the main page.
    More pages will be added throughout the week.


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