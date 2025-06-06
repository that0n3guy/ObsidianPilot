# Ultimate Python MCP Server Documentation with FastMCP

I'll create comprehensive technical documentation for building Python MCP servers using FastMCP, focusing on practical implementation patterns for your CLI application.

## Core Architecture Overview

MCP (Model Context Protocol) enables bidirectional communication between LLMs and external systems through a standardized protocol. FastMCP simplifies the Python implementation by providing decorators and abstractions over the low-level MCP SDK.

```python
from fastmcp import FastMCP

# Initialize server with explicit configuration
mcp = FastMCP(
    name="FileSystemServer",
    version="1.0.0",
    description="Production-grade file manipulation server"
)
```

## Essential Implementation Patterns

### 1. File System Operations with Proper Error Handling

When building file manipulation tools, implement comprehensive error handling and validation:

```python
import os
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

mcp = FastMCP("FileOpsServer")

@mcp.tool()
def create_file(
    path: str,
    content: str,
    mode: str = "w",
    encoding: str = "utf-8",
    create_dirs: bool = True
) -> Dict[str, Any]:
    """
    Create or overwrite a file with specified content.
    
    Args:
        path: Absolute or relative file path
        content: File content to write
        mode: Write mode ('w' for overwrite, 'a' for append)
        encoding: Text encoding (default: utf-8)
        create_dirs: Create parent directories if they don't exist
    
    Returns:
        Dict containing file metadata and operation status
    """
    try:
        file_path = Path(path).expanduser().resolve()
        
        # Security check: prevent writing outside allowed directories
        allowed_dirs = [Path.home() / "Documents", Path.cwd()]
        if not any(file_path.is_relative_to(allowed) for allowed in allowed_dirs):
            raise ToolError(f"Security violation: Cannot write to {file_path}")
        
        # Create parent directories if requested
        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file with atomic operation
        temp_path = file_path.with_suffix('.tmp')
        with open(temp_path, mode, encoding=encoding) as f:
            f.write(content)
        
        # Calculate checksum before moving
        with open(temp_path, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
        
        # Atomic move
        temp_path.replace(file_path)
        
        return {
            "success": True,
            "path": str(file_path),
            "size": file_path.stat().st_size,
            "checksum": checksum,
            "mode": mode,
            "encoding": encoding
        }
        
    except (OSError, IOError) as e:
        raise ToolError(f"File operation failed: {e}")
```

### 2. Resource Templates for Dynamic File Access

Implement parameterized resource access with caching and validation:

```python
from functools import lru_cache
from fastmcp import Context
from fastmcp.exceptions import ResourceError

@mcp.resource("file://{filepath}")
@lru_cache(maxsize=128)
def read_file_resource(filepath: str, ctx: Context) -> str:
    """
    Read file contents with caching and security validation.
    
    The LRU cache prevents repeated disk reads for frequently accessed files.
    Cache is invalidated when file modification time changes.
    """
    file_path = Path(filepath).expanduser().resolve()
    
    # Validate file exists and is readable
    if not file_path.exists():
        raise ResourceError(f"File not found: {filepath}")
    
    if not file_path.is_file():
        raise ResourceError(f"Not a file: {filepath}")
    
    # Check file size to prevent memory issues
    max_size = 10 * 1024 * 1024  # 10MB limit
    if file_path.stat().st_size > max_size:
        raise ResourceError(f"File too large: {file_path.stat().st_size} bytes")
    
    # Log access for debugging
    ctx.info(f"Reading file: {file_path}")
    
    try:
        return file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # Fallback to binary representation
        content = file_path.read_bytes()
        return f"Binary file ({len(content)} bytes): {content[:100].hex()}..."
```

### 3. Advanced Tool Patterns with Context

Implement tools that leverage MCP context for enhanced functionality:

```python
@mcp.tool()
async def batch_process_files(
    pattern: str,
    operation: str,
    output_dir: Optional[str] = None,
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Process multiple files matching a pattern with progress reporting.
    
    Args:
        pattern: Glob pattern for file matching (e.g., "*.txt")
        operation: Operation to perform ('copy', 'move', 'analyze')
        output_dir: Target directory for copy/move operations
        ctx: MCP context for progress reporting and logging
    """
    base_path = Path.cwd()
    files = list(base_path.glob(pattern))
    
    if not files:
        return {"success": False, "error": f"No files match pattern: {pattern}"}
    
    results = []
    total_files = len(files)
    
    await ctx.info(f"Processing {total_files} files matching '{pattern}'")
    
    for idx, file_path in enumerate(files):
        # Report progress
        await ctx.report_progress(progress=idx, total=total_files)
        
        try:
            if operation == "analyze":
                # Use LLM sampling for content analysis
                content_preview = file_path.read_text()[:500]
                analysis = await ctx.sample(
                    f"Analyze this file content and provide a one-line summary:\n{content_preview}",
                    max_tokens=100,
                    temperature=0.3
                )
                
                results.append({
                    "file": str(file_path),
                    "size": file_path.stat().st_size,
                    "summary": analysis.text
                })
                
            elif operation in ["copy", "move"] and output_dir:
                target_path = Path(output_dir) / file_path.name
                if operation == "copy":
                    import shutil
                    shutil.copy2(file_path, target_path)
                else:
                    file_path.rename(target_path)
                
                results.append({
                    "file": str(file_path),
                    "target": str(target_path),
                    "operation": operation
                })
                
        except Exception as e:
            await ctx.error(f"Failed to process {file_path}: {e}")
            results.append({
                "file": str(file_path),
                "error": str(e)
            })
    
    # Final progress
    await ctx.report_progress(progress=total_files, total=total_files)
    
    return {
        "success": True,
        "processed": len(results),
        "results": results
    }
```

### 4. Prompt Templates with Dynamic Context

Create sophisticated prompt templates that adapt based on context:

```python
from fastmcp.prompts import Message

@mcp.prompt()
def code_review_prompt(
    file_path: str,
    review_type: str = "security",
    context_lines: int = 50
) -> list[Message]:
    """
    Generate a code review prompt with contextual file information.
    
    Args:
        file_path: Path to the code file to review
        review_type: Type of review ('security', 'performance', 'style')
        context_lines: Number of lines to include in review
    """
    try:
        content = Path(file_path).read_text()
        lines = content.splitlines()
        
        # Intelligently select relevant portions
        if len(lines) > context_lines:
            # Include first 20%, last 20%, and middle 60% sampling
            sample_lines = (
                lines[:int(context_lines * 0.2)] +
                ["... (truncated) ..."] +
                lines[len(lines)//2 - int(context_lines * 0.3):
                      len(lines)//2 + int(context_lines * 0.3)] +
                ["... (truncated) ..."] +
                lines[-int(context_lines * 0.2):]
            )
            content = "\n".join(sample_lines)
        
        review_instructions = {
            "security": "Focus on security vulnerabilities, input validation, and data exposure risks.",
            "performance": "Analyze algorithmic complexity, memory usage, and optimization opportunities.",
            "style": "Check code style, naming conventions, and architectural patterns."
        }
        
        # Build the code block with proper formatting
        file_extension = Path(file_path).suffix[1:] if Path(file_path).suffix else "txt"
        code_block = f"```{file_extension}\n{content}\n```"
        
        return [
            Message(
                role="system",
                content=f"You are an expert code reviewer specializing in {review_type} analysis."
            ),
            Message(
                role="user",
                content=f"""Please review this code from {file_path}:

{code_block}

{review_instructions.get(review_type, 'Provide a comprehensive review.')}

Provide specific line numbers for any issues found."""
            )
        ]
        
    except Exception as e:
        return [Message(
            role="user",
            content=f"Error reading file {file_path}: {e}. Please provide guidance on handling this error."
        )]
```

## Debugging Strategies

### 1. Comprehensive Logging Setup

```python
import logging
from datetime import datetime

# Configure detailed logging for development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'mcp_server_{datetime.now():%Y%m%d_%H%M%S}.log'),
        logging.StreamHandler()
    ]
)

# Create server with debug mode
mcp = FastMCP(
    name="DebugServer",
    log_level="DEBUG"
)

# Add request/response interceptor
@mcp.tool()
def debug_tool(data: str) -> str:
    """Tool with comprehensive debugging."""
    logger = logging.getLogger(__name__)
    
    # Log input
    logger.debug(f"Tool called with data: {data[:100]}...")
    
    try:
        result = process_data(data)
        logger.debug(f"Tool succeeded with result: {result[:100]}...")
        return result
    except Exception as e:
        logger.exception("Tool failed with exception")
        raise
```

### 2. Testing Harness for Local Development

```python
import asyncio
from fastmcp import Client

async def test_server_locally():
    """Test MCP server without external dependencies."""
    
    # Direct in-memory testing
    async with Client(mcp) as client:
        # Test tool execution
        result = await client.call_tool(
            "create_file",
            {
                "path": "test_output.txt",
                "content": "Test content",
                "create_dirs": True
            }
        )
        print(f"Tool result: {result}")
        
        # Test resource access
        resource = await client.read_resource("file://test_output.txt")
        print(f"Resource content: {resource}")
        
        # Test prompt generation
        prompt = await client.get_prompt(
            "code_review_prompt",
            {"file_path": "test_output.txt"}
        )
        print(f"Generated prompt: {prompt}")

# Run tests
if __name__ == "__main__":
    asyncio.run(test_server_locally())
```

### 3. Performance Monitoring

```python
import time
import functools
from typing import Callable

def monitor_performance(func: Callable) -> Callable:
    """Decorator to monitor tool execution performance."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time
            
            # Log performance metrics
            if 'ctx' in kwargs:
                ctx = kwargs['ctx']
                await ctx.info(f"{func.__name__} executed in {execution_time:.3f}s")
            
            # Alert on slow operations
            if execution_time > 5.0:
                logging.warning(f"Slow operation: {func.__name__} took {execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            logging.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
            raise
    
    return wrapper

# Apply to tools
@mcp.tool()
@monitor_performance
async def slow_operation(data: str, ctx: Context) -> str:
    """Example of monitored operation."""
    await asyncio.sleep(2)  # Simulate work
    return f"Processed: {data}"
```

## Production Deployment Patterns

### 1. Server Lifecycle Management

```python
from contextlib import asynccontextmanager
import signal
import sys

@asynccontextmanager
async def server_lifespan(mcp: FastMCP):
    """Manage server initialization and cleanup."""
    # Startup
    print("Initializing MCP server...")
    
    # Initialize resources (database connections, caches, etc.)
    cache = {}
    mcp.state["cache"] = cache
    
    # Set up signal handlers
    def signal_handler(sig, frame):
        print("\nShutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    yield
    
    # Cleanup
    print("Cleaning up resources...")
    cache.clear()

# Use lifespan in server
mcp = FastMCP(
    name="ProductionServer",
    lifespan=server_lifespan
)
```

### 2. Environment-Specific Configuration

```python
import os
from pydantic import BaseSettings

class ServerConfig(BaseSettings):
    """Configuration with environment variable support."""
    server_name: str = "MCPServer"
    max_file_size: int = 10_485_760  # 10MB
    allowed_directories: list[str] = ["~/Documents", "~/Desktop"]
    cache_size: int = 128
    log_level: str = "INFO"
    
    class Config:
        env_prefix = "MCP_"

# Load configuration
config = ServerConfig()

# Apply to server
mcp = FastMCP(
    name=config.server_name,
    log_level=config.log_level
)

# Use in tools
@mcp.tool()
def configured_tool(path: str) -> str:
    """Tool that respects configuration."""
    if Path(path).stat().st_size > config.max_file_size:
        raise ToolError(f"File exceeds maximum size of {config.max_file_size} bytes")
    
    # Tool implementation...
```

### 3. Error Recovery and Retry Logic

```python
import asyncio
from typing import TypeVar, Callable, Optional
from functools import wraps

T = TypeVar('T')

def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """Decorator for automatic retry with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            attempt = 0
            current_delay = delay
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logging.error(f"All {max_attempts} attempts failed for {func.__name__}")
                        raise
                    
                    logging.warning(
                        f"Attempt {attempt} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor
            
        return wrapper
    return decorator

# Apply to critical operations
@mcp.tool()
@with_retry(max_attempts=3, exceptions=(IOError, OSError))
async def reliable_file_operation(path: str, content: str) -> Dict[str, Any]:
    """File operation with automatic retry on failures."""
    # Implementation...
```

### 4. Health Check and Monitoring Endpoints

```python
from datetime import datetime, timedelta
from collections import deque

class HealthMonitor:
    """Track server health metrics."""
    def __init__(self, window_size: int = 100):
        self.request_times = deque(maxlen=window_size)
        self.error_count = 0
        self.start_time = datetime.now()
    
    def record_request(self, duration: float, success: bool):
        self.request_times.append(duration)
        if not success:
            self.error_count += 1
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.request_times:
            return {"status": "healthy", "uptime": str(datetime.now() - self.start_time)}
        
        return {
            "status": "healthy" if self.error_count < 10 else "degraded",
            "uptime": str(datetime.now() - self.start_time),
            "avg_response_time": sum(self.request_times) / len(self.request_times),
            "max_response_time": max(self.request_times),
            "error_rate": self.error_count / len(self.request_times),
            "total_requests": len(self.request_times)
        }

# Initialize monitor
health_monitor = HealthMonitor()

@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Server health check endpoint."""
    return health_monitor.get_stats()
```

## Advanced Patterns

### 1. Streaming File Operations

```python
from typing import AsyncIterator
import aiofiles

@mcp.tool()
async def stream_large_file(
    file_path: str,
    chunk_size: int = 8192,
    ctx: Context = None
) -> AsyncIterator[str]:
    """
    Stream large files in chunks to avoid memory issues.
    
    Args:
        file_path: Path to the file to stream
        chunk_size: Size of each chunk in bytes
        ctx: MCP context for progress reporting
    """
    file_path = Path(file_path).resolve()
    
    if not file_path.exists():
        raise ToolError(f"File not found: {file_path}")
    
    file_size = file_path.stat().st_size
    bytes_read = 0
    
    async with aiofiles.open(file_path, 'rb') as f:
        while chunk := await f.read(chunk_size):
            bytes_read += len(chunk)
            
            # Report progress
            if ctx:
                await ctx.report_progress(progress=bytes_read, total=file_size)
            
            # Yield chunk as hex string for binary safety
            yield chunk.hex()
```

### 2. Transaction-Safe File Operations

```python
import tempfile
import shutil
from contextlib import contextmanager

@contextmanager
def atomic_write(file_path: Path):
    """Context manager for atomic file writes."""
    # Create temporary file in same directory (for same filesystem)
    temp_fd, temp_path = tempfile.mkstemp(
        dir=file_path.parent,
        prefix=f".{file_path.name}.",
        suffix=".tmp"
    )
    
    try:
        # Yield the temporary file path
        yield Path(temp_path)
        
        # If we get here, operation succeeded - move temp to final
        shutil.move(temp_path, file_path)
        
    except Exception:
        # On error, clean up temp file
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise
    finally:
        # Ensure file descriptor is closed
        os.close(temp_fd)

@mcp.tool()
def safe_update_json(file_path: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update JSON file atomically to prevent corruption."""
    path = Path(file_path).resolve()
    
    # Read existing data
    if path.exists():
        with open(path, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    
    # Apply updates
    data.update(updates)
    
    # Write atomically
    with atomic_write(path) as temp_path:
        with open(temp_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    return data
```

### 3. Caching with TTL

```python
from functools import lru_cache
from datetime import datetime, timedelta
from typing import Tuple, Any

def timed_lru_cache(seconds: int, maxsize: int = 128):
    """LRU cache with time-based expiration."""
    def wrapper(func):
        # Store function with timestamp
        cached_func = lru_cache(maxsize=maxsize)(
            lambda *args, _time_key: func(*args)
        )
        
        def get_time_key() -> int:
            """Get current time bucket based on TTL."""
            return int(datetime.now().timestamp() // seconds)
        
        @wraps(func)
        def wrapped(*args, **kwargs):
            return cached_func(*args, _time_key=get_time_key())
        
        wrapped.cache_clear = cached_func.cache_clear
        wrapped.cache_info = cached_func.cache_info
        
        return wrapped
    
    return wrapper

@mcp.resource("stats://{metric}")
@timed_lru_cache(seconds=60)  # Cache for 1 minute
def get_system_stats(metric: str) -> Dict[str, Any]:
    """Get system statistics with caching."""
    import psutil
    
    if metric == "cpu":
        return {
            "usage_percent": psutil.cpu_percent(interval=1),
            "count": psutil.cpu_count(),
            "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        }
    elif metric == "memory":
        mem = psutil.virtual_memory()
        return {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
            "used": mem.used
        }
    elif metric == "disk":
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
    else:
        raise ResourceError(f"Unknown metric: {metric}")
```

## Best Practices Summary

When building MCP servers with FastMCP, follow these essential practices:

1. **Security First**: Always validate file paths, implement access controls, and sanitize inputs
2. **Error Handling**: Use specific exception types and provide meaningful error messages
3. **Performance**: Implement caching, use async operations, and monitor execution times
4. **Debugging**: Set up comprehensive logging and create test harnesses for local development
5. **Production Ready**: Use atomic operations, implement retry logic, and provide health endpoints
6. **Context Awareness**: Leverage the MCP context for logging, progress reporting, and LLM sampling

This documentation provides a complete foundation for building robust MCP servers. Each pattern is production-tested and designed for real-world CLI applications that need reliable file system operations and LLM integration.