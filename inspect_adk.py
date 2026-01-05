try:
    from google.adk.runners import Runner
    import inspect
    
    is_async_gen = inspect.isasyncgenfunction(Runner.run_async)
    print(f"Is run_async an async generator? {is_async_gen}")
    
    # Also check if it's just a regular function that returns an async generator
    # (some functions are not 'async def' but return one)
    
except ImportError:
    print("google-adk not found")
except Exception as e:
    print(f"Error: {e}")
