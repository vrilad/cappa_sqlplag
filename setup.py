from setuptools import setup, find_packages

try:
   import pypandoc
   long_description = pypandoc.convert_file('README.md', 'rst')
   long_description = long_description.replace("\r","")  
except(IOError, ImportError):
    long_description = open('README.md').read()

setup(
    name='cappa_sqlplag',
    version='0.2.1',
    description='SQL-детектор плагиата, предназначенный для использования в комплексе автоматической проверки программ CAPPA',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='vrilad',
    url='https://github.com/vrilad/cappa_sqlplag',
    download_url='https://github.com/vrilad/cappa_sqlplag/releases',
    keywords=['cappa', 'sql', 'plagiarism'],
    packages=find_packages(),
)