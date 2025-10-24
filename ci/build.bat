
@echo off
setlocal enabledelayedexpansion

REM Check if conda is available
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: conda command not found. Please ensure conda is installed and in your PATH.
    exit /b 1
)

REM Initialize conda for batch scripts
call conda init cmd.exe >nul 2>&1

REM Activate the conda environment
echo Activating conda environment: pdal_ign_plugin
call conda activate pdal_ign_plugin
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate conda environment 'pdal_ign_plugin'. 
    echo Please ensure the environment exists. You can create it with:
    echo conda env create -f environment.yml
    exit /b 1
)

REM Set CONDA_PREFIX
set CONDA_PREFIX=%CONDA_PREFIX%
echo conda is %CONDA_PREFIX%

REM Create build directory (remove if exists)
if exist build (
    echo Removing existing build directory...
    RMDIR /S /Q build
)
mkdir build
if %errorlevel% neq 0 (
    echo ERROR: Failed to create build directory
    exit /b 1
)

cd build
if %errorlevel% neq 0 (
    echo ERROR: Failed to change to build directory
    exit /b 1
)

REM Run cmake
echo Running cmake...
cmake -G"NMake Makefiles" -DCONDA_PREFIX=%CONDA_PREFIX% -DCMAKE_BUILD_TYPE=Release ../
if %errorlevel% neq 0 (
    echo ERROR: cmake failed
    call conda deactivate
    cd ..
    exit /b 1
)

REM Run nmake
echo Running nmake install...
nmake install
if %errorlevel% neq 0 (
    echo ERROR: nmake install failed
    call conda deactivate
    cd ..
    exit /b 1
)

echo Build completed successfully!

REM Deactivate conda
call conda deactivate

cd ..
RMDIR /S /Q build

echo Build directory cleaned up.