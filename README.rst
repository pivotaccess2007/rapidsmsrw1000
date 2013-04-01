
Rapidsmsrw1000
========================

Below you will find basic setup instructions for the rapidsmsrw1000
project. To begin you should have the following applications installed on your
local development system:

- Python >= 2.6 (2.7 recommended)
- `pip >= 1.1 <http://www.pip-installer.org/>`_
- `virtualenv >= 1.8 <http://www.virtualenv.org/>`_
- MySQL >= 5.1
- git >= 1.7

For Ubuntu:

    sudo apt-get install python-dev

Getting Started
---------------

To setup your local environment you should create a virtualenv and install the
necessary requirements::

    virtualenv --distribute rapidsmsrw1000-env
    source rapidsmsrw1000-env/bin/activate
    cd rapidsmsrw1000
    pip install -r requirements/base.txt

Update your settings file::

    cp local.py.example settings.py

Configure settings as needed for your local environment.

Create the MySQL database and run the initial syncdb/migrate::

    mysql -u root -p
    mysql> CREATE DATABASE rapidsmsrw1000;
    mysql> CREATE USER rapidsmsrw1000 identified by '123456';
    mysql> GRANT ALL ON rapidsmsrw1000.* TO 'rapidsmsrw1000'@'%';
    mysql> GRANT ALL ON test_rapidsmsrw1000.* TO 'rapidsmsrw1000'@'%';
    mysql> FLUSH privileges;
    mysql> quit
    python manage.py syncdb

You should now be able to run the development server::

    python manage.py runserver
