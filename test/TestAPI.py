import unittest
import json
import requests
import os, shutil

TEST_URL = "http://0.0.0.0:8080/api/digitalobjects/"
TEST_REPOSITORY_DIR = "/home/ubuntu/repository"

# json sorting code from stackoverflow
# http://stackoverflow.com/questions/25851183/how-to-compare-two-json-objects-with-the-same-elements-in-a-different-order-equa
def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj

# clear the repository, ie nuke everything
def clear_repository():
    for f in os.listdir(TEST_REPOSITORY_DIR):
        file_path = os.path.join(TEST_REPOSITORY_DIR, f)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
           print(e)



class TestAPI(unittest.TestCase):

  # create an object using a test json metadata payload
  # then verify we can retrieve it ok
  def test_create_object(self):

      clear_repository()

      objectid = None
      with open("../metadata.json") as f:
           metadata = json.load(f)
           r = requests.post(TEST_URL, json=metadata )
           self.assertEqual(200, r.status_code)
           objectcontent = r.json()
           objectid = objectcontent['id']

           # now try and request the object information
           r = requests.get(TEST_URL + objectid)
           self.assertEqual(200, r.status_code)
           retrievedObject = r.json()
           self.assertEqual(objectid, retrievedObject['id'])

           # compare the returned metadata
           self.assertEqual(sorted(metadata), sorted(retrievedObject['metadata']))

      # add an entity, check the returned filesize matches
      entity_size = os.path.getsize('../entity.txt')
      files = {'entity_data': ('entity.txt', open('../entity.txt', 'rb'), 'application/file', {'Expires': '0'})}
      r = requests.post(TEST_URL + objectid + "/entities", files=files)
      self.assertEqual(200, r.status_code)
      entitycontent = r.json()
      self.assertEqual("entity.txt", entitycontent['filename'])
      self.assertEqual(entity_size, entitycontent['entity_length'])

      # check we can retrieve the entity file
      print (TEST_URL + objectid + "/entities/" + entitycontent['id'])
      r = requests.get(TEST_URL + objectid + "/entities/" + entitycontent['id'] )
      self.assertEqual(200, r.status_code)

      # entity filename should be in Content-Disposition header
      content_disposition = r.headers.get("Content-Disposition")
      self.assertEqual(content_disposition, 'attachment; filename=entity.txt')

      # compare the content with the original file
      with open('../entity.txt', 'rb') as myfile:
         data=myfile.read()
         self.assertEqual(data, r.content)

      # rename the entity file
      payload = {'filename':'modified-filename.txt'}
      r = requests.patch(TEST_URL + objectid + "/entities/" + entitycontent['id'], params=payload)
      self.assertEqual(r.status_code, 200)

      # retrieve the file again and check the name has changed but the contents haven't
      r = requests.get(TEST_URL + objectid + "/entities/" + entitycontent['id'] )
      self.assertEqual(200, r.status_code)

      # entity filename should be in Content-Disposition header
      content_disposition = r.headers.get("Content-Disposition")
      self.assertEqual(content_disposition, 'attachment; filename=modified-filename.txt')

      # delete the entity. subsequent calls to access the entity should give a 404 not found error
      r = requests.delete(TEST_URL + objectid + "/entities/" + entitycontent['id'])
      self.assertEqual(200, r.status_code)
      r = requests.get(TEST_URL + objectid + "/entities/" + entitycontent['id'])
      self.assertEqual(404, r.status_code)

      # as a final check, make sure we can still get the object details
      r = requests.get(TEST_URL + objectid)
      self.assertEqual(200, r.status_code)
      retrievedObject = r.json()
      self.assertEqual(objectid, retrievedObject['id'])

      # compare the returned metadata
      self.assertEqual(sorted(metadata), sorted(retrievedObject['metadata']))


  def test_get(self):
      r = requests.get(TEST_URL)
      self.assertEqual(200, r.status_code)

if __name__ == '__main__':
    unittest.main()