# -*- coding: utf-8 -*-
import os
import logging

try:
    import pymongo
    from pymongo import ReturnDocument
except ImportError:
    pymongo = None

logger = logging.getLogger(__name__)

class MongoType:
    def __init__(self, name):
        self.name = name
    def with_variant(self, *args, **kwargs):
        return self
    def __call__(self, *args, **kwargs):
        return self
    def __str__(self):
        return self.name

class MongoForeignKey:
    def __init__(self, target, **kwargs):
        self.target = target

class MongoColumn:
    def __init__(self, *args, **kwargs):
        db_name = None
        col_type = None
        if args:
            if isinstance(args[0], str):
                db_name = args[0]
                col_type = args[1] if len(args) > 1 else None
            else:
                col_type = args[0]
        self.db_name = db_name
        self.type = col_type
        self.primary_key = kwargs.get("primary_key", False)
        self.nullable = kwargs.get("nullable", True)
        self.default = kwargs.get("default", None)
        self.unique = kwargs.get("unique", False)
        self.fk_target = None
        for arg in args:
            if isinstance(arg, MongoForeignKey):
                self.fk_target = arg.target
        self.key = None # Will be set by metaclass

    def desc(self):
        return ("desc", self.key)

    def asc(self):
        return ("asc", self.key)

    def contains(self, val):
        return ("contains", self.key, val)

    def __eq__(self, other):
        return ("eq", self.key, other)

    def __ne__(self, other):
        return ("ne", self.key, other)

    def __gt__(self, other):
        return ("gt", self.key, other)

    def __lt__(self, other):
        return ("lt", self.key, other)

    def __ge__(self, other):
        return ("ge", self.key, other)

    def __le__(self, other):
        return ("le", self.key, other)

class MongoRelationship:
    def __init__(self, target_model_name, backref=None, **kwargs):
        self.target_model_name = target_model_name
        self.backref = backref
        self.name = None
        self.owner = None

    def __set_name__(self, owner, name):
        self.name = name
        self.owner = owner

    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        target_model = MongoModel._registry.get(self.target_model_name)
        if not target_model:
            raise ValueError(f"Model {self.target_model_name} not found in registry")

        # Check Scenario 1: Target model has FK pointing to owner
        fk_field = None
        for col_name, col in target_model._columns.items():
            if col.fk_target and col.fk_target.split('.')[0] == owner.__tablename__:
                fk_field = col_name
                break
        
        if fk_field:
            return target_model.query.filter_by(**{fk_field: instance.id}).all()

        # Check Scenario 2: Owner model has FK pointing to target
        fk_field = None
        for col_name, col in owner._columns.items():
            if col.fk_target and col.fk_target.split('.')[0] == target_model.__tablename__:
                fk_field = col_name
                break
                
        if fk_field:
            fk_val = getattr(instance, fk_field)
            if fk_val is None:
                return None
            return target_model.query.get(fk_val)

        return None

class MongoModelMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        is_base = (name == "MongoModel")
        
        columns = {}
        relationships = {}
        for k, v in list(attrs.items()):
            if isinstance(v, MongoColumn):
                columns[k] = v
                v.key = k
                if not v.db_name:
                    v.db_name = k
            elif isinstance(v, MongoRelationship):
                relationships[k] = v

        attrs["_columns"] = columns
        attrs["_relationships"] = relationships
        
        cls = super().__new__(mcs, name, bases, attrs)
        if not is_base:
            MongoModel._registry[name] = cls
        return cls

    @property
    def query(cls):
        return MongoQuery(cls)

class MongoModel(metaclass=MongoModelMetaclass):
    _registry = {}
    __tablename__ = None

    def __init__(self, **kwargs):
        # Set default values for columns
        for name, col in self._columns.items():
            val = col.default() if callable(col.default) else col.default
            setattr(self, name, val)
        # Set provided kwargs
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def query(self):
        return MongoQuery(self.__class__)

    def _to_dict(self):
        d = {}
        for k, col in self._columns.items():
            val = getattr(self, k, None)
            d[col.db_name] = val
        # Map primary key to _id
        if "id" in self._columns:
            d["_id"] = d.get("id")
        return d

    @classmethod
    def _from_dict(cls, d):
        if not d:
            return None
        # Map _id back to id if present
        if "_id" in d and "id" in cls._columns:
            d[cls._columns["id"].db_name] = d["_id"]
        
        # Determine the ID value for identity mapping
        id_val = None
        if "id" in cls._columns:
            id_val = d.get(cls._columns["id"].db_name)
        
        # Identity Map: Check if we already have this instance tracked in the session
        tracked_instance = None
        if MongoSQLAlchemy._instance and hasattr(MongoSQLAlchemy._instance, "session") and id_val is not None:
            for inst in MongoSQLAlchemy._instance.session._tracked:
                if isinstance(inst, cls) and getattr(inst, "id", None) == id_val:
                    tracked_instance = inst
                    break
        
        kwargs = {}
        for k, col in cls._columns.items():
            if col.db_name in d:
                kwargs[k] = d[col.db_name]
        
        if tracked_instance:
            # Update attributes on the existing instance to match latest DB state
            for k, v in kwargs.items():
                setattr(tracked_instance, k, v)
            return tracked_instance
        
        instance = cls(**kwargs)
        if MongoSQLAlchemy._instance and hasattr(MongoSQLAlchemy._instance, "session"):
            MongoSQLAlchemy._instance.session._tracked.add(instance)
        return instance

    def __getattr__(self, name):
        # Handle dynamic backref relations
        for model_name, model_cls in MongoModel._registry.items():
            for rel_name, rel in model_cls._relationships.items():
                if rel.backref == name:
                    # Find if we have an FK pointing to model_cls
                    for col_name, col in self._columns.items():
                        if col.fk_target and col.fk_target.split('.')[0] == model_cls.__tablename__:
                            fk_val = getattr(self, col_name)
                            if fk_val is None:
                                return None
                            return model_cls.query.get(fk_val)
                    # Find if model_cls has an FK pointing to us
                    for col_name, col in model_cls._columns.items():
                        if col.fk_target and col.fk_target.split('.')[0] == self.__tablename__:
                            # Returns list of model_cls items
                            return model_cls.query.filter_by(**{col_name: self.id}).all()
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

class MongoQuery:
    def __init__(self, model_class, filters=None, sort_fields=None):
        self.model_class = model_class
        self.filters = filters or {}
        self.sort_fields = sort_fields or []

    def _get_collection(self):
        if not MongoSQLAlchemy._client:
            raise RuntimeError("Database not initialized. Call init_app first.")
        db_name = MongoSQLAlchemy._db_name
        return MongoSQLAlchemy._client[db_name][self.model_class.__tablename__]

    def filter_by(self, **kwargs):
        new_filters = dict(self.filters)
        for k, v in kwargs.items():
            # Translate attribute key to db field name
            col = self.model_class._columns.get(k)
            db_key = col.db_name if col else k
            if db_key == "id":
                db_key = "_id"
            
            # Coerce integer type if needed
            if col and col.type and col.type.name == "Integer" and not isinstance(v, dict):
                try:
                    v = int(v)
                except (ValueError, TypeError):
                    pass
            
            # Coerce boolean filters to match both True/False and 1/0
            if col and col.type and col.type.name == "Boolean":
                if v in (True, 1):
                    new_filters[db_key] = {"$in": [True, 1]}
                elif v in (False, 0):
                    new_filters[db_key] = {"$in": [False, 0]}
                else:
                    new_filters[db_key] = v
            else:
                new_filters[db_key] = v
        return MongoQuery(self.model_class, new_filters, self.sort_fields)

    def filter(self, *args):
        new_filters = dict(self.filters)
        for arg in args:
            if isinstance(arg, tuple) and len(arg) == 3:
                op, key, val = arg
                col = self.model_class._columns.get(key)
                db_key = col.db_name if col else key
                if db_key == "id":
                    db_key = "_id"
                
                # Check for integer/boolean type coercion
                is_bool = col and col.type and col.type.name == "Boolean"
                is_int = col and col.type and col.type.name == "Integer"
                if is_int and not isinstance(val, dict):
                    try:
                        val = int(val)
                    except (ValueError, TypeError):
                        pass
                
                if op == "eq":
                    if is_bool:
                        if val in (True, 1):
                            new_filters[db_key] = {"$in": [True, 1]}
                        elif val in (False, 0):
                            new_filters[db_key] = {"$in": [False, 0]}
                        else:
                            new_filters[db_key] = val
                    else:
                        new_filters[db_key] = val
                elif op == "ne":
                    if is_bool:
                        if val in (True, 1):
                            new_filters[db_key] = {"$nin": [True, 1]}
                        elif val in (False, 0):
                            new_filters[db_key] = {"$nin": [False, 0]}
                        else:
                            new_filters[db_key] = {"$ne": val}
                    else:
                        new_filters[db_key] = {"$ne": val}
                elif op == "contains":
                    import re
                    new_filters[db_key] = {"$regex": re.escape(val)}
                elif op == "gt":
                    new_filters[db_key] = {"$gt": val}
                elif op == "lt":
                    new_filters[db_key] = {"$lt": val}
                elif op == "ge":
                    new_filters[db_key] = {"$gte": val}
                elif op == "le":
                    new_filters[db_key] = {"$lte": val}
            elif isinstance(arg, dict):
                new_filters.update(arg)
        return MongoQuery(self.model_class, new_filters, self.sort_fields)

    def order_by(self, *args):
        new_sort = list(self.sort_fields)
        for arg in args:
            if isinstance(arg, tuple) and len(arg) == 2:
                direction, field = arg
                col = self.model_class._columns.get(field)
                db_field = col.db_name if col else field
                if db_field == "id":
                    db_field = "_id"
                pymongo_dir = -1 if direction == "desc" else 1
                new_sort.append((db_field, pymongo_dir))
            else:
                # Fallback if raw field is passed (as string or Column object)
                field_name = arg.key if hasattr(arg, "key") else str(arg)
                if field_name == "id":
                    field_name = "_id"
                new_sort.append((field_name, 1))
        return MongoQuery(self.model_class, self.filters, new_sort)

    def first(self):
        col = self._get_collection()
        cursor = col.find(self.filters)
        if self.sort_fields:
            cursor = cursor.sort(self.sort_fields)
        doc = next(cursor, None)
        return self.model_class._from_dict(doc)

    def all(self):
        col = self._get_collection()
        cursor = col.find(self.filters)
        if self.sort_fields:
            cursor = cursor.sort(self.sort_fields)
        return [self.model_class._from_dict(doc) for doc in cursor]

    def count(self):
        col = self._get_collection()
        return col.count_documents(self.filters)

    def get(self, ident):
        col = self._get_collection()
        col_id = self.model_class._columns.get("id")
        if col_id and col_id.type and col_id.type.name == "Integer" and ident is not None:
            try:
                ident = int(ident)
            except (ValueError, TypeError):
                pass
        doc = col.find_one({"_id": ident})
        return self.model_class._from_dict(doc)

    def get_or_404(self, ident):
        from flask import abort
        res = self.get(ident)
        if res is None:
            abort(404)
        return res

    def update(self, dict_values):
        col = self._get_collection()
        # Translate keys
        db_values = {}
        for k, v in dict_values.items():
            mcol = self.model_class._columns.get(k)
            db_key = mcol.db_name if mcol else k
            db_values[db_key] = v
        
        res = col.update_many(self.filters, {"$set": db_values})
        return res.modified_count

class MongoSession:
    def __init__(self):
        self._pending_add = set()
        self._pending_delete = set()
        self._tracked = set()

    def init_app(self, app):
        pass

    def remove(self):
        self._pending_add.clear()
        self._pending_delete.clear()
        self._tracked.clear()

    def rollback(self):
        self._pending_add.clear()
        self._pending_delete.clear()
        self._tracked.clear()

    def create_all(self):
        pass

    def add(self, instance):
        self._pending_add.add(instance)
        self._pending_delete.discard(instance)

    def delete(self, instance):
        self._pending_delete.add(instance)
        self._pending_add.discard(instance)

    def get(self, model_class, ident):
        return model_class.query.get(ident)

    def commit(self):
        if not MongoSQLAlchemy._client:
            raise RuntimeError("Database not initialized.")
        
        db_name = MongoSQLAlchemy._db_name
        db = MongoSQLAlchemy._client[db_name]

        # Process additions/updates
        all_to_save = self._pending_add.union(self._tracked)
        for instance in list(all_to_save):
            col_name = instance.__tablename__
            col = db[col_name]
            
            # Generate auto-increment integer ID if not set
            if getattr(instance, "id", None) is None:
                # Use counters collection
                counter_doc = db["counters"].find_one_and_update(
                    {"_id": col_name},
                    {"$inc": {"seq": 1}},
                    upsert=True,
                    return_document=ReturnDocument.AFTER
                )
                instance.id = counter_doc["seq"]

            data = instance._to_dict()
            col.replace_one({"_id": instance.id}, data, upsert=True)

        # Process deletions
        for instance in list(self._pending_delete):
            if getattr(instance, "id", None) is not None:
                col_name = instance.__tablename__
                db[col_name].delete_one({"_id": instance.id})

        self._pending_add.clear()
        self._pending_delete.clear()
        self._tracked.clear()

    def rollback(self):
        self._pending_add.clear()
        self._pending_delete.clear()

    def execute(self, statement, *args, **kwargs):
        # Raw SQL execute no-op for MongoDB migrations
        logger.warning(f"Ignored raw SQL execution on MongoDB compatibility layer: {statement}")
        class MockResult:
            def all(self): return []
            def first(self): return None
        return MockResult()

class MongoSQLAlchemy:
    _client = None
    _db_name = "giao_trinh_ai"
    _instance = None

    def __init__(self):
        if pymongo is None:
            raise ImportError(
                "Thư viện 'pymongo' chưa được cài đặt. "
                "Vui lòng chạy 'pip install pymongo' để kết nối tới MongoDB."
            )
        self.Model = MongoModel
        self.Integer = MongoType("Integer")
        self.Boolean = MongoType("Boolean")
        self.DateTime = MongoType("DateTime")
        self.session = MongoSession()
        MongoSQLAlchemy._instance = self

    def get_or_404(self, model_class, ident):
        from flask import abort
        res = model_class.query.get(ident)
        if res is None:
            abort(404)
        return res

    def Column(self, *args, **kwargs):
        return MongoColumn(*args, **kwargs)

    def String(self, *args, **kwargs):
        return MongoType("String")

    def Text(self, *args, **kwargs):
        return MongoType("Text")

    def ForeignKey(self, target, **kwargs):
        return MongoForeignKey(target, **kwargs)

    def relationship(self, target_model_name, backref=None, **kwargs):
        return MongoRelationship(target_model_name, backref=backref, **kwargs)

    def text(self, sql_str):
        return sql_str

    def init_app(self, app):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/giao_trinh_ai")
        # Extract database name from URI
        parsed = pymongo.uri_parser.parse_uri(mongo_uri)
        db_name = parsed.get("database") or "giao_trinh_ai"
        
        MongoSQLAlchemy._client = pymongo.MongoClient(mongo_uri)
        MongoSQLAlchemy._db_name = db_name
        self.session.init_app(app)

    def create_all(self):
        self.session.create_all()
