import unittest
from decisions import validate_record, invalidate

def record():
    return {'revision':1,'assumptions':[{'id':'static','claim':'no inserts','requirement':'dataset'},{'id':'access','claim':'account required','requirement':'auth'}],'decisions':[{'id':'offset','depends_on':['static'],'artifacts':['core.py']},{'id':'client','depends_on':['offset'],'artifacts':['client.py']},{'id':'guard','depends_on':['access'],'artifacts':['auth.py']}]}

class DecisionTests(unittest.TestCase):
    def test_transitive_invalidation(self):
        self.assertEqual(invalidate(record(),{'dataset'}),['client','offset'])
    def test_bad_graph_rejected(self):
        for change in ['cycle','unknown','path','duplicate','revision','empty']:
            g=record()
            if change=='cycle':g['decisions'][0]['depends_on']=['client']
            if change=='unknown':g['decisions'][0]['depends_on']=['missing']
            if change=='path':g['decisions'][0]['artifacts']=['../.env']
            if change=='duplicate':g['decisions'][0]['id']='static'
            if change=='revision':g['revision']=2
            if change=='empty':g['assumptions']=[]
            with self.subTest(change=change),self.assertRaises(ValueError):validate_record(g)
    def test_no_invalidations_for_unchanged_requirement(self):
        self.assertEqual(invalidate(record(),{'display'}),[])
