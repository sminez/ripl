from setuptools import setup, find_packages
import os

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='ripl',
    version="0.1.1",
    description="A LISP that runs on the python VM",
    url="https://github.com/sminez/ripl",
    author="Innes Anderson-Morrison",
    author_email='innes.morrison@cocoon.life',
    install_requires=[
        'pygments==2.1.3',
        'prompt_toolkit==1.0.0',
        'nose>=1.3.7',
        'coverage==4.0.1',
        'pyperclip==1.5.27',
    ],
    packages=find_packages(),
    package_dir={'ripl': 'ripl'},
    zip_safe=False,
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 4 - Beta'
    ],
    entry_points={
        'console_scripts': [
            'ripl = ripl.cli:main',
        ]
    },
)
