from setuptools import setup, find_packages

try:
   import pypandoc
   long_description = pypandoc.convert_file('README.md', 'rst')
   long_description = long_description.replace("\r","")  
except(IOError, ImportError):
    with open('README.md', 'r', encoding='utf-8') as f:
        long_description = f.read()

setup(
    name='cappa_sqlplag',
    version='1.1.0',
    description='SQL-детектор плагиата, предназначенный для использования в комплексе автоматической проверки программ CAPPA',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='vrilad',
    url='https://github.com/vrilad/cappa_sqlplag',
    download_url='https://github.com/vrilad/cappa_sqlplag/releases',
    keywords=['cappa', 'sql', 'plagiarism'],
    packages=find_packages(),
)