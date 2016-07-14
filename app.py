#!/usr/bin/env python3

import connexion
from flask import Response, make_response
import os
import uuid
import json
import shutil

# the parent directory where our files live
__basedir = "/home/ubuntu/repository/"

# the base url used when returning urls for new or modified objects or entities
__baseurl = "http://0.0.0.0:8080/api/digitalobjects/"


def __ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

# add an entity to an existing object
# this simply creates a new child directory for the entity and puts the file inside
def add_entity_to_object(id, entity_data):
    objectdir = os.path.join(__basedir, id)
    if not os.path.exists(objectdir):
        return "object does not exist", 404
    # just use a uuid for the entity, although a pid would be better
    entity_uuid = str(uuid.uuid4())
    entity_dir = os.path.join(objectdir, entity_uuid)
    os.makedirs(entity_dir)
    entity_path = os.path.join(entity_dir, entity_data.filename)
    entity_data.save(entity_path)
    file_length = os.path.getsize(entity_path)
    return  {"id":entity_uuid, "filename":entity_data.filename, "entity_length":file_length}, 200

# create a new digital object
# this creates a new parent directory for the object,
# and dumps the metadata into a file called .metadata
def create_digital_object(metadata):
    object_uid = uuid.uuid4()
    objectdir = os.path.join(__basedir, str(object_uid))
    os.makedirs(objectdir)
    with open( os.path.join(objectdir, ".metadata"), 'w') as outfile:
       json.dump(metadata, outfile)
    return {"id":object_uid}, 200

# delete an entity from an object
# this will remove the entity directory and any file(s) contained therein
def delete_entity(parent_id, entity_id):
    filepath = os.path.join(__basedir, parent_id)
    if not os.path.exists(filepath):
        return "object does not exist", 404
    filepath = os.path.join(filepath, entity_id)
    if not os.path.exists(filepath):
        return "entity does not exist", 404
    shutil.rmtree(filepath)
    return "Deleted", 200

# return information about the requested object
def get_digital_object(id):
    # get a count of the entities by counting the number of subdirectories
    filepath = os.path.join(__basedir, id)
    if not os.path.exists(filepath):
        return "object does not exist", 404
    count = 0
    for f in os.listdir(filepath):
        child = os.path.join(filepath, f)
        if os.path.isdir(child):
           count = count + 1
    # get the metadata file and return it as json
    with open(os.path.join(filepath, ".metadata")) as data_file:
        metadata = json.load(data_file)
    return {"id":id, "published_by":"someuser", "files count":count, "metadata": metadata }, 200

# get all the digital objects we know about;
# in our case we just traverse the parent directory and return all the child directory names
def get_digital_objects(filter = None):
    object_ids = []
    for child in os.listdir(__basedir):
        test_path = os.path.join(__basedir, child)
        if os.path.isdir(test_path):
            object_ids.append(child)
    return object_ids

# get the file for a given entity
def get_entity_file(parent_id, entity_id):
    filepath = os.path.join(__basedir, parent_id, entity_id)
    if not os.path.exists(filepath):
        return "entity does not exist", 404
    # we only expect one file in the directory, maybe a more efficient way to do this?
    for child in os.listdir(filepath):
        filename = os.path.join(filepath, child)
        if os.path.isfile(filename):
            headers = {"Content-Disposition": "attachment; filename=%s" % child}
            with open(filename, 'r') as f:
                body = f.read()
                return make_response((body, headers))
    return "Not found", 404
    
# get the entity ids for a specified object
# just lists the child directory names for the object's own directory
def get_object_entities(id, filename = None, recursive = None):
    filepath = os.path.join(__basedir, id)
    if not os.path.exists(filepath):
        return "object does not exist", 404
    entities = []
    for child in os.listdir(filepath):
        if os.path.isdir(os.path.join(filepath, child)):
            entities.append(child)   
    return entities

# rename an entity file
def rename_entity(parent_id, entity_id, filename):
    filepath = os.path.join(__basedir, parent_id, entity_id)
    for child in os.listdir(filepath):
        if os.path.isfile(os.path.join(filepath, child)):
            os.rename(os.path.join(filepath, child), os.path.join(filepath, filename))
            return filename, 200
    return "Not found", 404

def update_digital_object(id):
    return 'do some magic!'

if __name__ == '__main__':
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.add_api('swagger.yaml', arguments={'title': ''}, validate_responses=True)
    app.run(port=8080)
