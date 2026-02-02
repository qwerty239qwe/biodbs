from __future__ import annotations
from pydantic import BaseModel, ValidationError
from typing import Tuple, List, Dict, Any, Callable, Optional, Type
import asyncio
import time
from functools import wraps


class BaseAPIConfig:
    """Configuration for API URL construction.

    Supports two modes:
        - **Template mode**: Pass ``url_format`` as a format string
          (e.g. ``"https://api.example.com/{category}/{endpoint}"``) and
          parameters will be interpolated via ``.format(**params)``.
        - **Builder mode**: Pass ``url_builder`` as a callable that takes
          a params dict and returns the full URL string. Use this for
          APIs whose URL structure varies by parameter (e.g. KEGG).

    If both are provided, ``url_builder`` takes precedence.
    """

    def __init__(
        self,
        url_format: Optional[str] = None,
        url_builder: Optional[Callable[[Dict[str, Any]], str]] = None,
    ):
        self._url_format = url_format
        self._url_builder = url_builder
        self._params: Dict[str, Any] = {}

    def __str__(self):
        disp_names = [
            self.__class__.__name__,
            f"API format: {self._url_format}",
            f"URL builder: {self._url_builder}",
            f"Current params: {self._params}",
        ]
        return "\n".join(disp_names)

    def update_params(self, **kwargs):
        self._params.update(kwargs)

    @property
    def api_url(self) -> str:
        if self._url_builder is not None:
            return self._url_builder(self._params)
        if self._url_format is not None:
            return self._url_format.format(**self._params)
        raise NotImplementedError(
            "Subclass must provide url_format, url_builder, or override api_url"
        )

    def copy(self):
        new = self.__class__()
        new._url_format = self._url_format
        new._url_builder = self._url_builder
        new.update_params(**self._params)
        return new

    def apply(self, **params):
        new_api = self.copy()
        new_api.update_params(**params)
        return new_api


class NameSpace:
    def __init__(self, model: type[BaseModel]):
        self._model = model
        self._valid_params = {}
    
    def validate(self, **kwargs) -> Tuple[bool, str]:
        err_msg = "No error found"
        try:
            ins = self._model(**kwargs)
            self._valid_params = ins.model_dump()
        except ValidationError as e:
            err_msg = str(e)
            return False, err_msg
        
        return True, err_msg
    
    @property
    def valid_params(self):
        return self._valid_params


class BaseDataFetcher:
    def __init__(self, api_config: BaseAPIConfig, namespace: NameSpace, headers):
        self._api_config = api_config
        self._namespace = namespace
        self._headers = headers
    
    def get(self, *args, **kwargs):
        raise NotImplementedError("This method should be implemented in subclass.")
    
    def schedule_process(
        self,
        get_func: Callable,
        args_list: Optional[List[tuple]] = None,
        kwargs_list: Optional[List[dict]] = None,
        rate_limit_per_second: int = 10,
        return_exceptions: bool = False,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """
        Execute multiple async/sync function calls with rate limiting.
        
        Args:
            get_func: The function to call (can be sync or async)
            args_list: List of positional arguments for each call
            kwargs_list: List of keyword arguments for each call
            rate_limit_per_second: Maximum number of requests per second
            return_exceptions: If True, exceptions are returned instead of raised
            progress_callback: Optional callback function(completed, total) for progress tracking
            
        Returns:
            List of results from all function calls
            
        Raises:
            ValueError: If args_list and kwargs_list have different lengths
        """
        args_list = args_list or []
        kwargs_list = kwargs_list or []
        
        # Determine total tasks
        total_tasks = max(len(args_list), len(kwargs_list))
        if total_tasks == 0:
            return []
        
        # Validate list lengths match
        if args_list and kwargs_list and len(args_list) != len(kwargs_list):
            raise ValueError("args_list and kwargs_list must have the same length")
        
        # Pad shorter list with empty values
        if len(args_list) < total_tasks:
            args_list.extend([()] * (total_tasks - len(args_list)))
        if len(kwargs_list) < total_tasks:
            kwargs_list.extend([{}] * (total_tasks - len(kwargs_list)))
        
        # Check if function is async
        is_async = asyncio.iscoroutinefunction(get_func)
        
        async def limited_gather():
            # Semaphore for concurrent request limiting
            semaphore = asyncio.Semaphore(rate_limit_per_second)
            
            # Track time for rate limiting
            last_batch_time = time.time()
            completed_count = 0
            
            async def rate_limited_call(index: int, args: tuple, kwargs: dict):
                nonlocal completed_count, last_batch_time
                
                async with semaphore:
                    # Rate limiting: ensure we don't exceed requests per second
                    if index > 0 and index % rate_limit_per_second == 0:
                        elapsed = time.time() - last_batch_time
                        if elapsed < 1.0:
                            await asyncio.sleep(1.0 - elapsed)
                        last_batch_time = time.time()
                    
                    # Execute function (handle both sync and async)
                    if is_async:
                        result = await get_func(*args, **kwargs)
                    else:
                        result = await asyncio.to_thread(get_func, *args, **kwargs)
                    
                    # Update progress
                    completed_count += 1
                    if progress_callback:
                        progress_callback(completed_count, total_tasks)
                    
                    return result
            
            # Create all tasks
            tasks = [
                rate_limited_call(i, args_list[i], kwargs_list[i])
                for i in range(total_tasks)
            ]
            
            # Execute with optional exception handling
            return await asyncio.gather(*tasks, return_exceptions=return_exceptions)
        
        # Run the async gather
        return asyncio.run(limited_gather())