STEM Learning Management System


Running the app:
1. CD to projects directory where the manage.py lives.
2. Here is the creation script for the virtual environment:
 python -m venv venv 
3. Activation Script:
venv\Scripts\activate or use venv\Scripts\activate.ps1 [just google my syntax its requiredinitially]

4. pip install django (use this to install django)
5. create a superuser: python manage.py createsuperuser (it will ask or email and username and password remember it, but don't stress you can create others.)
4. Use the command: Python manage.py makemigrations (this creates the tables)
5. pip install -r requirements.txt (to install all dependencies)
6. python manage.py runserver 8000 (to run on port 8000)

7. It should run now.

