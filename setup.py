from setuptools import setup, find_packages


setup(
    name='task_progress',
    packages=find_packages('src'),
    version='1.1.1',
    license='MIT',
    description = 'A simple API for progress information of tasks and Handlers to display them (with progress bars)',
    author="Julien Braine",
    author_email='julienbraine@yahoo.fr',
    url='https://github.com/JulienBrn/TaskProgressDisplay',
    download_url = 'https://github.com/JulienBrn/TaskProgressDisplay.git',
    package_dir={'': 'src'},
    keywords=['python',  'progress', 'task'],
    install_requires=['enlighten'],
)