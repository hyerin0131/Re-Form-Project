#############################################################################
##
##  astro-cat - JBW's super namespaces, used in various contexts throughout
##
## Copyright (C) 2015-2020 John Wainwright.  All rights reserved.
##
#############################################################################

__author__ = 'john'

from collections import defaultdict, Mapping

class NameSpace(dict):
    "a generic nested namespace or subspace, accessible via dotted-pathname indexing or nested attributes"
    
    subspace_class = None  # subspaces class, None => consed from containing space's class
    
    @classmethod
    def from_dict(cls, src, subspace_name='', structured=True,  subspace_class=None, auto_add_levels=False, properties={}, ignoreNones=False):
        "recursively builds new NameSpace from given source dict"
        result = cls(subspace_name=subspace_name, structured=structured, auto_add_levels=auto_add_levels, properties=properties)
        for k, v in src.items():
            if ignoreNones and v is None:
                continue
            def toVal(v):
                if isinstance(v, dict):
                    return cls.from_dict(v, subspace_name=k, subspace_class=subspace_class or cls.subspace_class or cls,
                                              structured=structured, auto_add_levels=auto_add_levels)
                elif isinstance(v, list):
                    return [toVal(ve) for ve in v]
                else:
                    return v
            result[k] = toVal(v)
        return result
    
    def __init__(self, subspace_name='', structured=True, auto_add_levels=False, properties={}):
        # structure namespaces unpack dotted pathname keys, unstructured don't - the latter are basic dicts with 
        #   some of the extra stuff NameSpace provides like subspace name-tracking etc.
        super(NameSpace, self).__setattr__('_structured',  structured)
        super(NameSpace, self).__setattr__('_subspace_name',  subspace_name)
        super(NameSpace, self).__setattr__('_auto_add_levels',  auto_add_levels)
        super(NameSpace, self).__setattr__('_properties',  properties)

    def set_structured(self, onOff):
        "enable/disable structured pathname interps"
        super(NameSpace, self).__setattr__('_structured', onOff)

    def set_from_dict(self, src,  subspace_class=None, structured=True, auto_add_levels=False, ignoreNones=False, replace=True):
        "recursively loads me with source dict, clearing first if replace mode"
        subspace_class = subspace_class or self.__class__.subspace_class or self.__class__
        if replace:
            self.clear()
        for k, v in src.items():
            if ignoreNones and v is None:
                continue
            if isinstance(v, dict):
                self[k] = subspace_class.from_dict(v, subspace_name=k, subspace_class=subspace_class,
                                                   structured=structured, auto_add_levels=auto_add_levels)
            else:
                self[k] = v
        return self
        
    def __getitem__(self, key):
        "access item in data dict, key can be dotted-pathname"
        if super(NameSpace, self).__getattribute__('_structured'):
            if '.' in key:
                # recursively follow path segs
                local_key, rest_of_key = key.split('.', 1)
                if local_key not in self:
                    # add missing intermediate levels if needed, constructing full subspace pathnames
                    subspace_name = (self._subspace_name + '.' if self._subspace_name else '') + local_key
                    self[local_key] = (self.__class__.subspace_class or self.__class__)(structured=super(NameSpace, self).__getattribute__('_structured'),
                                                                                        auto_add_levels=super(NameSpace, self).__getattribute__('_auto_add_levels'),
                                                                                        subspace_name=subspace_name)
                return self[local_key][rest_of_key]
            # else:
            #     try:
            #         return super(NameSpace, self).__getitem__(key)
            #     except KeyError:
            #         # add missing intermediate levels if needed, constructing full subspace pathnames
            #         subspace_name = (self._subspace_name + '.' if self._subspace_name else '') + key
            #         new_space = (self.__class__.subspace_class or self.__class__)(structured=super(NameSpace, self).__getattribute__('_structured'),
            #                                                                             auto_add_levels=super(NameSpace, self).__getattribute__('_auto_add_levels'),
            #                                                                             subspace_name=subspace_name)
            #         self[key] = new_space
            #         return new_space
        return super(NameSpace, self).__getitem__(key)

    def __setitem__(self, key, val):
        "set item in data dict. key can be a dotted-pathname, missing intermediate levels added for you"
        if super(NameSpace, self).__getattribute__('_structured') and '.' in key:
            # recursively follow path segs
            local_key, rest_of_key = key.split('.', 1)
            if local_key not in self:
                # add missing intermediate levels if needed, constructing full subspace pathnames
                subspace_name = (self._subspace_name + '.' if self._subspace_name else '') + local_key
                self[local_key] = (self.__class__.subspace_class or self.__class__)(structured=super(NameSpace, self).__getattribute__('_structured'),
                                                                                    auto_add_levels=super(NameSpace, self).__getattribute__('_auto_add_levels'),
                                                                                    subspace_name=subspace_name)
            self[local_key][rest_of_key] = val
        else:
            super(NameSpace, self).__setitem__(key, val)
        super(NameSpace, self).__setattr__('_data_dirty',  True)

    def __getattr__(self, name):
        "attribute access data dict"
        if name in self:
            return self[name]
        elif super(NameSpace, self).__getattribute__('_auto_add_levels'):
            # add missing intermediate levels if needed, constructing full subspace pathnames
            subspace_name = (self._subspace_name + '.' if self._subspace_name else '') + name
            self[name] = new_lvl = (self.__class__.subspace_class or self.__class__)(structured=super(NameSpace, self).__getattribute__('_structured'),
                                                                                    auto_add_levels=True,
                                                                                    subspace_name=subspace_name)
            return new_lvl
        else:
            raise AttributeError(name)
        
    def __setattr__(self, name, val):
        "attribute setting in data dict, will *not* add missing fileds or levels (unless enabled), use indexed access for that"
        if super(NameSpace, self).__getattribute__('_auto_add_levels') or name in self:
            self[name] = val
        else:
            super(NameSpace, self).__setattr__(name, val)
            
    def __contains__(self, key):
        try:
            self.__getitem__(key)
        except KeyError:
            return False
        return True
    
    def get(self, key, default=None):
        "soft-fail get"
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def set(self, key, val):
        # functional alias for indexed assign, typically used in cataloger rule action expressions
        self[key] = val

    def has(self, key):
        "determines if key is present and indexed value is non-null without adding intermediate structure levels"
        if super(NameSpace, self).__getattribute__('_structured') and '.' in key:
            # recursively follow path segs
            local_key, rest_of_key = key.split('.', 1)
            if not self.get(local_key):
                return False
            else:
                return self[local_key].has(rest_of_key)
        else:
            return bool(self.get(key))
            
    def walk(self, full_pathname=False, subspace=None, recurse=True, leaf_subspaces=[]):
        "a generator over the tree of leaf objects in me (or subspace if supplied), returning (pathname, val) tuples for each leaf value"
        def _children(ns, prefix=''):
            my_prefix = prefix + '.' if prefix else ''
            for k, v in ns.items():
                if recurse and isinstance(v, NameSpace) and k not in leaf_subspaces:
                    for ck, v in _children(v, my_prefix + k):
                        yield ck, v
                else:
                    yield my_prefix + k, v
        walk_space = subspace if subspace != None else self
        for k, v in _children(walk_space, prefix=walk_space._subspace_name if full_pathname else ''):
            yield k, v

    def flatten(self):
        "default flatten, implemented by NestedNamespace to build a flattened single NameSpace from closest unique bindings"
        return self

    def pathname_for_key(self, key):
        "constructs full pathname for key within this space, possibly already a named subspace"
        return (self._subspace_name + '.' if self._subspace_name else '') + key

    def relative_pathname(self, pathname):
        "constructs self-relative pathname from full pathname"
        return pathname[len(self._subspace_name + '.' if self._subspace_name else ''):]

    def relative_subspacename(self):
        "constructs self-relative pathname from full pathname"
        return self._subspace_name.split('.')[-1] if self._subspace_name else ''

    def fields(self, subspace=None):
        "an iterator over the fields in (possibly-nested) obj (or given obj's subspace if supplied), returning field-pathname, val tuples"
        return self.walk(subspace=subspace)
    
    # def treeWidgetItems(self, item_class=QTreeWidgetItem, valueColumn=False,
    #                     branch_flags=Qt.ItemIsEnabled, leaf_flags=None, pathSep='.', pathPrefix='',
    #                     subspace_predicate=None, item_predicate=None, item_process=None):
    #     "return TreeWidgetItem trees selected by optional predicates"
    #     top_level_items = []
    #     #saved_items = []
    #     def _add_subspace(ss, parent, prefix):
    #         "recursable adding of subspaces"
    #         for k, v in ss.items():
    #             my_pathname = prefix + (pathSep if not prefix.endswith(pathSep) else '') + k if prefix else k
    #             is_subspace = isinstance(v, NameSpace)
    #             selected_subspace = is_subspace and (not subspace_predicate or subspace_predicate(my_pathname, v))
    #             selected_item = not is_subspace and (not item_predicate or item_predicate(my_pathname, v))
    #             if selected_subspace or selected_item:
    #                 item = item_class([k, ''])
    #                 #saved_items.append(item)
    #                 item.setData(0, ShortNameRole, k)
    #                 item.setData(0, FullPathNameRole, my_pathname)
    #                 if item_process:
    #                     item_process(item, my_pathname)
    #                 if parent:
    #                     parent.addChild(item)
    #                 else:
    #                     top_level_items.append(item)
    #                 if is_subspace:
    #                     item.setFlags(item.flags() | branch_flags)
    #                     _add_subspace(v, item, my_pathname)
    #                 else:
    #                     if leaf_flags:
    #                         item.setFlags(item.flags() | leaf_flags)
    #                     if valueColumn:
    #                         item.setData(1, Qt.DisplayRole, str(v))
    #     # add my subspaces recursively
    #     _add_subspace(self, None, pathPrefix)
    #     # returns both top-level-items and a save-list of all items to prevent GC
    #     return top_level_items #, saved_items
    
# ------ useful namespace subclasses  ------

class ReadOnlyNameSpace(NameSpace):
    """A read-only namespace."""

    # All items must be set by calling superclass methods on NameSpace

    class ReadOnlyNameSpaceError(Exception):
        pass

    def __setitem__(self, key, val):
        raise self.ReadOnlyNameSpaceError("Cannot set items in a read-only namespace")
    
class DictNamespace(dict):
    "A simple dict, no dotted pathname subspace structure"

    @classmethod
    def from_dict(cls, src, subspace_name='', **kwargs):
        "just load a new instance  from src"
        return cls(subspace_name=subspace_name).set_from_dict(src)
    
    def __init__(self, subspace_name=''):
        self._subspace_name = subspace_name
        self._structured = False
        
    def set_from_dict(self, src, **kwargs):
        "just load my dict from src"
        self.clear()
        for k, v in src.items():
            self[k] = v
        return self
    
class NestedNameSpace(NameSpace):
    "a nested namespace, used as a stacked namespace in nested code evaluations to hold frame bindings for a sequence"
    # assignment is to local space, iters similarly, lookups will failover to outer spaces
    
    def __init__(self, outer=None, **kwargs):
        super(NameSpace, self).__setattr__('_outer',  outer)
        super(NestedNameSpace, self).__init__(**kwargs)

    def __getitem__(self, key):
        "access item in data dict, key can be dotted-pathname, fail-over to outer space"
        try:
            return super(NestedNameSpace, self).__getitem__(key)
        except KeyError:
            # follow outer nestings
            outer = super(NameSpace, self).__getattribute__('_outer')

            # if key == 'urn':
            #     print('missing key', key, 'outer=', id(outer))
            #     print(outer)
                #import pdb; pdb.set_trace()

            if outer:
                # try:
                return outer[key]
                # except:
                #     if key == 'urn':
                #         import pdb; pdb.set_trace()
                #         print('missing key', key)
                #     else:
                #         raise
            else:

                raise KeyError(key)

    def get_local(self, key, default=None):
        "only look for key binding in current local namespace, no failover"
        try:
            return super(NestedNameSpace, self).__getitem__(key)
        except KeyError:
            return default

    def has_local_key(self, key):
        "an 'in' test for local namespace"
        try:
            super(NestedNameSpace, self).__getitem__(key)
        except KeyError:
            return False
        return True

    def push_frame(self):
        "enter a nesting level, return a new nesting level with self as the immediate outer frame"
        return self.__class__(outer=self,
                              structured=super(NameSpace, self).__getattribute__('_structured'),
                              subspace_name=super(NameSpace, self).__getattribute__('_subspace_name'),
                              properties=super(NameSpace, self).__getattribute__('_properties'))

    def flatten(self):
        "build a flattened single NameSpace from closest unique bindings"
        ns = self
        flat = NameSpace(structured=super(NameSpace, self).__getattribute__('_structured'))
        while ns:
            for k, v in ns.items():
                if k not in flat:
                    flat[k] = v
            ns = super(NameSpace, ns).__getattribute__('_outer')
        return flat

# ------ useful virtual subspace classes  ------

class VirtualSubspace(Mapping, NameSpace):
    "base virtual subspace"
    # provides base implementations of reqd magic methods for a mapping protocol,
    # all of which complain that subclasses need to implement
    
    class SubspaceError(Exception):
        pass
    
    def __iter__(self):
        raise self.SubspaceError("Cannot iterate subspace")
    
    def keys(self):
        raise self.SubspaceError("Cannot get subspace keys")
    
    def __contains__(self, value):
        raise self.SubspaceError("Cannot check containment in subspace")
    
    def __len__(self):
        raise self.SubspaceError("Cannot compute subspace length")
    
    def __getitem__(self, key):
        raise self.SubspaceError("Cannot get items in subspace")
    
    def __setitem__(self, key, val):
        raise self.SubspaceError("Cannot set items in subspace")
    
class PersistentSubspace(VirtualSubspace):
    "base class for subspaces that map to DBModel tables"
    # exposes the possibly-dotted name field of a persistent DBModel table as the subspace 
    # lookup by a key that turns out to be a dotted prefix to a set of records in the backing table
    # appear to return a collection of the matching records.  If a single record matches, it comes 
    # back as a singleton.  There's no cacheing yet, all accesses involve DB access.
    
    def __init__(self, model_class, subspace_name='', structured=False, prefix=''):
        super(NameSpace, self).__setattr__('_model_class', model_class)
        # may include a prefix if this is a sub-subspace within the table based on dotted entries in the name field
        super(NameSpace, self).__setattr__('prefix', prefix)
        # make this an unstructured subspace, we wan't to treat dotted device names as single literals to match names in device library tables
        super(PersistentSubspace, self).__init__(subspace_name, structured=structured)
        
    def __getitem__(self, key):
        "access model table row by name or row-subset by prefix"
        #  NOTE: no caching yet, each access is a DB access
        val = self._model_class.objects.get_by_name(self.prefix + key)
        if val != None:
            return val
        # not found, may be a partial index, so try key as dotted-name prefix search for table subspace
        prefix = self.prefix + key + '.'
        if self._model_class.objects.prefix_exists(prefix):
            return PersistentSubspace(self._model_class, prefix=prefix) 
        raise KeyError(self.prefix + key)
    
    def __contains__(self, key):
        return self._model_class.objects.name_exists(self.prefix + key)
    
    def __iter__(self):
        for name in self._model_class.objects.get_all_names_by_prefx(self.prefix, sort=True):
            yield name
    
    def __len__(self):
        return self._model_class.objects.count_by_prefix(self.prefix)
    
    # def treeWidgetItems(self, item_class=QTreeWidgetItem, branch_flags=Qt.ItemIsEnabled, leaf_flags=None):
    #     "build an item structure mapping the lexical, common-prefix dotted-name namespace suitable for giving to a QTreeViewWidget"
    #     # this builds on the fact that the main DB key is a single text field name, which have been created with dotted names
    #     # so we provide this deconstructor to help surface the implied hierarchy in the UI
    #     top_level_items = []
    #     sub_trees = {}
    #     self._saved_treeWidgetItems = []  # need this to stop GC on return to Qt caller
    #     for key, val in self.items():
    #         parent = None
    #         paths = key.split('.')
    #         for i, p in enumerate(paths[:-1]):
    #             prefix = '.'.join(paths[:i+1])
    #             if prefix in sub_trees:
    #                 parent = sub_trees[prefix]
    #             else:
    #                 sub_trees[prefix] = item = item_class([p])
    #                 self._saved_treeWidgetItems.append(item)
    #                 item.setFlags(branch_flags)
    #                 if parent:
    #                     parent.addChild(item)
    #                 else:
    #                     top_level_items.append(item)
    #                 parent = item
    #         item = item_class([paths[-1]])
    #         self._saved_treeWidgetItems.append(item)
    #         item.setData(0, DirectoryItemModel.FullPathName, self.pathname_for_key(key))
    #         if leaf_flags != None:
    #             item.setFlags(leaf_flags)
    #         if parent:
    #             parent.addChild(item)
    #         else:
    #             top_level_items.append(item)
    #     #
    #     return top_level_items
    
# ---------------  PathnameMixin -------------

class PathnameMixin(object):
    "provides namespace pathname storage & access to those objects with canonical locations in the main directory namespace"
    # several parts of the system may access (or even have lazily-constructed) certain objects at their canonical location in the 
    # main directory namespace, such as device drivers & devices, image sources, etc..  This mixin helps these objects know
    # their own pathname in the directory
    
    pass

# -------- Qt QTreeView model delegate for the main object directory (and subdirectories therein) --------
    
class ModelIndex(list):
    "python-side QModelIndex proxy that is a list so it can be easily passed back to calling C++ classes"
    # ModelIndex is [row, column, internalId]
    
    @classmethod
    def fromList(cls, index_as_list):
        return cls(*index_as_list)
    
    def __init__(self, row=-1, column=-1, internal_id=-1):  # defaults to an invalid ModelIndex
        self.extend([row, column, internal_id]) 
                     
    def isValid(self):
        return self != [-1, -1, -1]
    
    def internalId(self):
        return self[2]
    
    def row(self):
        return self[0]
    
# class DirectoryItemModelDelegate(object):
#     "Qt TreeView model delegate for the main object namespace directory"
#     # used by the C++ DirectoryItemModel to access the directoru
#
#     def __init__(self, directory):
#         self.directory = directory
#         self.rebuild()
#
#     def rebuild(self):
#         "rebuild model"
#         #  row_map is keyed by internalId, items are row-ordered vectors of child items as (id, key) pairs
#         # parent_map stores tuples of subspace & index for parents by ids
#         root_id = self.next_id = 0
#         self.row_map = defaultdict(list)
#         self.parent_map = {root_id: (self.directory, ModelIndex())}
#         for row, key in enumerate(sorted(self.directory.keys())):
#             self.row_map[root_id].append((self.alloc_id(), key))
#
#     def alloc_id(self):
#         self.next_id += 1
#         return self.next_id
#
#     def rowCount(self, index=ModelIndex()):
#         "return child row count for given item"
#         index = ModelIndex.fromList(index)
#         if index.isValid():
#             parent_id = index.internalId()
#             item_id, key = self.row_map[parent_id][index.row()]
#         else:
#             item_id, key = 0, 'root'
#         return len(self.row_map.get(item_id, []))
#
#     def columnCount(self, index=ModelIndex()):
#         "return column count, always 1 for now"
#         return 1
#
#     def index(self, row, column, parent = ModelIndex()):
#         "return modelindex for row & column in given parent"
#         # get parent entry in row_map
#         # index is row in parent, where parent ID in row_map is index's internalId()
#         parent = ModelIndex.fromList(parent)
#         if parent.isValid():
#             grand_parent_id  = parent.internalId()
#             parent_id, key = self.row_map[grand_parent_id][parent.row()]
#         else:
#             parent_id = 0  # root
#         # validate address
#         if column != 0 or row < 0 or row >= len(self.row_map[parent_id]):
#             # invalid address, return invalid index
#             return ModelIndex()
#         # create index for item, the internal ID is the index of the parent subspace entry in row_map, so that effectively row is w.r.t parent
#         index = self.createIndex(row, column, parent_id)
#         # check if addressed item is itself a subspace and add entry for it to row_map (so we lazily build out maps)
#         item_id, key = self.row_map[parent_id][row]
#         parent_space = self.parent_map[parent_id][0]
#         if parent_space._structured:
#             # if we are gettng indexes for elements in a structured namespace, load next level namespaces
#             val = parent_space[key]
#             if isinstance(val, NameSpace) and item_id not in self.parent_map:
#                 # remember susbspace & index for this parent
#                 self.parent_map[item_id] = (val, index)
#                 # and add a row_map entry for it's children
#                 for row, key in enumerate(sorted(val.keys())):
#                     self.row_map[item_id].append((self.alloc_id(), key))
#         #
#         return index
#
#     def parent(self, index):
#         "return parent index of indexed item"
#         index = ModelIndex.fromList(index)
#         parent_id = index.internalId() if index.isValid() else 0
#         # return index for parent from parent_map tuple
#         return self.parent_map[parent_id][1]
#
#     def data(self, index, role=Qt.DisplayRole):
#         "return indexed data for given role"
#         index = ModelIndex.fromList(index)
#         parent_id = index.internalId() if index.isValid() else 0
#         # grab key entry (2nd) in parent's row_map tuple for indexed item
#         key = self.row_map[parent_id][index.row()][1]
#         if role == Qt.DisplayRole:
#             # return local key as display data for now
#             return key
#         elif role == DirectoryItemModel.FullPathName:
#             # full pathname
#             return self.parent_map[parent_id][0].pathname_for_key(key)
#         else:
#             return None
#
#     def createIndex(self, row, column, internal_id):
#         return ModelIndex(row, column, internal_id)
#
#

# --------- the global interesting-object directory ---------
# a dotted namespace, mostly for user python scripts to access these objects
#