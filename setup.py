from setuptools import setup, find_packages

setup(
    name='mdcrawler',
    version='0.0.1',
    description='read MSON (JSON in Markdown) out of MarkDown files and saves as JSON',
    license='MIT',
    packages=[".","contrib"],
    author='Steffen Köhler',
    author_email='steffen@koehlers.de',
    keywords=['markdown','json','mistletoe'],
    url='https://github.com/stko/markdown_crawler'
)