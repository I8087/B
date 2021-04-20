@echo off
rem Don't echo each command.

rem Set the title of the prompt to batch file's name.
title build-test.cmd

rem Build each b test program.
for %%i in (test*.b) do py -3 ../src/__main__.py -f win32 -S -o %%~ni.exe %%i

rem Test each b test program.
for %%i in (test*.exe) do (
    echo %%i - START
    call %%i
    echo %%i - END - %errorlevel%
    del %%i
)

rem Pause so the build information and each program's error code can be viewed.
pause
