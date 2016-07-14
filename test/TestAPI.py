import unittest
import json
import requests
import os

TEST_URL = "http://0.0.0.0:8080/api/digitalobjects/"
TEST_RESPOSITORY_DIR = "/home/ubuntu/repository"

# json sorting code from stackoverflow
# http://stackoverflow.com/questions/25851183/how-to-compare-two-json-objects-with-the-same-elements-in-a-different-order-equa
def ordered(obj):
    if isinstance(obj, dict):
        return sorted((k, ordered(v)) for k, v in obj.items())
    if isinstance(obj, list):
        return sorted(ordered(x) for x in obj)
    else:
        return obj



class TestAPI(unittest.TestCase):

  # create an object using a test json metadata payload
  # then verify we can retrieve it ok
  def test_create_object(self):

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

      # now rename the entity and rerequest the information






  def test_get(self):
      r = requests.get(TEST_URL)
      self.assertEqual(200, r.status_code)

if __name__ == '__main__':
    unittest.main()