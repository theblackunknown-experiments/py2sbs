
setlocal

call py -m twine upload --verbose^
 -r testpypi^
 %~dp0\dist\*^
 %*

