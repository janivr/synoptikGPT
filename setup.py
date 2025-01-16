from setuptools import setup, find_packages

setup(
    name='synoptik-gpt',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'streamlit',
        'pandas',
        'openai',
        'python-dotenv'
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'mypy',
            'black',
            'flake8'
        ]
    },
    author=' Janiv Ratson',
    description='Real Estate Portfolio Management Assistant',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)