@ECHO OFF

SET CLR_RED=[31m
SET CLR_GRN=[32m
SET CLR_CYN=[36m
SET CLR_NIL=[0m

:main

ECHO %CLR_CYN%Heading to the venv directory...%CLR_NIL%
cd ../venv/Scripts || GOTO :error

ECHO %CLR_CYN%Activating venv...%CLR_NIL%
call activate || GOTO :error

ECHO %CLR_CYN%Heading back to the repo root...%CLR_NIL%
cd ../.. || GOTO :error

ECHO %CLR_CYN%Updating the current code to the latest version (1/3)...%CLR_NIL%
git reset --hard origin || GOTO :error

ECHO %CLR_CYN%Updating the current code to the latest version (2/3)...%CLR_NIL%
git pull || GOTO :error

ECHO %CLR_CYN%Updating the current code to the latest version (3/3)...%CLR_NIL%
git reset --hard origin || GOTO :error

ECHO %CLR_CYN%Installing/Upgrading the requirements...%CLR_NIL%
pip install -r requirements.txt --upgrade || GOTO :error

ECHO %CLR_GRN%Done deploying.%CLR_NIL%
PAUSE

GOTO end

:error

ECHO %CLR_RED%Error occurred during deployment.%CLR_NIL%
PAUSE

:end
