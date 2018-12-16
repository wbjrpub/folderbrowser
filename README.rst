Python Package Skeleton
=======================

|PyPI| |Codecov| |CircleCI|

.. |PyPI| image:: https://img.shields.io/pypi/v/makenew-pypackage.svg
   :target: https://pypi.python.org/pypi/makenew-pypackage
   :alt: PyPI
.. |Codecov| image:: https://img.shields.io/codecov/c/github/makenew/pypackage.svg
   :target: https://codecov.io/gh/makenew/pypackage
   :alt: Codecov
.. |CircleCI| image:: https://img.shields.io/circleci/project/github/makenew/pypackage.svg
   :target: https://circleci.com/gh/makenew/pypackage
   :alt: CircleCI

Package skeleton for an Python module.

Description
-----------

Bootstrap a new Python_ package in less than a minute.

.. _Python: https://www.python.org/

Features
~~~~~~~~

- Package management with setuptools_ and publishing to PyPI_.
- Secure dependency management with Pipenv_.
- Linting with Pylint_.
- pytest_ helps you write better programs.
- Code coverage reporting with Codecov_.
- CircleCI_ ready.
- `Keep a CHANGELOG`_.
- Consistent coding with EditorConfig_.
- Badges from Shields.io_.

.. _CircleCI: https://circleci.com/
.. _Codecov: https://codecov.io/
.. _EditorConfig: http://editorconfig.org/
.. _Keep a CHANGELOG: http://keepachangelog.com/
.. _Pipenv: https://pipenv.readthedocs.io/
.. _PyPI: https://pypi.python.org/pypi
.. _Pylint: https://www.pylint.org/
.. _Shields.io: http://shields.io/
.. _pytest: https://docs.pytest.org/
.. _setuptools: https://pythonhosted.org/setuptools/.

Bootstrapping a New Project
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create an empty (**non-initialized**) repository on GitHub.
2. Clone the master branch of this repository with

   ::

       $ git clone --single-branch https://github.com/makenew/pypackage.git new-pypackage
       $ cd new-pypackage

   Optionally, reset to the latest
   `release <https://github.com/makenew/pypackage/releases>`__ with

   ::

       $ git reset --hard v1.2.0

3. Run

   ::

       $ ./makenew.sh

   This will replace the boilerplate, delete itself,
   remove the git remote, remove upstream tags,
   and stage changes for commit.

4. Create the required CircleCI environment variables with

   ::

       $ .circleci/envvars.sh

5. Review, commit, and push the changes to GitHub with

   ::

     $ git diff --cached
     $ git commit -m "Replace makenew boilerplate"
     $ git remote add origin git@github.com:<user>/<new-python-package>.git
     $ git push -u origin master

6. Ensure the CircleCI build passes,
   then publish the initial version of the package with

   ::

     $ pipenv install --dev
     $ pipenv run bumpversion patch
     $ git push
     $ git push --tags

Updating
~~~~~~~~

If you want to pull in future updates from this skeleton,
you can fetch and merge in changes from this repository.

Add this as a new remote with

::

    $ git remote rename origin upstream

and then configure your ``origin`` branch as normal.

Otherwise, add this as a new remote with

::

    $ git remote add upstream git@github.com:makenew/pypackage.git

You can then fetch and merge changes with

::

    $ git fetch --no-tags upstream
    $ git merge upstream/master

Changelog
^^^^^^^^^

Note that ``CHANGELOG.md`` is just a template for this skeleton. The
actual changes for this project are documented in the commit history and
summarized under
`Releases <https://github.com/makenew/pypackage/releases>`__.

Installation
------------

This package is registered on the `Python Package Index (PyPI)`_
as makenew_pypackage_.

Install it with

::

    $ pipenv install makenew_pypackage

If you are writing a Python package which will depend on this,
add this to your requirements in ``setup.py``.

.. _makenew_pypackage: https://pypi.python.org/pypi/makenew-pypackage
.. _Python Package Index (PyPI): https://pypi.python.org/

Development and Testing
-----------------------

Quickstart
~~~~~~~~~~

::

    $ git clone https://github.com/makenew/pypackage.git
    $ cd pypackage
    $ pipenv install --dev

Run each command below in a separate terminal window:

::

    $ make watch

Primary development tasks are defined in the `Makefile`.

Source Code
~~~~~~~~~~~

The `source code_` is hosted on GitHub.
Clone the project with

::

    $ git clone https://github.com/makenew/pypackage.git

.. _source_code: https://github.com/makenew/pypackage

Requirements
~~~~~~~~~~~~

You will need `Python 3`_ with Pipenv_.

Install the development dependencies with

::

    $ pipenv install --dev

.. _Pipenv: https://pipenv.readthedocs.io/
.. _Python 3: https://www.python.org/

Tests
~~~~~

Lint code with

::

    $ make lint


Run tests with

::

    $ make test

Run tests on chages with

::

    $ make watch

Publishing
~~~~~~~~~~

Use the bumpversion_ command to release a new version.
Push the created git tag which will trigger a CircleCI publish job.

... _bumpversion: https://github.com/peritus/bumpversion

CircleCI
--------

*CircleCI should already be configured: this section is for reference only.*

The following environment variables must be set on CircleCI_:

- ``TWINE_USERNAME``: Username for publishing on PyPI.
- ``TWINE_PASSWORD``: Password for publishing on PyPI.
- ``CODECOV_TOKEN``: Codecov token for uploading coverage reports (optional).

These may be set manually or by running the script ``./circleci/envvars.sh``.

.. _CircleCI: https://circleci.com/

Contributing
------------

Please submit and comment on bug reports and feature requests.

To submit a patch:

1. Fork it (https://github.com/makenew/pypackage/fork).
2. Create your feature branch (`git checkout -b my-new-feature`).
3. Make changes.
4. Commit your changes (`git commit -am 'Add some feature'`).
5. Push to the branch (`git push origin my-new-feature`).
6. Create a new Pull Request.

License
-------

This Python package is licensed under the MIT license.

Warranty
--------

This software is provided by the copyright holders and contributors "as is" and
any express or implied warranties, including, but not limited to, the implied
warranties of merchantability and fitness for a particular purpose are
disclaimed. In no event shall the copyright holder or contributors be liable for
any direct, indirect, incidental, special, exemplary, or consequential damages
(including, but not limited to, procurement of substitute goods or services;
loss of use, data, or profits; or business interruption) however caused and on
any theory of liability, whether in contract, strict liability, or tort
(including negligence or otherwise) arising in any way out of the use of this
software, even if advised of the possibility of such damage.