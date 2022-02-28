***********************
LIDA Lifetimes Database
***********************

This is a Django web project for the LIDA database in development. This documentation
file is aimed solely at future developer of the project and it should compile some
useful information about the project, brief description of the project structure, the
data model, known issues with the project so far, and finally the plans for the future.

The documentation also expects a reasonable well knowledge of python and django.
Good python knowledge is essential, while regarding Django, the knowledge level required
is not really above the level of the official Django tutorial.


Getting started
===============

- Prepare a clean python virtual environment (the project has so far been developed and
  tested on Python 3.8)

- Clone the package: ``git clone git@github.com:ExoMol/lida-web.git``

- Install the dependencies: ``pip install -r requirements.txt``

- Create a new SQL database on your local system, I've been using MySQL, but other
  databases are possible (just the *local settings* file must be tweaked). This needs
  the database server to be running on your local system.

- Create the ``lida/lida/local_settings.py`` file with the local settings - these are
  all the local-development-only and sensitive settings, which should not be part
  of the version control system. This is what my own ``local_settings.py`` file looks
  like this:

  .. code-block:: python

    import sys

    # Quick-start development settings - unsuitable for production
    # See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

    # SECURITY WARNING: keep the secret key used in production secret!
    SECRET_KEY = 'some random string, this is only crucial for production server'

    # SECURITY WARNING: don't run with debug turned on in production!
    DEBUG = True

    # Database
    # https://docs.djangoproject.com/en/3.2/ref/settings/#databases
    # noinspection PyUnresolvedReferences
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',  # for MySQL option
            'NAME': 'lida',  # corresponds to the database running on local
            'USER': 'name',  # corresponds to the database running on local
            'PASSWORD': 'password',  # corresponds to the database running on local
            'HOST': 'localhost',
            'PORT': '3306',
        }
    }

    if 'test' in sys.argv:
        # I have experienced that sqlite backend was considerably faster when running
        # unit tests, to whenever `manage.py` is run with 'test' argument, backend
        # changes to sqlite
        DATABASES['default'] = {
            'ENGINE': 'django.db.backends.sqlite3',
            # 'NAME': str(Path(__file__).resolve().parent.parent / 'test_db.sqlite'),
        }

- Run the tests to see if all works: from within the top-level ``lida`` directory (and
  the virtual environment), run ``python manage.py test``

- Run the migrations to bring your local SQL database in sync with the LIDA data model:
  ``python manage.py migrate``

- See if the local development server can be started: ``python manage.py runserver``.
  If all is ok, there should be a functioning website running at ``localhost``, albeit
  without any data.

- I have already generated some portion of the LIDA data and populated them in my local
  copy. The data are way too big to be included in version control. The MySQL dump file
  will be shared outside this package and it can be loaded into the running MySQL
  database. If everything goes well, this should sync the data content of this project
  on the local system of any future developer with my last state of the project.


Project structure
=================

To be included.


Known issues
============

To be included.


Future work suggestions
=======================

To be included.
