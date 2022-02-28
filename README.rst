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
And I really strongly recommend diving into the code and getting through all of it
ensuring all is understood, before further development.


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
  like this (don't forget to update all relevant data):

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

Note
----

The project is very closely related to the ``exomol2lida`` code
(`here <https://github.com/ExoMol/exomol2lida>`_), ``exomol2lida`` provides the data
in the exact format that is expected by the ``lida-web`` project. Any developer of
``lida-web`` needs to be familiar with ``exomol2lida``.


Project structure
=================

The ``lida-web`` project follows a fairly standard django structure. The project
settings and the highest-level url mappings are located in the ``lida`` package.

Than we have two django apps: ``app_site`` and ``app_api``.

The ``app_site`` is pretty much everything to do with the website frontend, backend etc,
concerning browsing the data.

The ``app_api`` is at this moment not really present (apart from the skeleton) and is
designed to handle the data requesting API in the future. The *About API* page template
and view are also part of the ``app_api`` app.

Then there is the top-level template in the ``templates`` folder, which is used as a
base for all the templates defined in the apps, the ``static`` folder with static files
such as the favicon, logos, other images, etc, the page-level css file, and the
bootstrap and datatables libraries (css and javascript)

Finally there is the ``res`` folder, containing some top level scripts (more about those
further on).

Note on the *datatables* library
--------------------------------

The LIDA data are served in interactive data tables, supporting stuff such as filtering,
sorting, dynamic *as-scroll* data rendering, etc. This is a fairly well known javascript
and JQuery `library <https://datatables.net/>`_.
As the amount of data (states or transitions) per each molecule is very high, the
datatables must be run in the server-side mode, where the table itself does not tap
directly to the data, but rather user interaction with it creates ajax requests, which
are intercepted by the django backend and based on those, the data are requested from
the underlying database and served up back to the datatables, which then serve the data.

This happens any time user interacts with the table, so any scrolling, pagination
change, new filtering string, or any column sorting click. All these actions create
a request over a particular URL, which results in one of the
``app_site.views.views_ajax`` Django views to serve the correct data from the database
to the actual html view.

The data serving is handled by the
`django-datatables-serverside <https://github.com/hanicinecm/django-datatables-serverside>`_,
package (also ``pip`` installable), which has been
written by me purposefully for this project. Unfortunately, this package is not yet
at all documented, but hopefully I'll get back to it. If there are any questions, I'm
happy to provide guidance.

The ``app_site.urls`` and ``app_site.views`` are split between the html and ajax
views/urls, one defining endpoints for html and serving html content, the other
defining endpoints for ajax requests and serving ajax data to the datatables.net.


Data model
==========

The current data model of the web project can be seen on the following
*Django Model Dependency Diagram*:

.. image:: lida-web-diagram.png
  :width: 800

The highest-level unit of the data is the ``Molecule`` model, which roughly corresponds
to a molecule in ExoMol, each molecule having a unique ``formula_str``.
There is a 1-to-1 relationship between ``Molecule`` and ``Isotopologue``, where only a
single isotopologue is allowed per molecule (the most abundant one typically).
1-to-many relationship is implemented between ``Isotopologue`` and ``State`` models as
well as between ``State`` and ``Transition`` models.

There is a caveat on the ``formula_str`` attribute belonging to ``Molecule``: this is
not always the same formula as in ExoMol. As these need to be unique, there are cases
where the ExoMol molecule formula need to be changed: For example (not sure it exists
in ExoMol), if we want two isotopologues of H2 both in the LIDA database, we need to
call one H2, another one D2. The isotopologue formulas belonging to these two then will
have ExoMol-compatible formulas of (1H)2, and (2H)2. Similar situation is for HCN, where
the ExoMol dataset distinguishes between two different isomers on the *states* file
level, whereas in LIDA, we will have two ``Molecule`` instances: ``"HCN", "HNC"``.

It is evident that the database is horribly non-normalized, as there is effectively
redundant data all over the place. ``State.state_html`` is dependent on
``State.vib_state_html``, ``State.el_state_html``, and
``State.isotopologue.molecule.molecule_html``. Or we have ``State`` attributes like
``vib_state_str``, ``vib_state_html``, ``vib_state_html_notags``, ``vib_state_sort_key``
where all of those are basically derived from ``vib_state_str``. This data redundancy
is there for higher computational overhead. ``vib_state_str`` is a plane text
representation, *html* is what gets rendered, *html_notags* are there for filtering
and searching through datatables (which show html representations) and *sort keys* are
there for sorting the datatables columns - adding leading zeros to vibrational states.

This redundancy creates some potential for inconsistent data, as data fields related
to each other will always need to be changed in sync (if anything gets changes).
A high-level function is provided for syncing all the fields for all the models,
discussed further on.

Apart from the various model fields, the model classes also implement each some methods
such as ``get_from_*`` and ``create_from_*``, which should *always* be used for
accessing and creating new data instances, as these make sure that no duplicates are
created etc.

The best way towards understanding the data model is to dive into the
``app_site.models`` package and read the docstrings.


Top-level scripts
=================

There are two top-level scripts provided so far, located in the ``res`` directory.

The ``populate_molecule`` script defines a function to populate a single-molecule data
from the exact format created by the ``exomol2lida`` package (related but completely
stand-alone repository). The populating function needs to be imported
*from within the Django shell* (``python manage.py shell``) and run from there also.

The ``sync_inconsistent_db`` should be run if any changes are made to some of the
existing model instances data fields and the database is inconsistent as a result.
For example, if the html of a ``Molecule`` instance is changed, the html of the
attached ``State`` instances need to be all changed as well. That can be done (for
the whole database thought) by running the ``sync_inconsistent_db``
*from within the django shell*.


Known existing issues
=====================

- A lot of the intended functionality is missing (read the following section).

- The *scrolling* datatables show a cosmetic issue: when scrolled all the way to the
  end of e.g. *States of CN* or any other states or transitions datatable, there is
  an ugly empty space at the end which should not be there. I suspect that datatables
  for some reason wrongly calculate the thickness of each row, or something like this.
  Some experimenting with the tables styles in the ``main.css`` sheet might be in order.

- Only 24/27 so-far-processed molecules were populated so far by ``populate_molecule``
  script (from ``exomol2lida`` outputs, these will be shared). There were problems with
  couple of molecules with running the population script:

  - HCN: The problem is that HNC already exists in the database (was previously
    populated) and the HCN has the same isotopologue formula, as HNC, which is not
    allowed. The best action is to implement some mapping between the input isotopologue
    formula, as read from ExoMol (which is saved in the ``exomol2lida`` outputs) and the
    one which should be used by the website (which should have the correct element
    order). This should be an easy fix.

  - H3: I'm not really sure what is happening there, I have a feeling that one of the
    states has undefined energy and the NaN energy cannot be saved into the SQL.
    Not sure how best to solve it, if on the ``lida-web`` level or on the
    ``exomol2lida`` when building inputs for ``lida-web``.

  - VO: Another tricky one, the .states file in exomol for this dataset was a bit of
    a mess where there were many electronic states identified by different strings,
    which were actually the same state. Problem is caused by this. Either a cleaner
    .states file is needed, or mapping to correct state strings needs to be done in
    ``exomol2lida`` *before* the states lumping is done in there.

- The data population (using the ``populate_molecule`` functionality) is really slow.
  Slower than data generation at the moment. Some optimization might be in order,
  especially moving towards to large, more challenging molecules, where the lida data
  do not yet exist.


Future work suggestions
=======================

- Add more molecules into the database. So far only 24 molecules were added to my local
  database, because I only have data for 24 molecules generated by the ``exomol2lida``
  project. It has to be said that these were the *low hanging fruits* and the rest of
  the data will be more challenging, as the ``exomol2lida`` might need to be optimized
  somewhat to generate the data in a finite time.

- The *About Lida* and *Contact* pages need to be implemented. The *About* page should
  contain all the math used to generate the data from the ExoMol line lists, together
  with the usual, motivation etc.

- There should be some filtering functionality implemented. In almost no circumstances
  will any plasma model be interested in hundreds of states and thousands of
  transitions. There needs to be a way to limit the number of data to show (and
  ultimately to return over API). Question is how to limit: Thresholding energy,
  lifetime, or other for the states? Thresholding partial lifetimes for the energies?
  Some sort of smarter clumping, clustering or similar? All of these will require the
  ability to re-normalize the partial lifetimes to always add up to the total lifetimes.
  Another question is how to implement this in the front end UI. Another field by the
  datatables? Or a global setting somewhere applying the same reduction of states and
  transitions all across the page?

- The public API needs to be implemented. My initial idea is that if user requests data
  from url such as ``www.{lida-domain.com}/api/molecule/{molecule-slug}`` or similar,
  a json file is returned with the appropriate data - this would be all the states with
  data, all the transitions with data... This is not an easy problem to solve to keep
  the files reasonable size. Also all the molecules could be requested, or maybe
  only transitions to/from a single state (but currently we do not have a *state slug*
  which would be unique to a state and usable inside the url as a human-readable
  state representation, state ids are used in the transitions html views)

- The public API *about* page needs to be there documenting the API usage.

- The API needs to also support the same data filtering/reduction/clumping as discussed
  a couple points higher. This can be controlled via URL itself or with arguments to
  the url.

- And finally, of course, the project needs to be deployed on a live server. I have
  absolutely no clue what entails, so I have no tips here...