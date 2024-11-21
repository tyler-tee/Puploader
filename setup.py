from setuptools import setup
from os import path

currrent_direct = path.abspath(path.dirname(__file__))
with open(path.join(currrent_direct, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Puploader',
    version='0.1.0',
    packages=['Puploader'],
    url='https://github.com/tyler-tee/puploader',
    license='MIT',
    author='Tyler Talaga',
    author_email='ttalaga@wgu.edu',
    description='Simple Flask app built to receive, store, and serve dog photos.',
    long_description=long_description,
    long_description_content_type='text/markdown'
)
