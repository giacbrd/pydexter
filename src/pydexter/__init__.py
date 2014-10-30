# Copyright 2014 Giacomo Berardi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

__author__ = 'Giacomo Berardi <barnets@gmail.com>'

import requests, re, sys
from requests.exceptions import InvalidURL, HTTPError
from operator import itemgetter

# All the Dexter API calls start with
REST = "/rest/"

# Django regex for url validation
url_regex = re.compile(
    r'^(?:http)s?://' # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
    r'localhost|' # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|' # ...or ipv4
    r'\[?[A-F0-9]*:[A-F0-9:]+\]?)' # ...or ipv6
    r'(?::\d+)?' # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def structure_annotations(annotations):
    """Processes the response of the API call annotate.
    Returns a list with a partitioning of the text,
    in which the annotations are represented by tuples (``mention'', ``entity name'')"""
    text = annotations["document"]["fields"]["body"]["value"]
    spots = annotations["spots"]
    result = []
    prev_end = 0
    #FIXME avoid sorting?
    spots = sorted(spots, key=itemgetter("start"))
    for spot in spots:
        start = spot["start"]
        if start != prev_end:
            result.append(text[prev_end:start])
        prev_end = spot["end"]
        result.append((text[start:prev_end], spot["wikiname"]))
    if prev_end <= len(text):
        result.append(text[prev_end:])
    return result


class DexterClient:
    """A connection to a Dexter REST API server"""

    def __init__(self, url, default_params={"lp":0}):
        self.url = url.rstrip("/") + REST
        if url_regex.match(self.url) is None:
            raise InvalidURL("Malformed url: " + self.url)
        self.req = requests.Session()
        self.default_params = default_params

    def get_id(self, entity_title):
        """Returns the ID of an entity"""
        return self.__request("get-id", {"title": entity_title})["id"]

    def annotate(self, text, wikiname=False, min_conf=0.5, max_spots=50):
        """Annotate a document with Wikipedia entities"""
        return self.__request("annotate", {"text": text, "wn": wikiname, "min-conf": min_conf, "n": max_spots}, is_post=False)

    def nice_annotate(self, text, min_conf=0.5):
        """Returns a list with a partitioning of the text,
        in which the annotations are represented by tuples (``mention'', ``entity name'')"""
        return structure_annotations(self.annotate(text, wikiname=True, min_conf=min_conf))

    def spot(self, text, wikiname=False):
        """Detects all the mentions that could refer to an entity in the text"""
        return self.__request("spot", {"text": text, "wn": wikiname}, is_post=True)["spots"]

    def get_spots(self, entity, wikiname=False):
        """Provides all the spots that could refer to the given entity"""
        return self.__simple_request("get-spots", entity, wikiname)["spots"]

    def get_desc(self, entity, title_only=False):
        """Provides the description of an entity"""
        entity_id = self.__resolve_id(entity)
        return self.__request("get-desc", {"id": entity_id, "title-only": title_only})

    def get_candidates(self, query, max_candidates=10):
        """Given a query, returns a list of candidates entities represented by the query"""
        return self.__request("get-candidates", {"query": query, "n": max_candidates})

    def relatedness(self, entity1, entity2, rel_measure="milnewitten", wikiname=False):
        """Return the semantic relatedness between two entities"""
        entity_id1 = self.__resolve_id(entity1)
        entity_id2 = self.__resolve_id(entity2)
        return self.__request("relatedness", {"e1": entity_id1, "e2": entity_id2, "rel": rel_measure, "wn": wikiname})

    #TODO def spot_relatedness

    def get_target_entities(self, entity, wikiname=False):
        """Given an entity, returns the entities linked by given entity"""
        return self.__simple_request("get-target-entities", entity, wikiname)["outcomingEntities"]

    def get_source_entities(self, entity, wikiname=False):
        """Given an entity, returns the entities that link to the given entity"""
        return self.__simple_request("get-source-entities", entity, wikiname)["incomingEntities"]

    def get_entity_categories(self, entity, wikiname=False):
        """Given an entity, returns its categories"""
        return self.__simple_request("get-entity-categories", entity, wikiname)["parentCategories"]

    def get_belonging_entities(self, category, wikiname=False):
        """Given a category, returns the entities that belong to the category"""
        return self.__simple_request("get-belonging-entities", category, wikiname)["outcomingEntities"]

    def get_parent_categories(self, category, wikiname=False):
        """Given a category, returns its parent categories"""
        return self.__simple_request("get-parent-categories", category, wikiname)["parentCategories"]

    def get_child_categories(self, category, wikiname=False):
        """Given a category, returns its child categories"""
        return self.__simple_request("get-child-categories", category, wikiname)["childCategories"]

    def __resolve_id(self, entity):
        """Returns the id of an entity (if it not already a entity/category id)"""
        if isinstance(entity, (int, long)):
            return entity
        else:
            return self.get_id(entity)

    def __simple_request(self, command, arg, wikiname):
        """Shortcut for requests with the only entity/category id as argument"""
        arg_id = self.__resolve_id(arg)
        return self.__request(command, {"id": arg_id, "wn": wikiname})

    def __request(self, path, params, is_post=False):
        """Core method which executes the request http connection"""
        params.update(self.default_params)
        result = None
        reqUrl = self.url + path
        if is_post:
            result = self.req.post(reqUrl, data=params)
        else:
            result = self.req.get(reqUrl, params=params)
        if result.status_code != requests.codes.ok:
            raise HTTPError("HTTP error for " + reqUrl + " (status code " + str(result.status_code) + "):\n\n" + result.text)
        result = result.json()
        if "error" in result and len(result) == 1:
            # This is probably never reached
            raise Exception("Dexter error for " + reqUrl + ": " + result["error"])
        return result


if __name__ == "__main__":
    dxtr = DexterClient(sys.argv[1])
    import pprint
    pp = pprint.PrettyPrinter()
    pp.pprint(dxtr.nice_annotate("Dexter is an American television drama.", min_conf=0.8))
