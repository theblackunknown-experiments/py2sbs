
setlocal

rmdir /S /Q build

call py setup.py^
 egg_info --tag-build=DEV --tag-date^
 rotate --match=*.whl --keep 2^
 bdist_wheel
