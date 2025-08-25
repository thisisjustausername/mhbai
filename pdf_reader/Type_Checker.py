# Copyright (c) 2025 Leon Gattermeyer
#
# This file is part of mhbai.
#
# Licensed under the AGPL-3.0 License. See LICENSE file in the project root for full license information.

# Description: type checker
# Status: IN DEVELOPMENT

import inspect
import types
from typing_extensions import get_args, get_origin
from typing import Literal, get_type_hints, Annotated, Optional, List, Union, Dict
from functools import wraps

# TODO finish all in this file, type_check is incorrect too, since it needs to be recursive

# ik it is ironical to add rn not being checked type hints to a type checker
def check_Dict(name: str, value, expected_type):
    pass


def type_check(func):   
    @wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        hints = get_type_hints(func, include_extras=True)
        for name, value in bound.arguments.items():
            annotation = hints.get(name, None)
            if annotation is None:
                continue

            origin = get_origin(annotation)

            if origin is Annotated:
                base_type, *metadata = get_args(annotation)
                annotation = base_type
                origin = get_origin(annotation)

            if get_origin(annotation) is Literal:
                allowed_values = get_args(annotation)
                if value not in allowed_values:
                    raise TypeError(f"{name} must be of type {allowed_values}, got {value!r}")
                continue

            if get_origin(annotation) is Union:
                union_types = get_args(annotation)
                if not any(isinstance(value, t) if not isinstance(t, types.GenericAlias) else isinstance(value, t.__origin__) for t in union_types if t is not type(None)):
                    if value is not None:
                        raise TypeError(f"{name} must be of type {union_types}, got {type(value).__name__}")
                continue

            if not isinstance(value, annotation):
                raise TypeError(f"{name} must be of type {annotation}, got {type(value).__name__}")
        
        return func(*args, **kwargs)
        
    return wrapper