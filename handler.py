'''
This module contains a Handler class, meant for organizing
and loading collections of various tags and various TagDefs.

Handlers are meant to organize large quantities of different types of
tags which all reside in the same 'tagsdir' root folder. A Handler
contains methods for indexing all valid tags within its tagsdir,
loading all indexed tags, writing all loaded tags back to their files,
and resetting the tags or individual def_id collections to empty.

Handlers contain a basic log creation function for logging successes
and failures when serializing tags. This function can also os.rename()
all temp files generated during the save operation to their non-temp
filenames and logs all errors encountered while trying to os.rename()
these files and backup old files.
'''
import os
import sys

from datetime import datetime
from importlib import import_module
from os.path import dirname, split, splitext, join, isfile, relpath
from traceback import format_exc
from types import ModuleType

from supyr_struct.tag import Tag
from supyr_struct.defs.tag_def import TagDef

# make sure the new constants are injected and used
from binilla.constants import *
from binilla.util import *


######################################################
# MUCH OF THE BELOW CODE HAS NOT BEEN MODIFIED IN A  #
# LONG TIME, AND WILL BE COMPLETELY REDONE TO BRING  #
# IT TO THE QUALITY LEVEL OF THE REST OF THE LIBRARY #
######################################################


class Handler():
    '''
    A class for organizing and loading collections of tags of various def_ids.

    Handlers are meant to organize large quantities of different types of
    tags which all reside in the same 'tagsdir' root folder. This class
    contains methods for indexing all valid tags within self.tagsdir,
    loading all indexed tags, and writing all loaded tags back to their files.

    Handlers contain a basic log creation function for logging
    successes and failures when saving tags. This function can also
    os.rename all temp files generated during the save operation to
    their non-temp filenames and logs all errors encountered while
    trying to os.rename these files and backup old files.

    Tags saved through a Handler are not saved to the Tag.filepath string,
    but rather to self.tagsdir + filepath where filepath is the key that
    the Tag is under in self.tags[def_id].

    Instance properties:
        dict:
            tags
            id_ext_map ------ maps each def_id(key) to its extension(value)
        int:
            rename_tries
            debug
            tags_indexed
            tags_loaded
        bool:
            allow_corrupt
            check_extension
            write_as_temp
            backup
        str:
            current_tag ----- the filepath of the current tag that this
                              Handler is indexing/loading/writing.
            log_filename
            tagsdir

    Read this classes __init__.__doc__ for descriptions of these properties.
    '''

    frozen_imp_paths = ()

    # whether or not the case of the path that a tag is keyed by matters.
    # If False, all paths will be converted to lowercase
    # when being stored, retrieved, and deleted
    case_sensitive = True

    # whether or not the path that a tag is keyed by is relative
    # to self.tagsdir, where os.path.join(self.tagsdir, path)
    # can be used to obtain the absolute path to the tag.
    tagsdir_relative = False

    log_filename = 'log.log'
    default_import_rootpath = "supyr_struct"
    default_defs_path = "supyr_struct.defs"

    tagsdir = "%s%stags%s" % (
        dirname(os.path.abspath(os.curdir)), PATHDIV, PATHDIV)

    def __init__(self, **kwargs):
        '''
        Initializes a Handler with the supplied keyword arguments.

        Keyword arguments:

        # bool
        allow_corrupt ---- Enables returning corrupt tags rather than discard
                           them and reporting the exception. Instead, the
                           exception will be printed to the console and the tag
                           will be returned like normal. For debug use only.
        check_extension -- Whether or not(when indexing tags) to make sure a
                           tag's extension also matches the extension for that
                           def_id. The main purpose is to prevent loading temp
                           files. This is only useful when overloading the
                           constructors 'get_def_id' function since the default
                           constructor verifies tags by their extension.
        write_as_temp ---- Whether or not to keep tags as temp files when
                           calling self.write_tags. Overridden by supplying
                           'temp' as a keyword when calling self.write_tags.
        backup ----------- Whether or not to backup a file that exists
                           with the same name as a tag that is being saved.
                           The file will be renamed with the extension
                           '.backup'. If a backup already exists then
                           the oldest backup will be kept.

        # dict
        tags ------------- A dict of dicts which holds every loaded tag.
                           Nested dicts inside the tags dict each hold all of
                           one def_id of tag, with each of the tags keyed by
                           their tag path(which is relative to self.tagsdir).
                           Accessing a tag is done like so:
                               tags[def_id][filepath] = Tag

        # int
        debug ------------ The level of debugging information to show. 0 to 10.
                           The higher the number, the more information shown.
                           Currently this is of very limited use.
        rename_tries ----- The number of times that self.get_unique_filename()
                           can fail to make the 'filepath' string argument
                           unique before raising a RuntimeError. This renaming
                           process is used when calling self.extend_tags() with
                           'replace'=False to merge a collection of tags into
                           the tags of this Handler.
        tags_indexed ----- This is the number of tags that were found when
                           self.index_tags() was run.
        tags_loaded ------ This is the number of tags that were loaded when
                           self.load_tags() was run.

        # iterable
        valid_def_ids ---- Some form of iterable containing the def_id
                           strings that this Handler will be working with.
                           You may instead provide a single def_id string
                           if working with just one kind of tag.

        # str
        tagsdir ---------- A filepath string pointing to the working directory
                           which all our tags are loaded from and written to.
                           When adding a tag to tags[def_id][filepath]
                           the filepath key is the path to the tag relative to
                           this tagsdir string. So if the tagsdir
                           string were 'c:/tags/' and a tag were located in
                           'c:/tags/test/a.tag', filepath would be 'test/a.tag'
        log_filename ----- The name of the file all logs will be written to.
                           The file will be created in the tagsdir folder
                           if it doesn't exist. If it does exist, the file will
                           be opened and any log writes will be appended to it.
        '''

        # this is the filepath to the tag currently being constructed
        self.current_tag = ''
        self.tags_indexed = self.tags_loaded = 0
        self.tags = {}

        self.import_rootpath = ''
        self.defs_filepath = ''
        self.defs_path = ''
        self.id_ext_map = {}
        self.defs = {}

        # valid_def_ids will determine which tag types are possible to load
        if isinstance(kwargs.get("valid_def_ids"), str):
            kwargs["valid_def_ids"] = tuple([kwargs["valid_def_ids"]])

        self.debug = kwargs.pop("debug", 0)
        self.rename_tries = kwargs.pop("rename_tries", sys.getrecursionlimit())
        self.log_filename = kwargs.pop("log_filename", self.log_filename)
        self.backup = bool(kwargs.pop("backup", True))
        self.int_test = bool(kwargs.pop("int_test", True))
        self.allow_corrupt = bool(kwargs.pop("allow_corrupt", False))
        self.write_as_temp = bool(kwargs.pop("write_as_temp", True))
        self.check_extension = bool(kwargs.pop("check_extension", True))

        self.import_rootpath = kwargs.pop("import_rootpath",
                                          self.import_rootpath)
        self.defs_filepath = kwargs.pop("defs_filepath", self.defs_filepath)
        self.defs_path = kwargs.pop("defs_path", self.defs_path)

        self.tagsdir = sanitize_path(kwargs.pop("tagsdir", self.tagsdir))
        self.tags = kwargs.pop("tags", self.tags)

        # make sure there is an ending folder slash on the tags directory
        if len(self.tagsdir) and not self.tagsdir.endswith(PATHDIV):
            self.tagsdir += PATHDIV

        if kwargs.get("reload_defs", True):
            self.reload_defs(**kwargs)
        elif kwargs.get("defs"):
            defs = kwargs["defs"]
            if isinstance(defs, dict):
                defs = defs.values()
            for tagdef in defs:
                self.add_def(tagdef)

        # make slots in self.tags for the types we want to load
        if kwargs.get("reset_tags", True):
            self.reset_tags(self.defs.keys())

    def add_def(self, tagdefs):
        '''docstring'''
        if isinstance(tagdefs, TagDef):
            # a TagDef was provided. nothing to do
            pass
        elif isinstance(tagdefs, type) and issubclass(tagdefs, TagDef):
            # a TagDef class was provided
            tagdefs = tagdef()
        elif not isinstance(tagdefs, ModuleType):
            # no idea what was provided, but we dont care. ERROR!
            raise TypeError("Incorrect type for the provided 'tagdef'.\n" +
                            "Expected %s, %s, or %s, but got %s" %
                            (type(TagDef), type, ModuleType, type(tagdefs)))
        elif hasattr(tagdefs, "get"):
            # a whole module was provided
            tagdefs = tagdefs.get()
        else:
            # a whole module was provided without a get function
            raise AttributeError(
                "The provided module does not have a 'get' " +
                "method to get the TagDef class or instance.")

        ###########################################
        # FIX THIS SO YOU CAN PROVIDE ITERABLES OF TAGDEFS
        ###########################################

        if not hasattr(tagdefs, '__iter__'):
            tagdefs = (tagdefs,)

        for tagdef in tagdefs:
            self.defs[tagdef.def_id] = tagdef
            self.id_ext_map[tagdef.def_id] = tagdef.ext
            self.tags[tagdef.def_id] = {}

        return tagdef

    def add_tag(self, tag, filepath=None):
        '''
        Adds the provided tag to this handlers tag collection.
        filepath is expected to be a relative filepath if
        self.tagsdir_relative == True
        If it isnt provided, then tag.filepath is expected to be
        an absolute filepath. If self.tagsdir_relative = True,
        tag.filepath is relative expected to be relative to self.tagsdir,
        where is_in_dir(tag.filepath, self.tagsdir) == True
        '''
        def_id = tag.def_id
        tag_coll = self.tags.get(def_id, {})

        abs_filepath = tag.filepath
        if abs_filepath:
            if not filepath and self.tagsdir_relative:
                filepath = relpath(abs_filepath, self.tagsdir)
        elif filepath:
            abs_filepath = join(self.tagsdir, filepath)
        else:
            raise ValueError("No filepath provided to index tag under")

        if not self.case_sensitive:
            filepath = filepath.lower()
            abs_filepath = abs_filepath.lower()

        tag.filepath = abs_filepath
        tag_coll[filepath] = tag
        self.tags[def_id] = tag_coll

    def build_tag(self, **kwargs):
        '''
        Builds and returns a tag object.
        This method assumes any provided filepath is NOT relative to
        this handlers tagsdir, but rather is an absolute filepath.
        '''
        def_id = kwargs.get("def_id", None)
        filepath = sanitize_path(kwargs.get("filepath", ''))
        rawdata = kwargs.get("rawdata", None)
        int_test = kwargs.get("int_test", False)
        allow_corrupt = kwargs.get("allow_corrupt", self.allow_corrupt)

        # set the current tag path so outside processes
        # have some info on what is being constructed
        self.current_tag = filepath

        if not def_id:
            def_id = self.get_def_id(filepath)
            if not def_id:
                raise LookupError('Unable to determine def_id for:' +
                                  '\n' + ' '*BPI + self.current_tag)

        tagdef = self.get_def(def_id)

        # if it could find a TagDef, then use it
        if tagdef:
            new_tag = tagdef.build(filepath=filepath, rawdata=rawdata,
                                   definition=tagdef, int_test=int_test,
                                   allow_corrupt=allow_corrupt)
            new_tag.handler = self
            return new_tag

        raise LookupError(("Unable to locate definition for " +
                           "tag type '%s' for file:\n%s'%s'") %
                          (def_id, ' '*BPI, self.current_tag))

    def clear_unloaded_tags(self):
        '''
        Goes through each def_id in self.tags and each of the
        collections in self.tags[def_id] and removes any tags
        which are indexed, but not loaded.
        '''
        tags = self.tags

        for def_id in tags:
            coll = tags[def_id]

            # need to make the collection's keys a tuple or else
            # we will run into issues after deleting any keys
            for path in tuple(coll):
                if coll[path] is None:
                    del coll[path]

        self.tally_tags()

    def delete_tag(self, *, tag=None, def_id=None, filepath=''):
        if tag is not None:
            def_id = tag.def_id
            if filepath:
                pass
            elif self.tagsdir_relative:
                filepath = relpath(tag.filepath, self.tagsdir)
            else:
                filepath = tag.filepath
        elif def_id is None:
            def_id = self.get_def_id(filepath)

        if not self.case_sensitive:
            filepath = filepath.lower()

        filepath = sanitize_path(filepath)
        if filepath in self.tags.get(def_id, ()):
            del self.tags[def_id][filepath]

    def get_def_id(self, filepath):
        if filepath.startswith('.') or '.' not in filepath:
            # an extension was provided rather than a filepath
            ext = filepath.lower()
        else:
            ext = splitext(filepath)[-1].lower()

        if ext not in self.id_ext_map.values():
            return

        for def_id in self.id_ext_map:
            if self.id_ext_map[def_id].lower() == ext:
                return def_id

    def get_def(self, def_id):
        return self.defs.get(def_id)

    def get_tag(self, filepath, def_id=None, load_unloaded=False):
        '''
        filepath is expected to be a relative filepath if
        self.tagsdir_relative == True
        '''
        if not def_id:
            def_id = self.get_def_id(filepath)

        if not def_id:
            raise LookupError('Unable to determine def_id for:' +
                              '\n' + ' '*BPI + self.current_tag)

        tag_coll = self.tags.get(def_id, {})
        if not self.case_sensitive:
            filepath = filepath.lower()

        if tag_coll.get(filepath) is not None:
            return tag_coll[filepath]
        elif load_unloaded:
            return self.load_tag(filepath, def_id)
        else:
            raise KeyError("Could not locate the specified tag.")

    def get_unique_filename(self, filepath, dest, src=(), rename_tries=0):
        '''
        Attempts to rename the string 'filepath' to a name that
        does not already exist in 'dest' or 'src'. This is done by
        incrementing a number on the end of the filepath(if it's a
        valid integer), or appending one if one doesnt already exist.

        Raises RuntimeError if 'rename_tries' is exceeded.

        Required arguments:
            filepath(str)
            dest(iterable)
        Optional arguments:
            src(iterable)
            rename_tries(int)

        src and dest are iterables which contain the filepaths to
        check against to see if the generated filename is unique.
        '''
        splitpath, ext = splitext(sanitize_path(filepath))
        newpath = splitpath

        # this is the max number of attempts to os.rename a tag
        # that the below routine will attempt. this is to
        # prevent infinite recursion, or really long stalls
        if not isinstance(rename_tries, int) or rename_tries <= 0:
            rename_tries = self.rename_tries

        # sets are MUCH faster for testing membership than lists
        src = set(src)
        dest = set(dest)

        # find the location of the last underscore
        last_us = None
        for i in range(len(splitpath)):
            if splitpath[i] == '_':
                last_us = i

        # if the stuff after the last underscore is not an
        # integer, treat it as if there is no last underscore
        try:
            i = int(splitpath[last_us+1:])
            oldpath = splitpath[:last_us] + '_'
        except Exception:
            i = 0
            oldpath = splitpath + '_'

        # increase rename_tries by the number we are starting at
        rename_tries += i

        # make sure the name doesnt already
        # exist in both src or dest
        while (newpath + ext) in dest or (newpath + ext) in src:
            newpath = oldpath + str(i)
            if i > rename_tries:
                raise RuntimeError("Maximum attempts exceeded while " +
                                   "trying to find a unique name for " +
                                   "the tag:\n    %s" % filepath)
            i += 1

        return newpath + ext

    def iter_to_collection(self, new_tags, tags=None):
        '''
        Converts an arbitrarily deep collection of
        iterables into a two level deep tags of nested
        dicts containing tags using the following structure:
        tags[def_id][filepath] = Tag

        Returns the organized tags.
        Raises TypeError if 'tags' is not a dict

        Required arguments:
            new_tags(iterable)
        Optional arguments:
            tags(dict)

        If tags is None or unsupplied, a
        new dict will be created and returned.
        Any duplicate tags in the provided 'new_tags'
        will be overwritten by the last one added.
        '''

        if tags is None:
            tags = dict()

        if not isinstance(tags, dict):
            raise TypeError("The argument 'tags' must be a dict.")

        if isinstance(new_tags, Tag):
            if new_tags.def_id not in tags:
                tags[new_tags.def_id] = dict()
            tags[new_tags.def_id][new_tags.filepath] = new_tags
        elif isinstance(new_tags, dict):
            for key in new_tags:
                self.iter_to_collection(new_tags[key], tags)
        elif hasattr(new_tags, '__iter__'):
            for element in new_tags:
                self.iter_to_collection(tags, element)

        return tags

    def reload_defs(self, **kwargs):
        """ this function is used to dynamically load and index
        all tag definitions for all valid tags. This allows
        functionality to be extended simply by creating a new
        definition and dropping it into the defs folder."""
        ######################################################
        #
        # This whole function is pretty much a mess and needs
        # to be rewritten, especially since it wont work if a
        # definitions directory is given that isnt within an
        # already loaded module.
        #
        ######################################################

        self.defs.clear()

        if not self.defs_path:
            self.defs_path = self.default_defs_path

        valid_ids = kwargs.get("valid_def_ids")
        if not hasattr(valid_ids, '__iter__'):
            valid_ids = None
        elif not valid_ids:
            return

        # get the filepath or import path to the tag definitions module
        self.defs_path = kwargs.get("defs_path", self.defs_path)
        self.import_rootpath = kwargs.get("import_rootpath",
                                          self.import_rootpath)

        # if the defs_path is an empty string, return
        if not self.defs_path:
            return

        # cut off the trailing '.' if it exists
        if self.defs_path.endswith('.'):
            self.defs_path = self.defs_path[:-1]

        # import the root definitions module to get its absolute path
        defs_module = import_module(self.defs_path)

        # try to get the absolute folder path of the defs module
        try:
            # Try to get the filepath of the module
            self.defs_filepath = split(defs_module.__file__)[0]
        except Exception:
            # If the module doesnt have an __init__.py in the folder
            # then an exception will occur trying to get '__file__'
            # in the above code. This method must be used(which I
            # think looks kinda hacky)
            self.defs_filepath = tuple(defs_module.__path__)[0]
        self.defs_filepath = sanitize_path(self.defs_filepath)

        if 'imp_paths' in kwargs:
            imp_paths = kwargs['imp_paths']
        elif is_main_frozen():
            imp_paths = self.frozen_imp_paths
        else:
            # Log the location of every python file in the defs root
            # search for possibly valid definitions in the defs folder
            imp_paths = []
            for root, directories, files in os.walk(self.defs_filepath):
                for module_path in files:
                    base, ext = splitext(module_path)

                    # do NOT use relpath here
                    fpath = root.split(self.defs_filepath)[-1]

                    # make sure the file name ends with .py and isnt already loaded
                    if ext.lower() in (".py", ".pyw") and base not in imp_paths:
                        imp_paths.append((fpath + '.' + base)\
                                         .replace(PATHDIV, '.').lstrip('.'))

        # load the defs that were found
        for mod_name in imp_paths:
            # try to import the definition module
            try:
                def_module = import_module(
                    join(self.defs_path, mod_name)\
                    .replace(PATHDIV, '.'))
            except Exception:
                def_module = None
                if self.debug >= 1:
                    print(format_exc() + "\nThe above exception occurred " +
                          "while trying to import a tag definition.\n\n")
                    continue

            # make sure this is a valid tag module by making a few checks
            if hasattr(def_module, 'get'):
                # finally, try to add the definition
                # and its constructor to the lists
                try:
                    tagdefs = def_module.get()

                    if not hasattr(tagdefs, '__iter__'):
                        tagdefs = (tagdefs,)

                    for tagdef in tagdefs:
                        try:
                            # if a def doesnt have a usable def_id, skip it
                            def_id = tagdef.def_id
                            if not bool(def_id):
                                continue

                            if def_id in self.defs:
                                raise KeyError(("The def_id '%s' already " +
                                                "exists in the loaded defs " +
                                                "dict.") % def_id)

                            # if it does though, add it to the definitions
                            if valid_ids is None or def_id in valid_ids:
                                self.add_def(tagdef)
                        except Exception:
                            if self.debug >= 3:
                                raise

                except Exception:
                    if self.debug >= 2:
                        print(format_exc() +
                              "\nThe above exception occurred " +
                              "while trying to load a tag definition.")

    def extend_tags(self, new_tags, replace=True):
        '''
        Adds all entries from new_tags to this Handlers tags.

        Required arguments:
            new_tags(iterable)
        Optional arguments:
            replace(bool)

        Replaces tags with the same name if 'replace' is True.
        Default is True

        If 'replace' is False, this function will attempt to
        os.rename conflicting tag paths. self.rename_tries is
        the max number of attempts to os.rename a tag path.
        '''

        if not hasattr(self, "tags") or not isinstance(self.tags, dict):
            self.reset_tags()

        # organize new_tags in the way the below algorithm requires
        new_tags = self.iter_to_collection(new_tags)

        # make these local for faster referencing
        get_unique_filename = self.get_unique_filename
        tags = self.tags

        for def_id in new_tags:
            if def_id not in tags:
                tags[def_id] = new_tags[def_id]
                continue

            for filepath in list(new_tags[def_id]):
                src = new_tags[def_id]
                dest = tags[def_id]

                # if this IS the same tag then just skip it
                if dest[filepath] is src[filepath]:
                    continue
                elif replace and filepath in dest:
                    dest[filepath] = src[filepath]
                elif filepath in dest:
                    newpath = get_unique_filename(filepath, dest, src)

                    dest[newpath] = src[filepath]
                    dest[newpath].filepath = newpath
                    src[newpath] = src[filepath]
                else:
                    dest[filepath] = src[filepath]

        # recount how many tags are loaded/indexed
        self.tally_tags()

    def index_tags(self, searchdir=None):
        '''
        Allocates empty dict entries in self.tags under
        the proper def_id for each tag found in self.tagsdir.

        The created dict keys are the paths of the tag relative to
        self.tagsdir and the values are set to None.

        Returns the number of tags that were found in the folder.
        '''

        self.tags_indexed = 0

        tagsdir = self.tagsdir
        if searchdir is None:
            searchdir = tagsdir

        # local references for faster access
        id_ext_get = self.id_ext_map.get
        get_def_id = self.get_def_id
        tags_get = self.tags.get
        check = self.check_extension
        
        for root, directories, files in os.walk(searchdir):
            for filename in files:
                filepath = sanitize_path(join(root, filename))
                if not self.case_sensitive:
                    filepath = filepath.lower()

                def_id = get_def_id(filepath)
                tag_coll = tags_get(def_id)
                self.current_tag = filepath

                # check that the def_id exists in self.tags and make
                # sure we either aren't validating extensions, or that
                # the files extension matches the one for that def_id.
                if (tag_coll is not None and (not check or
                    splitext(filename.lower())[-1] == id_ext_get(def_id))):
                    if self.tagsdir_relative:
                        filepath = relpath(filepath, tagsdir)

                    # if def_id is valid, create a new mapping in tags
                    # using its filepath (minus the tagsdir) as the key
                    rel_filepath, ext = splitext(filepath)

                    # make the extension lower case so it is always
                    # possible to find the file in self.tags
                    # regardless of the case of the file extension.
                    rel_filepath += ext.lower()

                    # Make sure the tag isn't already loaded
                    if rel_filepath not in tag_coll:
                        tag_coll[rel_filepath] = None
                        self.tags_indexed += 1

        # recount how many tags are loaded/indexed
        self.tally_tags()

        return self.tags_indexed

    def load_tag(self, filepath, def_id=None, **kwargs):
        '''
        Builds a tag object, adds it to the tag collection, and returns it.
        Unlike build_tag(), this filepath may or may not be relative
        to self.tagsdir. This is determined by self.tagsdir_relative
        '''
        kwargs.setdefault('allow_corrupt', self.allow_corrupt)

        abs_filepath = filepath
        if abs_filepath and self.tagsdir_relative:
            abs_filepath = join(self.tagsdir, abs_filepath)

        if not self.case_sensitive:
            filepath = filepath.lower()
            abs_filepath = abs_filepath.lower()

        new_tag = self.build_tag(filepath=abs_filepath, def_id=def_id, **kwargs)
        if new_tag:
            self.tags[new_tag.def_id][filepath] = new_tag
            return new_tag

    def load_tags(self, paths=None, **kwargs):
        '''
        Goes through each def_id in self.tags and attempts to
        load each tag that is currently indexed, but that isnt loaded.
        Each entry in self.tags is a dict where each key is a
        tag's filepath relative to self.tagsdir and the value is
        the tag itself. If the tag isn't loaded the value is None.

        If an exception occurs while constructing a tag, the offending
        tag will be removed from self.tags[def_id] and a
        formatted exception string along with the name of the offending
        tag will be printed to the console.

        Returns the number of tags that were successfully loaded.

        If 'paths' is a string, this function will try to load just
        the specified tag. If successful, the loaded tag will be returned.
        If 'paths' is an iterable, this function will try to load all
        the tags whose paths are in the iterable. Return value is normal.

        If self.allow_corrupt == True, tags will still be returned as
        successes even if they are corrupted. This is a debugging tool.
        '''

        # local references for faster access
        tagsdir = self.tagsdir
        tags = self.tags
        allow = kwargs.get('allow_corrupt', self.allow_corrupt)
        new_tag = None
        build_tag = self.build_tag

        # decide if we are loading a single tag, a collection
        # of tags, or all tags that have been indexed
        if paths is None:
            paths_coll = tags
        else:
            get_def_id = self.get_def_id
            paths_coll = {}

            if isinstance(paths, str):
                paths = (paths,)
            elif not hasattr(paths, '__iter__'):
                raise TypeError("'paths' must be either a filepath string " +
                                "or some form of iterable containing " +
                                "strings, not '%s'" % type(paths))

            # loop over each filepath and create an entry for it in paths_coll
            for filepath in paths:
                if not self.case_sensitive:
                    filepath = filepath.lower()
                # make sure each supplied filepath is relative to self.tagsdir
                filepath = relpath(filepath, tagsdir)
                def_id = get_def_id(join(tagsdir, filepath))

                if def_id is None:
                    raise LookupError(
                        "Couldn't locate def_id for:\n    " + paths)
                elif isinstance(tags.get(def_id), dict):
                    paths_coll[def_id][filepath] = None
                else:
                    paths_coll[def_id] = {filepath: None}

        # Loop over each def_id in the tag paths to load in sorted order
        for def_id in sorted(paths_coll):
            tag_coll = tags.get(def_id)

            if not isinstance(tag_coll, dict):
                tag_coll = tags[def_id] = {}

            # Loop through each filepath in coll in sorted order
            for filepath in sorted(paths_coll[def_id]):
                # only load the tag if it isnt already loaded
                if tag_coll.get(filepath) is not None:
                    continue

                self.current_tag = filepath

                # incrementing tags_loaded and decrementing tags_indexed
                # in this loop is done for reporting the loading progress
                try:
                    new_tag = build_tag(filepath=tagsdir + filepath,
                                        allow_corrupt=allow)
                    tag_coll[filepath] = new_tag
                    self.tags_loaded += 1
                except (OSError, MemoryError) as e:
                    print(format_exc())
                    print(('The above error occurred while ' +
                           'opening\\parsing:\n    %s\n    ' +
                           'Remaining unloaded tags will ' +
                           'be de-indexed and skipped\n') % filepath)
                    del tag_coll[filepath]
                    self.clear_unloaded_tags()
                    return
                except Exception:
                    print(format_exc())
                    print(('The above error encountered while ' +
                           'opening\\parsing:\n    %s\n    ' +
                           'Tag may be corrupt\n') % filepath)
                    del tag_coll[filepath]
                self.tags_indexed -= 1

        # recount how many tags are loaded/indexed
        self.tally_tags()

        return self.tags_loaded

    def reset_tags(self, def_ids=None):
        '''
        Resets the dicts of the specified Tag_IDs in self.tags.
        Raises TypeError if 'def_ids' is not an iterable or dict.

        Optional arguments:
            def_ids(iterable, dict)

        If 'def_ids' is None or unsupplied, resets the entire tags.
        '''

        if def_ids is None:
            def_ids = self.defs

        if isinstance(def_ids, dict):
            def_ids = tuple(def_ids.keys())
        elif isinstance(def_ids, str):
            def_ids = (def_ids,)
        elif not hasattr(def_ids, '__iter__'):
            raise TypeError("'def_ids' must be some form of iterable.")

        for def_id in def_ids:
            # create a dict to hold all tags of one type.
            # tags are indexed by their filepath
            self.tags[def_id] = {}

        for def_id in tuple(self.tags.keys()):
            # remove any tag collections without a corrosponding definition
            if def_id not in self.defs:
                self.tags.pop(def_id, None)

        # recount how many tags are loaded/indexed
        self.tally_tags()

    def tally_tags(self):
        '''
        Goes through each def_id in self.tags and each of the
        collections in self.tags[def_id] and counts how many
        tags are indexed and how many are loaded.

        Sets self.tags_loaded to how many loaded tags were found and
        sets self.tags_indexed to how many indexed tags were found.
        '''
        loaded = indexed = 0
        tags = self.tags

        # Recalculate how many tags are loaded and indexed
        for def_id in tags:
            coll = tags[def_id]
            for path in coll:
                if coll[path] is None:
                    indexed += 1
                else:
                    loaded += 1

        self.tags_loaded = loaded
        self.tags_indexed = indexed

    def write_tags(self, **kwargs):
        '''
        Goes through each def_id in self.tags and attempts
        to save each tag that is currently loaded.

        Any exceptions that occur while writing the tags will be converted
        to formatted strings and concatenated together along with the name
        of the offending tags into a single 'exceptions' string.

        Returns a 'statuses' dict and the 'exceptions' string.
        statuses is used with self.make_tag_write_log() to
        os.rename all temp tag files to their non-temp names, backup the
        original tags, and make a log string to write to a log file.
        The structure of the statuses dict is as follows:
        statuses[def_id][filepath] = True/False/None.

        True  = Tag was properly saved
        False = Tag could not be saved
        None  = Tag was not saved

        Optional arguments:
            print_errors(bool)
            int_test(bool)
            backup(bool)
            temp(bool)

        If 'print_errors' is True, exceptions will be printed as they occur.
        If 'int_test' is True, each tag will be quick loaded after it's written
        to test its data integrity. Quick loading means skipping rawdata.
        If 'temp' is True, each tag written will be suffixed with '.temp'
        If 'backup' is True, any tags that would be overwritten are instead
        renamed with the extension '.backup'. If a backup already exists
        then the oldest one is kept and the current file is deleted.

        Passes the 'backup', 'temp', and 'int_test' kwargs over to
        each tags serialize() method.
        '''
        print_errors = kwargs.pop('print_errors', True)
        int_test = kwargs.pop('int_test', self.int_test)
        backup = kwargs.pop('backup', self.backup)
        temp = kwargs.pop('temp', self.write_as_temp)

        statuses = {}
        exceptions = '\n\nExceptions that occurred while writing tags:\n\n'

        tagsdir = self.tagsdir

        # Loop through each def_id in self.tags in order
        for def_id in sorted(self.tags):
            coll = self.tags[def_id]
            statuses[def_id] = these_statuses = {}

            # Loop through each filepath in coll in order
            for filepath in sorted(coll):

                # only write the tag if it is loaded
                if coll[filepath] is None:
                    continue

                self.current_tag = filepath

                try:
                    coll[filepath].serialize(filepath=tagsdir + filepath,
                                             temp=temp, int_test=int_test,
                                             backup=backup)
                    these_statuses[filepath] = True
                except Exception:
                    tmp = format_exc() + ('\n\nAbove error occurred ' +
                           'while writing the tag:\n    %s\n    ' +
                           'Tag may be corrupt.\n') % filepath
                    exceptions += '\n%s\n' % tmp
                    if print_errors:
                        print(tmp)
                    these_statuses[filepath] = False

        return(statuses, exceptions)
