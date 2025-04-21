#!/bin/bash
set -e

# Script to run tests for GLiNER MLOps pipeline
# Usage: ./run_tests.sh [options]
#
# Options:
#   --coverage     Generate coverage report
#   --xml          Generate JUnit XML report for CI
#   --verbose      Show verbose output
#   --skip-lint    Skip linting check

echo "Starting test suite for GLiNER MLOps pipeline..."

# Parse arguments
COVERAGE=0
XML_REPORT=0
VERBOSE=0
SKIP_LINT=0

for arg in "$@"; do
  case $arg in
    --coverage)
      COVERAGE=1
      shift
      ;;
    --xml)
      XML_REPORT=1
      shift
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    --skip-lint)
      SKIP_LINT=1
      shift
      ;;
  esac
done

# Create directory for test results
mkdir -p test-results

# Run linting if not skipped
if [ $SKIP_LINT -eq 0 ]; then
  echo "Running linting checks..."
  
  pylint_cmd="python -m pylint app --rcfile=.pylintrc"
  
  if [ $VERBOSE -eq 1 ]; then
    $pylint_cmd
  else
    $pylint_cmd > test-results/pylint.log || {
      echo "Linting failed. See test-results/pylint.log for details."
      exit 1
    }
  fi
  
  echo "Linting passed."
fi

# Prepare test command
test_cmd="python -m pytest tests/"

# Add options based on arguments
if [ $COVERAGE -eq 1 ]; then
  test_cmd="$test_cmd --cov=app"
  
  if [ $XML_REPORT -eq 1 ]; then
    test_cmd="$test_cmd --cov-report=xml:test-results/coverage.xml"
  else
    test_cmd="$test_cmd --cov-report=term"
  fi
fi

if [ $XML_REPORT -eq 1 ]; then
  test_cmd="$test_cmd --junitxml=test-results/junit.xml"
fi

if [ $VERBOSE -eq 1 ]; then
  test_cmd="$test_cmd -v"
fi

# Run tests
echo "Running tests with command: $test_cmd"
$test_cmd

# Check if coverage threshold is met (if coverage was enabled)
if [ $COVERAGE -eq 1 ]; then
  echo "Checking coverage threshold..."
  coverage_percent=$(coverage report | grep TOTAL | awk '{print $NF}' | sed 's/%//')
  
  if (( $(echo "$coverage_percent < 80" | bc -l) )); then
    echo "Coverage threshold not met: $coverage_percent% < 80%"
    exit 1
  else
    echo "Coverage threshold met: $coverage_percent% >= 80%"
  fi
fi

echo "All tests passed successfully!"
exit 0