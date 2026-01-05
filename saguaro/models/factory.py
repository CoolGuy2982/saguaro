try:
    from google.adk.models.lite_llm import LiteLlm
except ImportError:
    # This might happen if google-adk is not installed in the dev environment
    # We will define a dummy class for type hinting or just rely on the error being raised when used if strictly required,
    # but the instructions say "raise a clear ImportError" if the import fails.
    # However, the instruction says "Add a try/except block for the import of google.adk. If it fails... raise a clear ImportError."
    # This likely means when the module is imported or when the function is called? 
    # Usually better to fail at import time if it's a core dependency, but let's follow the instruction to raise it.
    LiteLlm = None

def get_model_wrapper(model_name: str):
    """
    Wraps a model string into an ADK-compatible model object.
    
    Args:
        model_name: The name of the model (e.g. "gemini-1.5-flash", "openai/gpt-4o").
        
    Returns:
        str: The model name if it's a standard Gemini model.
        LiteLlm: A LiteLlm wrapper if it's a non-Gemini model (contains '/').
        
    Raises:
        ImportError: If google-adk is not installed.
    """
    if LiteLlm is None:
         raise ImportError("The 'google-adk' package is required. Please install it with 'pip install google-adk'.")

    # If model_name is a standard Gemini string (starts with "gemini-" and has no forward slashes)
    if model_name.startswith("gemini-") and "/" not in model_name:
        return model_name
    
    # If model_name contains a slash, instantiate and return LiteLlm
    if "/" in model_name:
        return LiteLlm(model=model_name)
        
    # Fallback/Default behavior for other strings (assuming they might be gemini or handled by ADK default)
    # The requirement says: "If model_name is a standard Gemini string ... return the string as-is."
    # It doesn't explicitly say what to do with "foo-bar" that doesn't start with gemini and has no slash.
    # But usually ADK handles strings. Let's return as string if no slash.
    return model_name
