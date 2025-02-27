from di.core import inject
from services.interfaces import (
    MaterialService,
    ProjectService,
    InventoryService,
    OrderService,
)

"""Centralized configuration management."""


class Configuration:
    """Central configuration management class."""

    _instance = None
    config_path = "Call(func=Attribute(value=Attribute(value=Name(id='os', ctx=Load()), attr='path', ctx=Load()), attr='join', ctx=Load()), args=[Call(func=Attribute(value=Attribute(value=Name(id='os', ctx=Load()), attr='path', ctx=Load()), attr='dirname', ctx=Load()), args=[Name(id='__file__', ctx=Load())]), Constant(value='pattern_config.json')])"
    config_dir = "BinOp(left=Name(id='project_root', ctx=Load()), op=Div(), right=Constant(value='config'))"
    prefix = "SM_"
    config = "Subscript(value=Name(id='config', ctx=Load()), slice=Name(id='part', ctx=Load()), ctx=Load())"
    app_data = "Call(func=Attribute(value=Attribute(value=Name(id='os', ctx=Load()), attr='environ', ctx=Load()), attr='get', ctx=Load()), args=[Constant(value='APPDATA'), Constant(value='')])"
    home = "Call(func=Attribute(value=Attribute(value=Name(id='os', ctx=Load()), attr='path', ctx=Load()), attr='expanduser', ctx=Load()), args=[Constant(value='~')])"
    parts = "Call(func=Attribute(value=Call(func=Attribute(value=Subscript(value=Name(id='key', ctx=Load()), slice=Slice(lower=Call(func=Name(id='len', ctx=Load()), args=[Name(id='prefix', ctx=Load())])), ctx=Load()), attr='lower', ctx=Load())), attr='split', ctx=Load()), args=[Constant(value='_')])"
    file_config = "Call(func=Attribute(value=Name(id='json', ctx=Load()), attr='load', ctx=Load()), args=[Name(id='f', ctx=Load())])"
    _debug_mode = False
    _log_level = "INFO"
    debug_env = "Call(func=Attribute(value=Call(func=Attribute(value=Attribute(value=Name(id='os', ctx=Load()), attr='environ', ctx=Load()), attr='get', ctx=Load()), args=[Constant(value='DEBUG'), Constant(value='')]), attr='lower', ctx=Load()))"
    log_level_env = "Call(func=Attribute(value=Call(func=Attribute(value=Attribute(value=Name(id='os', ctx=Load()), attr='environ', ctx=Load()), attr='get', ctx=Load()), args=[Constant(value='LOG_LEVEL'), Constant(value='')]), attr='upper', ctx=Load()))"
    PATTERN_CONFIG = "Call(func=Attribute(value=Name(id='PatternConfiguration', ctx=Load()), attr='load_from_file', ctx=Load()))"
    total_weights = "BinOp(left=BinOp(left=Attribute(value=Name(id='self', ctx=Load()), attr='complexity_components_weight', ctx=Load()), op=Add(), right=Attribute(value=Name(id='self', ctx=Load()), attr='complexity_skill_level_weight', ctx=Load())), op=Add(), right=Attribute(value=Name(id='self', ctx=Load()), attr='complexity_material_diversity_weight', ctx=Load()))"
    config_dict = "DictComp(key=Name(id='k', ctx=Load()), value=Name(id='v', ctx=Load()), generators=[comprehension(target=Tuple(elts=[Name(id='k', ctx=Store()), Name(id='v', ctx=Store())], ctx=Store()), iter=Call(func=Attribute(value=Attribute(value=Name(id='self', ctx=Load()), attr='__dict__', ctx=Load()), attr='items', ctx=Load())), ifs=[UnaryOp(op=Not(), operand=Call(func=Attribute(value=Name(id='k', ctx=Load()), attr='startswith', ctx=Load()), args=[Constant(value='_')]))], is_async=0)])"
    config_data = "Call(func=Attribute(value=Name(id='json', ctx=Load()), attr='load', ctx=Load()), args=[Name(id='config_file', ctx=Load())])"
    APP_NAME = "Store Management System"
    APP_VERSION = "0.1.0"
    APP_DESCRIPTION = "Inventory and Project Management Application"
    __all__ = "List(elts=[Constant(value='APP_NAME'), Constant(value='APP_VERSION'), Constant(value='APP_DESCRIPTION'), Constant(value='DATABASE_CONFIG'), Constant(value='LOGGING_CONFIG'), Constant(value='ENVIRONMENT_CONFIG'), Constant(value='FEATURE_FLAGS'), Constant(value='PERFORMANCE_CONFIG'), Constant(value='get_database_path'), Constant(value='get_log_path'), Constant(value='get_backup_path'), Constant(value='get_config_path')], ctx=Load())"
    current_file = (
        "Call(func=Name(id='Path', ctx=Load()), args=[Name(id='__file__', ctx=Load())])"
    )
    project_root = "Call(func=Name(id='_find_project_root', ctx=Load()))"
    db_dir = "BinOp(left=Name(id='project_root', ctx=Load()), op=Div(), right=Constant(value='data'))"
    log_dir = "BinOp(left=Name(id='project_root', ctx=Load()), op=Div(), right=Constant(value='logs'))"
    backup_dir = "BinOp(left=Name(id='project_root', ctx=Load()), op=Div(), right=Constant(value='backups'))"