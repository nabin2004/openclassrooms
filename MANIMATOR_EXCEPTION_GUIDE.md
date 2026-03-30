# ManimatorException Usage Guide

This guide provides comprehensive documentation on how to use the `ManimatorException` class throughout the Manimator codebase for robust error handling and logging.

## Overview

`ManimatorException` is a specialized exception class that extends Python's `logging.Logger` to provide integrated exception handling with detailed logging capabilities. It's designed specifically for the Manimator animation generation pipeline.

## Key Features

- **Integrated Logging**: Combines exception handling with comprehensive logging
- **Error Context Tracking**: Captures scene_id, error_line, failing_code, and error types
- **Custom Log Levels**: Uses `ManimatorLogLevel` enum for consistent logging
- **Automatic Logger Setup**: Configures console handlers with proper formatting
- **Structured Error Data**: Provides detailed error summaries for debugging

## Basic Usage

```python
from manimator.logging.logger import ManimatorException, ManimatorLogLevel
from manimator.contracts.validation import ErrorType

# Create an exception instance
exception = ManimatorException(
    name="validator",
    error_type=ErrorType.SYNTAX,
    scene_id=1,
    error_message="Syntax error in generated code",
    error_line=42,
    failing_code="self.play(invalid_syntax)"
)

# Log an error
exception.log_error("Validation failed", ManimatorLogLevel.ERROR)

# Log with extra context
exception.log_error(
    "Code generation failed",
    ManimatorLogLevel.ERROR,
    extra_data={"model": "gpt-4", "attempt": 3}
)
```

## Usage in Different Classes

### 1. Validator Agent

The validator agent can use `ManimatorException` to track validation failures:

```python
from manimator.logging.logger import ManimatorException, ManimatorLogLevel
from manimator.contracts.validation import ErrorType

async def validate_code(code: str, spec: SceneSpec, retry_count: int = 0):
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        # Create exception for syntax error
        exception = ManimatorException(
            name="validator",
            error_type=ErrorType.SYNTAX,
            scene_id=spec.scene_id,
            error_message=str(e),
            error_line=e.lineno,
            failing_code=code
        )
        
        # Log the error with context
        exception.log_error(
            f"Syntax validation failed for scene {spec.scene_id}",
            ManimatorLogLevel.ERROR,
            extra_data={"retry_count": retry_count}
        )
        
        return ValidationResult(
            passed=False,
            scene_id=spec.scene_id,
            failing_code=code,
            error_type=ErrorType.SYNTAX,
            error_message=str(e),
            error_line=e.lineno,
            retry_count=retry_count,
            original_spec=spec,
        )
```

### 2. Code Generator Agent

The code generator can use exceptions to track generation failures:

```python
from manimator.logging.logger import ManimatorException, ManimatorLogLevel
from manimator.contracts.validation import ErrorType

async def generate_code(spec: SceneSpec) -> str:
    try:
        # Code generation logic here
        pass
    except Exception as e:
        # Create exception for generation failure
        exception = ManimatorException(
            name="codegen",
            error_type=ErrorType.SYNTAX,  # or appropriate type
            scene_id=spec.scene_id,
            error_message=f"Code generation failed: {str(e)}",
            failing_code="generation_failed"
        )
        
        # Log with generation context
        exception.log_error(
            "Failed to generate Manim code",
            ManimatorLogLevel.ERROR,
            extra_data={
                "scene_class": spec.scene_class.value,
                "object_count": len(spec.objects),
                "animation_count": len(spec.animations)
            }
        )
        
        # Re-raise or handle appropriately
        exception.raise_with_logging("Code generation failed")
```

### 3. Planner Agent

The planner agent can track planning failures and LLM issues:

```python
from manimator.logging.logger import ManimatorException, ManimatorLogLevel
from manimator.contracts.validation import ErrorType

async def plan_scene(scene: SceneEntry, feedback: str | None = None) -> SceneSpec:
    try:
        response = await litellm.acompletion(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        # Process response...
    except Exception as e:
        # Create exception for planning failure
        exception = ManimatorException(
            name="planner",
            error_type=ErrorType.SYNTAX,  # or create new error type
            scene_id=scene.id,
            error_message=f"Scene planning failed: {str(e)}",
            failing_code="llm_call_failed"
        )
        
        # Log with planning context
        exception.log_error(
            f"Failed to plan scene: {scene.title}",
            ManimatorLogLevel.ERROR,
            extra_data={
                "model": MODEL,
                "scene_title": scene.title,
                "feedback": feedback,
                "temperature": 0.3
            }
        )
        
        raise ValueError(f"Failed to parse SceneSpec: {e}")
```

### 4. Repair Agent

The repair agent can track repair attempts and failures:

```python
from manimator.logging.logger import ManimatorException, ManimatorLogLevel
from manimator.contracts.validation import ErrorType

async def repair_code(validation_result: ValidationResult) -> str:
    try:
        # Repair logic here
        pass
    except Exception as e:
        # Create exception for repair failure
        exception = ManimatorException(
            name="repair",
            error_type=ErrorType.SYNTAX,
            scene_id=validation_result.scene_id,
            error_message=f"Repair failed: {str(e)}",
            error_line=validation_result.error_line,
            failing_code=validation_result.failing_code
        )
        
        # Log with repair context
        exception.log_error(
            f"Failed to repair scene {validation_result.scene_id}",
            ManimatorLogLevel.ERROR,
            extra_data={
                "retry_count": validation_result.retry_count,
                "original_error": validation_result.error_type.value,
                "max_retries": MAX_RETRIES
            }
        )
        
        # Raise with logging
        exception.raise_with_logging("Code repair failed")
```

### 5. Pipeline/Graph

The main pipeline can track system-level errors:

```python
from manimator.logging.logger import ManimatorException, ManimatorLogLevel
from manimator.contracts.validation import ErrorType

async def process_pipeline(state: dict):
    try:
        # Pipeline processing logic
        pass
    except Exception as e:
        # Create system-level exception
        exception = ManimatorException(
            name="pipeline",
            error_type=ErrorType.TIMEOUT,  # or appropriate system error
            error_message=f"Pipeline processing failed: {str(e)}",
            failing_code="pipeline_execution"
        )
        
        # Log system error
        exception.log_error(
            "Critical pipeline failure",
            ManimatorLogLevel.CRITICAL,
            extra_data={
                "state_keys": list(state.keys()),
                "pipeline_step": "processing",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Get error summary for reporting
        error_summary = exception.get_error_summary()
        print(f"Pipeline Error Summary: {error_summary}")
        
        exception.raise_with_logging("Pipeline failed")
```

## Advanced Usage Patterns

### 1. Error Aggregation

```python
class ErrorCollector:
    def __init__(self):
        self.exceptions = []
    
    def add_exception(self, exception: ManimatorException):
        self.exceptions.append(exception)
    
    def get_all_summaries(self) -> list:
        return [exc.get_error_summary() for exc in self.exceptions]
    
    def log_all_errors(self):
        for exc in self.exceptions:
            exc.log_error("Collected error", ManimatorLogLevel.ERROR)
```

### 2. Context Managers

```python
from contextlib import contextmanager

@contextmanager
def manimator_error_handler(component_name: str, scene_id: int = None):
    try:
        yield
    except Exception as e:
        exception = ManimatorException(
            name=component_name,
            scene_id=scene_id,
            error_message=str(e),
            failing_code="context_manager_error"
        )
        exception.raise_with_logging(f"Error in {component_name}")
```

### 3. Retry Logic Integration

```python
async def retry_with_logging(operation, max_retries: int, component_name: str):
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            exception = ManimatorException(
                name=component_name,
                error_message=f"Attempt {attempt + 1} failed: {str(e)}",
                failing_code=f"retry_attempt_{attempt + 1}"
            )
            
            exception.log_error(
                f"Retry attempt {attempt + 1} failed",
                ManimatorLogLevel.WARNING,
                extra_data={"attempt": attempt + 1, "max_retries": max_retries}
            )
            
            if attempt == max_retries - 1:
                exception.raise_with_logging("All retry attempts failed")
```

## Best Practices

1. **Always include component name**: Use descriptive names for the `name` parameter
2. **Provide context**: Include relevant data in `extra_data` parameter
3. **Use appropriate error types**: Choose from `ErrorType` enum or extend it
4. **Log before raising**: Use `raise_with_logging()` for consistent behavior
5. **Include scene context**: Always provide `scene_id` when available
6. **Track line numbers**: Include `error_line` for code-related errors
7. **Preserve failing code**: Store the actual code that caused the error

## Error Types Reference

```python
class ErrorType(str, Enum):
    SYNTAX = "syntax"           # Syntax errors in generated code
    NAME_ERROR = "name_error"   # Missing objects/names
    IMPORT = "import"          # Import statement issues
    EMPTY_SCENE = "empty_scene" # No animations or objects
    CAMERA_CONFLICT = "camera_conflict"  # Camera operation conflicts
    TIMEOUT = "timeout"        # Operation timeouts
```

## Log Levels Reference

```python
class ManimatorLogLevel(Enum):
    DEBUG = "DEBUG"      # Detailed debugging information
    INFO = "INFO"        # General information messages
    WARNING = "WARNING"  # Warning messages
    ERROR = "ERROR"      # Error messages
    CRITICAL = "CRITICAL"  # Critical system errors
```

This comprehensive guide should help you integrate `ManimatorException` effectively throughout the Manimator codebase for better error handling and debugging capabilities.
