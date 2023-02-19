from setuptools import setup, find_packages

setup(
    name='mew_pl',
    version='0.0.2',
    install_requires=[
        'colorama'
    ],
    include=['ply', 'targets'],
    entry_points = {
        'console_scripts': [
            'mew = mew_pl.__main__:main'
        ]
    },
    packages=find_packages(),
    py_modules=[]
)
