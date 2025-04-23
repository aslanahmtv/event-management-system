from typing import Any, Callable, Optional, Type, Union
import sys

import redbird.repos
from redbird.repos import MemoryRepo, MongoRepo
from redbird.templates import TemplateRepo

from app.apis.config import settings


def str_to_class(classname: str) -> Union[Type[TemplateRepo], None]:
    """Get a Python class corresponding to the string input. It only works with
     classes that are subclasses of `TemplateRepo`, otherwise it returns None.

    Args:
        classname (str): Name of class to get.

    Returns:
        Union[Type[TemplateRepo], None]: Valid repository class,
         or None if the input doesn't correspond to a valid class.
    """
    try:
        class_ = getattr(sys.modules[redbird.repos.__name__], classname)
        assert issubclass(class_, TemplateRepo)
        return class_
    except (AttributeError, AssertionError):
        return None


def get_repository(
    repo_type: str = settings.REPOSITORY_NAME,
    *args: Any,
    **kwargs: Any,
) -> Optional[TemplateRepo]:
    """Get a repository instance by type"""
    if repo_type == "MongoRepo":
        # Pass the MongoDB URL from settings
        if "uri" not in kwargs:
            kwargs["uri"] = settings.MONGODB_URL
        if "db_name" not in kwargs:
            kwargs["db_name"] = settings.DB_NAME
        
        return MongoRepo(*args, **kwargs)
    elif repo_type == "MemoryRepo":
        # Return in-memory repository for testing
        return MemoryRepo(*args, **kwargs)
    else:
        # Try to get the class by name
        repo_class = str_to_class(repo_type)
        if repo_class:
            return repo_class(*args, **kwargs)
        
        # Return None for unsupported db types instead of raising error
        return None