@echo off
REM Downloads, patches, and builds CBSH2-RTC for reference solution verification.
REM CBSH2-RTC is not included in this repo (USC Research License).
REM This script clones it from the authors' GitHub and applies our CLI11 patch.
REM
REM Run from a Visual Studio Developer Command Prompt, or ensure cmake/git/curl are on PATH.

setlocal
set SCRIPT_DIR=%~dp0
set BUILD_DIR=%SCRIPT_DIR%build
set COMMIT=a834df1e16c1668a677b68fef6699371c4233d33
set CLI11_URL=https://github.com/CLIUtils/CLI11/releases/download/v2.4.1/CLI11.hpp
set BOOST_URL=https://archives.boost.io/release/1.86.0/source/boost_1_86_0.zip

echo === CBSH2-RTC Setup ===

REM Step 1: Clone
if exist "%BUILD_DIR%\CBSH2-RTC" (
    echo CBSH2-RTC already cloned, skipping.
) else (
    echo Cloning CBSH2-RTC...
    mkdir "%BUILD_DIR%" 2>nul
    git clone https://github.com/Jiaoyang-Li/CBSH2-RTC.git "%BUILD_DIR%\CBSH2-RTC"
    cd /d "%BUILD_DIR%\CBSH2-RTC"
    git checkout %COMMIT%
)

REM Step 2: Download Boost headers
if exist "%BUILD_DIR%\boost" (
    echo Boost headers already present, skipping.
) else (
    echo Downloading Boost 1.86.0 headers...
    cd /d "%BUILD_DIR%"
    curl -L -o boost.zip "%BOOST_URL%"
    tar -xf boost.zip
    ren boost_1_86_0 boost
    del boost.zip
)

REM Step 3: Download CLI11 and apply patch
cd /d "%BUILD_DIR%\CBSH2-RTC"
if not exist "inc\CLI11.hpp" (
    echo Downloading CLI11...
    curl -L -o inc\CLI11.hpp "%CLI11_URL%"
)

echo Applying CLI11 patch...
git apply "%SCRIPT_DIR%cli11_patch.diff" 2>nul

REM Step 4: Build
echo Building...
mkdir build 2>nul
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DBOOST_ROOT="%BUILD_DIR%\boost"
cmake --build . --config Release

echo.
echo === Done ===
echo Binary: %BUILD_DIR%\CBSH2-RTC\build\Release\cbs.exe
echo.
echo Example usage:
echo   cbs.exe -m ^<map.map^> -a ^<scenario.scen^> -k ^<agent_count^> -t 60
