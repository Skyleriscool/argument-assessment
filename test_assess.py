import copy
import io
import json
import sys
import subprocess
import unittest
from unittest.mock import patch
from assess import check_input, validate_response, prepare, main, ROOT

def fixture():
    data={'reviewed':True,'turns':[
        {'turn_id':'t1','speaker_id':'s1','speaker_label':'A','text':'Choose the park because it is free. Also walk because it saves fuel.'},
        {'turn_id':'t2','speaker_id':'s2','speaker_label':'B','text':'Hello!'},
        {'turn_id':'t3','speaker_id':'s1','speaker_label':'A','text':'Bring water because walking is thirsty work.'},
        {'turn_id':'t4','speaker_id':'s3','speaker_label':'C','text':'Choose shade because I dislike heat.'}]}
    def arg(i,text,score):
        return {'argument_id':i,'argument_excerpt':text,
            'criterion_scores':dict.fromkeys(['logic','evidence','relevance','counterargument_handling'],score),
            'overall_score':score,'score_band':None,'rationale':'Synthetic fixture.',
            'evidence':[{'quote':text,'role':'strength','criterion':'logic'}],
            'improvement_suggestion':'Explain the premise.','uncertainty':{'level':'high','reasons':['Synthetic.']}}
    response={'schema_version':'1.0','turns':[
        {'turn_id':'t1','speaker_id':'s1','status':'assessable','arguments':[arg('a1','Choose the park because it is free.',20),arg('a2','Also walk because it saves fuel.',40)]},
        {'turn_id':'t2','speaker_id':'s2','status':'not_assessable','reason':'Greeting.'},
        {'turn_id':'t3','speaker_id':'s1','status':'assessable','arguments':[arg('a3',data['turns'][2]['text'],90)]},
        {'turn_id':'t4','speaker_id':'s3','status':'assessable','arguments':[arg('a4',data['turns'][3]['text'],60)]}],
        'conversation_summary':{'key_disagreements':[], 'strongest_arguments':[
            {'speaker_id':'s1','argument_id':'a3','explanation':'Best supported.'},
            {'speaker_id':'s3','argument_id':'a4','explanation':'Only argument.'}]}}
    return data,response

class ContractTests(unittest.TestCase):
    def test_equal_argument_weight_not_turn_weight(self):
        d,r=fixture(); out=validate_response(d,r)
        self.assertEqual(out['participants'][0]['average'],50)
        self.assertIsNone(out['participants'][1]['average'])
        self.assertTrue(out['participants'][2]['limited_sample'])
    def test_arithmetic_and_neutral_counterargument(self):
        d,r=fixture();d['turns'][0]['counterargument_turn_ids']=[]
        r['turns'][0]['arguments'][0]['overall_score']=99
        out=validate_response(d,r)
        self.assertEqual(out['assessment']['turns'][0]['arguments'][0]['overall_score'],27.5)
    def test_fabricated_quote_rejected(self):
        d,r=fixture();r['turns'][0]['arguments'][0]['evidence'][0]['quote']='Invented source.'
        with self.assertRaises(ValueError):validate_response(d,r)
    def test_cross_turn_argument_rejected(self):
        d,r=fixture();r['turns'][0]['arguments'][0]['argument_excerpt']=d['turns'][2]['text']
        with self.assertRaises(ValueError):validate_response(d,r)
    def test_omission_rejected(self):
        d,r=fixture();r['turns'].pop()
        with self.assertRaises(ValueError):validate_response(d,r)
    def test_changed_speaker_rejected(self):
        d,r=fixture();r['turns'][0]['speaker_id']='s99'
        with self.assertRaises(ValueError):validate_response(d,r)
    def test_duplicate_argument_id_rejected(self):
        d,r=fixture();r['turns'][0]['arguments'][1]['argument_id']='a1'
        with self.assertRaises(ValueError):validate_response(d,r)
    def test_reviewed_groups_preserved(self):
        d,r=fixture();d['turns'][0]['argument_groups']=[d['turns'][0]['text']]
        with self.assertRaises(ValueError):validate_response(d,r)
    def test_no_review_no_assessment(self):
        d,_=fixture();d['reviewed']=False
        with self.assertRaises(ValueError):check_input(d)
    def test_over_limit_rejected(self):
        d,_=fixture();d['turns'][0]['text']='a'*4001
        with self.assertRaises(ValueError):check_input(d)
    def test_bad_summary_reference_rejected(self):
        d,r=fixture();r['conversation_summary']['strongest_arguments'][0]['argument_id']='a4'
        with self.assertRaises(ValueError):validate_response(d,r)
    def test_invalid_score_rejected(self):
        d,r=fixture();r['turns'][0]['arguments'][0]['criterion_scores']['logic']=101
        with self.assertRaises(Exception):validate_response(d,r)
    def test_parser_demands_review(self):
        self.assertFalse(prepare('A: Hello\nB: Goodbye')['reviewed'])
        with self.assertRaises(ValueError):prepare('unlabeled words')
    def test_cli_length_error_is_actionable(self):
        d,_=fixture();d['turns'][0]['text']='a'*4001
        result=subprocess.run([sys.executable,str(ROOT/'assess.py'),'assess'],input=json.dumps(d),text=True,capture_output=True)
        self.assertEqual(result.returncode,1)
        self.assertIn('shorten',result.stderr)
        self.assertEqual(result.stdout,'')
    def test_challenge_preserves_original_and_explains_changes(self):
        d,r=fixture()
        original=validate_response(d,copy.deepcopy(r))
        r['turns'][0]['arguments'][0]['criterion_scores']['logic']=60
        r['turns'][0]['arguments'][0]['rationale']='Reconsidered the logical support.'
        revised=validate_response(d,r)
        request={'input':d,'original':original,'challenge':'Please reconsider the logical support.'}
        output=io.StringIO()
        with patch('sys.argv',['assess.py','challenge']),patch('sys.stdin',io.StringIO(json.dumps(request))),patch('sys.stdout',output),patch('assess.call_model',return_value=revised):
            main()
        result=json.loads(output.getvalue())
        self.assertEqual(result['original']['assessment']['turns'][0]['arguments'][0]['overall_score'],20)
        self.assertEqual(result['revised']['assessment']['turns'][0]['arguments'][0]['overall_score'],30)
        self.assertIn('Reconsidered',result['changes'][0]['explanation'])

if __name__=='__main__':unittest.main()
