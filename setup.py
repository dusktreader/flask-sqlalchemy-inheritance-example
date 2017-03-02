import ast
import glob

from setuptools import setup, find_packages


with open('.project_metadata.py') as meta_file:
    project_metadata = ast.literal_eval(meta_file.read())


setup(
    name=project_metadata['name'],
    version=project_metadata['release'],
    author=project_metadata['author'],
    author_email=project_metadata['author_email'],
    description=project_metadata['description'],

    dependency_links=[
        'https://github.com/mitsuhiko/flask-sqlalchemy/archive/9eff8b6597987c9ac4ae86d8672d5abf9f8e4312.zip#egg=Flask-SQLAlchemy-99.99',   # noqa
    ],
    install_requires=[
        'Flask',
        'inflection',
        'pprintpp',
        'psycopg2',
        'py-buzz',

        'Flask-SQLAlchemy==99.99',
    ],
    extras_require={
        'dev': [
            'flake8',
            'freezegun',
            'pep8-naming',
            'pytest',
            'pytest-catchlog',
            'pytest-flask',
        ],
    },
    include_package_data=True,
    packages=find_packages(),
    scripts=glob.glob('bin/*'),
)
