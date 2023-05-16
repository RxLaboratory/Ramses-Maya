@echo off
:: Builds the module (copies needed files) to the build subfolder,

SET version=0.8.18-Beta

:: The repo (current dir)
SET repoPath=%~dp0
:: The Ramses API repo
SET apiPath="%repoPath%..\Ramses-Py"
:: The DuPYF repo
SET dupyfPath="%repoPath%..\..\Python\DuPYF"

:: The build path
SET build_path=%~dp0build

echo Building "%repoPath%" in "%build_path%"...

:: Clean
rd /s /q "%build_path%"
md "%build_path%"

:: bin
md "%build_path%\bin"
xcopy "%repoPath%bin" "%build_path%\bin\" /y

:: icons
md "%build_path%\icons"
xcopy "%repoPath%icons" "%build_path%\icons\" /y

:: import_presets
md "%build_path%\import_presets"
xcopy "%repoPath%import_presets" "%build_path%\import_presets\" /y

:: publish_presets
md "%build_path%\publish_presets"
xcopy "%repoPath%publish_presets" "%build_path%\publish_presets\" /y

:: shelves
md "%build_path%\shelves"
xcopy "%repoPath%shelves" "%build_path%\shelves\" /y

:: plug-ins
md "%build_path%\plug-ins"
:: root files
echo " " > "%build_path%\plug-ins\Ramses.py"
echo " " > "%build_path%\plug-ins\README.txt"
xcopy /Y "%repoPath%plug-ins\Ramses.py" "%build_path%\plug-ins\Ramses.py"
xcopy /Y "%repoPath%plug-ins\README.md" "%build_path%\plug-ins\README.txt"
:: dumaf
md "%build_path%\plug-ins\dumaf"
xcopy "%repoPath%plug-ins\dumaf" "%build_path%\plug-ins\dumaf" /y
md "%build_path%\plug-ins\dumaf\icons"
xcopy "%repoPath%plug-ins\dumaf\icons" "%build_path%\plug-ins\dumaf\icons" /y
:: dupyf
md "%build_path%\plug-ins\dupyf"
xcopy "%dupyfPath%\dupyf" "%build_path%\plug-ins\dupyf" /y
:: ramses
md "%build_path%\plug-ins\ramses"
xcopy "%apiPath%\ramses" "%build_path%\plug-ins\ramses" /y
:: ramses_maya
md "%build_path%\plug-ins\ramses_maya"
xcopy "%repoPath%\plug-ins\ramses_maya" "%build_path%\plug-ins\ramses_maya" /y
:: yaml
md "%build_path%\plug-ins\yaml"
xcopy "%repoPath%\plug-ins\yaml" "%build_path%\plug-ins\yaml" /y

:: root files
echo " " > "%build_path%\LICENSE.txt"
echo " " > "%build_path%\Ramses.mod"
echo " " > "%build_path%\README.txt"
xcopy /Y "%repoPath%LICENSE.txt" "%build_path%\LICENSE.txt"
xcopy /Y "%repoPath%Ramses.mod" "%build_path%\Ramses.mod"
xcopy /Y "%repoPath%README.md" "%build_path%\README.txt"

:: update version
call :FindReplace "#version#" "%version%" "%build_path%\Ramses.mod"
call :FindReplace "#path#" "D:\Path\To\Ramses-Maya" "%build_path%\Ramses.mod"
call :FindReplace "#version#" "%version%" "%build_path%\plug-ins\ramses_maya\constants.py"

exit /b 

:FindReplace <findstr> <replstr> <file>
set tmp="%temp%\tmp.txt"
If not exist %temp%\_.vbs call :MakeReplace
for /f "tokens=*" %%a in ('dir "%3" /s /b /a-d /on') do (
  for /f "usebackq" %%b in (`Findstr /mic:"%~1" "%%a"`) do (
    echo(&Echo Replacing "%~1" with "%~2" in file %%~nxa
    <%%a cscript //nologo %temp%\_.vbs "%~1" "%~2">%tmp%
    if exist %tmp% move /Y %tmp% "%%~dpnxa">nul
  )
)
del %temp%\_.vbs
exit /b

:MakeReplace
>%temp%\_.vbs echo with Wscript
>>%temp%\_.vbs echo set args=.arguments
>>%temp%\_.vbs echo .StdOut.Write _
>>%temp%\_.vbs echo Replace(.StdIn.ReadAll,args(0),args(1),1,-1,1)
>>%temp%\_.vbs echo end with