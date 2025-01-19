@echo off
echo -------------------------------
echo Checking Git Status...
echo -------------------------------
git status
echo.

:confirm_stage
set /p user_input_stage=Do you want to stage all changes? (yes/no): 
if /i "%user_input_stage%"=="yes" (
    echo -------------------------------
    echo Staging All Changes...
    echo -------------------------------
    git add .
) else if /i "%user_input_stage%"=="no" (
    echo Exiting process.
    exit /b
) else (
    echo Invalid input. Please enter 'yes' or 'no'.
    goto confirm_stage
)

echo.

:confirm_commit
set /p user_input_commit=Do you want to commit the changes? (yes/no): 
if /i "%user_input_commit%"=="yes" (
    echo -------------------------------
    echo Committing Changes...
    echo -------------------------------
    git commit -m "Updated SQL query generation to align with PostgreSQL syntax and improved context handling"
) else if /i "%user_input_commit%"=="no" (
    echo Exiting process.
    exit /b
) else (
    echo Invalid input. Please enter 'yes' or 'no'.
    goto confirm_commit
)

echo.
echo Please enter your commit message:
set /p COMMIT_MSG=
git commit -m "%COMMIT_MSG%"

echo.

:confirm_push
set /p user_input_push=Do you want to push the changes to the remote repository? (yes/no): 
if /i "%user_input_push%"=="yes" (
    echo -------------------------------
    echo Pushing Changes to Remote...
    echo -------------------------------
    git push origin main
) else if /i "%user_input_push%"=="no" (
    echo Exiting process.
    exit /b
) else (
    echo Invalid input. Please enter 'yes' or 'no'.
    goto confirm_push
)

echo -------------------------------
echo All done!
echo -------------------------------

pause